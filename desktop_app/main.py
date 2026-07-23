import os
import sys

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

import customtkinter as ctk
from PIL import Image

from views.ishihara_test import IshiharaTestPage


HOME_WIDTH = 900
HOME_HEIGHT = 650
TEST_WIDTH = 1400
TEST_HEIGHT = 900


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

        self.show_main_page()

    def show_main_page(self):
        self._set_fixed_size(HOME_WIDTH, HOME_HEIGHT)
        self._show_page(MainPage)

    def show_frame(self, frame_class):
        self._set_fixed_size(TEST_WIDTH, TEST_HEIGHT)
        self._show_page(frame_class)

    def _show_page(self, frame_class):
        if self.current_frame is not None:
            self.current_frame.destroy()

        frame = frame_class(self)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

    def _set_fixed_size(self, width, height):
        self.minsize(1, 1)
        self.maxsize(10000, 10000)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.maxsize(width, height)


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
        print("사용자 모드 클릭")

    def on_designer_mode(self):
        print("개발자/디자이너 모드 클릭")

    def on_test_mode(self):
        self.parent.show_frame(IshiharaTestPage)

    def on_settings_mode(self):
        print("설정 클릭")


if __name__ == "__main__":
    app = ColorVisionApp()
    app.mainloop()
