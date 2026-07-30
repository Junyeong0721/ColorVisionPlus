import os
import json
import random
import customtkinter as ctk
from PIL import Image, ImageDraw
from views.result_page import ResultPage


class IshiharaTestPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8FAFC")
        self.parent = parent

        self.base_dir = os.path.dirname(os.path.dirname(__file__))

        with open(
            os.path.join(self.base_dir, "assets", "answer.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.answer_data = json.load(f)

        self.plates = list(self.answer_data.keys())
        self.current_index = 0
        self.user_answers = {}
        self.selected_answer = None
        self.cached_choices = {}

        self.build_ui()
        self.bind_events()
        self.show_plate()

    def bind_events(self):
        root = self.winfo_toplevel()
        root.bind_all("<Return>", self.on_enter_pressed)
        root.bind_all("<KP_Enter>", self.on_enter_pressed)

    def on_enter_pressed(self, event=None):
        if self.next_btn.cget("state") == "normal":
            self.next_plate()

    def destroy(self):
        try:
            root = self.winfo_toplevel()
            root.unbind_all("<Return>")
            root.unbind_all("<KP_Enter>")
        except Exception:
            pass
        super().destroy()

    def get_rounded_image(self, image_path, size=(280, 280), radius=20):
        """이시하라 이미지의 색감 손상 없이 모서리만 둥글게 깎아주는 함수"""
        raw_img = Image.open(image_path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        
        rounded_img = Image.new("RGBA", size, (0, 0, 0, 0))
        rounded_img.paste(raw_img, (0, 0), mask)
        return ctk.CTkImage(light_image=rounded_img, dark_image=rounded_img, size=size)

    def build_ui(self):
        # ----------------------------------------------------
        # 1. 메인 레이아웃
        # ----------------------------------------------------
        main_layout = ctk.CTkFrame(self, fg_color="#F8FAFC")
        main_layout.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # 2. 물결 배경 이미지
        # ----------------------------------------------------
        bg_image_path = os.path.join(self.base_dir, "assets", "bg_wave.png")
        if os.path.exists(bg_image_path):
            try:
                bg_pil = Image.open(bg_image_path)
                bg_img = ctk.CTkImage(
                    light_image=bg_pil,
                    dark_image=bg_pil,
                    size=(1400, 320)
                )
                self.bg_label = ctk.CTkLabel(
                    main_layout, 
                    image=bg_img, 
                    text="", 
                    fg_color="transparent"
                )
                self.bg_label.place(relx=1.0, rely=1.0, anchor="se")
                self.bg_label.lower()
            except Exception as e:
                print("웨이브 로드 실패:", e)

        # ----------------------------------------------------
        # 3. 우측 컨텐츠 영역
        # ----------------------------------------------------
        content_area = ctk.CTkFrame(main_layout, fg_color="transparent")
        content_area.pack(fill="both", expand=True, padx=45, pady=(25, 15))

        # ----------------------------------------------------
        # 4. 상단 이전 버튼 & 헤더
        # ----------------------------------------------------
        top_bar = ctk.CTkFrame(content_area, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 4))

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

        title = ctk.CTkLabel(
            content_area,
            text="색각 유형 테스트",
            font=("맑은 고딕", 25, "bold"),
            text_color="#0F172A",
            fg_color="transparent"
        )
        title.pack(pady=(0, 4))

        subtitle = ctk.CTkLabel(
            content_area,
            text="이시하라 테스트를 통해 색각 유형을 확인해보세요.",
            font=("맑은 고딕", 13),
            text_color="#64748B",
            fg_color="transparent"
        )
        subtitle.pack(pady=(0, 20))

        # ----------------------------------------------------
        # 5. 진행도 바
        # ----------------------------------------------------
        step_frame = ctk.CTkFrame(content_area, fg_color="transparent")
        step_frame.pack(pady=(0, 22))

        step1_col = ctk.CTkFrame(step_frame, fg_color="transparent")
        step1_col.pack(side="left")

        step1 = ctk.CTkFrame(step1_col, fg_color="#52B788", corner_radius=14, width=28, height=28)
        step1.pack(anchor="center")
        step1.pack_propagate(False)
        ctk.CTkLabel(step1, text="1", text_color="white", font=("맑은 고딕", 13, "bold"), fg_color="transparent").pack(expand=True)

        ctk.CTkLabel(step1_col, text="테스트 진행", font=("맑은 고딕", 12, "bold"), text_color="#1E293B", fg_color="transparent").pack(pady=(4, 0))

        line1 = ctk.CTkFrame(step_frame, fg_color="#52B788", height=2, width=120)
        line1.pack(side="left", padx=10, pady=(0, 18))

        step2_col = ctk.CTkFrame(step_frame, fg_color="transparent")
        step2_col.pack(side="left")

        step2 = ctk.CTkFrame(step2_col, fg_color="#E2E8F0", corner_radius=14, width=28, height=28)
        step2.pack(anchor="center")
        step2.pack_propagate(False)
        ctk.CTkLabel(step2, text="2", text_color="#64748B", font=("맑은 고딕", 13), fg_color="transparent").pack(expand=True)

        ctk.CTkLabel(step2_col, text="결과 분석", font=("맑은 고딕", 12), text_color="#94A3B8", fg_color="transparent").pack(pady=(4, 0))

        line2 = ctk.CTkFrame(step_frame, fg_color="#CBD5E1", height=2, width=120)
        line2.pack(side="left", padx=10, pady=(0, 18))

        step3_col = ctk.CTkFrame(step_frame, fg_color="transparent")
        step3_col.pack(side="left")

        step3 = ctk.CTkFrame(step3_col, fg_color="#E2E8F0", corner_radius=14, width=28, height=28)
        step3.pack(anchor="center")
        step3.pack_propagate(False)
        ctk.CTkLabel(step3, text="3", text_color="#64748B", font=("맑은 고딕", 13), fg_color="transparent").pack(expand=True)

        ctk.CTkLabel(step3_col, text="결과 확인", font=("맑은 고딕", 12), text_color="#94A3B8", fg_color="transparent").pack(pady=(4, 0))

        # ----------------------------------------------------
        # 6. 메인 카드 영역
        # ----------------------------------------------------
        self.card = ctk.CTkFrame(
            content_area,
            corner_radius=24,
            fg_color="white",
            border_width=1,
            border_color="#F1F5F9"
        )
        self.card.pack(fill="x", padx=10, pady=(0, 24))

        card_inner = ctk.CTkFrame(self.card, fg_color="transparent")
        card_inner.pack(padx=35, pady=40, anchor="center")

        # 이시하라 이미지 배치 배경 영역
        self.left_bg_card = ctk.CTkFrame(
            card_inner,
            fg_color="#F6F4ED",
            corner_radius=16,
            width=290,
            height=290
        )
        self.left_bg_card.pack(side="left", padx=(0, 45))
        self.left_bg_card.pack_propagate(False)

        self.image_label = ctk.CTkLabel(self.left_bg_card, text="", fg_color="transparent")
        self.image_label.pack(expand=True)

        self.right = ctk.CTkFrame(card_inner, fg_color="transparent")
        self.right.pack(side="left", anchor="w")

        self.progress_label = ctk.CTkLabel(
            self.right,
            text="",
            font=("맑은 고딕", 16, "bold"),
            text_color="#52B788",
            fg_color="transparent"
        )
        self.progress_label.pack(anchor="w", pady=(0, 6))

        self.question_label = ctk.CTkLabel(
            self.right,
            text="이 숫자는 무엇인가요?",
            font=("맑은 고딕", 22, "bold"),
            text_color="#0F172A",
            fg_color="transparent"
        )
        self.question_label.pack(anchor="w", pady=(0, 4))

        self.info_label = ctk.CTkLabel(
            self.right,
            text="보이는 숫자를 선택해주세요.",
            text_color="#64748B",
            font=("맑은 고딕", 13),
            fg_color="transparent"
        )
        self.info_label.pack(anchor="w", pady=(0, 20))

        self.button_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        self.button_frame.pack(anchor="w")

        # ----------------------------------------------------
        # 7. 팁 상자
        # ----------------------------------------------------
        tip_box = ctk.CTkFrame(
            content_area,
            fg_color="#EAF5EE",
            corner_radius=12
        )
        tip_box.pack(fill="x", padx=10, pady=(0, 24))

        tip_inner = ctk.CTkFrame(tip_box, fg_color="transparent")
        tip_inner.pack(padx=24, pady=12, side="left")

        ctk.CTkLabel(tip_inner, text="💡", font=("맑은 고딕", 14), fg_color="transparent").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(tip_inner, text="팁 ", font=("맑은 고딕", 12.5, "bold"), text_color="#2D6A4F", fg_color="transparent").pack(side="left")
        ctk.CTkLabel(
            tip_inner, 
            text="Enter 키를 눌러 다음 문제로 이동할 수 있습니다.", 
            font=("맑은 고딕", 12.5), 
            text_color="#475569",
            fg_color="transparent"
        ).pack(side="left")

        # ----------------------------------------------------
        # 8. 하단 이동 버튼
        # ----------------------------------------------------
        bottom = ctk.CTkFrame(content_area, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 16))

        self.prev_btn = ctk.CTkButton(
            bottom,
            text="<  이전",
            font=("맑은 고딕", 13.5, "bold"),
            fg_color="white",
            hover_color="#F1F5F9",
            text_color="#475569",
            border_width=1,
            border_color="#CBD5E1",
            corner_radius=22,
            width=100,
            height=44,
            command=self.prev_plate
        )
        self.prev_btn.pack(side="left")

        self.next_btn = ctk.CTkButton(
            bottom,
            text="다음  >",
            font=("맑은 고딕", 13.5, "bold"),
            fg_color="#52B788",
            hover_color="#40916C",
            text_color="white",
            corner_radius=22,
            width=100,
            height=44,
            command=self.next_plate
        )
        self.next_btn.pack(side="right")

        # ----------------------------------------------------
        # 9. 저작권 표기 Footer (옵션 A 적용)
        # ----------------------------------------------------
        copyright_label = ctk.CTkLabel(
            content_area,
            text="* 본 색각 테스트에 사용된 검사표는 \n이시하라 시노부(Dr. Shinobu Ishihara)박사의 Ishihara Color Vision Test 표준 원안을 기반으로 구성되었습니다.",
            font=("맑은 고딕", 12),
            text_color="#94A3B8",
            fg_color="transparent"
        )
        copyright_label.pack(pady=(0, 10))

    def go_back(self):
        root = self.winfo_toplevel()
        root.unbind_all("<Return>")
        root.unbind_all("<KP_Enter>")
        
        try:
            from views.intro_test import IntroTestPage
            self.parent.show_frame(IntroTestPage)
        except ImportError:
            from views.intro_test import TestIntroPage
            self.parent.show_frame(TestIntroPage)

    def show_plate(self):
        plate_name = self.plates[self.current_index]

        self.progress_label.configure(
            text=f"{self.current_index + 1} / {len(self.plates)}"
        )

        image_path = os.path.join(
            self.base_dir, "assets", "plates", f"{plate_name}.png"
        )

        img = self.get_rounded_image(image_path, size=(270, 270), radius=20)

        self.image_label.configure(image=img)
        self.image_label.image = img

        if plate_name in self.user_answers:
            self.selected_answer = self.user_answers[plate_name]
            self.next_btn.configure(state="normal", fg_color="#52B788")
        else:
            self.selected_answer = None
            self.next_btn.configure(state="disabled", fg_color="#52B788")

        self.make_buttons()

    def make_buttons(self):
        for w in self.button_frame.winfo_children():
            w.destroy()

        plate_name = self.plates[self.current_index]

        if plate_name in self.cached_choices:
            choices = self.cached_choices[plate_name]
        else:
            data = self.answer_data[plate_name]
            choices = set()

            for key in ["normal", "protan", "deutan"]:
                value = data.get(key, "")
                if value != "":
                    choices.add(value)

            while len(choices) < 8:
                fake = str(random.randint(1, 99))
                if fake not in choices:
                    choices.add(fake)

            choices = list(choices)
            random.shuffle(choices)
            self.cached_choices[plate_name] = choices

        for i, value in enumerate(choices):
            row = i // 4
            col = i % 4

            selected = (value == self.selected_answer)

            btn_fg = "white"
            btn_border = "#52B788" if selected else "#E2E8F0"
            btn_text = "#1E293B"

            btn = ctk.CTkButton(
                self.button_frame,
                text=value,
                width=80,
                height=42,
                corner_radius=10,
                fg_color=btn_fg,
                hover_color="#F8FAFC",
                border_width=2 if selected else 1,
                border_color=btn_border,
                text_color=btn_text,
                font=("맑은 고딕", 14, "bold"),
                command=lambda v=value: self.select_answer(v)
            )

            btn.grid(row=row, column=col, padx=5, pady=5)

        selected = (self.selected_answer == "보이지 않음")
        btn_fg = "white"
        btn_border = "#52B788" if selected else "#E2E8F0"
        btn_text = "#1E293B"

        btn_none = ctk.CTkButton(
            self.button_frame,
            text="숫자가 보이지 않음",
            height=42,
            corner_radius=10,
            fg_color=btn_fg,
            hover_color="#F8FAFC",
            border_width=2 if selected else 1,
            border_color=btn_border,
            text_color=btn_text,
            font=("맑은 고딕", 13),
            command=lambda: self.select_answer("보이지 않음")
        )

        btn_none.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=(8, 0))

    def select_answer(self, answer):
        plate = self.plates[self.current_index]
        self.selected_answer = answer
        self.user_answers[plate] = answer

        self.next_btn.configure(state="normal", fg_color="#52B788")
        self.make_buttons()
        
        self.focus_set()

    def prev_plate(self):
        if self.current_index <= 0:
            return
        self.current_index -= 1
        self.show_plate()

    def next_plate(self):
        if self.current_index == len(self.plates) - 1:
            self.finish_test()
            return
        self.current_index += 1
        self.show_plate()

    def finish_test(self):
        root = self.winfo_toplevel()
        root.unbind_all("<Return>")
        root.unbind_all("<KP_Enter>")

        score = {"normal": 0, "protan": 0, "deutan": 0}

        for plate, answer in self.user_answers.items():
            data = self.answer_data[plate]
            if answer == data["normal"]:
                score["normal"] += 1
            elif answer == data["protan"]:
                score["protan"] += 1
            elif answer == data["deutan"]:
                score["deutan"] += 1

        if score["normal"] >= 10:
            result = "정상 색각"
        elif score["protan"] >= score["deutan"]:
            result = "적색약(Protan) 의심"
        else:
            result = "녹색약(Deutan) 의심"

        self.parent.current_result = {
            "score": score,
            "result": result,
            "total": len(self.plates),
            "correct": max(score.values()),
            "accuracy": round(max(score.values()) / len(self.plates) * 100)
        }

        self.parent.show_frame(ResultPage)
