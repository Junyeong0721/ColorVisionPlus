import customtkinter as ctk
from PIL import Image
import os


class ResultPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        self.parent = parent

        self.result = \
            parent.current_result

        self.base_dir = os.path.dirname(
            os.path.dirname(__file__)
        )

        self.build_ui()

    # ======================================

    def build_ui(self):

        self.configure(
            fg_color="#F5F7F6"
        )

        result_type = \
            self.result["result"]

        total = \
            self.result["total"]

        correct = \
            self.result["correct"]

        accuracy = \
            self.result["accuracy"]

        top_bar = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        top_bar.pack(
            fill="x",
            padx=35,
            pady=(20, 0)
        )

        home_button = ctk.CTkButton(

            top_bar,

            text="← 메인으로",

            width=120,
            height=36,

            fg_color="white",

            text_color="black",

            border_width=1,

            command=self.parent.show_main_page

        )

        home_button.pack(
            side="left"
        )

        # ==========================
        # 완료 아이콘
        # ==========================

        icon = ctk.CTkLabel(

            self,

            text="✓",

            font=(
                "맑은 고딕",
                60,
                "bold"
            ),

            text_color="#5DBA7B"

        )

        icon.pack(
            pady=(10, 10)
        )

        title = ctk.CTkLabel(

            self,

            text="테스트가 완료되었습니다!",

            font=(
                "맑은 고딕",
                34,
                "bold"
            )

        )

        title.pack()

        sub = ctk.CTkLabel(

            self,

            text="아래에서 결과를 확인하고 맞춤 설정을 적용해보세요.",

            text_color="gray50",

            font=(
                "맑은 고딕",
                18
            )

        )

        sub.pack(
            pady=(10, 35)
        )

        # ==========================
        # 결과 카드
        # ==========================

        card = ctk.CTkFrame(

            self,

            width=1050,
            height=240,

            corner_radius=30,

            fg_color="white"

        )

        card.pack()

        card.pack_propagate(False)

        left = ctk.CTkFrame(

            card,

            fg_color="transparent"

        )

        left.place(
            x=50,
            y=50
        )

        title = ctk.CTkLabel(

            left,

            text="예상 색각 유형",

            font=(
                "맑은 고딕",
                18,
                "bold"
            )

        )

        title.pack(
            anchor="w"
        )

        result_label = ctk.CTkLabel(

            left,

            text=result_type,

            font=(
                "맑은 고딕",
                34,
                "bold"
            )

        )

        result_label.pack(
            anchor="w",
            pady=(35, 10)
        )

        desc = self.make_description(
            result_type
        )

        desc_label = ctk.CTkLabel(

            left,

            text=desc,

            justify="left",

            text_color="gray45",

            font=(
                "맑은 고딕",
                17
            )

        )

        desc_label.pack(
            anchor="w"
        )

        # =====================
        # 오른쪽
        # =====================

        right = ctk.CTkFrame(

            card,

            fg_color="transparent"

        )

        right.place(
            x=730,
            y=50
        )

        title = ctk.CTkLabel(

            right,

            text="테스트 요약",

            font=(
                "맑은 고딕",
                18,
                "bold"
            )

        )

        title.pack(
            anchor="w",
            pady=(0, 25)
        )

        self.make_info_row(
            right,
            "총 문항 수",
            total
        )

        self.make_info_row(
            right,
            "정답 수",
            correct
        )

        self.make_info_row(
            right,
            "정확도",
            f"{accuracy}%"
        )

        # ==========================
        # 필터 카드
        # ==========================

        filter_card = ctk.CTkFrame(

            self,

            width=1050,
            height=220,

            corner_radius=30,

            fg_color="#F0F7F2"

        )

        filter_card.pack(
            pady=30
        )

        filter_card.pack_propagate(
            False
        )

        title = ctk.CTkLabel(

            filter_card,

            text="추천 보정 필터",

            font=(
                "맑은 고딕",
                24,
                "bold"
            )

        )

        title.place(
            x=40,
            y=35
        )

        filter_name = self.get_filter_name(
            result_type
        )

        filter_label = ctk.CTkLabel(

            filter_card,

            text=filter_name,

            font=(
                "맑은 고딕",
                22,
                "bold"
            )

        )

        filter_label.place(
            x=50,
            y=110
        )

        desc = ctk.CTkLabel(

            filter_card,

            text="색상 구분을 조금 더 쉽게 도와주는 보정 필터입니다.",

            text_color="gray50",

            font=(
                "맑은 고딕",
                16
            )

        )

        desc.place(
            x=50,
            y=150
        )

        preview = ctk.CTkFrame(

            filter_card,

            width=220,
            height=130,

            corner_radius=20,

            fg_color="white"

        )

        preview.place(
            x=770,
            y=45
        )

        p = ctk.CTkLabel(

            preview,

            text="필터\n미리보기",

            font=(
                "맑은 고딕",
                20
            )

        )

        p.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        # ==========================
        # 하단 버튼
        # ==========================

        bottom = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )

        bottom.pack(
            pady=20
        )

        retry = ctk.CTkButton(

            bottom,

            text="테스트 다시하기",

            width=240,
            height=60,

            fg_color="white",

            text_color="black",

            border_width=1,

            command=self.retry

        )

        retry.pack(
            side="left",
            padx=20
        )

        apply_btn = ctk.CTkButton(

            bottom,

            text="맞춤 설정 적용하기",

            width=280,
            height=60,

            fg_color="#63C98A"

        )

        apply_btn.pack(
            side="left"
        )

    # ======================================

    def make_info_row(
            self,
            parent,
            text,
            value
    ):

        row = ctk.CTkFrame(

            parent,

            fg_color="transparent"

        )

        row.pack(
            fill="x",
            pady=10
        )

        l = ctk.CTkLabel(

            row,

            text=text,

            font=(
                "맑은 고딕",
                18
            )

        )

        l.pack(
            side="left"
        )

        r = ctk.CTkLabel(

            row,

            text=str(value),

            font=(
                "맑은 고딕",
                20,
                "bold"
            )

        )

        r.pack(
            side="right"
        )

    # ======================================

    def make_description(
            self,
            result
    ):

        if "Protan" in result:

            return \
                "적색 계열 색상을\n구분하는 데 어려움이 있을 수 있습니다."

        elif "Deutan" in result:

            return \
                "녹색 계열 색상을\n구분하는 데 어려움이 있을 수 있습니다."

        else:

            return \
                "특별한 색각 이상 징후가 발견되지 않았습니다."

    # ======================================

    def get_filter_name(
            self,
            result
    ):

        if "Protan" in result:
            return "Protan 보정 필터"

        elif "Deutan" in result:
            return "Deutan 보정 필터"

        else:
            return "기본 필터"

    # ======================================

    def retry(self):

        from views.ishihara_test import \
            IshiharaTestPage

        self.parent.show_frame(
            IshiharaTestPage
        )
