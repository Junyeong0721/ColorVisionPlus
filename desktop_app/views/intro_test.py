import os

import customtkinter as ctk

from PIL import Image

from views.ishihara_test import IshiharaTestPage


class IntroTestPage(ctk.CTkFrame):

    BG_COLOR = "#F5F7F6"
    CARD_COLOR = "#FFFFFF"

    GREEN = "#67C587"
    GREEN_HOVER = "#54B174"

    TITLE_COLOR = "#1F2937"
    SUB_COLOR = "#6B7280"

    DIVIDER = "#E5E7EB"

    CARD_RADIUS = 28

    WINDOW_PADDING = 40

    def __init__(self, parent):

        super().__init__(parent)

        self.parent = parent

        self.configure(
            fg_color=self.BG_COLOR
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(
            current_dir,
            "..",
            "assets",
            "intro"
        )

        self.icon_intro = ctk.CTkImage(
            Image.open(
                os.path.join(
                    assets_dir,
                    "intro_icon.png"
                )
            ),
            size=(150, 150)
        )

        self.icon_light = ctk.CTkImage(
            Image.open(
                os.path.join(
                    assets_dir,
                    "light.png"
                )
            ),
            size=(30, 30)
        )

        self.icon_monitor = ctk.CTkImage(
            Image.open(
                os.path.join(
                    assets_dir,
                    "monitor.png"
                )
            ),
            size=(30, 30)
        )

        self.icon_eye = ctk.CTkImage(
            Image.open(
                os.path.join(
                    assets_dir,
                    "eye.png"
                )
            ),
            size=(30, 30)
        )

        self.icon_clock = ctk.CTkImage(
            Image.open(
                os.path.join(
                    assets_dir,
                    "clock.png"
                )
            ),
            size=(30, 30)
        )

        self.build_ui()

    # -------------------------------------------------

    def build_ui(self):

        top_bar = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        top_bar.pack(
            fill="x",
            padx=35,
            pady=(20, 0)
        )

        back_button = ctk.CTkButton(
            top_bar,
            text="← 메인으로",
            width=120,
            height=36,
            fg_color="white",
            hover_color="#EEF2F0",
            text_color=self.TITLE_COLOR,
            border_width=1,
            border_color=self.DIVIDER,
            command=self.parent.show_main_page
        )

        back_button.pack(
            side="left"
        )

        title = ctk.CTkLabel(
            self,
            text="ColorVision+",
            font=("맑은 고딕", 18, "bold"),
            text_color=self.GREEN
        )

        title.pack(
            pady=(8, 10)
        )

        card = ctk.CTkFrame(
            self,
            width=900,
            height=720,
            corner_radius=self.CARD_RADIUS,
            fg_color=self.CARD_COLOR
        )

        card.pack(
            pady=10
        )

        card.pack_propagate(False)

        content = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        content.pack(
            expand=True,
            fill="both",
            padx=55,
            pady=40
        )

        image_label = ctk.CTkLabel(
            content,
            image=self.icon_intro,
            text=""
        )

        image_label.pack(
            pady=(0, 18)
        )

        page_title = ctk.CTkLabel(
            content,
            text="색각 유형 테스트",
            font=("맑은 고딕", 30, "bold"),
            text_color=self.TITLE_COLOR
        )

        page_title.pack()

        description = ctk.CTkLabel(
            content,
            text=(
                "이시하라 테스트를 통해 자신의 색각 유형을 확인합니다.\n"
                "정확한 결과를 위해 아래 안내사항을 확인해주세요."
            ),
            font=("맑은 고딕", 15),
            justify="center",
            text_color=self.SUB_COLOR
        )

        description.pack(
            pady=(12, 32)
        )

        notice_card = ctk.CTkFrame(
            content,
            corner_radius=20,
            fg_color="#FAFAFA"
        )

        notice_card.pack(
            fill="x"
        )
        notices = [

            (
                self.icon_light,
                "밝은 환경에서 테스트하세요",
                "주변이 너무 어둡거나 밝지 않은 곳에서 진행하는 것을 권장합니다."
            ),

            (
                self.icon_monitor,
                "모니터 색상을 확인하세요",
                "블루라이트 필터나 색상 보정 기능은 꺼두는 것이 좋습니다."
            ),

            (
                self.icon_eye,
                "보이는 그대로 선택하세요",
                "정답을 맞히려고 하기보다 실제로 보이는 숫자를 선택해주세요."
            ),

            (
                self.icon_clock,
                "테스트는 약 5~10분 정도 소요됩니다",
                "총 15장의 플레이트가 제공됩니다."
            )

        ]

        for index, (icon, title, desc) in enumerate(notices):

            row = ctk.CTkFrame(
                notice_card,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=25,
                pady=15
            )

            icon_label = ctk.CTkLabel(
                row,
                image=icon,
                text=""
            )

            icon_label.pack(
                side="left",
                padx=(0, 18)
            )

            text_frame = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            text_frame.pack(
                side="left",
                fill="x",
                expand=True
            )

            title_label = ctk.CTkLabel(
                text_frame,
                text=title,
                anchor="w",
                font=("맑은 고딕", 15, "bold"),
                text_color=self.TITLE_COLOR
            )

            title_label.pack(
                anchor="w"
            )

            desc_label = ctk.CTkLabel(
                text_frame,
                text=desc,
                anchor="w",
                justify="left",
                font=("맑은 고딕", 13),
                text_color=self.SUB_COLOR
            )

            desc_label.pack(
                anchor="w",
                pady=(2, 0)
            )

            if index != len(notices) - 1:

                divider = ctk.CTkFrame(
                    notice_card,
                    height=1,
                    fg_color=self.DIVIDER
                )

                divider.pack(
                    fill="x",
                    padx=20
                )

        ctk.CTkLabel(
            content,
            text=""
        ).pack(
            pady=10
        )

        self.start_button = ctk.CTkButton(

            content,

            text="테스트 시작하기   →",

            width=320,

            height=52,

            corner_radius=14,

            font=("맑은 고딕", 17, "bold"),

            fg_color=self.GREEN,

            hover_color=self.GREEN_HOVER,

            command=self.start_test

        )

        self.start_button.pack(
            pady=(18, 0)
        )

    # -------------------------------------------------

    def start_test(self):

        self.parent.show_frame(
            IshiharaTestPage
        )


# ---------------------------------------------------------
# 단독 실행 테스트
# ---------------------------------------------------------

if __name__ == "__main__":

    class PreviewApp(ctk.CTk):

        def __init__(self):

            super().__init__()

            self.title("ColorVision+")

            self.geometry("1400x900")

            self.resizable(False, False)

            ctk.set_appearance_mode("Light")
            ctk.set_default_color_theme("green")

            frame = IntroTestPage(self)

            frame.pack(
                fill="both",
                expand=True
            )

        # 실제 프로젝트에서는 main.py의 show_frame을 사용한다.
        # Preview에서는 버튼이 눌렸을 때 테스트 페이지 대신 안내창만 띄운다.

        def show_frame(self, page):

            popup = ctk.CTkToplevel(self)

            popup.title("Preview")

            popup.geometry("380x180")

            ctk.CTkLabel(

                popup,

                text="프로젝트에서는\nIshiharaTestPage로 이동합니다.",

                font=("맑은 고딕",16)

            ).pack(
                expand=True,
                pady=20
            )

            ctk.CTkButton(

                popup,

                text="확인",

                command=popup.destroy

            ).pack(
                pady=(0,20)
            )


    app = PreviewApp()

    app.mainloop()
