import customtkinter as ctk

from views.ishihara_test import IshiharaTestPage


class HomePage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        title = ctk.CTkLabel(

            self,

            text="ColorVision+",

            font=(
                "맑은 고딕",
                45,
                "bold"
            )

        )

        title.pack(
            pady=100
        )

        btn = ctk.CTkButton(

            self,

            text="색각 유형 테스트 시작",

            width=300,
            height=60,

            command=lambda:
            parent.show_frame(
                IshiharaTestPage
            )

        )

        btn.pack()