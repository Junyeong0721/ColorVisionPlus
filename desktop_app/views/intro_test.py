import os
import customtkinter as ctk
from PIL import Image
from views.ishihara_test import IshiharaTestPage


class IntroTestPage(ctk.CTkFrame):

    BG_COLOR = "#F8FAFC"
    CARD_COLOR = "#FFFFFF"

    GREEN = "#52B788"
    GREEN_HOVER = "#40916C"

    TITLE_COLOR = "#0F172A"
    SUB_COLOR = "#64748B"

    DIVIDER_COLOR = "#F1F5F9"
    CARD_RADIUS = 24

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.configure(fg_color=self.BG_COLOR)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(current_dir)
        assets_dir = os.path.join(self.base_dir, "assets", "intro")

        def load_img(filename, size):
            path = os.path.join(assets_dir, filename)
            if os.path.exists(path):
                return ctk.CTkImage(Image.open(path), size=size)
            return None

        self.icon_intro = load_img("intro_icon.png", (140, 140))
        self.icon_light = load_img("light.png", (28, 28))
        self.icon_monitor = load_img("monitor.png", (28, 28))
        self.icon_eye = load_img("eye.png", (28, 28))
        self.icon_clock = load_img("clock.png", (28, 28))
        self.icon_warning = load_img("warning.png", (26, 26))

        self.build_ui()

    def build_ui(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # 본문 영역
        content_area = ctk.CTkFrame(main, fg_color="transparent")
        content_area.pack(fill="both", expand=True)

        # 은은한 하단 물결 배경
        bg_image_path = os.path.join(self.base_dir, "assets", "bg_wave.png")
        if os.path.exists(bg_image_path):
            bg_img = ctk.CTkImage(Image.open(bg_image_path), size=(1400, 260))
            bg_label = ctk.CTkLabel(
                content_area,
                image=bg_img,
                text="",
                fg_color="transparent"
            )
            bg_label.place(relx=0.5, rely=1.0, anchor="s", relwidth=1.0)
            bg_label.lower()

        # 카드 컨테이너
        card_container = ctk.CTkFrame(content_area, fg_color="transparent")
        card_container.pack(fill="both", expand=True, padx=50, pady=25)

        card = ctk.CTkFrame(
            card_container,
            corner_radius=self.CARD_RADIUS,
            fg_color=self.CARD_COLOR,
            border_width=1,
            border_color="#F1F5F9"
        )
        card.pack(fill="both", expand=True)

        # [요청3 반영] 카드 내부 상하 패딩을 25 -> 35 로 늘려서 하단 휑함을 해결
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(padx=60, pady=35, fill="both", expand=True)

        # ----------------------------------------------------
        # 상단 헤더
        # ----------------------------------------------------
        if self.icon_intro:
            image_label = ctk.CTkLabel(content, image=self.icon_intro, text="")
            image_label.pack(pady=(0, 8))

        page_title = ctk.CTkLabel(
            content,
            text="색각 유형 테스트",
            font=("맑은 고딕", 25, "bold"),
            text_color=self.TITLE_COLOR
        )
        page_title.pack(pady=(0, 6))

        # [요청1 & 요청2 반영] 글자 크기 12.5 -> 14 로 키우고 카드와의 간격을 28px로 시원하게 배치
        description = ctk.CTkLabel(
            content,
            text=(
                "이시하라 테스트를 통해 자신의 색각 유형을 확인해보세요.\n"
                "정확한 결과를 위해 아래 안내사항을 확인해주세요."
            ),
            font=("맑은 고딕", 14),
            justify="center",
            text_color=self.SUB_COLOR
        )
        description.pack(pady=(0, 28))

        # ----------------------------------------------------
        # 1. 안내사항 회색 박스
        # ----------------------------------------------------
        notice_card = ctk.CTkFrame(
            content,
            corner_radius=16,
            fg_color="#F8FAFC",
            border_width=1,
            border_color="#F1F5F9"
        )
        notice_card.pack(fill="x", pady=(0, 18))

        notices = [
            (
                self.icon_light,
                "밝은 환경에서 테스트하세요",
                "주변이 너무 어둡거나 밝지 않은 곳에서 테스트하는 것이 좋습니다."
            ),
            (
                self.icon_monitor,
                "모니터 색상 설정을 확인하세요",
                "색온도나 필터 기능이 꺼져 있는지 확인해주세요."
            ),
            (
                self.icon_eye,
                "정답을 맞히려 하지 마세요",
                "보이는 그대로의 숫자를 선택하는 것이 가장 중요합니다."
            ),
            (
                self.icon_clock,
                "테스트 시간은 약 5~10분 소요됩니다",
                "총 15장의 이미지로 구성되어 있습니다."
            )
        ]

        for index, (icon, title, desc) in enumerate(notices):
            row = ctk.CTkFrame(notice_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=11)

            if icon:
                icon_label = ctk.CTkLabel(row, image=icon, text="")
                icon_label.pack(side="left", padx=(0, 18), anchor="center")

            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, anchor="center")

            title_label = ctk.CTkLabel(
                text_frame,
                text=title,
                anchor="w",
                font=("맑은 고딕", 13.5, "bold"),
                text_color=self.TITLE_COLOR
            )
            title_label.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                text_frame,
                text=desc,
                anchor="w",
                justify="left",
                font=("맑은 고딕", 12),
                text_color=self.SUB_COLOR
            )
            desc_label.pack(anchor="w", pady=(2, 0))

            if index < len(notices) - 1:
                divider = ctk.CTkFrame(
                    notice_card,
                    height=1,
                    fg_color=self.DIVIDER_COLOR,
                    corner_radius=0
                )
                divider.pack(fill="x", padx=20)
                divider.pack_propagate(False)

        # ----------------------------------------------------
        # 2. 노란색 주의사항 박스
        # ----------------------------------------------------
        warning_card = ctk.CTkFrame(
            content,
            corner_radius=14,
            fg_color="#FFFBEB",
            border_width=1,
            border_color="#FDE68A"
        )
        warning_card.pack(fill="x", pady=(0, 24))

        warning_inner = ctk.CTkFrame(warning_card, fg_color="transparent")
        warning_inner.pack(padx=24, pady=14, fill="x")

        if self.icon_warning:
            warn_icon_lbl = ctk.CTkLabel(warning_inner, image=self.icon_warning, text="")
            warn_icon_lbl.pack(side="left", padx=(0, 16), anchor="center")
        else:
            warn_icon_lbl = ctk.CTkLabel(
                warning_inner,
                text="⚠️",
                font=("맑은 고딕", 20),
                text_color="#D97706"
            )
            warn_icon_lbl.pack(side="left", padx=(0, 16), anchor="center")

        warn_text_frame = ctk.CTkFrame(warning_inner, fg_color="transparent")
        warn_text_frame.pack(side="left", fill="x", expand=True, anchor="center")

        warn_text_1 = ctk.CTkLabel(
            warn_text_frame,
            text="•   본 테스트는 참고용입니다.",
            font=("맑은 고딕", 13.5, "bold"),
            text_color="#B45309",
            anchor="w"
        )
        warn_text_1.pack(anchor="w")

        warn_text_2 = ctk.CTkLabel(
            warn_text_frame,
            text="•   의학적 진단을 대신할 수 없으므로, 정확한 검사는 전문의와 상담하세요.",
            font=("맑은 고딕", 13.5),
            text_color="#B45309",
            anchor="w"
        )
        warn_text_2.pack(anchor="w", pady=(2, 0))

        # ----------------------------------------------------
        # 3. 하단 테스트 시작 버튼
        # ----------------------------------------------------
        self.start_button = ctk.CTkButton(
            content,
            text="테스트 시작하기  >",
            width=230,
            height=46,
            corner_radius=12,
            font=("맑은 고딕", 15, "bold"),
            fg_color=self.GREEN,
            hover_color=self.GREEN_HOVER,
            text_color="white",
            command=self.start_test
        )
        self.start_button.pack(pady=(0, 0))

    def start_test(self):
        self.parent.show_frame(IshiharaTestPage)
