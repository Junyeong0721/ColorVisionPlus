from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter

from PIL import Image, ImageEnhance, ImageOps


TYPE_LABELS = {
    "normal": "일반 보기",
    "protanomaly": "적색약",
    "protanopia": "적색맹",
    "deuteranomaly": "녹색약",
    "deuteranopia": "녹색맹",
    "tritanomaly": "청색약",
    "tritanopia": "청색맹",
}


TYPE_DESCRIPTIONS = {
    "normal": "보정 없이 원본 색상을 표시합니다.",
    "protanomaly": "적색 계열 구분을 돕도록 명도와 색상 차이를 강화합니다.",
    "protanopia": "적색 계열 결손에 가까운 환경에서 구분성을 높입니다.",
    "deuteranomaly": "녹색 계열과 갈색/적색 계열의 차이를 강화합니다.",
    "deuteranopia": "녹색 계열 결손에 가까운 환경에서 구분성을 높입니다.",
    "tritanomaly": "청색/황색 계열 차이를 더 뚜렷하게 만듭니다.",
    "tritanopia": "청색 계열 결손에 가까운 환경에서 구분성을 높입니다.",
}


DEFAULT_TYPE_PRESETS = {
    "normal": {
        "correction_strength": 0,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 1.0,
    },
    "protanomaly": {
        "correction_strength": 60,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 1.0,
    },
    "protanopia": {
        "correction_strength": 72,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 0.98,
    },
    "deuteranomaly": {
        "correction_strength": 60,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 1.0,
    },
    "deuteranopia": {
        "correction_strength": 72,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 0.98,
    },
    "tritanomaly": {
        "correction_strength": 60,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 1.02,
    },
    "tritanopia": {
        "correction_strength": 70,
        "contrast_boost": 20,
        "saturation_shift": 0,
        "brightness_shift": 0,
        "gamma": 1.02,
    },
}


# Daltonization-style correction matrices.
#
# These are linear transforms derived from color-deficiency simulation matrices:
# corrected = original + remap_error * (original - simulated).
# The goal is not to make colors "normal", but to move commonly confused
# differences into channels that are easier for each CVD family to distinguish.
CORRECTION_MATRICES = {
    "protanomaly": (
        1.0, 0.0, 0.0, 0,
        0.478897, 0.476911, 0.044192, 0,
        0.597282, -0.688692, 1.091410, 0,
    ),
    "protanopia": (
        1.0, 0.0, 0.0, 0,
        0.478897, 0.476911, 0.044192, 0,
        0.597282, -0.688692, 1.091410, 0,
    ),
    "deuteranomaly": (
        1.436619, -0.631397, 0.194779, 0,
        0.0, 1.0, 0.0, 0,
        -0.184239, 0.186309, 0.997930, 0,
    ),
    "deuteranopia": (
        1.436619, -0.631397, 0.194779, 0,
        0.0, 1.0, 0.0, 0,
        -0.184239, 0.186309, 0.997930, 0,
    ),
    "tritanomaly": (
        0.741159, -0.407208, 0.666049, 0,
        0.075098, 0.585234, 0.339668, 0,
        0.0, 0.0, 1.0, 0,
    ),
    "tritanopia": (
        0.741159, -0.407208, 0.666049, 0,
        0.075098, 0.585234, 0.339668, 0,
        0.0, 0.0, 1.0, 0,
    ),
}


SIMULATION_MATRICES = {
    "normal": (
        1.0, 0.0, 0.0, 0,
        0.0, 1.0, 0.0, 0,
        0.0, 0.0, 1.0, 0,
    ),
    "protanomaly": (
        0.152286, 1.052583, -0.204868, 0,
        0.114503, 0.786281, 0.099216, 0,
        -0.003882, -0.048116, 1.051998, 0,
    ),
    "protanopia": (
        0.152286, 1.052583, -0.204868, 0,
        0.114503, 0.786281, 0.099216, 0,
        -0.003882, -0.048116, 1.051998, 0,
    ),
    "deuteranomaly": (
        0.367322, 0.860646, -0.227968, 0,
        0.280085, 0.672501, 0.047413, 0,
        -0.011820, 0.042940, 0.968881, 0,
    ),
    "deuteranopia": (
        0.367322, 0.860646, -0.227968, 0,
        0.280085, 0.672501, 0.047413, 0,
        -0.011820, 0.042940, 0.968881, 0,
    ),
    "tritanomaly": (
        1.255528, -0.076749, -0.178779, 0,
        -0.078411, 0.930809, 0.147602, 0,
        0.004733, 0.691367, 0.303900, 0,
    ),
    "tritanopia": (
        1.255528, -0.076749, -0.178779, 0,
        -0.078411, 0.930809, 0.147602, 0,
        0.004733, 0.691367, 0.303900, 0,
    ),
}


@dataclass
class CorrectionOptions:
    cvd_type: str = "normal"
    correction_strength: int = 0
    contrast_boost: int = 20
    saturation_shift: int = 0
    brightness_shift: int = 0
    gamma: float = 1.0


def clamp_number(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def normalized_type(cvd_type: str) -> str:
    return cvd_type if cvd_type in TYPE_LABELS else "normal"


def default_options_for_type(cvd_type: str) -> CorrectionOptions:
    safe_type = normalized_type(cvd_type)
    preset = DEFAULT_TYPE_PRESETS[safe_type]
    return CorrectionOptions(cvd_type=safe_type, **preset)


def make_preview(image: Image.Image, max_size: int = 520) -> Image.Image:
    preview = ImageOps.exif_transpose(image).convert("RGB")
    preview.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return preview


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    clean = hex_color.strip().lstrip("#")
    if len(clean) != 6:
        raise ValueError("HEX 색상은 6자리여야 합니다.")
    return tuple(int(clean[index:index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def simulate_cvd_hex(hex_color: str, cvd_type: str) -> str:
    safe_type = normalized_type(cvd_type)
    rgb = hex_to_rgb(hex_color)
    image = Image.new("RGB", (1, 1), rgb)
    simulated = image.convert("RGB", SIMULATION_MATRICES[safe_type])
    return rgb_to_hex(simulated.getpixel((0, 0)))


def corrected_cvd_preview_hex(hex_color: str, options: CorrectionOptions) -> str:
    rgb = hex_to_rgb(hex_color)
    image = Image.new("RGB", (1, 1), rgb)
    corrected, _metadata = apply_correction(image, options)
    simulated = corrected.convert("RGB", SIMULATION_MATRICES[normalized_type(options.cvd_type)])
    return rgb_to_hex(simulated.getpixel((0, 0)))


def color_distance(hex_a: str, hex_b: str) -> float:
    rgb_a = hex_to_rgb(hex_a)
    rgb_b = hex_to_rgb(hex_b)
    return sum((a - b) ** 2 for a, b in zip(rgb_a, rgb_b)) ** 0.5


def apply_correction(
    image: Image.Image,
    options: CorrectionOptions,
) -> tuple[Image.Image, dict]:
    start = perf_counter()
    original = ImageOps.exif_transpose(image).convert("RGB")
    safe_type = normalized_type(options.cvd_type)
    strength = int(clamp_number(options.correction_strength, 0, 100))

    if safe_type == "normal" or strength == 0:
        result = original.copy()
    else:
        matrix = CORRECTION_MATRICES[safe_type]
        transformed = original.convert("RGB", matrix)
        result = Image.blend(original, transformed, strength / 100)
        result = _apply_postprocessing(result, options)

    elapsed_ms = round((perf_counter() - start) * 1000, 1)
    metadata = {
        "processing_time_ms": elapsed_ms,
        "width": original.width,
        "height": original.height,
        "options": asdict(options),
    }
    return result, metadata


def _apply_postprocessing(
    image: Image.Image,
    options: CorrectionOptions,
) -> Image.Image:
    result = image
    contrast = clamp_number(options.contrast_boost, 0, 100)
    saturation = clamp_number(options.saturation_shift, -50, 50)
    brightness = clamp_number(options.brightness_shift, -50, 50)
    gamma = clamp_number(options.gamma, 0.5, 2.0)

    if contrast:
        result = ImageEnhance.Contrast(result).enhance(1 + (contrast / 100) * 0.7)

    if saturation:
        result = ImageEnhance.Color(result).enhance(max(0.1, 1 + saturation / 75))

    if brightness:
        result = ImageEnhance.Brightness(result).enhance(max(0.1, 1 + brightness / 100))

    if abs(gamma - 1.0) > 0.01:
        inv_gamma = 1 / gamma
        table = [
            int(clamp_number(((value / 255) ** inv_gamma) * 255, 0, 255))
            for value in range(256)
        ]
        result = result.point(table * 3)

    return result
