import os
import customtkinter as ctk
from PIL import Image


class ResultPage(ctk.CTkFrame):

    # 디자인 테마 컬러
    BG_COLOR = "#F8FAFC"
    CARD_BG = "#FFFFFF"

    GREEN = "#52B788"
    GREEN_HOVER = "#40916C"

    TITLE_COLOR = "#0F172A"
    SUB_COLOR = "#64748B"
    DIVIDER_COLOR = "#E2E8F0"

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # current_result 데이터 가져오기
        self.result = getattr(parent, "current_result", {
            "result": "정상 색각",
            "total": 15,
            "correct": 15,
            "accuracy": 100
        })

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(current_dir)
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.result_assets_dir = os.path.join(self.assets_dir, "result")

        self.build_ui()

    def build_ui(self):
        self.configure(fg_color=self.BG_COLOR)

        # ----------------------------------------------------
        # 메인 레이아웃
        # ----------------------------------------------------
        main_layout = ctk.CTkFrame(self, fg_color="transparent")
        main_layout.pack(fill="both", expand=True)

        # 하단 전체 물결 배경
        bg_image_path = os.path.join(self.result_assets_dir, "bg_wave.png")
        if not os.path.exists(bg_image_path):
            bg_image_path = os.path.join(self.assets_dir, "bg_wave.png")

        if os.path.exists(bg_image_path):
            try:
                bg_img = ctk.CTkImage(Image.open(bg_image_path), size=(1400, 260))
                bg_label = ctk.CTkLabel(
                    main_layout,
                    image=bg_img,
                    text="",
                    fg_color="transparent"
                )
                bg_label.place(relx=1.0, rely=1.0, anchor="se")
                bg_label.lower()
            except Exception:
                pass

        # 오른쪽 메인 영역
        content_area = ctk.CTkFrame(
            main_layout,
            fg_color="transparent"
        )
        content_area.pack(fill="both", expand=True, padx=45, pady=(45, 25))

        raw_result_type = self.result.get("result", "정상 색각")
        if "Protan" in raw_result_type or "적색약" in raw_result_type:
            display_result_type = "적색약 (Protan)"
        elif "Deutan" in raw_result_type or "녹색약" in raw_result_type:
            display_result_type = "녹색약 (Deutan)"
        else:
            display_result_type = "정상 색각"

        total = self.result.get("total", 15)
        correct = self.result.get("correct", 0)
        accuracy = self.result.get("accuracy", 0)

        # ----------------------------------------------------
        # Top Header : [< 이전] 뒤로가기
        # ----------------------------------------------------
        top_bar = ctk.CTkFrame(content_area, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 6))

        back_btn = ctk.CTkButton(
            top_bar,
            text="<  이전",
            font=("맑은 고딕", 13, "bold"),
            text_color="#64748B",
            fg_color="transparent",
            hover_color="#E2E8F0",
            width=60,
            height=28,
            anchor="w",
            command=self.go_back
        )
        back_btn.pack(side="left")

        # ----------------------------------------------------
        # 상단 완료 헤더
        # ----------------------------------------------------
        header_frame = ctk.CTkFrame(content_area, fg_color="transparent")
        header_frame.pack(pady=(0, 28))

        check_badge = ctk.CTkFrame(
            header_frame,
            fg_color="#D1FAE5",
            corner_radius=32,
            width=64,
            height=64
        )
        check_badge.pack(pady=(0, 12))
        check_badge.pack_propagate(False)

        icon_check_path = os.path.join(self.result_assets_dir, "icon_check.png")
        if os.path.exists(icon_check_path):
            check_img = ctk.CTkImage(Image.open(icon_check_path), size=(32, 32))
            check_label = ctk.CTkLabel(check_badge, image=check_img, text="", fg_color="transparent")
            check_label.pack(expand=True)
        else:
            ctk.CTkLabel(check_badge, text="✓", font=("맑은 고딕", 26, "bold"), text_color="#059669").pack(expand=True)

        title = ctk.CTkLabel(
            header_frame,
            text="테스트가 완료되었습니다!",
            font=("맑은 고딕", 28, "bold"),
            text_color=self.TITLE_COLOR
        )
        title.pack(pady=(0, 6))

        sub = ctk.CTkLabel(
            header_frame,
            text="아래에서 결과를 확인하고 맞춤형 설정을 적용해보세요.",
            text_color=self.SUB_COLOR,
            font=("맑은 고딕", 14)
        )
        sub.pack()

        # ----------------------------------------------------
        # 1. 결과 요약 카드
        # ----------------------------------------------------
        summary_shadow = ctk.CTkFrame(
            content_area,
            corner_radius=20,
            fg_color="#F1F5F9",
            border_width=1,
            border_color="#E2E8F0"
        )
        summary_shadow.pack(fill="x", pady=(0, 22))

        summary_card = ctk.CTkFrame(
            summary_shadow,
            corner_radius=18,
            fg_color="white",
            border_width=0
        )
        summary_card.pack(fill="both", expand=True, padx=1.5, pady=1.5)

        card_inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        card_inner.pack(padx=28, pady=24, fill="both")

        # --- 좌측: 예상 색각 유형 ---
        left = ctk.CTkFrame(card_inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left,
            text="예상 색각 유형",
            font=("맑은 고딕", 15, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(anchor="w", padx=(28, 0), pady=(0, 22))

        # 내부 아이콘 및 설명 카드
        left_content = ctk.CTkFrame(left, fg_color="transparent")
        left_content.pack(anchor="w", padx=(28, 0))

        # 유형별 배지 배경색 및 아이콘 결정
        badge_bg, icon_file = self.get_type_style(display_result_type)

        eye_badge = ctk.CTkFrame(
            left_content,
            fg_color=badge_bg,
            corner_radius=32,
            width=64,
            height=64
        )
        eye_badge.pack(side="left", padx=(0, 18), anchor="c")
        eye_badge.pack_propagate(False)

        eye_image_path = os.path.join(self.result_assets_dir, icon_file)
        if os.path.exists(eye_image_path):
            eye_img = ctk.CTkImage(Image.open(eye_image_path), size=(40, 40))
            eye_label = ctk.CTkLabel(eye_badge, image=eye_img, text="", fg_color="transparent")
            eye_label.pack(expand=True)
        else:
            ctk.CTkLabel(eye_badge, text="👁️", font=("맑은 고딕", 24)).pack(expand=True)

        info_text_frame = ctk.CTkFrame(left_content, fg_color="transparent")
        info_text_frame.pack(side="left", anchor="w")

        ctk.CTkLabel(
            info_text_frame,
            text=display_result_type,
            font=("맑은 고딕", 18, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(anchor="w")

        desc = self.make_description(display_result_type)
        ctk.CTkLabel(
            info_text_frame,
            text=desc,
            justify="left",
            text_color=self.SUB_COLOR,
            font=("맑은 고딕", 13)
        ).pack(anchor="w", pady=(4, 8))

        star_frame = ctk.CTkFrame(info_text_frame, fg_color="transparent")
        star_frame.pack(anchor="w")

        ctk.CTkLabel(
            star_frame,
            text="신뢰도  ",
            font=("맑은 고딕", 13),
            text_color=self.SUB_COLOR
        ).pack(side="left")

        ctk.CTkLabel(
            star_frame,
            text="★ ★ ★ ★ ",
            font=("맑은 고딕", 16),
            text_color="#10B981"
        ).pack(side="left")

        ctk.CTkLabel(
            star_frame,
            text="★",
            font=("맑은 고딕", 16),
            text_color="#CBD5E1"
        ).pack(side="left")

        ctk.CTkLabel(
            star_frame,
            text=" (높음)",
            font=("맑은 고딕", 13, "bold"),
            text_color="#10B981"
        ).pack(side="left")

        # 중앙 구분선
        divider = ctk.CTkFrame(card_inner, fg_color=self.DIVIDER_COLOR, width=1)
        divider.pack(side="left", fill="y", padx=(16, 28), pady=2)

        # --- 우측: 테스트 요약 ---
        right = ctk.CTkFrame(card_inner, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            right,
            text="테스트 요약",
            font=("맑은 고딕", 15, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(anchor="w", pady=(0, 18))

        self.make_info_row(right, "icon_list.png", "#ECFDF5", "총 문항 수", total)
        self.make_info_row(right, "icon_check.png", "#E0F2FE", "정답 수", correct)
        self.make_info_row(right, "icon_chart.png", "#F3E8FF", "정확도", f"{accuracy}%")

        # ----------------------------------------------------
        # 2. 추천 보정 필터 카드
        # ----------------------------------------------------
        filter_shadow = ctk.CTkFrame(
            content_area,
            corner_radius=20,
            fg_color="#E6F4EA",
            border_width=1,
            border_color="#D1EBE0"
        )
        filter_shadow.pack(fill="x", pady=(0, 24))

        filter_card = ctk.CTkFrame(
            filter_shadow,
            corner_radius=18,
            fg_color="#F4FBF7",
            border_width=0
        )
        filter_card.pack(fill="both", expand=True, padx=1.5, pady=1.5)

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(padx=24, pady=18, fill="both")

        filter_left = ctk.CTkFrame(filter_inner, fg_color="transparent")
        filter_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            filter_left,
            text="추천 보정 필터",
            font=("맑은 고딕", 15, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(anchor="w")

        ctk.CTkLabel(
            filter_left,
            text="아래 필터를 적용하면 색을 더 쉽게 구분할 수 있어요.",
            text_color=self.SUB_COLOR,
            font=("맑은 고딕", 12)
        ).pack(anchor="w", pady=(2, 10))

        filter_detail_box = ctk.CTkFrame(
            filter_left,
            fg_color="white",
            corner_radius=14,
            border_width=1,
            border_color="#E2E8F0"
        )
        filter_detail_box.pack(anchor="w", fill="x", padx=(0, 15))

        fd_inner = ctk.CTkFrame(filter_detail_box, fg_color="transparent")
        fd_inner.pack(padx=14, pady=10, fill="x")

        # 원 두 개 포개진 아이콘
        overlap_icon = ctk.CTkFrame(fd_inner, fg_color="transparent", width=34, height=34)
        overlap_icon.pack(side="left", padx=(0, 10))
        overlap_icon.pack_propagate(False)

        c1 = ctk.CTkFrame(overlap_icon, fg_color="#34D399", corner_radius=12, width=24, height=24)
        c1.place(x=0, y=5)
        c2 = ctk.CTkFrame(overlap_icon, fg_color="#059669", corner_radius=12, width=24, height=24)
        c2.place(x=9, y=5)

        fd_text_frame = ctk.CTkFrame(fd_inner, fg_color="transparent")
        fd_text_frame.pack(side="left", fill="x", expand=True)

        filter_title_frame = ctk.CTkFrame(fd_text_frame, fg_color="transparent")
        filter_title_frame.pack(anchor="w")

        filter_name = self.get_filter_name(display_result_type)
        ctk.CTkLabel(
            filter_title_frame,
            text=filter_name,
            font=("맑은 고딕", 13, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(side="left", padx=(0, 6))

        rec_tag = ctk.CTkFrame(filter_title_frame, fg_color="#DCFCE7", corner_radius=6)
        rec_tag.pack(side="left")
        ctk.CTkLabel(rec_tag, text="추천", font=("맑은 고딕", 10, "bold"), text_color="#166534").pack(padx=6, pady=1)

        filter_desc = self.get_filter_description(display_result_type)
        ctk.CTkLabel(
            fd_text_frame,
            text=filter_desc,
            font=("맑은 고딕", 11),
            text_color=self.SUB_COLOR
        ).pack(anchor="w", pady=(1, 0))

        preview_btn = ctk.CTkButton(
            fd_inner,
            text="👁  미리보기",
            font=("맑은 고딕", 11, "bold"),
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#334155",
            corner_radius=8,
            width=80,
            height=32
        )
        preview_btn.pack(side="right")

        # 우측 적용 전/후 미리보기 미니 카드
        filter_right = ctk.CTkFrame(filter_inner, fg_color="transparent")
        filter_right.pack(side="right", fill="y")

        preview_card = ctk.CTkFrame(
            filter_right,
            fg_color="white",
            corner_radius=14,
            border_width=1,
            border_color="#E2E8F0"
        )
        preview_card.pack(expand=True)

        pc_inner = ctk.CTkFrame(preview_card, fg_color="transparent")
        pc_inner.pack(padx=14, pady=8)

        notch_frame = ctk.CTkFrame(pc_inner, fg_color="transparent")
        notch_frame.pack(anchor="w", pady=(0, 4))

        for color in ["#CBD5E1", "#CBD5E1", "#CBD5E1"]:
            dot = ctk.CTkFrame(notch_frame, fg_color=color, corner_radius=2, width=4, height=4)
            dot.pack(side="left", padx=1.5)

        label_frame = ctk.CTkFrame(pc_inner, fg_color="transparent")
        label_frame.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(label_frame, text="적용 전", font=("맑은 고딕", 10.5, "bold"), text_color=self.SUB_COLOR).pack(side="left", padx=(18, 0))
        ctk.CTkLabel(label_frame, text="적용 후", font=("맑은 고딕", 10.5, "bold"), text_color=self.SUB_COLOR).pack(side="right", padx=(0, 18))

        img_box_frame = ctk.CTkFrame(pc_inner, fg_color="transparent")
        img_box_frame.pack()

        img_before = ctk.CTkFrame(img_box_frame, fg_color="#86EFAC", corner_radius=6, width=72, height=52)
        img_before.pack(side="left", padx=(0, 6))

        img_after = ctk.CTkFrame(img_box_frame, fg_color="#10B981", corner_radius=6, width=72, height=52)
        img_after.pack(side="left")

        # ----------------------------------------------------
        # 3. 하단 액션 버튼
        # ----------------------------------------------------
        bottom = ctk.CTkFrame(content_area, fg_color="transparent")
        bottom.pack(pady=(6, 0))

        retry_btn = ctk.CTkButton(
            bottom,
            text="↺  테스트 다시하기",
            font=("맑은 고딕", 13, "bold"),
            fg_color="white",
            hover_color="#F1F5F9",
            text_color="#334155",
            border_width=1,
            border_color="#CBD5E1",
            corner_radius=10,
            width=150,
            height=42,
            command=self.retry
        )
        retry_btn.pack(side="left", padx=(0, 10))

        apply_btn = ctk.CTkButton(
            bottom,
            text="맞춤 설정 적용하기  >",
            font=("맑은 고딕", 13, "bold"),
            fg_color=self.GREEN,
            hover_color=self.GREEN_HOVER,
            text_color="white",
            corner_radius=10,
            width=165,
            height=42,
            command=self.apply_recommended_filter
        )
        apply_btn.pack(side="left")

    # ======================================
    # 헬퍼 메소드
    # ======================================

    def get_type_style(self, result):
        """색각 유형에 따른 배경색과 아이콘 파일명 반환"""
        if "Protan" in result or "적색약" in result:
            return "#FEE2E2", "eye_protan.png"      # 연빨강 배경 + 적색약 아이콘
        elif "Deutan" in result or "녹색약" in result:
            return "#FEF3C7", "eye_deutan.png"      # 연노랑/주황 배경 + 녹색약 아이콘
        else:
            return "#DCFCE7", "eye_normal.png"      # 연초록 배경 + 정상 아이콘

    def go_back(self):
        from views.ishihara_test import IshiharaTestPage
        self.parent.show_frame(IshiharaTestPage)

    def make_info_row(self, parent, icon_filename, bg_color, text, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        badge = ctk.CTkFrame(row, fg_color=bg_color, corner_radius=16, width=32, height=32)
        badge.pack(side="left", padx=(0, 10))
        badge.pack_propagate(False)

        icon_path = os.path.join(self.result_assets_dir, icon_filename)

        if os.path.exists(icon_path):
            img = ctk.CTkImage(Image.open(icon_path), size=(18, 18))
            badge_label = ctk.CTkLabel(badge, image=img, text="", fg_color="transparent")
            badge_label.pack(expand=True)
        else:
            ctk.CTkLabel(badge, text="•", font=("맑은 고딕", 13), text_color="#334155").pack(expand=True)

        ctk.CTkLabel(
            row,
            text=text,
            font=("맑은 고딕", 13),
            text_color=self.SUB_COLOR
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=str(value),
            font=("맑은 고딕", 13.5, "bold"),
            text_color=self.TITLE_COLOR
        ).pack(side="right", padx=(0, 4))

    def make_description(self, result):
        if "Protan" in result or "적색약" in result:
            return "적색 계열 색을 구분하는 데\n어려움이 있을 수 있습니다."
        elif "Deutan" in result or "녹색약" in result:
            return "녹색 계열 색을 구분하는 데\n어려움이 있을 수 있습니다."
        else:
            return "특별한 색각 이상 징후가\n발견되지 않았습니다."

    def get_filter_name(self, result):
        if "Protan" in result or "적색약" in result:
            return "Protan 보정 필터"
        elif "Deutan" in result or "녹색약" in result:
            return "Deutan 보정 필터"
        else:
            return "기본 필터"

    def get_filter_description(self, result):
        if "Protan" in result or "적색약" in result:
            return "적색 계열 색을 더 선명하게 보정해줍니다."
        elif "Deutan" in result or "녹색약" in result:
            return "녹색 계열 색을 더 선명하게 보정해줍니다."
        else:
            return "기본 화면 설정을 유지하며 색감을 최적화합니다."

    def retry(self):
        from views.ishihara_test import IshiharaTestPage
        self.parent.show_frame(IshiharaTestPage)

    def apply_recommended_filter(self):
        self.parent.apply_test_result_to_user_mode(self.result)
