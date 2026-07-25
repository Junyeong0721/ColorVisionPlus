import os
import sys

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

import customtkinter as ctk
from PIL import Image

from core.color_correction import default_options_for_type
from core.settings_store import SettingsStore
from views.developer_mode import DeveloperModePage
from views.intro_test import IntroTestPage
from views.settings_page import SettingsPage
from views.user_mode import UserModePage


HOME_WIDTH = 900
HOME_HEIGHT = 650
TEST_WIDTH = 1400
TEST_HEIGHT = 900
SIDEBAR_WIDTH = 250


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
        self.sidebar = None
        self.content_host = None
        self.active_nav = "home"

        self.show_main_page()

    def show_main_page(self):
        self._set_fixed_size(HOME_WIDTH, HOME_HEIGHT)
        self._reset_shell()
        frame = MainPage(self)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame
        self.active_nav = "home"

    def show_user_mode(self, preset_options=None):
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

        self.show_user_mode(preset_options=preset)


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

    def bind_global(self, sequence, func):
        self.app.bind_all(sequence, func)

    def unbind_global(self, sequence):
        self.app.unbind_all(sequence)


class AppSidebar(ctk.CTkFrame):
    BG = "#FBFEFD"
    ACTIVE = "#EAF6EF"
    TEXT = "#334E63"
    MUTED = "#6B7F90"
    ACCENT = "#27966A"

    def __init__(self, app):
        super().__init__(app, fg_color=self.BG, corner_radius=0, width=SIDEBAR_WIDTH)
        self.app = app
        self.items = {}
        self.grid_propagate(False)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self,
            text="ColorVision+",
            font=("Arial", 21, "bold"),
            text_color="#1F2937",
            anchor="w",
        ).pack(fill="x", padx=30, pady=(28, 54))

        self.add_item("home", "⌂", "홈", self.app.show_main_page)
        self.add_item("user", "○", "사용자 모드", self.app.show_user_mode)
        self.add_item("test", "◎", "색각 유형 테스트", self.app.show_test_intro)
        self.add_item("developer", "▣", "개발자 모드", self.app.show_developer_mode)
        self.add_item("settings", "⚙", "설정", self.app.show_settings_page)

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        self.add_static_item("?", "도움말")

    def add_item(self, key, icon, text, command):
        item = self.create_item(icon, text)
        item.pack(fill="x", padx=16, pady=8)
        self.items[key] = item
        self.bind_click(item, command)

    def add_static_item(self, icon, text):
        item = self.create_item(icon, text)
        item.pack(fill="x", padx=16, pady=(8, 24))

    def create_item(self, icon, text):
        item = ctk.CTkFrame(self, fg_color="transparent", corner_radius=14, height=58)
        item.pack_propagate(False)
        icon_label = ctk.CTkLabel(item, text=icon, font=("Arial", 25), text_color=self.TEXT, width=48)
        icon_label.pack(side="left", padx=(16, 8))
        text_label = ctk.CTkLabel(
            item,
            text=text,
            font=("맑은 고딕", 15),
            text_color=self.TEXT,
            anchor="w",
        )
        text_label.pack(side="left", fill="x", expand=True)
        item.nav_icon = icon_label
        item.nav_text = text_label
        return item

    def set_active(self, active_key):
        for key, item in self.items.items():
            is_active = key == active_key
            item.configure(fg_color=self.ACTIVE if is_active else "transparent")
            item.nav_icon.configure(text_color=self.ACCENT if is_active else self.TEXT)
            item.nav_text.configure(
                text_color=self.ACCENT if is_active else self.TEXT,
                font=("맑은 고딕", 15, "bold" if is_active else "normal"),
            )

    def bind_click(self, widget, command):
        widget.bind("<Button-1>", lambda _event: command())
        try:
            widget.configure(cursor="hand2")
        except ValueError:
            pass
        for child in widget.winfo_children():
            self.bind_click(child, command)


class MainPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8F9FA")
        self.parent = parent

        self.pack_propagate(False)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo", "colorvision_logo.png")
        self.logo_image = ctk.CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(132, 84),
        )

        self.logo_label = ctk.CTkLabel(
            self,
            image=self.logo_image,
            text="",
        )
        self.logo_label.pack(pady=(26, 4))

        self.title_label = ctk.CTkLabel(
            self,
            text="ColorVision+",
            font=ctk.CTkFont(family="Arial", size=36, weight="bold"),
            text_color="#212529",
        )
        self.title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="색각 이상 사용자를 위한 맞춤형 접근성 플랫폼\nMaking colors accessible for everyone.",
            font=ctk.CTkFont(family="맑은 고딕", size=14),
            text_color="#6C757D",
            justify="center",
        )
        self.subtitle_label.pack(pady=(8, 28))

        current_profile = self.parent.current_profile
        profile_text = (
            f"최근 프로필: {current_profile.name}"
            if current_profile is not None
            else "처음이라면 사용자 모드에서 유형을 직접 선택하거나 테스트를 시작해보세요."
        )

        self.profile_label = ctk.CTkLabel(
            self,
            text=profile_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color="#2E7D32",
        )
        self.profile_label.pack(pady=(0, 14))

        self.menu_container = ctk.CTkFrame(
            self,
            fg_color="transparent",
            width=724,
            height=232,
        )
        self.menu_container.pack(padx=88, pady=(0, 20))
        self.menu_container.pack_propagate(False)
        self.menu_container.grid_columnconfigure((0, 1), weight=1, minsize=350)
        self.menu_container.grid_rowconfigure((0, 1), weight=1, minsize=108)

        self.create_menu_card(
            0,
            0,
            "U",
            "사용자 모드",
            "화면 보정 및 색상 필터 적용",
            "#E8F5E9",
            "#2E7D32",
            self.on_user_mode,
        )
        self.create_menu_card(
            0,
            1,
            "</>",
            "개발자/디자이너 모드",
            "시뮬레이션 및 접근성 분석",
            "#E3F2FD",
            "#1565C0",
            self.on_designer_mode,
        )
        self.create_menu_card(
            1,
            0,
            "T",
            "색각 유형 테스트",
            "이시하라 색각 테스트",
            "#F3E5F5",
            "#6A1B9A",
            self.on_test_mode,
        )
        self.create_menu_card(
            1,
            1,
            "⚙",
            "설정",
            "앱 설정 및 환경 구성",
            "#FFF8E1",
            "#F57F17",
            self.on_settings_mode,
        )

        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", pady=(0, 24))

        self.info_label = ctk.CTkLabel(
            self.footer_frame,
            text="ⓘ  |  GitHub",
            font=ctk.CTkFont(size=13),
            text_color="#495057",
        )
        self.info_label.pack()

        self.version_label = ctk.CTkLabel(
            self.footer_frame,
            text="v0.1.0",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        )
        self.version_label.pack(pady=(5, 0))

    def create_menu_card(self, row, col, icon, title, desc, bg_color, text_color, command):
        card = ctk.CTkFrame(
            self.menu_container,
            width=350,
            height=100,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E9ECEF",
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
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
        icon_box.grid(row=0, column=0, padx=(22, 16), sticky="w")
        icon_box.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_box,
            text=icon,
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            text_color=text_color,
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
            font=ctk.CTkFont(family="맑은 고딕", size=15, weight="bold"),
            text_color="#212529",
            anchor="w",
        )
        title_lbl.grid(row=0, column=0, sticky="ew")

        desc_lbl = ctk.CTkLabel(
            text_frame,
            text=desc,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color="#868E96",
            anchor="w",
        )
        desc_lbl.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        arrow_lbl = ctk.CTkLabel(
            card,
            text="›",
            font=ctk.CTkFont(family="Arial", size=24),
            text_color="#CED4DA",
            width=24,
            anchor="center",
        )
        arrow_lbl.grid(row=0, column=2, padx=(6, 20), sticky="e")

        self._bind_click(card, command)

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
