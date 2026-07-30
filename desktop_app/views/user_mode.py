from __future__ import annotations

import ctypes
import os
from tkinter import messagebox, simpledialog

import customtkinter as ctk
from PIL import Image

from core.color_correction import (
    CorrectionOptions,
    TYPE_DESCRIPTIONS,
    TYPE_LABELS,
    color_distance,
    corrected_cvd_preview_hex,
    default_options_for_type,
    simulate_cvd_hex,
)
from core.screen_overlay import WindowsScreenColorOverlay


TYPE_TO_LABEL = TYPE_LABELS


class UserModePage(ctk.CTkFrame):
    BG = "#F8FBFA"
    SIDEBAR = "#FBFEFD"
    CARD = "#FFFFFF"
    SOFT_CARD = "#F1FAF6"
    LINE = "#E5ECE9"
    TITLE = "#102033"
    TEXT = "#334E63"
    MUTED = "#6B7F90"
    ACCENT = "#41B883"
    ACCENT_DARK = "#27966A"
    RED = "#CC4B37"
    BLUE = "#2F80ED"
    PURPLE = "#8F6AC8"

    def __init__(self, parent, preset_options: CorrectionOptions | None = None):
        super().__init__(parent, fg_color=self.BG)
        self.parent = parent
        self.store = parent.settings_store
        self.overlay = WindowsScreenColorOverlay()
        self.tint_overlay: ctk.CTkToplevel | None = None
        self.selected_profile_id = parent.current_profile.profile_id
        self._is_updating_controls = False
        self.slider_labels: dict[str, ctk.CTkLabel] = {}
        self.sliders: dict[str, ctk.CTkSlider] = {}
        self.toggle_buttons: list[ctk.CTkButton] = []

        if preset_options is None:
            self.options = parent.current_profile.to_options()
            self.start_message = "준비됨 - 화면 보정 켜기를 누르면 적용됩니다."
        else:
            self.options = preset_options
            self.selected_profile_id = ""
            self.start_message = "추천값 준비됨 - 켜면 적용됩니다."

        self.build_ui()
        self.apply_options_to_controls()
        self.update_all_visuals()
        self.update_status(self.start_message)
        self.parent.bind_global("<Control-Alt-c>", self.toggle_overlay_from_hotkey)

    def destroy(self):
        self.stop_overlay()
        self.parent.unbind_global("<Control-Alt-c>")
        super().destroy()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_content()

    def build_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=44, pady=(26, 6))

        back = ctk.CTkButton(
            top,
            text="‹  이전",
            width=96,
            height=36,
            fg_color="transparent",
            hover_color="#EEF5F2",
            text_color=self.TEXT,
            font=("맑은 고딕", 15),
            command=self.parent.show_main_page,
        )
        back.pack(side="left")

        hero = ctk.CTkFrame(content, fg_color="transparent")
        hero.grid(row=1, column=0, sticky="ew", padx=44, pady=(0, 18))

        self.hero_icon = ctk.CTkFrame(
            hero,
            width=70,
            height=70,
            corner_radius=35,
            fg_color="#DDF4E8",
            border_width=1,
            border_color="#B8E3CF",
        )
        self.hero_icon.pack()
        self.hero_icon.pack_propagate(False)
        self.hero_icon_text = ctk.CTkLabel(
            self.hero_icon,
            text="✓",
            font=("Arial", 40, "bold"),
            text_color=self.ACCENT_DARK,
        )
        self.hero_icon_text.place(relx=0.5, rely=0.5, anchor="center")

        self.hero_title = ctk.CTkLabel(
            hero,
            text="화면 보정 시스템",
            font=("맑은 고딕", 30, "bold"),
            text_color=self.TITLE,
        )
        self.hero_title.pack(pady=(16, 8))

        ctk.CTkLabel(
            hero,
            text="이미지를 바꾸지 않고 화면 위에 전체 화면 색상 보정 필터를 적용합니다.",
            font=("맑은 고딕", 16),
            text_color=self.MUTED,
        ).pack()

        self.build_result_card(content)
        self.build_filter_card(content)
        self.build_bottom_actions(content)

    def build_result_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            corner_radius=20,
            border_width=1,
            border_color=self.LINE,
        )
        card.grid(row=2, column=0, sticky="ew", padx=44, pady=(0, 26))
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, minsize=1)
        card.grid_columnconfigure(2, minsize=410)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(36, 28), pady=32)
        left.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            left,
            text="현재 화면 보정 유형",
            font=("맑은 고딕", 17, "bold"),
            text_color=self.TITLE,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 26))

        self.type_icon = ctk.CTkFrame(
            left,
            width=150,
            height=150,
            corner_radius=75,
            fg_color="#FDF1EC",
            border_width=1,
            border_color="#F4DED6",
        )
        self.type_icon.grid(row=1, column=0, rowspan=2, padx=(0, 30), sticky="w")
        self.type_icon.grid_propagate(False)
        self.type_color_swatch = ctk.CTkFrame(
            self.type_icon,
            width=88,
            height=88,
            corner_radius=44,
            fg_color="#DDE5EA",
            border_width=4,
            border_color="#FFFFFF",
        )
        self.type_color_swatch.place(relx=0.5, rely=0.5, anchor="center")

        self.type_title = ctk.CTkLabel(
            left,
            text="일반 보기",
            font=("맑은 고딕", 24, "bold"),
            text_color=self.TITLE,
            anchor="w",
        )
        self.type_title.grid(row=1, column=1, sticky="ew", pady=(14, 8))

        self.type_desc = ctk.CTkLabel(
            left,
            text="원본에 가까운 화면입니다.",
            font=("맑은 고딕", 15),
            text_color=self.TEXT,
            anchor="w",
            justify="left",
            wraplength=390,
        )
        self.type_desc.grid(row=2, column=1, sticky="ew")

        self.type_buttons: dict[str, ctk.CTkButton] = {}
        type_row = ctk.CTkFrame(left, fg_color="transparent")
        type_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(28, 0))
        type_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        type_defs = [
            ("protanomaly", "적색약"),
            ("deuteranomaly", "녹색약"),
            ("tritanomaly", "청색약"),
            ("normal", "일반 보기"),
        ]
        for index, (cvd_type, label) in enumerate(type_defs):
            button = ctk.CTkButton(
                type_row,
                text=label,
                height=42,
                corner_radius=12,
                fg_color="white",
                hover_color="#EEF5F2",
                text_color=self.TEXT,
                border_width=1,
                border_color=self.LINE,
                font=("맑은 고딕", 14, "bold"),
                command=lambda value=cvd_type: self.select_cvd_type(value),
            )
            button.grid(row=0, column=index, sticky="ew", padx=5)
            self.type_buttons[cvd_type] = button

        self.type_hint_label = ctk.CTkLabel(
            left,
            text="보정이 켜진 상태에서 유형을 바꾸면 현재 화면에 바로 반영됩니다.",
            font=("맑은 고딕", 12),
            text_color=self.MUTED,
            anchor="w",
        )
        self.type_hint_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        divider = ctk.CTkFrame(card, width=1, fg_color=self.LINE)
        divider.grid(row=0, column=1, sticky="ns", pady=40)

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew", padx=(36, 44), pady=36)
        right.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            right,
            text="보정 상태",
            font=("맑은 고딕", 17, "bold"),
            text_color=self.TITLE,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 22))

        self.state_value = self.info_row(right, 1, "☰", "#DDF4E8", self.ACCENT_DARK, "적용 상태", "꺼짐")
        self.strength_value = self.info_row(right, 2, "✓", "#E6F2FF", self.BLUE, "보정 강도", "60")
        self.backend_value = self.info_row(right, 3, "▥", "#EFE8FA", self.PURPLE, "적용 방식", "대기 중")

        control = ctk.CTkFrame(
            right,
            fg_color="#F6FBF8",
            corner_radius=16,
            border_width=1,
            border_color="#DDEFE7",
        )
        control.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(22, 0))
        control.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            control,
            text="전체 화면 보정",
            font=("맑은 고딕", 15, "bold"),
            text_color=self.TITLE,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 2))

        self.control_status_label = ctk.CTkLabel(
            control,
            text="꺼짐 - 아직 화면에는 적용되지 않았습니다.",
            font=("맑은 고딕", 12),
            text_color=self.MUTED,
            anchor="w",
            justify="left",
            width=300,
            wraplength=300,
        )
        self.control_status_label.grid(row=1, column=0, sticky="ew", padx=20)

        self.primary_toggle_button = ctk.CTkButton(
            control,
            text="화면 보정 켜기",
            height=54,
            corner_radius=14,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_DARK,
            text_color="white",
            font=("맑은 고딕", 15, "bold"),
            command=self.toggle_overlay,
        )
        self.primary_toggle_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(16, 10))
        self.toggle_buttons.append(self.primary_toggle_button)

        self.control_message_label = ctk.CTkLabel(
            control,
            text="",
            font=("맑은 고딕", 12),
            text_color=self.MUTED,
            anchor="w",
            justify="left",
            width=300,
            wraplength=300,
        )
        self.control_message_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 4))

        self.add_slider(control, 4, 0, "correction_strength", "보정 강도", 0, 100, 1)

        ctk.CTkLabel(
            control,
            text="단축키: Ctrl+Alt+C",
            font=("맑은 고딕", 12, "bold"),
            text_color=self.ACCENT_DARK,
            anchor="w",
        ).grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 18))

    def info_row(self, parent, row, icon, bg, color, label, value):
        icon_box = ctk.CTkFrame(parent, width=46, height=46, corner_radius=23, fg_color=bg)
        icon_box.grid(row=row, column=0, sticky="w", pady=8)
        icon_box.grid_propagate(False)
        ctk.CTkLabel(
            icon_box,
            text=icon,
            font=("Arial", 20, "bold"),
            text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            parent,
            text=label,
            font=("맑은 고딕", 15),
            text_color=self.TEXT,
            anchor="w",
        ).grid(row=row, column=1, sticky="w", padx=18)

        value_label = ctk.CTkLabel(
            parent,
            text=value,
            font=("맑은 고딕", 15, "bold"),
            text_color=self.TITLE,
            anchor="e",
            width=118,
        )
        value_label.grid(row=row, column=2, sticky="e")
        return value_label

    def build_filter_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.SOFT_CARD,
            corner_radius=20,
            border_width=1,
            border_color="#DDEFE7",
        )
        card.grid(row=3, column=0, sticky="ew", padx=44, pady=(0, 24))
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, minsize=350)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=36, pady=28)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left,
            text="세부 조절 및 추천 필터",
            font=("맑은 고딕", 18, "bold"),
            text_color=self.TITLE,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        self.effect_summary_label = ctk.CTkLabel(
            left,
            text="",
            font=("맑은 고딕", 13),
            text_color=self.MUTED,
            anchor="w",
            justify="left",
        )
        self.effect_summary_label.grid(row=1, column=0, sticky="ew", pady=(8, 18))

        filter_box = ctk.CTkFrame(
            left,
            fg_color=self.CARD,
            corner_radius=14,
            border_width=1,
            border_color=self.LINE,
        )
        filter_box.grid(row=2, column=0, sticky="ew")
        filter_box.grid_columnconfigure(1, weight=1)

        filter_icon_shell = ctk.CTkFrame(
            filter_box,
            width=74,
            height=74,
            fg_color="transparent",
        )
        filter_icon_shell.grid(row=0, column=0, padx=22, pady=20)
        filter_icon_shell.grid_propagate(False)

        filter_icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "icons",
            "filter_eye_plus.png",
        )
        filter_icon_source = Image.open(filter_icon_path)
        self.filter_icon_image = ctk.CTkImage(
            light_image=filter_icon_source,
            dark_image=filter_icon_source,
            size=(58, 43),
        )
        self.filter_icon_label = ctk.CTkLabel(
            filter_icon_shell,
            image=self.filter_icon_image,
            text="",
        )
        self.filter_icon_label.place(relx=0.5, rely=0.5, anchor="center")

        self.filter_title = ctk.CTkLabel(
            filter_box,
            text="일반 보기 필터",
            font=("맑은 고딕", 17, "bold"),
            text_color=self.TITLE,
            anchor="w",
        )
        self.filter_title.grid(row=0, column=1, sticky="ew", pady=(22, 0))

        self.filter_desc = ctk.CTkLabel(
            filter_box,
            text="원본에 가까운 화면을 유지합니다.",
            font=("맑은 고딕", 13),
            text_color=self.TEXT,
            anchor="w",
        )
        self.filter_desc.grid(row=1, column=1, sticky="ew", pady=(4, 22))

        ctk.CTkButton(
            filter_box,
            text="프로필 저장",
            width=124,
            height=44,
            fg_color="white",
            hover_color="#EEF5F2",
            text_color=self.TEXT,
            border_width=1,
            border_color=self.LINE,
            font=("맑은 고딕", 13, "bold"),
            command=self.save_profile,
        ).grid(row=0, column=2, rowspan=2, padx=22)

        sliders = ctk.CTkFrame(left, fg_color="transparent")
        sliders.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        sliders.grid_columnconfigure((0, 1), weight=1)
        self.add_slider(sliders, 0, 0, "contrast_boost", "대비 강화", 0, 100, 1)
        self.add_slider(sliders, 0, 1, "saturation_shift", "채도 조절", -50, 50, 1)
        self.add_slider(sliders, 1, 0, "brightness_shift", "밝기 조절", -50, 50, 1)

        preview = ctk.CTkFrame(
            card,
            fg_color=self.CARD,
            corner_radius=14,
            border_width=1,
            border_color=self.LINE,
        )
        preview.grid(row=0, column=1, sticky="nsew", padx=(0, 36), pady=48)
        preview.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            preview,
            text="보정 전",
            font=("맑은 고딕", 12, "bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, pady=(8, 8))
        ctk.CTkLabel(
            preview,
            text="보정 후",
            font=("맑은 고딕", 12, "bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=1, pady=(8, 8))

        self.swatches = []
        self.preview_samples = [
            ("빨강", "#D72638"),
            ("초록", "#2EAD4B"),
            ("파랑", "#246BFE"),
            ("노랑", "#F2C94C"),
            ("보라", "#8E44AD"),
            ("갈색", "#8B5E34"),
        ]
        before_grid = ctk.CTkFrame(preview, fg_color="transparent")
        after_grid = ctk.CTkFrame(preview, fg_color="transparent")
        before_grid.grid(row=1, column=0, padx=(14, 6), pady=(0, 14), sticky="nsew")
        after_grid.grid(row=1, column=1, padx=(6, 14), pady=(0, 14), sticky="nsew")

        for index, (_name, _color) in enumerate(self.preview_samples):
            before_block = ctk.CTkFrame(before_grid, width=58, height=36, corner_radius=8, fg_color="#FFFFFF")
            after_block = ctk.CTkFrame(after_grid, width=58, height=36, corner_radius=8, fg_color="#FFFFFF")
            before_block.grid(row=index // 2, column=index % 2, padx=5, pady=5)
            after_block.grid(row=index // 2, column=index % 2, padx=5, pady=5)
            before_block.grid_propagate(False)
            after_block.grid_propagate(False)
            self.swatches.append((before_block, after_block))

        self.status_label = ctk.CTkLabel(
            left,
            text="",
            font=("맑은 고딕", 12),
            text_color=self.MUTED,
            anchor="w",
            justify="left",
        )
        self.status_label.grid(row=4, column=0, sticky="ew", pady=(14, 0))

    def build_bottom_actions(self, parent):
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=44, pady=(0, 28))
        bottom.grid_columnconfigure((0, 1, 2, 3), weight=1)

        reset = ctk.CTkButton(
            bottom,
            text="↻  기본값 복원",
            height=60,
            width=240,
            corner_radius=14,
            fg_color="white",
            hover_color="#EEF5F2",
            text_color=self.TEXT,
            border_width=1,
            border_color=self.LINE,
            font=("맑은 고딕", 16, "bold"),
            command=self.reset_to_type_defaults,
        )
        reset.grid(row=0, column=1, sticky="e", padx=(0, 14))

        self.footer_toggle_button = ctk.CTkButton(
            bottom,
            text="화면 보정 켜기  ›",
            height=60,
            width=260,
            corner_radius=14,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_DARK,
            text_color="white",
            font=("맑은 고딕", 16, "bold"),
            command=self.toggle_overlay,
        )
        self.footer_toggle_button.grid(row=0, column=2, sticky="w")
        self.toggle_buttons.append(self.footer_toggle_button)

    def add_slider(self, parent, row, col, key, label, min_value, max_value, step):
        shell = ctk.CTkFrame(parent, fg_color="transparent")
        shell.grid(row=row, column=col, sticky="ew", padx=8, pady=8)
        shell.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            shell,
            text=label,
            font=("맑은 고딕", 12),
            text_color=self.TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        value = ctk.CTkLabel(
            shell,
            text="",
            font=("맑은 고딕", 12, "bold"),
            text_color=self.ACCENT_DARK,
            width=44,
            anchor="e",
        )
        value.grid(row=0, column=1)
        self.slider_labels[key] = value

        slider = ctk.CTkSlider(
            shell,
            from_=min_value,
            to=max_value,
            number_of_steps=int(round((max_value - min_value) / step)),
            command=lambda raw, slider_key=key: self.on_slider_change(slider_key, raw),
        )
        slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.sliders[key] = slider

    def show_test_intro(self):
        from views.intro_test import IntroTestPage

        self.parent.show_frame(IntroTestPage)

    def bind_click(self, widget, command):
        widget.bind("<Button-1>", lambda _event: command())
        try:
            widget.configure(cursor="hand2")
        except ValueError:
            pass
        for child in widget.winfo_children():
            self.bind_click(child, command)

    def toggle_overlay_from_hotkey(self, _event=None):
        self.toggle_overlay()

    def toggle_overlay(self):
        if self.is_overlay_active():
            self.stop_overlay()
        else:
            self.start_overlay()

    def start_overlay(self):
        fallback_reason = ""
        try:
            state = self.overlay.start(self.options)
            self.update_overlay_ui(True, "Windows 색상 필터", state.message)
            return
        except Exception as exc:
            fallback_reason = str(exc)

        try:
            self.start_tint_overlay()
            message = "Windows 전체 화면 필터를 사용할 수 없어 투명 보정 레이어로 실행했습니다."
            if fallback_reason:
                message = f"{message} ({fallback_reason})"
            self.update_overlay_ui(
                True,
                "투명 오버레이",
                message,
            )
        except Exception:
            self.stop_overlay()
            self.update_status("현재 환경에서 화면 오버레이를 실행할 수 없습니다.", error=True)

    def stop_overlay(self):
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

        self.update_overlay_ui(False, "대기 중", "화면 보정이 꺼졌습니다.")

    def is_overlay_active(self) -> bool:
        return self.overlay.active or self.tint_overlay is not None

    def apply_overlay_options(self):
        if self.overlay.active:
            try:
                self.overlay.apply(self.options)
                self.update_overlay_ui(True, "Windows 색상 필터", "조절값을 현재 화면에 반영했습니다.")
            except Exception:
                self.update_status("화면 보정 갱신에 실패했습니다. 다시 켜 주세요.", error=True)
        elif self.tint_overlay is not None:
            self.update_tint_overlay()
            self.update_overlay_ui(True, "투명 오버레이", "조절값을 투명 오버레이에 반영했습니다.")

    def start_tint_overlay(self):
        overlay = ctk.CTkToplevel(self.parent)
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
        settings = self.store.load_settings()
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

    def select_cvd_type(self, cvd_type: str):
        was_active = self.is_overlay_active()
        self.options = default_options_for_type(cvd_type)
        self.selected_profile_id = ""
        self.apply_options_to_controls()
        self.update_all_visuals()
        self.apply_overlay_options()
        label = TYPE_TO_LABEL.get(cvd_type, "일반 보기")
        if was_active:
            self.update_status(f"{label} 보정으로 바꾸고 현재 화면에 바로 반영했습니다.")
        else:
            self.update_status(f"{label} 보정을 선택했습니다. 화면 보정 켜기를 누르면 전체 화면에 적용됩니다.")

    def on_slider_change(self, key: str, raw_value: float):
        if self._is_updating_controls:
            return
        setattr(self.options, key, int(round(float(raw_value))))
        self.selected_profile_id = ""
        self.update_slider_label(key)
        self.update_all_visuals()
        self.apply_overlay_options()
        if not self.is_overlay_active():
            self.update_status("조절값이 준비되었습니다. 화면 보정 켜기를 누르면 전체 화면에 적용됩니다.")

    def apply_options_to_controls(self):
        self._is_updating_controls = True
        for key, slider in self.sliders.items():
            slider.set(getattr(self.options, key))
            self.update_slider_label(key)
        self._is_updating_controls = False

    def update_slider_label(self, key: str):
        self.slider_labels[key].configure(text=str(int(getattr(self.options, key))))

    def reset_to_type_defaults(self):
        self.options = default_options_for_type(self.options.cvd_type)
        self.selected_profile_id = ""
        self.apply_options_to_controls()
        self.update_all_visuals()
        self.apply_overlay_options()
        self.update_status("현재 색각 유형의 기본값으로 복원했습니다.")

    def update_all_visuals(self):
        self.update_type_button_state()
        self.update_type_copy()
        self.update_preview_swatches()
        self.strength_value.configure(text=str(int(self.options.correction_strength)))

    def update_type_copy(self):
        label = TYPE_TO_LABEL.get(self.options.cvd_type, "일반 보기")
        self.type_title.configure(text=f"{label} 화면 보정")
        self.type_desc.configure(text=TYPE_DESCRIPTIONS.get(self.options.cvd_type, TYPE_DESCRIPTIONS["normal"]))
        self.filter_title.configure(text=f"{label} 보정 필터")

        if self.options.cvd_type.startswith("protan"):
            self.set_type_color("#FFF1EC", "#F4D8CF", "#D94B3D")
            self.filter_desc.configure(text="빨강은 주황/황색 쪽으로 이동시키고 초록은 유지해 명도 차이를 키웁니다.")
        elif self.options.cvd_type.startswith("deuter"):
            self.set_type_color("#EEF9F2", "#CFEEDB", "#36B26B")
            self.filter_desc.configure(text="초록은 청록 계열로 이동시키고 적색은 유지해 명도/채도 차이를 키웁니다.")
        elif self.options.cvd_type.startswith("tritan"):
            self.set_type_color("#EEF4FF", "#D5E5FF", self.BLUE)
            self.filter_desc.configure(text="파랑은 보라/청록 계열로, 황색은 주황 계열로 이동시킵니다.")
        else:
            self.set_type_color("#F4F7F8", "#E3E9EC", "#DDE5EA")
            self.filter_desc.configure(text="원본에 가까운 화면을 유지합니다.")

    def set_type_color(self, background: str, border: str, color: str):
        self.type_icon.configure(fg_color=background, border_color=border)
        self.type_color_swatch.configure(fg_color=color)

    def update_type_button_state(self):
        active_group = self.options.cvd_type
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
                button.configure(fg_color=self.ACCENT, hover_color=self.ACCENT_DARK, text_color="white", border_color=self.ACCENT)
            else:
                button.configure(fg_color="white", hover_color="#EEF5F2", text_color=self.TEXT, border_color=self.LINE)

    def update_preview_swatches(self):
        before_colors = [
            simulate_cvd_hex(color, self.options.cvd_type)
            for _name, color in self.preview_samples
        ]
        after_colors = [
            corrected_cvd_preview_hex(color, self.options)
            for _name, color in self.preview_samples
        ]

        for (before_block, after_block), before, after in zip(self.swatches, before_colors, after_colors):
            before_block.configure(fg_color=before)
            after_block.configure(fg_color=after)

        pairs = [(0, 1), (2, 3), (2, 4), (1, 5)]
        before_score = sum(color_distance(before_colors[left], before_colors[right]) for left, right in pairs)
        after_score = sum(color_distance(after_colors[left], after_colors[right]) for left, right in pairs)
        delta = round(after_score - before_score)

        if self.options.cvd_type == "normal":
            message = "일반 보기는 시뮬레이션에서도 원본에 가깝게 표시됩니다."
        elif delta > 0:
            message = f"보정 후 선택 유형 기준 색상 간격이 약 {delta}만큼 커졌습니다."
        else:
            message = "효과가 약하면 보정 강도와 대비를 높여보세요."
        self.effect_summary_label.configure(text=message)

    def update_overlay_ui(self, active: bool, backend: str, message: str):
        if active:
            self.hero_title.configure(text="화면 보정이 적용 중입니다")
            self.hero_icon.configure(fg_color="#DDF4E8", border_color="#B8E3CF")
            self.hero_icon_text.configure(text="✓", text_color=self.ACCENT_DARK)
            self.state_value.configure(text="켜짐")
            self.backend_value.configure(text=backend)
            self.control_status_label.configure(
                text=f"켜짐 - {TYPE_TO_LABEL.get(self.options.cvd_type, '일반 보기')} 보정이 현재 화면에 적용 중입니다.",
                text_color=self.ACCENT_DARK,
            )
            for button in self.toggle_buttons:
                button.configure(text="화면 보정 끄기", fg_color=self.RED, hover_color="#A83A2A")
        else:
            self.hero_title.configure(text="화면 보정 시스템")
            self.hero_icon.configure(fg_color="#DDF4E8", border_color="#B8E3CF")
            self.hero_icon_text.configure(text="✓", text_color=self.ACCENT_DARK)
            self.state_value.configure(text="꺼짐")
            self.backend_value.configure(text=backend)
            self.control_status_label.configure(
                text="꺼짐 - 아직 화면에는 적용되지 않았습니다.",
                text_color=self.MUTED,
            )
            for button in self.toggle_buttons:
                button.configure(text="화면 보정 켜기  ›", fg_color=self.ACCENT, hover_color=self.ACCENT_DARK)
        self.update_status(message)

    def save_profile(self):
        profile_name = simpledialog.askstring(
            "프로필 저장",
            "프로필 이름을 입력해 주세요.",
            initialvalue=self.current_profile_name(),
            parent=self,
        )
        if profile_name is None:
            return
        profile_name = profile_name.strip()
        if not profile_name:
            self.update_status("프로필 이름을 입력해 주세요.", error=True)
            return

        target_id = self.selected_profile_id or None
        for profile in self.store.load_profiles():
            if profile.name == profile_name and profile.profile_id != target_id:
                if not messagebox.askyesno("중복 프로필", "같은 이름의 프로필이 있습니다. 이 프로필을 덮어쓸까요?"):
                    return
                target_id = profile.profile_id
                break

        saved = self.store.save_profile_from_options(profile_name, self.options, target_id)
        self.selected_profile_id = saved.profile_id
        self.parent.current_profile = saved
        self.update_status(f"'{saved.name}' 화면 보정 프로필을 저장했습니다.")

    def current_profile_name(self) -> str:
        if self.selected_profile_id:
            profile = self.store.get_profile(self.selected_profile_id)
            if profile:
                return profile.name
        return "내 화면 보정"

    def update_status(self, message: str, error: bool = False):
        color = self.RED if error else self.MUTED
        self.status_label.configure(text=message, text_color=color)
        self.control_message_label.configure(text=self.compact_status_message(message), text_color=color)

    def compact_status_message(self, message: str) -> str:
        if "투명 보정 레이어" in message:
            return "투명 오버레이로 실행 중입니다."
        if "전체 화면 색상 필터" in message or "Windows 색상 필터" in message:
            return "Windows 색상 필터로 실행 중입니다."
        if "반영했습니다" in message:
            return "현재 화면에 반영했습니다."
        if "선택했습니다" in message:
            return "선택 완료 - 켜면 적용됩니다."
        if "기본값" in message:
            return "기본값으로 복원했습니다."
        if "프로필" in message and "저장" in message:
            return "프로필을 저장했습니다."
        if len(message) > 34:
            return f"{message[:31]}..."
        return message
