
import flet as ft
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install

install()
console=Console()

ft.app.error_handler = RichHandler
class GUI:
    def __init__(self, client):
        self.client = client
        self.page = None

    def build(self):
        try:
            self.page = ft.Page(title="Decentralized Client")
            self.page.add(ft.Text("Добро пожаловать в Decentralized Client"))
            send_button = ft.Button(text="Отправить сообщение", on_click=self.send_message)
            self.page.add(send_button)
            return self.page
        except Exception as e:
            console.print_exception(show_locals=True)

    def send_message(self, e):
        message = "Привет!"
        self.client.send_message(message)
        print(f"Сообщение отправлено: {message}")

    def run(self):
        try:
            ft.app(target=self.build)
        except Exception as e:
            console.print_exception(show_locals=True)
