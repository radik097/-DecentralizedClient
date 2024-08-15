import asyncio
import platform
import logging
from rich.logging import RichHandler
from database import Database
from client import DecentralizedClient
import random
import flet as ft
import os

# Настройка логирования с использованием rich
logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[RichHandler()])
log = logging.getLogger("rich")

def generate_client_id():
    """Генерация случайного client_id."""
    return str(random.randint(100000, 999999))

async def main(page=None):
    log.info("Запуск программы")
    client_id = generate_client_id()
    log.info(f"Сгенерирован client_id: {client_id}")
    db = Database(f"{client_id}.db")

    client = DecentralizedClient(client_id, db, page)

    if page:
        message_list = ft.Column()
        input_box = ft.TextField(hint_text="Введите сообщение", expand=True)
        file_picker = ft.FilePicker(on_result=lambda e: send_file(e.file_path, client))
        send_button = ft.ElevatedButton("Отправить", on_click=lambda e: send_message(input_box.value, client, message_list, input_box))
        attach_button = ft.ElevatedButton("Прикрепить файл", on_click=lambda e: file_picker.pick_file())

        page.add(message_list)
        page.add(ft.Row([input_box, send_button, attach_button]))
        page.update()

    await client.start()

def send_message(message, client, message_list, input_box):
    asyncio.create_task(client.send_message(message))
    message_list.controls.append(ft.Text(f"Вы: {message}"))
    input_box.value = ""
    input_box.page.update()

def send_file(file_path, client):
    file_type = "photo" if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else "document"
    asyncio.create_task(client.send_message(f"[{file_type}]({file_path})"))

if __name__ == "__main__":
    if platform.system() == "Linux" or platform.system() == "Darwin":
        asyncio.run(main())
    else:
        try:
            ft.app(target=main)
        except Exception as e:
            log.error(f"Ошибка запуска GUI режима, переключаемся на CLI режим: {e}")
            asyncio.run(main())
