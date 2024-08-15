import sqlite3
import pickle
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from rich.traceback import Traceback
import traceback
install()
console=Console()


log = logging.getLogger("rich")
  
class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                client_id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_public_key(self, client_id, public_key):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO data (client_id, public_key) VALUES (?, ?)",
                           (client_id, public_key))
            self.conn.commit()
            log.info(f"Публичный ключ клиента {client_id} записан в базу данных.")
        except sqlite3.IntegrityError:
            log.warning(f"Клиент {client_id} уже существует в базе данных.")
            console.print_exception(show_locals=True)

    def update_public_key(self, client_id, public_key):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE data SET public_key = ? WHERE client_id = ?",
                        (public_key, client_id))
            self.conn.commit()
            log.info(f"Публичный ключ клиента {client_id} обновлен в базе данных.")
        except Exception as e:
            log.error(f"Ошибка при обновлении публичного ключа: {e}", exc_info=True)
            console.print_exception(show_locals=True)

    def get_public_key(self, client_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT public_key FROM data WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            log.error(f"Ошибка при получении публичного ключа: {e}", exc_info=True)
            console.print_exception(show_locals=True)
            return None

    def database_exists(self, client_id, current_public_key):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT public_key FROM data WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            
            if result is None:
                self.add_public_key(client_id, current_public_key)
                log.info("Данных о клиенте не найдено. Запись данных в базу.")
                return False
            else:
                stored_public_key = result[0]
                
                if stored_public_key != current_public_key:
                    self.update_public_key(client_id, current_public_key)
                    log.info("Обнаружены изменения в публичном ключе клиента. Обновление данных в базе.")
                    return False
                
                log.info("Данные о клиенте найдены и совпадают с текущими.")
                return True
            
        except Exception as e:
            log.error(f"Ошибка при проверке существования базы данных: {e}", exc_info=True)
            console.print_exception(show_locals=True)
            return False

    def serialize_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM data")
        data = cursor.fetchall()
        return pickle.dumps(data)

    def deserialize_db(self, data):
        records = pickle.loads(data)
        for record in records:
            client_id, public_key = record
            if self.get_public_key(client_id) is None:
                self.add_public_key(client_id, public_key)
            else:
                self.update_public_key(client_id, public_key)
    
    def synchronize_with_peer(self, peer_db_data):
        self.deserialize_db(peer_db_data)
        log.info("База данных успешно синхронизирована с партнером.")
