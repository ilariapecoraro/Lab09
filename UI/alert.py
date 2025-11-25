
import flet as ft

class AlertManager:
    def __init__(self, page: ft.Page):
        self._page = page
        self._alert_dialog = ft.AlertDialog(
            title=ft.Text(""),
            actions=[ft.TextButton("OK", on_click=self.close)]
        )

    def show_alert(self, message: str):
        self._alert_dialog.title.value = message
        if self._alert_dialog not in self._page.overlay:
            self._page.overlay.append(self._alert_dialog)
        self._alert_dialog.open = True
        self._page.update()

    def close(self, e):
        self._alert_dialog.open = False
        self._page.update()
