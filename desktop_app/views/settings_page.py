import customtkinter as ctk


class SettingsPage(ctk.CTkFrame):
    BG = "#F8FBFA"
    CARD = "#FFFFFF"
    LINE = "#E5ECE9"
    TITLE = "#102033"
    MUTED = "#6B7F90"
    ACCENT = "#41B883"

    def __init__(self, parent):
        super().__init__(parent, fg_color=self.BG)
        self.parent = parent
        self.build_ui()

    def build_ui(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=44, pady=34)

        ctk.CTkButton(
            wrapper,
            text="‹  이전",
            width=96,
            height=36,
            fg_color="transparent",
            hover_color="#EEF5F2",
            text_color="#334E63",
            font=("맑은 고딕", 15),
            command=self.parent.show_main_page,
        ).pack(anchor="w")

        card = ctk.CTkFrame(
            wrapper,
            fg_color=self.CARD,
            corner_radius=20,
            border_width=1,
            border_color=self.LINE,
        )
        card.pack(fill="both", expand=True, pady=(92, 0))

        icon = ctk.CTkFrame(card, width=78, height=78, corner_radius=39, fg_color="#DDF4E8")
        icon.pack(pady=(76, 20))
        icon.pack_propagate(False)
        ctk.CTkLabel(
            icon,
            text="⚙",
            font=("Arial", 36, "bold"),
            text_color=self.ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="설정",
            font=("맑은 고딕", 30, "bold"),
            text_color=self.TITLE,
        ).pack()

        ctk.CTkLabel(
            card,
            text="설정 기능은 아직 연결하지 않았습니다.",
            font=("맑은 고딕", 16),
            text_color=self.MUTED,
        ).pack(pady=(10, 0))
