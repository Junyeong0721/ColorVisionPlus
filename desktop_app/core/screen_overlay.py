from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass

from core.color_correction import CORRECTION_MATRICES, CorrectionOptions, normalized_type


IDENTITY_5X5 = (
    1.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 1.0,
)


class MagColorEffect(ctypes.Structure):
    _fields_ = [("transform", ctypes.c_float * 25)]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def multiply_3x3(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [
            sum(left[row][i] * right[i][col] for i in range(3))
            for col in range(3)
        ]
        for row in range(3)
    ]


def saturation_matrix(amount: int) -> list[list[float]]:
    factor = clamp(1 + amount / 80, 0.2, 1.8)
    inv = 1 - factor
    r, g, b = 0.2126, 0.7152, 0.0722
    return [
        [r * inv + factor, g * inv, b * inv],
        [r * inv, g * inv + factor, b * inv],
        [r * inv, g * inv, b * inv + factor],
    ]


def correction_matrix_3x3(options: CorrectionOptions) -> list[list[float]]:
    cvd_type = normalized_type(options.cvd_type)
    identity = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    if cvd_type == "normal":
        base = identity
    else:
        raw = CORRECTION_MATRICES[cvd_type]
        base = [
            [raw[0], raw[1], raw[2]],
            [raw[4], raw[5], raw[6]],
            [raw[8], raw[9], raw[10]],
        ]

    strength = clamp(options.correction_strength, 0, 100) / 100
    blended = [
        [
            identity[row][col] * (1 - strength) + base[row][col] * strength
            for col in range(3)
        ]
        for row in range(3)
    ]

    return multiply_3x3(saturation_matrix(options.saturation_shift), blended)


def build_fullscreen_color_effect(options: CorrectionOptions) -> tuple[float, ...]:
    if normalized_type(options.cvd_type) == "normal" or options.correction_strength <= 0:
        return IDENTITY_5X5

    matrix = correction_matrix_3x3(options)
    contrast = 1 + clamp(options.contrast_boost, 0, 100) / 100 * 0.35
    brightness = clamp(options.brightness_shift, -50, 50) / 100 * 0.18
    offset = (0.5 * (1 - contrast)) + brightness

    # The Magnification API uses a row-vector color matrix. To express
    # output_channel = sum(input_channel * coefficient), store coefficients by
    # input row and output column.
    effect = [
        [matrix[0][0] * contrast, matrix[1][0] * contrast, matrix[2][0] * contrast, 0.0, 0.0],
        [matrix[0][1] * contrast, matrix[1][1] * contrast, matrix[2][1] * contrast, 0.0, 0.0],
        [matrix[0][2] * contrast, matrix[1][2] * contrast, matrix[2][2] * contrast, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [offset, offset, offset, 0.0, 1.0],
    ]
    return tuple(value for row in effect for value in row)


@dataclass
class ScreenOverlayState:
    active: bool = False
    backend: str = "windows_magnification"
    message: str = ""


class WindowsScreenColorOverlay:
    def __init__(self):
        self._mag = None
        self._initialized = False
        self.state = ScreenOverlayState()

    @property
    def is_supported(self) -> bool:
        return os.name == "nt"

    @property
    def active(self) -> bool:
        return self.state.active

    def start(self, options: CorrectionOptions) -> ScreenOverlayState:
        if not self.is_supported:
            raise RuntimeError("Windows 화면 보정 API를 사용할 수 없습니다.")

        self._load_api()

        if not self._initialized:
            if not self._mag.MagInitialize():
                raise ctypes.WinError(ctypes.get_last_error())
            self._initialized = True

        if not self._mag.MagSetFullscreenTransform(ctypes.c_float(1.0), 0, 0):
            raise ctypes.WinError(ctypes.get_last_error())

        self.apply(options)
        self.state = ScreenOverlayState(
            active=True,
            backend="windows_magnification",
            message="Windows 전체 화면 색상 필터가 켜졌습니다.",
        )
        return self.state

    def apply(self, options: CorrectionOptions) -> ScreenOverlayState:
        if not self._initialized:
            return self.state

        effect = MagColorEffect((ctypes.c_float * 25)(*build_fullscreen_color_effect(options)))
        if not self._mag.MagSetFullscreenColorEffect(ctypes.byref(effect)):
            raise ctypes.WinError(ctypes.get_last_error())
        return self.state

    def stop(self) -> ScreenOverlayState:
        if self._initialized and self._mag is not None:
            identity = MagColorEffect((ctypes.c_float * 25)(*IDENTITY_5X5))
            self._mag.MagSetFullscreenColorEffect(ctypes.byref(identity))
            self._mag.MagSetFullscreenTransform(ctypes.c_float(1.0), 0, 0)
            self._mag.MagUninitialize()

        self._initialized = False
        self.state = ScreenOverlayState(
            active=False,
            backend="windows_magnification",
            message="화면 보정이 꺼졌습니다.",
        )
        return self.state

    def _load_api(self) -> None:
        if self._mag is not None:
            return

        self._mag = ctypes.WinDLL("Magnification.dll", use_last_error=True)
        self._mag.MagInitialize.restype = ctypes.c_bool
        self._mag.MagUninitialize.restype = ctypes.c_bool
        self._mag.MagSetFullscreenTransform.argtypes = [
            ctypes.c_float,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self._mag.MagSetFullscreenTransform.restype = ctypes.c_bool
        self._mag.MagSetFullscreenColorEffect.argtypes = [ctypes.POINTER(MagColorEffect)]
        self._mag.MagSetFullscreenColorEffect.restype = ctypes.c_bool
