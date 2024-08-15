import asyncio
import ssl
import logging
import websockets
from websockets import serve, ConnectionClosedError, exceptions
from security import generate_self_signed_cert
import flet as ft
import os
import requests
from tempfile import gettempdir

log = logging.getLogger("rich")

class DecentralizedClient:
    def __init__(self, client_id, db, page=None):
        self.client_id = client_id
        self.db = db
        self.peer_id = None
        self.connected = False
        self.websocket = None
        self.page = page
        self.message_list = None if page is None else ft.Column()
        self.known_peers = ["192.168.178.10:12345"]
        self.certfile, self.keyfile = generate_self_signed_cert(client_id)

    async def start(self):
        await self.discover_peers()

        if not self.connected:
            log.info("Не удалось найти клиентов. Запуск сервера...")
            await self.start_server()

    async def start_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        async def handler(websocket, path):
            log.info(f"Клиент подключился: {websocket.remote_address}")
            self.websocket = websocket
            await self.handle_client_connection(websocket)

        server = await serve(handler, "0.0.0.0", 12345, ssl=ssl_context)
        log.info("Сервер запущен на 0.0.0.0:12345")
        await server.wait_closed()

    async def discover_peers(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        for address in self.known_peers:
            try:
                log.info(f"Попытка подключения к {address}")
                uri = f"wss://{address}"
                async with websockets.connect(uri, ssl=ssl_context) as websocket:
                    self.connected = True
                    self.websocket = websocket
                    await self.exchange_keys(websocket)
                    await self.synchronize_db(websocket)
                    await self.start_chat(websocket)
                    break
            except (ConnectionRefusedError, ssl.SSLError, websockets.exceptions.InvalidHandshake) as e:
                log.warning(f"Не удалось подключиться: {e}")
                continue

    async def exchange_keys(self, websocket):
        try:
            await websocket.send(self.client_id)
            self.peer_id = await websocket.recv()

            log.info(f"Ключи шифрования успешно обменены с клиентом {self.peer_id}.")
            
        except Exception as e:
            log.error(f"Ошибка обмена ключами: {e}", exc_info=True)

    async def handle_client_connection(self, websocket):
        try:
            await self.exchange_keys(websocket)
            
            peer_data = await websocket.recv()
            self.db.synchronize_with_peer(peer_data)

            local_db_data = self.db.serialize_db()
            await websocket.send(local_db_data)

            await self.start_chat(websocket)
        except Exception as e:
            log.error(f"Ошибка при обработке соединения: {e}", exc_info=True)

    async def synchronize_db(self, websocket):
        try:
            local_db_data = self.db.serialize_db()
            
            if not local_db_data:
                log.warning("База данных пуста, синхронизация не выполняется.")
                return
            
            await websocket.send(local_db_data)
            log.info("База данных успешно синхронизирована.")
        except Exception as e:
            log.error(f"Ошибка синхронизации базы данных: {e}", exc_info=True)

    async def start_chat(self, websocket):
        log.info("Чат начался. Введите '/quit' для выхода.")

        if self.page:
            self.page.add(self.message_list)
            self.page.update()

            input_box = ft.TextField(hint_text="Введите сообщение", expand=True)
            send_button = ft.ElevatedButton("Отправить", on_click=lambda e: asyncio.create_task(self.send_message(input_box.value)))
            send_file_button = ft.ElevatedButton("Отправить файл", on_click=lambda e: asyncio.create_task(self.send_file()))

            self.page.add(ft.Row([input_box, send_button, send_file_button]))
            self.page.update()

            while True:
                await asyncio.sleep(0.1)  # Ожидание в GUI

        else:
            try:
                while True:
                    message = input("Вы: ")
                    if message.lower() == '/quit':
                        log.info("Чат завершен.")
                        break
                    await websocket.send(message)
                    log.info("Сообщение отправлено.")
                    
                    response = await websocket.recv()
                    log.info(f"Получено сообщение: {response}")
                    
                    self.handle_message(response)
            except websockets.exceptions.ConnectionClosedError:
                log.info("Соединение было закрыто.")
            except Exception as e:
                log.error(f"Ошибка в чате: {e}", exc_info=True)
            finally:
                await websocket.close()

    def handle_message(self, message):
        if message.startswith("[File]("):
            file_path = message[7:-1]
            local_path = self.download_file(file_path)
            print(f"Получено файл: {local_path}")
        else:
            print(f"Партнер: {message}")

    def download_file(self, file_url):
        try:
            if file_url.startswith('http'):
                response = requests.get(file_url)
                file_name = os.path.join(gettempdir(), os.path.basename(file_url))
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                return file_name
            else:
                return file_url
        except Exception as e:
            log.error(f"Ошибка загрузки файла: {e}")
            return None

    async def send_message(self, message, file_path=None):
        if file_path:
            message = f"[File]({file_path})"
        await self.websocket.send(message)
        log.info(f"Сообщение отправлено: {message}")

    async def send_file(self):
        file_picker = ft.FilePicker(on_result=lambda e: asyncio.create_task(self.send_message(f"[File]({e.data})")))
        self.page.add(file_picker)
        file_picker.pick_files(file_type=FilePickerFileType.IMAGE)
