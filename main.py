import asyncio
import platform
import logging
from rich.logging import RichHandler
from database import Database
from client import DecentralizedClient
import random
  
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
    await client.start()

if __name__ == "__main__":
    if platform.system() == "Linux" or platform.system() == "Darwin":
        asyncio.run(main())
    else:
        try:
            import flet as ft
            ft.app(target=main)
        except Exception as e:
            log.error(f"Ошибка запуска GUI режима, переключаемся на CLI режим: {e}")
            asyncio.run(main())
