
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

    async def start_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        async def handler(websocket, path):
            log.info(f"Клиент подключился: {websocket.remote_address}")
            await self.handle_client_connection(websocket)

        server = await serve(handler, self.host, self.port, ssl=ssl_context)
        log.info(f"Сервер запущен на {self.host}:{self.port}")
        await server.wait_closed()

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
