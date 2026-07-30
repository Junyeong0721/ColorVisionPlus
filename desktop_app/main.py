import os
import sys

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

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
