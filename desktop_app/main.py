import os
import sys
import ctypes

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

try:
    import pystray
except Exception:
    pystray = None

from core.color_correction import CorrectionOptions, TYPE_LABELS, default_options_for_type
from core.settings_store import SettingsStore
from core.screen_overlay import WindowsScreenColorOverlay
from views.developer_mode import DeveloperModePage
from views.intro_test import IntroTestPage
from views.settings_page import SettingsPage
from views.user_mode import UserModePage


HOME_WIDTH = 900
HOME_HEIGHT = 650
TEST_WIDTH = 1400
TEST_HEIGHT = 900
SIDEBAR_WIDTH = 250
HOTKEY_POLL_MS = 80
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_C = 0x43


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")


class ColorVisionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ColorVision+")
        self.configure(fg_color="#F8F9FA")
        self.resizable(False, False)

        self.current_frame = None
        self.current_result = None
        self.settings_store = SettingsStore()
        self.current_profile = self.settings_store.get_last_profile()
        self.current_correction_options = self.current_profile.to_options()
        self.screen_correction = ScreenCorrectionController(self, self.current_correction_options)
        self.tray_icon = AppTrayIcon(self)
        self.quick_overlay_menu = None
        self._hotkey_pressed = False
        self.sidebar = None
        self.content_host = None
        self.active_nav = "home"

        self.protocol("WM_DELETE_WINDOW", self.handle_window_close)
        self.show_main_page()
        self.tray_icon.start()
        self.poll_overlay_hotkey()

    def show_main_page(self):
        self.show_app_window()
        self._set_fixed_size(HOME_WIDTH, HOME_HEIGHT)
        self._reset_shell()
        frame = MainPage(self)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame
        self.active_nav = "home"

    def show_user_mode(self, preset_options=None):
        if preset_options is not None:
            self.set_correction_options(preset_options)
        self._show_page(UserModePage, active_nav="user", preset_options=preset_options)

    def show_developer_mode(self):
        self._show_page(DeveloperModePage, active_nav="developer")

    def show_settings_page(self):
        self._show_page(SettingsPage, active_nav="settings")

    def show_test_intro(self):
        self._show_page(IntroTestPage, active_nav="test")

    def show_frame(self, frame_class, **kwargs):
        self._show_page(frame_class, active_nav=self._nav_key_for_frame(frame_class), **kwargs)

    def _show_page(self, frame_class, active_nav=None, **kwargs):
        self.show_app_window()
        self._ensure_shell()
        self.active_nav = active_nav or self._nav_key_for_frame(frame_class)
        self.sidebar.set_active(self.active_nav)

        if self.current_frame is not None:
            self.current_frame.destroy()

        frame = frame_class(self.content_host, **kwargs)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

    def _reset_shell(self):
        for child in self.winfo_children():
            child.destroy()
        self.sidebar = None
        self.content_host = None
        self.current_frame = None
        self.grid_columnconfigure(0, weight=0, minsize=0)
        self.grid_columnconfigure(1, weight=0, minsize=0)
        self.grid_rowconfigure(0, weight=0)

    def _ensure_shell(self):
        self._set_fixed_size(TEST_WIDTH, TEST_HEIGHT)

        if self.sidebar is not None and self.content_host is not None:
            return

        for child in self.winfo_children():
            child.destroy()
        self.current_frame = None

        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = AppSidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content_host = AppContentHost(self)
        self.content_host.grid(row=0, column=1, sticky="nsew")

    def _nav_key_for_frame(self, frame_class):
        name = frame_class.__name__
        if name == "UserModePage":
            return "user"
        if name in {"IntroTestPage", "IshiharaTestPage", "ResultPage"}:
            return "test"
        if name == "DeveloperModePage":
            return "developer"
        if name == "SettingsPage":
            return "settings"
        return "home"

    def _set_fixed_size(self, width, height):
        self.minsize(1, 1)
        self.maxsize(10000, 10000)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.maxsize(width, height)

    def apply_test_result_to_user_mode(self, result):
        result_text = result.get("result", "") if isinstance(result, dict) else ""

        if "Protan" in result_text:
            preset = default_options_for_type("protanomaly")
        elif "Deutan" in result_text:
            preset = default_options_for_type("deuteranomaly")
        elif "Tritan" in result_text:
            preset = default_options_for_type("tritanomaly")
        else:
            preset = default_options_for_type("normal")

        self.set_correction_options(preset)
        self.show_user_mode(preset_options=preset)

    def handle_window_close(self):
        if self.tray_icon is not None and self.tray_icon.available:
            self.withdraw()
            self.close_quick_overlay_menu()
            return
        if self.screen_correction.active:
            self.withdraw()
            return
        self.exit_app()

    def show_app_window(self):
        if self.state() == "withdrawn":
            self.deiconify()
        self.lift()

    def exit_app(self):
        self.screen_correction.stop()
        if self.tray_icon is not None:
            self.tray_icon.stop()
        if self.quick_overlay_menu is not None and self.quick_overlay_menu.winfo_exists():
            self.quick_overlay_menu.destroy()
        self.destroy()

    def poll_overlay_hotkey(self):
        if os.name == "nt":
            is_pressed = (
                self._key_down(VK_CONTROL)
                and self._key_down(VK_MENU)
                and self._key_down(VK_C)
            )
            if is_pressed and not self._hotkey_pressed:
                self.toggle_quick_overlay_menu()
            self._hotkey_pressed = is_pressed
        self.after(HOTKEY_POLL_MS, self.poll_overlay_hotkey)

    def _key_down(self, virtual_key: int) -> bool:
        return bool(ctypes.windll.user32.GetAsyncKeyState(virtual_key) & 0x8000)

    def toggle_quick_overlay_menu(self):
        if self.quick_overlay_menu is not None and self.quick_overlay_menu.winfo_exists():
            self.quick_overlay_menu.destroy()
            self.quick_overlay_menu = None
            return

        self.quick_overlay_menu = QuickOverlayMenu(self)
        self.quick_overlay_menu.focus_force()

    def close_quick_overlay_menu(self):
        if self.quick_overlay_menu is not None and self.quick_overlay_menu.winfo_exists():
            self.quick_overlay_menu.destroy()
        self.quick_overlay_menu = None

    def reset_quick_overlay_position(self):
        self.close_quick_overlay_menu()
        self.quick_overlay_menu = QuickOverlayMenu(self)
        self.quick_overlay_menu.focus_force()

    def reset_correction_settings(self):
        self.set_correction_options(default_options_for_type(self.current_correction_options.cvd_type))

    def set_correction_options(self, options: CorrectionOptions):
        self.current_correction_options = options
        self.screen_correction.set_options(options)
        self.refresh_overlay_dependents()

    def set_correction_type(self, cvd_type: str):
        self.set_correction_options(default_options_for_type(cvd_type))

    def set_correction_strength(self, raw_value: float):
        self.current_correction_options.correction_strength = int(round(float(raw_value)))
        self.set_correction_options(self.current_correction_options)

    def toggle_screen_correction(self):
        if self.screen_correction.active:
            self.screen_correction.stop()
        else:
            self.screen_correction.start()
        self.refresh_overlay_dependents()

    def start_screen_correction(self):
        self.screen_correction.start()
        self.refresh_overlay_dependents()

    def stop_screen_correction(self):
        self.screen_correction.stop()
        self.refresh_overlay_dependents()

    def refresh_overlay_dependents(self):
        if hasattr(self.current_frame, "sync_from_app"):
            self.current_frame.sync_from_app()
        if self.quick_overlay_menu is not None and self.quick_overlay_menu.winfo_exists():
            self.quick_overlay_menu.refresh()


class ScreenCorrectionController:
    def __init__(self, app, options: CorrectionOptions):
        self.app = app
        self.options = options
        self.overlay = WindowsScreenColorOverlay()
        self.tint_overlay: ctk.CTkToplevel | None = None
        self.backend = "대기 중"
        self.message = "화면 보정이 꺼졌습니다."

    @property
    def active(self) -> bool:
        return self.overlay.active or self.tint_overlay is not None

    def set_options(self, options: CorrectionOptions):
        self.options = options
        if self.active:
            self.apply_options()

    def start(self):
        fallback_reason = ""
        try:
            state = self.overlay.start(self.options)
            self.backend = "Windows 색상 필터"
            self.message = state.message
            return
        except Exception as exc:
            fallback_reason = str(exc)

        try:
            self.start_tint_overlay()
            self.backend = "투명 오버레이"
            self.message = "Windows 전체 화면 필터를 사용할 수 없어 투명 보정 레이어로 실행했습니다."
            if fallback_reason:
                self.message = f"{self.message} ({fallback_reason})"
        except Exception:
            self.stop()
            self.backend = "대기 중"
            self.message = "현재 환경에서 화면 오버레이를 실행할 수 없습니다."

    def stop(self):
        if self.overlay.active:
            try:
                self.overlay.stop()
            except Exception:
                pass

        if self.tint_overlay is not None:
            try:
                self.tint_overlay.destroy()
            except Exception:
                pass
            self.tint_overlay = None

        self.backend = "대기 중"
        self.message = "화면 보정이 꺼졌습니다."

    def apply_options(self):
        if self.overlay.active:
            try:
                self.overlay.apply(self.options)
                self.backend = "Windows 색상 필터"
                self.message = "조절값을 현재 화면에 반영했습니다."
            except Exception:
                self.message = "화면 보정 갱신에 실패했습니다. 다시 켜 주세요."
        elif self.tint_overlay is not None:
            self.update_tint_overlay()
            self.backend = "투명 오버레이"
            self.message = "조절값을 투명 오버레이에 반영했습니다."

    def start_tint_overlay(self):
        overlay = ctk.CTkToplevel(self.app)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.configure(fg_color=self.tint_color())
        overlay.attributes("-alpha", self.tint_alpha())

        width = overlay.winfo_screenwidth()
        height = overlay.winfo_screenheight()
        overlay.geometry(f"{width}x{height}+0+0")
        overlay.update_idletasks()
        self.make_click_through(overlay)
        self.tint_overlay = overlay

    def update_tint_overlay(self):
        if self.tint_overlay is None:
            return
        self.tint_overlay.configure(fg_color=self.tint_color())
        self.tint_overlay.attributes("-alpha", self.tint_alpha())

    def tint_color(self) -> str:
        if self.options.cvd_type.startswith("protan"):
            return "#FFD166"
        if self.options.cvd_type.startswith("deuter"):
            return "#4DD0E1"
        if self.options.cvd_type.startswith("tritan"):
            return "#B56CFF"
        return "#FFFFFF"

    def tint_alpha(self) -> float:
        settings = self.app.settings_store.load_settings()
        base_opacity = float(settings.get("overlay_opacity", 0.35))
        strength = max(8, int(self.options.correction_strength)) / 100
        return max(0.04, min(0.45, base_opacity * strength))

    def make_click_through(self, window):
        if os.name != "nt":
            return
        hwnd = window.winfo_id()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            -20,
            style | 0x00080000 | 0x00000020 | 0x00000008,
        )


class QuickOverlayMenu(ctk.CTkToplevel):
    WIDTH = 360
    BG = "#171717"
    PANEL = "#202020"
    LINE = "#383838"
    TEXT = "#F8FAFC"
    MUTED = "#A3A3A3"
    GREEN = "#41B883"
    GREEN_DARK = "#27966A"
    RED = "#D94B3D"

    def __init__(self, app: ColorVisionApp):
        super().__init__(app)
        self.app = app
        self.type_buttons: dict[str, ctk.CTkButton] = {}
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=self.BG)
        self.geometry(f"{self.WIDTH}x{self.winfo_screenheight()}+0+0")
        self.bind("<Escape>", lambda _event: self.close())
        self.build_ui()
        self.refresh()

    def build_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=0)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 12))
        ctk.CTkLabel(
            header,
            text="ColorVision+",
            font=("Malgun Gothic", 17, "bold"),
            text_color=self.TEXT,
            anchor="w",
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="X",
            width=30,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#333333",
            text_color=self.MUTED,
            command=self.close,
        ).pack(side="right")

        ctk.CTkFrame(container, height=1, fg_color=self.LINE).pack(fill="x")

        body = ctk.CTkFrame(container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        self.status_label = ctk.CTkLabel(
            body,
            text="화면 보정 꺼짐",
            font=("Malgun Gothic", 24, "bold"),
            text_color=self.TEXT,
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(0, 6))

        self.message_label = ctk.CTkLabel(
            body,
            text="Ctrl + Alt + C 로 메뉴를 닫을 수 있습니다.",
            font=("Malgun Gothic", 12),
            text_color=self.MUTED,
            anchor="w",
            justify="left",
            wraplength=310,
        )
        self.message_label.pack(fill="x", pady=(0, 18))

        self.toggle_button = self.menu_button(
            body,
            "화면 보정 켜기",
            self.app.toggle_screen_correction,
            color=self.GREEN,
            hover=self.GREEN_DARK,
        )
        self.toggle_button.pack(fill="x", pady=(0, 14))

        self.section_label(body, "색각 유형")
        for cvd_type in ("protanomaly", "deuteranomaly", "tritanomaly", "normal"):
            button = self.menu_button(
                body,
                TYPE_LABELS[cvd_type],
                lambda value=cvd_type: self.app.set_correction_type(value),
                color="transparent",
                hover="#303030",
            )
            button.pack(fill="x", pady=3)
            self.type_buttons[cvd_type] = button

        self.section_label(body, "보정 강도")
        slider_box = ctk.CTkFrame(body, fg_color=self.PANEL, corner_radius=10)
        slider_box.pack(fill="x", pady=(2, 18))
        slider_box.grid_columnconfigure(0, weight=1)
        self.strength_value = ctk.CTkLabel(
            slider_box,
            text="60",
            font=("Malgun Gothic", 15, "bold"),
            text_color=self.TEXT,
        )
        self.strength_value.grid(row=0, column=1, padx=(0, 14), pady=(12, 0))
        self.strength_slider = ctk.CTkSlider(
            slider_box,
            from_=0,
            to=100,
            number_of_steps=100,
            button_color=self.GREEN,
            progress_color=self.GREEN,
            command=self.app.set_correction_strength,
        )
        self.strength_slider.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 14))

        self.section_label(body, "바로가기")
        self.menu_button(body, "사용자 모드 열기", self.open_user_mode).pack(fill="x", pady=3)
        self.menu_button(body, "색각 테스트 열기", self.open_test).pack(fill="x", pady=3)

        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 20))
        self.menu_button(
            footer,
            "앱 종료",
            self.app.exit_app,
            color="#2A1717",
            hover="#3A2020",
            text_color="#FCA5A5",
        ).pack(fill="x")

    def section_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Malgun Gothic", 12, "bold"),
            text_color=self.MUTED,
            anchor="w",
        ).pack(fill="x", pady=(14, 6))

    def menu_button(self, parent, text, command, color=None, hover=None, text_color=None):
        return ctk.CTkButton(
            parent,
            text=text,
            height=42,
            corner_radius=9,
            anchor="w",
            fg_color=color if color is not None else self.PANEL,
            hover_color=hover if hover is not None else "#303030",
            text_color=text_color if text_color is not None else self.TEXT,
            font=("Malgun Gothic", 13, "bold"),
            command=command,
        )

    def refresh(self):
        self.lift()
        options = self.app.current_correction_options
        active = self.app.screen_correction.active
        label = TYPE_LABELS.get(options.cvd_type, "일반 보기")
        self.status_label.configure(text=f"{label} 보정 {'켜짐' if active else '꺼짐'}")
        self.message_label.configure(text=self.app.screen_correction.message)
        self.toggle_button.configure(
            text="화면 보정 끄기" if active else "화면 보정 켜기",
            fg_color=self.RED if active else self.GREEN,
            hover_color="#A83A2A" if active else self.GREEN_DARK,
        )
        self.strength_value.configure(text=str(int(options.correction_strength)))
        self.strength_slider.set(int(options.correction_strength))

        active_group = options.cvd_type
        if active_group.startswith("protan"):
            active_group = "protanomaly"
        elif active_group.startswith("deuter"):
            active_group = "deuteranomaly"
        elif active_group.startswith("tritan"):
            active_group = "tritanomaly"
        else:
            active_group = "normal"

        for cvd_type, button in self.type_buttons.items():
            if cvd_type == active_group:
                button.configure(fg_color=self.GREEN, hover_color=self.GREEN_DARK, text_color="#FFFFFF")
            else:
                button.configure(fg_color="transparent", hover_color="#303030", text_color=self.TEXT)

    def open_user_mode(self):
        self.close()
        self.app.show_user_mode()

    def open_test(self):
        self.close()
        self.app.show_test_intro()

    def close(self):
        self.app.close_quick_overlay_menu()


class AppTrayIcon:
    def __init__(self, app: ColorVisionApp):
        self.app = app
        self.icon = None
        self.available = False

    def start(self):
        if os.name != "nt" or pystray is None or self.available:
            return

        self.icon = pystray.Icon(
            "ColorVisionPlus",
            self.load_image(),
            "ColorVision+",
            menu=pystray.Menu(
                pystray.MenuItem("열기", self.dispatch(self.app.show_app_window), default=True),
                pystray.MenuItem("화면 보정 켜기/끄기", self.dispatch(self.app.toggle_screen_correction)),
                pystray.MenuItem("오버레이 메뉴", self.dispatch(self.app.toggle_quick_overlay_menu)),
                pystray.MenuItem("오버레이 위치 초기화", self.dispatch(self.app.reset_quick_overlay_position)),
                pystray.MenuItem("설정 초기화", self.dispatch(self.app.reset_correction_settings)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("앱 종료", self.dispatch(self.app.exit_app)),
            ),
        )

        try:
            self.icon.run_detached()
            self.available = True
        except Exception:
            self.icon = None
            self.available = False

    def stop(self):
        if self.icon is None:
            self.available = False
            return

        try:
            self.icon.stop()
        except Exception:
            pass
        self.icon = None
        self.available = False

    def dispatch(self, command):
        def handler(icon=None, item=None):
            try:
                if self.app.winfo_exists():
                    self.app.after(0, command)
            except Exception:
                pass

        return handler

    def load_image(self):
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "logo",
            "colorvision_logo.png",
        )

        if os.path.exists(logo_path):
            try:
                with Image.open(logo_path) as logo:
                    logo = logo.convert("RGBA")
                    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
                    logo.thumbnail((size - 8, size - 8), resample)
                    offset = ((size - logo.width) // 2, (size - logo.height) // 2)
                    image.alpha_composite(logo, offset)
                    return image
            except Exception:
                pass

        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 56, 56), radius=14, fill="#2D6A4F")
        draw.ellipse((21, 21, 43, 43), fill="#FFFFFF")
        draw.text((44, 10), "+", fill="#FFFFFF")
        return image


class AppContentHost(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color="#F8FBFA")
        self.app = app

    @property
    def current_result(self):
        return self.app.current_result

    @current_result.setter
    def current_result(self, value):
        self.app.current_result = value

    @property
    def current_profile(self):
        return self.app.current_profile

    @current_profile.setter
    def current_profile(self, value):
        self.app.current_profile = value

    @property
    def settings_store(self):
        return self.app.settings_store

    @property
    def current_correction_options(self):
        return self.app.current_correction_options

    @property
    def screen_correction_backend(self):
        return self.app.screen_correction.backend

    @property
    def screen_correction_message(self):
        return self.app.screen_correction.message

    def show_main_page(self):
        self.app.show_main_page()

    def show_user_mode(self, preset_options=None):
        self.app.show_user_mode(preset_options=preset_options)

    def show_developer_mode(self):
        self.app.show_developer_mode()

    def show_test_intro(self):
        self.app.show_test_intro()

    def show_settings_page(self):
        self.app.show_settings_page()

    def show_frame(self, frame_class, **kwargs):
        self.app.show_frame(frame_class, **kwargs)

    def apply_test_result_to_user_mode(self, result):
        self.app.apply_test_result_to_user_mode(result)

    def set_correction_options(self, options):
        self.app.set_correction_options(options)

    def toggle_screen_correction(self):
        self.app.toggle_screen_correction()

    def start_screen_correction(self):
        self.app.start_screen_correction()

    def stop_screen_correction(self):
        self.app.stop_screen_correction()

    def is_screen_correction_active(self):
        return self.app.screen_correction.active

    def toggle_quick_overlay_menu(self):
        self.app.toggle_quick_overlay_menu()

    def bind_global(self, sequence, func):
        self.app.bind_all(sequence, func)

    def unbind_global(self, sequence):
        self.app.unbind_all(sequence)


class AppSidebar(ctk.CTkFrame):
    BG = "#FFFFFF"
    ACTIVE_BG = "#EAF5EE"
    HOVER_BG = "#F1F5F9"
    TEXT_ACTIVE = "#2D6A4F"
    TEXT_MAIN = "#334155"
    TEXT_SUB = "#64748B"

    def __init__(self, app):
        super().__init__(app, fg_color=self.BG, corner_radius=0, width=SIDEBAR_WIDTH)
        self.app = app
        self.items = {}
        self.icons = {}
        self.wave_image = None
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        self.icons_dir = os.path.join(self.assets_dir, "icons")
        self.load_icons()
        self.build_ui()

    def load_icons(self):
        for key, filename in {
            "home": "home.png",
            "user": "user.png",
            "test": "test.png",
            "developer": "developer.png",
            "settings": "settings.png",
            "help": "help.png",
        }.items():
            path = os.path.join(self.icons_dir, filename)
            if os.path.exists(path):
                self.icons[key] = ctk.CTkImage(Image.open(path), size=(20, 20))
            else:
                self.icons[key] = None

    def build_ui(self):
        right_border = ctk.CTkFrame(self, width=1, fg_color="#E2E8F0", corner_radius=0)
        right_border.pack(side="right", fill="y")

        ctk.CTkLabel(
            self,
            text="ColorVision+",
            font=("Malgun Gothic", 19, "bold"),
            text_color="#1F2937",
            anchor="w",
            fg_color="transparent",
        ).pack(fill="x", padx=24, pady=(28, 54))

        self.add_item("home", self.icons["home"], "홈", self.app.show_main_page)
        self.add_item("user", self.icons["user"], "사용자 모드", self.app.show_user_mode)
        self.add_item("test", self.icons["test"], "색각 유형 테스트", self.app.show_test_intro)
        self.add_item("developer", self.icons["developer"], "개발자 모드", self.app.show_developer_mode)
        self.add_item("settings", self.icons["settings"], "설정", self.app.show_settings_page)

        self.add_wave_background()

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        self.add_static_item(self.icons["help"], "도움말")

    def add_wave_background(self):
        wave_path = os.path.join(self.assets_dir, "bg_sidewave.png")
        if not os.path.exists(wave_path):
            return

        wave = Image.open(wave_path)
        self.wave_image = ctk.CTkImage(light_image=wave, dark_image=wave, size=(SIDEBAR_WIDTH, 260))
        wave_label = ctk.CTkLabel(self, image=self.wave_image, text="", fg_color="transparent")
        wave_label.place(relx=0, rely=1, anchor="sw")
        wave_label.lower()

    def add_item(self, key, icon, text, command):
        item = self.create_item(icon, text, command=command)
        item.pack(fill="x", padx=16, pady=4)
        self.items[key] = item

    def add_static_item(self, icon, text):
        item = self.create_item(icon, text, command=self.show_help)
        item.pack(fill="x", padx=16, pady=(8, 24))

    def create_item(self, icon, text, command):
        item = ctk.CTkButton(
            self,
            image=icon,
            text=f"  {text}" if icon else text,
            anchor="w",
            width=210,
            height=46,
            corner_radius=12,
            fg_color="transparent",
            hover_color=self.HOVER_BG,
            text_color=self.TEXT_MAIN,
            font=("Malgun Gothic", 14),
            command=command,
        )
        return item

    def set_active(self, active_key):
        for key, item in self.items.items():
            is_active = key == active_key
            item.configure(
                fg_color=self.ACTIVE_BG if is_active else "transparent",
                hover_color=self.ACTIVE_BG if is_active else self.HOVER_BG,
                text_color=self.TEXT_ACTIVE if is_active else self.TEXT_MAIN,
                font=("Malgun Gothic", 14, "bold" if is_active else "normal"),
            )

    def show_help(self):
        popup = ctk.CTkToplevel(self.app)
        popup.title("도움말")
        popup.geometry("360x180")
        popup.resizable(False, False)
        popup.configure(fg_color="#FFFFFF")
        ctk.CTkLabel(
            popup,
            text="도움말 기능은 준비 중입니다.",
            font=("Malgun Gothic", 15, "bold"),
            text_color=self.TEXT_MAIN,
        ).pack(expand=True)
        ctk.CTkButton(
            popup,
            text="확인",
            width=90,
            height=34,
            fg_color="#52B788",
            hover_color="#40916C",
            command=popup.destroy,
        ).pack(pady=(0, 24))


class MainPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8F9FA")
        self.parent = parent
        self.card_icon_images = []

        self.pack_propagate(False)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.main_assets_dir = os.path.join(base_dir, "assets", "main")

        background = self.build_home_background(HOME_WIDTH, HOME_HEIGHT)
        self.home_bg_image = ctk.CTkImage(
            light_image=background,
            dark_image=background,
            size=(HOME_WIDTH, HOME_HEIGHT),
        )

        self.background_label = ctk.CTkLabel(
            self,
            image=self.home_bg_image,
            text="",
        )
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        card_width = 300
        card_height = 90
        gap_x = 20
        gap_y = 20
        start_x = (HOME_WIDTH - (card_width * 2 + gap_x)) // 2
        start_y = 280

        cards = [
            ("user", "사용자 모드", "화면 보정 및 색상 필터 적용", "#E8F5E9", "#2E7D32", self.on_user_mode),
            ("developer", "개발자/디자이너 모드", "시뮬레이션 및 접근성 분석", "#E3F2FD", "#1565C0", self.on_designer_mode),
            ("test", "색각 유형 테스트", "이시하라 색각 테스트", "#F3E5F5", "#7B1FA2", self.on_test_mode),
            ("settings", "설정", "앱 설정 및 환경 구성", "#FFF8E1", "#F57F17", self.on_settings_mode),
        ]

        for index, card_data in enumerate(cards):
            row = index // 2
            col = index % 2
            x = start_x + col * (card_width + gap_x)
            y = start_y + row * (card_height + gap_y)
            self.create_menu_card(x, y, card_width, card_height, *card_data)

    def build_home_background(self, width, height):
        bg_path = os.path.join(self.main_assets_dir, "home_bg.png")
        logo_path = os.path.join(self.main_assets_dir, "home_logo.png")

        if os.path.exists(bg_path):
            image = Image.open(bg_path).convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
        else:
            image = Image.new("RGBA", (width, height), "#FBFCFD")

        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((280, 200), Image.Resampling.LANCZOS)
            logo_x = (width - logo.width) // 2
            image.paste(logo, (logo_x, 35), logo)

        draw = ImageDraw.Draw(image)
        font_title = self.load_font(36, bold=True)
        font_subtitle = self.load_font(13)
        font_english = self.load_font(11)
        font_footer = self.load_font(10)

        draw.text((width // 2, 175), "ColorVision+", fill="#1E293B", font=font_title, anchor="mm")
        draw.text((width // 2, 215), "색각 이상 사용자를 위한 맞춤형 접근성 플랫폼", fill="#475569", font=font_subtitle, anchor="mm")
        draw.text((width // 2, 235), "Making colors accessible for everyone.", fill="#64748B", font=font_english, anchor="mm")
        draw.text((width // 2, height - 20), "v0.1.0", fill="#94A3B8", font=font_footer, anchor="mm")
        return image.convert("RGB")

    def load_font(self, size, bold=False):
        font_name = "malgunbd.ttf" if bold else "malgun.ttf"
        windows_font = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_name)
        for font_path in (windows_font, font_name):
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def create_menu_card(self, x, y, width, height, icon_type, title, desc, bg_color, text_color, command):
        card = ctk.CTkFrame(
            self,
            width=width,
            height=height,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#F1F5F9",
        )
        card.place(x=x, y=y)
        card.grid_propagate(False)

        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)
        card.grid_rowconfigure(0, weight=1)

        icon_box = ctk.CTkFrame(
            card,
            fg_color=bg_color,
            width=50,
            height=50,
            corner_radius=24,
        )
        icon_box.grid(row=0, column=0, padx=(18, 12), sticky="w")
        icon_box.grid_propagate(False)

        icon_image = self.create_card_icon(icon_type, text_color)
        self.card_icon_images.append(icon_image)
        icon_label = ctk.CTkLabel(
            icon_box,
            image=icon_image,
            text="",
            width=50,
            height=50,
            anchor="center",
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew", pady=(1, 0))
        text_frame.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
            text_color="#0F172A",
            anchor="w",
        )
        title_lbl.grid(row=0, column=0, sticky="ew")

        desc_lbl = ctk.CTkLabel(
            text_frame,
            text=desc,
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            text_color="#64748B",
            anchor="w",
        )
        desc_lbl.grid(row=1, column=0, sticky="ew", pady=(1, 0))

        arrow_lbl = ctk.CTkLabel(
            card,
            text=">",
            font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"),
            text_color="#CBD5E1",
            width=24,
            anchor="center",
        )
        arrow_lbl.grid(row=0, column=2, padx=(0, 18), sticky="e")

        self._bind_click(card, command)

    def create_card_icon(self, icon_type, color):
        scale = 3
        size = 20
        canvas_size = size * scale
        image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        width = 5

        if icon_type == "user":
            draw.ellipse((20, 8, 40, 28), outline=color, width=width)
            draw.arc((8, 30, 52, 68), 200, 340, fill=color, width=width)
        elif icon_type == "developer":
            draw.line((20, 15, 8, 30, 20, 45), fill=color, width=width)
            draw.line((40, 15, 52, 30, 40, 45), fill=color, width=width)
            draw.line((35, 12, 25, 48), fill=color, width=width)
        elif icon_type == "test":
            for row in range(3):
                for col in range(3):
                    cx = 18 + col * 12
                    cy = 18 + row * 12
                    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=color)
        elif icon_type == "settings":
            draw.ellipse((20, 20, 40, 40), outline=color, width=width)
            for x1, y1, x2, y2 in (
                (30, 4, 30, 14),
                (30, 46, 30, 56),
                (4, 30, 14, 30),
                (46, 30, 56, 30),
                (11, 11, 18, 18),
                (42, 42, 49, 49),
                (11, 49, 18, 42),
                (42, 18, 49, 11),
            ):
                draw.line((x1, y1, x2, y2), fill=color, width=width)

        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=resized, dark_image=resized, size=(size, size))

    def _bind_click(self, widget, command):
        widget.bind("<Button-1>", lambda _event: command())

        for internal_name in ("_canvas", "_text_label", "_image_label"):
            internal_widget = getattr(widget, internal_name, None)
            if internal_widget is not None:
                internal_widget.bind("<Button-1>", lambda _event: command())

        try:
            widget.configure(cursor="hand2")
        except ValueError:
            pass

        for child in widget.winfo_children():
            self._bind_click(child, command)

    def on_user_mode(self):
        self.parent.show_user_mode()

    def on_designer_mode(self):
        self.parent.show_developer_mode()

    def on_test_mode(self):
        self.parent.show_test_intro()

    def on_settings_mode(self):
        self.parent.show_settings_page()


if __name__ == "__main__":
    app = ColorVisionApp()
    app.mainloop()
