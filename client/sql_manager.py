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
        Выполняет SQL запрос. SELECT автоматически идёт на реплику.

        :param query: SQL запрос
        :param use_replica: принудительно использовать реплику
        :param params: параметры для запроса
        :param fetch: возвращать результат (только для SELECT)
        :return: результаты запроса или количество изменённых строк
        """
        # Автоматическое определение типа запроса
        query = query.strip()
        if not use_replica and query.lower().startswith("select"):
            use_replica = True

        config = self.replica_config if use_replica else self.master_config
        result = None

        try:
            with psycopg2.connect(**config, cursor_factory=DictCursor) as conn:
                with conn.cursor() as cursor:
                    # Логируем реальный SQL
                    self._log_query(cursor, query, params)

                    # Выполняем
                    cursor.execute(query, params)

                    # Получаем результат
                    if fetch or query.lower().startswith("select"):
                        result = [dict(row) for row in cursor.fetchall()]
                    else:
                        result = cursor.rowcount

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

    def _log_query(self, cursor, query: str, params: tuple | dict | None):
        """
        Логирует SQL-запрос с подставленными значениями и указывает источник (master/replica)
        """
        # Получаем dsn из соединения
        dsn = str(cursor.connection.dsn)

        # Определяем, мастер это или реплика по порту или хосту
        is_replica = (
            f"host={self.replica_config['host']}" in dsn and 
            f"port={self.replica_config['port']}" in dsn
        )

        source = "replica" if is_replica else "master"

        if params:
            try:
                sql_with_values = cursor.mogrify(query, params).decode('utf-8')
            except Exception:
                sql_with_values = f"{query} -- params: {params}"
        else:
            sql_with_values = query

        print(f"[{source}] {sql_with_values}")
