import asyncio
import platform
import logging
from rich.logging import RichHandler
from database import Database
from client import DecentralizedClient
import random
import flet as ft
from flet_core.file_picker import FilePickerFileType
import os
import json
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
        
        file_picker = ft.FilePicker(on_result=lambda e: send_file(e.data, client))
        send_button = ft.ElevatedButton("Отправить", on_click=lambda e: send_message(input_box.value, client, message_list, input_box))
        attach_button = ft.ElevatedButton("Прикрепить файл", on_click=lambda e: file_picker.pick_files(file_type=FilePickerFileType.IMAGE))
        page.add(message_list)
        page.add(ft.Row([input_box, send_button, attach_button, file_picker]))
        page.update()

    await client.start()

def send_message(message, client, message_list, input_box, file_path=None):
    asyncio.create_task(client.send_message(message, file_path))
    message_list.controls.append(ft.Text(f"Вы: {message}"))

    if file_path:
        message_list.controls.append(ft.Text("Файл прикреплен"))
        message_list.controls.append(ft.Icon(ft.icons.ATTACHMENT))

    input_box.value = ""
    input_box.page.update()

def send_file(data, client):
    files_data = json.loads(data)
    files = files_data.get('files', [])

    if files:
        for file in files:
            file_path = file.get('path')
            if file_path:
                client.send_message(f"[File]({file_path})", file_path=file_path)

if __name__ == "__main__":
    if platform.system() == "Linux" or platform.system() == "Darwin":
        asyncio.run(main())
    else:
        try:
            ft.app(target=main)
        except Exception as e:
            log.error(f"Ошибка запуска GUI режима, переключаемся на CLI режим: {e}")
            asyncio.run(main())
