import asyncio
import ssl
import logging
import websockets
from websockets import serve
from security import generate_self_signed_cert

log = logging.getLogger("rich")

class Server:
    def __init__(self, host, port, certfile, keyfile):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        # self.known_servers = known_servers  # Список известных серверов

    async def start_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        async def handler(websocket, path):
            log.info(f"Клиент подключился: {websocket.remote_address}")
            await self.handle_client_connection(websocket)

        server = await serve(handler, self.host, self.port, ssl=ssl_context)
        log.info(f"Сервер запущен на {self.host}:{self.port}")
        await server.wait_closed()

    async def connect_to_server(self, server_address):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with websockets.connect(f"wss://{server_address}", ssl=ssl_context) as websocket:
                log.info(f"Успешно подключились к серверу {server_address}")
                return True
        except ConnectionRefusedError:
            log.info(f"Не удалось подключиться к серверу {server_address}")
            return False

    async def check_known_servers_and_start(self):
        for server_address in self.known_servers:
            connected = await self.connect_to_server(server_address)
            if connected:
                log.info(f"Подключение к серверу {server_address} установлено. Собственный сервер запускаться не будет.")
                return

        log.info("Не удалось подключиться ни к одному серверу. Запуск собственного сервера.")
        await self.start_server()

    async def handle_client_connection(self, websocket):
        try:
            async for message in websocket:
                log.info(f"Получено сообщение: {message}")
                response = self.process_message(message)
                await websocket.send(response)
        except websockets.ConnectionClosed:
            log.info(f"Соединение закрыто с {websocket.remote_address}")
        except Exception as e:
            log.error(f"Ошибка обработки соединения: {e}")

    def process_message(self, message):
        # Простая эхо-логика для демонстрации
        return f"Эхо: {message}"

