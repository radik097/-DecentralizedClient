
import unittest
from client_module import Client
from unittest.mock import patch, MagicMock
import asyncio

class TestClient(unittest.IsolatedAsyncioTestCase):

    @patch('client_module.websockets.connect')
    async def test_connect(self, mock_connect):
        client = Client('localhost', ['192.168.178.10:12345'])
        mock_connect.return_value.__aenter__.return_value = MagicMock()
        await client.connect()
        self.assertTrue(client.connected)

    async def test_send_message(self):
        client = Client('localhost', ['192.168.178.10:12345'])
        client.websocket = MagicMock()
        client.websocket.closed = False
        with patch.object(client.websocket, 'send', return_value=asyncio.Future()) as mock_send:
            mock_send.return_value.set_result(None)
            await client.send_message('Hello World')
            mock_send.assert_called_with('Hello World')

    async def test_download_file(self):
        client = Client('localhost', ['192.168.178.10:12345'])
        with patch('client_module.requests.get') as mock_get:
            mock_get.return_value.content = b"Test data"
            mock_get.return_value.raise_for_status = MagicMock()
            result = client.download_file('http://example.com/file.txt')
            self.assertIn('file.txt', result)

    async def test_handle_message(self):
        client = Client('localhost', ['192.168.178.10:12345'])
        with patch.object(client, 'download_file', return_value='/path/to/file.txt') as mock_download:
            client.handle_message('[File](http://example.com/file.txt)')
            mock_download.assert_called_with('http://example.com/file.txt')

if __name__ == '__main__':
    unittest.main()
