# client_module.py
import ssl
import logging
import websockets
from security import generate_self_signed_cert
import os
import requests
from tempfile import gettempdir
from rich.console import Console
from rich.traceback import install
from server_module import Server

install()
console=Console()


log = logging.getLogger("rich")

class DecentralizedClient:
    def __init__(self, client_id, known_peers, page=None):
        self.client_id = client_id
        self.known_peers = known_peers
        self.connected = False
        self.websocket = None
        self.page = page
        self.certfile, self.keyfile = generate_self_signed_cert(client_id)

    async def connect(self):
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
                    break
            except ConnectionRefusedError:
                log.info(f"Не удалось подключиться к {address}")
            except Exception as e:
                log.error(f"Ошибка подключения к {address}: {e} ")
                console.print_exception(show_locals=True)
        log.info("Запуск сервера для обработки соединений.")
        await Server(host="0.0.0.0", port=8080, certfile=self.certfile, keyfile=self.keyfile).start_server()
    async def send_message(self, message, file_path=None):
        if not self.websocket or self.websocket.closed:
            log.error("Соединение не установлено или закрыто.")
            return
        
        if file_path:
            message = f"[File]({file_path})"
        await self.websocket.send(message)
        log.info(f"Сообщение отправлено: {message}")

    def download_file(self, file_url):
        try:
            if file_url.startswith('http'):
                response = requests.get(file_url)
                response.raise_for_status()
                safe_filename = os.path.basename(file_url)
                file_name = os.path.join(gettempdir(), safe_filename)
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                return file_name
            else:
                return file_url
        except requests.RequestException as e:
            log.error(f"Ошибка загрузки файла: {e}")
            console.print_exception(show_locals=True)
            return None

    def handle_message(self, message):
        try:    
            if message.startswith("[File]("):
                file_path = message[7:-1]
                local_path = self.download_file(file_path)
                if local_path:
                    print(f"Получен файл: {local_path}")
                else:
                    print("Ошибка при загрузке файла.")
            else:
                print(f"Партнер: {message}")
        except Exception as e:
            log.error(f"Ошибка обработки сообщения: {e}")
            console.print_exception(show_locals=True)

    #Function start(self)
    async def start(self):
        await self.connect()
        try:
            if self.connected:
                while True:
                    message = await self.websocket.recv()
                    self.handle_message(message)
                    if self.page:
                        self.page.update()
        except ConnectionRefusedError:
            pass
        except websockets.ConnectionClosed:
            log.info("Соединение закрыто.")
        except Exception as e:
            log.error(f"Ошибка обработки соединения: {e}")
            console.print_exception(show_locals=True)
            