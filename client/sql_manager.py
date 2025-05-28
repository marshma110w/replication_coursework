import psycopg2
from psycopg2.extras import DictCursor
from config import MASTER_CONFIG, REPLICA_CONFIG
import time


class PostgreSQLManager:
    def __init__(self):
        self.master_config = MASTER_CONFIG
        self.replica_config = REPLICA_CONFIG

    def execute_query(
        self,
        query: str,
        use_replica: bool = False,
        params: tuple | dict | None = None,
        fetch: bool = False
    ) -> list[dict] | int | None:
        """
        Выполняет SQL запрос на master или replica

        :param query: SQL запрос
        :param use_replica: использовать реплику
        :param params: параметры для запроса
        :param fetch: возвращать результат запроса
        :return: результаты запроса или количество изменённых строк
        """
        config = self.replica_config if use_replica else self.master_config
        result = None

        print(f"[Q] {query}")

        try:
            with psycopg2.connect(**config, cursor_factory=DictCursor) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = [dict(row) for row in cursor.fetchall()] if fetch else cursor.rowcount
                    conn.commit()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            raise

        return result

    def execute_script(self, script_path: str, use_replica: bool = False) -> None:
        """Выполняет SQL скрипт из файла"""
        try:
            with open(script_path, 'r') as f:
                queries = [q.strip() for q in f.read().split(';') if q.strip()]

            for query in queries:
                self.execute_query(query, use_replica=use_replica)

            print(f"Script {script_path} executed successfully")
        except Exception as e:
            print(f"Error executing script {script_path}: {e}")
            raise

    def check_connection(self, use_replica: bool = False) -> tuple[bool, float | None]:
        """Проверяет доступность базы данных и возвращает (success, ping_time)"""
        config = self.replica_config if use_replica else self.master_config
        start = time.time()
        try:
            with psycopg2.connect(**config, cursor_factory=DictCursor) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            latency = round((time.time() - start) * 1000, 2)  # в миллисекундах
            return True, latency
        except Exception:
            return False, None
