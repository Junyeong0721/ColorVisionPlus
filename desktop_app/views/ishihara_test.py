from views.result_page import ResultPage
import customtkinter as ctk
from PIL import Image
import os
import json
import random


class IshiharaTestPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.base_dir = os.path.dirname(
            os.path.dirname(__file__)
        )

        # --------------------
        # answer.json 로드
        # --------------------

        with open(
                os.path.join(
                    self.base_dir,
                    "assets",
                    "answer.json"
                ),
                "r",
                encoding="utf-8"
        ) as f:

            self.answer_data = json.load(f)

        self.plates = list(
            self.answer_data.keys()
        )

        self.current_index = 0

        # 사용자가 선택한 답
        self.user_answers = {}

        # 현재 선택
        self.selected_answer = None

        # 문제별 선택지 저장
        self.cached_choices = {}

        self.build_ui()

        self.show_plate()

    # ==================================================
    # UI
    # ==================================================

    def build_ui(self):

        self.configure(
            fg_color="#F5F7F6"
        )

        title = ctk.CTkLabel(
            self,
            text="색각 유형 테스트",
            font=("맑은 고딕", 34, "bold")
        )

        title.pack(
            pady=(35, 10)
        )

        subtitle = ctk.CTkLabel(
            self,
            text="이시하라 테스트를 통해 색각 유형을 확인해보세요.",
            font=("맑은 고딕", 16),
            text_color="gray55"
        )

        

        subtitle.pack(
            pady=(0, 25)
        )

        
        # 카드

        self.card = ctk.CTkFrame(
            self,
            width=1150,
            height=560,
            corner_radius=30,
            fg_color="white"
        )

        self.card.pack(
            pady=(0,20)
        )

        self.card.pack_propagate(False)

        content = ctk.CTkFrame(
            self.card,
            fg_color="transparent"
        )

        content.pack(
            expand=True,
            fill="both",
            padx=45,
            pady=45
        )

        # --------------------
        # 좌측 이미지
        # --------------------

        self.left = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )

        self.left.grid(
            row=0,
            column=0,
            padx=(10, 80)
        )

        self.image_label = ctk.CTkLabel(
            self.left,
            text=""
        )

        self.image_label.pack()

        # --------------------
        # 우측
        # --------------------

        self.right = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )

        self.right.grid(
            row=0,
            column=1,
            sticky="n"
        )

        self.progress_label = ctk.CTkLabel(
            self.right,
            text="",
            font=("맑은 고딕",18,"bold"),
            text_color="#64B883"
        )

        self.progress_label.pack(
            anchor="w",
            pady=(10,5)
        )


        self.question_label = ctk.CTkLabel(
            self.right,
            text="이 숫자는 무엇인가요?",
            font=("맑은 고딕", 28, "bold")
        )

        self.question_label.pack(
            anchor="w",
            pady=(5, 15)
        )

        self.info_label = ctk.CTkLabel(
            self.right,
            text="보이는 숫자를 선택해주세요.",
            text_color="gray50",
            font=("맑은 고딕", 16)
        )

        self.info_label.pack(
            anchor="w",
            pady=(0, 30)
        )

        self.button_frame = ctk.CTkFrame(
            self.right,
            fg_color="transparent"
        )

        self.button_frame.pack()

        # --------------------
        # 하단 버튼
        # --------------------

        bottom = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        bottom.pack(
            fill="x",
            padx=170,
            pady=35
        )

        self.prev_btn = ctk.CTkButton(
            bottom,
            text="◀ 이전",
            width=170,
            height=55,
            command=self.prev_plate
        )

        self.prev_btn.pack(
            side="left"
        )

        self.next_btn = ctk.CTkButton(
            bottom,
            text="다음 ▶",
            width=170,
            height=55,
            state="disabled",
            command=self.next_plate
        )

        self.next_btn.pack(
            side="right"
        )

    # ==================================================
    # 문제 표시
    # ==================================================

    def show_plate(self):

        plate_name = self.plates[
            self.current_index
        ]

        self.progress_label.configure(

            text=f"{self.current_index+1} / {len(self.plates)}"

        )

        image_path = os.path.join(
            self.base_dir,
            "assets",
            "plates",
            f"{plate_name}.png"
        )

        img = ctk.CTkImage(

            Image.open(
                image_path
            ),

            size=(430, 430)

        )

        self.image_label.configure(
            image=img
        )

        self.image_label.image = img

        if plate_name in self.user_answers:

            self.selected_answer = \
                self.user_answers[
                    plate_name
                ]

            self.next_btn.configure(
                state="normal"
            )

        else:

            self.selected_answer = None

            self.next_btn.configure(
                state="disabled"
            )

        self.make_buttons()

    # ==================================================
    # 버튼 생성
    # ==================================================

    def make_buttons(self):

        for w in \
                self.button_frame.winfo_children():

            w.destroy()

        plate_name = self.plates[
            self.current_index
        ]

        # --------------------------
        # 선택지 캐싱
        # --------------------------

        if plate_name in self.cached_choices:

            choices = \
                self.cached_choices[
                    plate_name
                ]

        else:

            data = self.answer_data[
                plate_name
            ]

            choices = set()

            for key in [

                "normal",
                "protan",
                "deutan"

            ]:

                value = data.get(
                    key,
                    ""
                )

                if value != "":
                    choices.add(value)

            while len(
                    choices
            ) < 8:

                fake = str(
                    random.randint(
                        1,
                        99
                    )
                )

                if fake not in choices:

                    choices.add(fake)

            choices = list(
                choices
            )

            random.shuffle(
                choices
            )

            self.cached_choices[
                plate_name
            ] = choices

        # --------------------------
        # 숫자 버튼
        # --------------------------

        for i, value in enumerate(
                choices
        ):

            row = i // 4
            col = i % 4

            selected = (
                value ==
                self.selected_answer
            )

            btn = ctk.CTkButton(

                self.button_frame,

                text=value,

                width=120,
                height=65,

                corner_radius=18,

                fg_color=(
                    "#90D7A7"
                    if selected
                    else "white"
                ),

                hover_color="#DDF3E3",

                border_width=1,
                border_color="#DDDDDD",

                text_color="black",

                font=(
                    "맑은 고딕",
                    18
                ),

                command=lambda v=value:
                self.select_answer(v)

            )

            btn.grid(

                row=row,
                column=col,

                padx=10,
                pady=10

            )

        # --------------------------
        # 보이지 않음 버튼
        # --------------------------

        selected = (
                self.selected_answer
                ==
                "보이지 않음"
        )

        btn = ctk.CTkButton(

            self.button_frame,

            text="숫자가 보이지 않음",

            width=540,
            height=65,

            corner_radius=18,

            fg_color=(
                "#90D7A7"
                if selected
                else "white"
            ),

            hover_color="#DDF3E3",

            border_width=1,
            border_color="#DDDDDD",

            text_color="black",

            command=lambda:
            self.select_answer(
                "보이지 않음"
            )

        )

        btn.grid(

            row=2,
            column=0,

            columnspan=4,

            pady=(20, 0)

        )

    # ==================================================
    # 답 선택
    # ==================================================

    def select_answer(
            self,
            answer
    ):

        plate = self.plates[
            self.current_index
        ]

        self.selected_answer = answer

        self.user_answers[
            plate
        ] = answer

        self.next_btn.configure(
            state="normal"
        )

        # 버튼 색만 갱신
        self.make_buttons()

    # ==================================================
    # 이전
    # ==================================================

    def prev_plate(self):

        if self.current_index <= 0:
            return

        self.current_index -= 1

        self.show_plate()

    # ==================================================
    # 다음
    # ==================================================

    def next_plate(self):

        if self.current_index == \
                len(self.plates)-1:

            self.finish_test()
            return

        self.current_index += 1

        self.show_plate()

    # ==================================================
    # 결과 계산
    # ==================================================

    def finish_test(self):

        score = {

            "normal": 0,
            "protan": 0,
            "deutan": 0

        }

        for plate, answer in \
                self.user_answers.items():

            data = self.answer_data[
                plate
            ]

            if answer == data[
                "normal"
            ]:

                score[
                    "normal"
                ] += 1

            elif answer == data[
                "protan"
            ]:

                score[
                    "protan"
                ] += 1

            elif answer == data[
                "deutan"
            ]:

                score[
                    "deutan"
                ] += 1

        print(score)

        # 임시 결과 판정

        if score["normal"] >= 10:

            result = "정상 색각"

        elif score[
                "protan"
        ] >= score[
                "deutan"
        ]:

            result = "적색약(Protan) 의심"

        else:

            result = "녹색약(Deutan) 의심"

        print(result)

        self.parent.current_result = {

            "score": score,
            "result": result,
            "total": len(self.plates),

         "correct": max(score.values()),

        "accuracy":
            round(
                max(score.values())
                /
                len(self.plates)
                * 100
            )
    }

        self.parent.show_frame(
            ResultPage
    )