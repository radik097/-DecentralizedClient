import asyncio
import platform
import logging
from rich.logging import RichHandler
from database import Database
from client_module import DecentralizedClient
import random
import flet as ft
from flet_core.file_picker import FilePickerFileType
import os
import json
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
import traceback

# Установка rich для улучшенного отображения ошибок
install()
console = Console()

# Настройка логирования с использованием rich
logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[RichHandler()])
log = logging.getLogger("rich")

known_clients = ["192.168.178.10:8080", "172.31.79.68:8080", "192.168.56.1:8080"]
CONFIG_FILE = "known_users.json"

def load_known_users():
    """Загрузка известных пользователей из конфигурационного файла."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return []

def save_known_users(known_users):
    """Сохранение известных пользователей в конфигурационный файл."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(known_users, f)

def generate_client_id():
    """Генерация или загрузка уникального client_id."""
    known_users = load_known_users()

    # Проверка на наличие существующего client_id и его ключей
    for file in os.listdir():
        if file.endswith("_key.pem") and file.split("_")[0] in known_users:
            return file.split("_")[0]

    # Генерация нового client_id
    client_id = str(random.randint(100000, 999999))
    while client_id in known_users:
        client_id = str(random.randint(100000, 999999))
    
    # Сохранение нового client_id
    known_users.append(client_id)
    save_known_users(known_users)

    return client_id

async def main(page=None):
    log.info("Запуск программы")
    client_id = generate_client_id()
    log.info(f"Используется client_id: {client_id}")
    db = Database(f"{client_id}.db")

    client = DecentralizedClient(client_id, known_clients, page)

    if page:
        message_list = ft.Column()
        input_box = ft.TextField(hint_text="Введите сообщение", expand=True)
        
        file_picker = ft.FilePicker(on_result=lambda e: send_file(e.data, client))
        send_button = ft.ElevatedButton("Отправить", on_click=lambda e: send_message(input_box.value, client, message_list, input_box))
        attach_button = ft.ElevatedButton("Прикрепить файл", on_click=lambda e: file_picker.pick_files(file_type=FilePickerFileType.IMAGE))
        
        page.add(message_list)
        page.add(ft.Row([input_box, send_button, attach_button, file_picker]))
        page.update()

    try:
        await client.start()
    except Exception as e:
        console.print_exception(show_locals=True)

def send_message(message, client, message_list, input_box):
    """Отправка сообщения клиенту."""
    asyncio.create_task(client.send_message(message))
    message_list.controls.append(ft.Text(f"Вы: {message}"))

    input_box.value = ""
    input_box.page.update()

def send_file(data, client):
    """Отправка файла клиенту."""
    files_data = json.loads(data)
    files = files_data.get('files', [])

    if files:
        for file in files:
            file_path = file.get('path')
            if file_path:
                asyncio.create_task(client.send_message(f"[File]({file_path})"))

if __name__ == "__main__":
    if platform.system() in ["Linux", "Darwin"]:
        asyncio.run(main())
    else:
        try:
            ft.app(target=main)
        except Exception as e:
            log.error(f"Ошибка запуска GUI режима, переключаемся на CLI режим: {e}")
            console.print_exception()
            asyncio.run(main())
