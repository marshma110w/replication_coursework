# stress_test.py
import time
import random
from concurrent.futures import ThreadPoolExecutor
from sql_manager import PostgreSQLManager


def single_read(manager):
    manager.execute_query("SELECT * FROM items", use_replica=True, fetch=True)


def single_write(manager):
    name = f"Стресс_товар_{random.randint(1000, 9999)}"
    query = """
    INSERT INTO items (name, description, barcode, category_id, weight, warehouse_id, quantity)
    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """
    result = manager.execute_query(query, params=(
        name,
        "Товар для стресс-теста",
        f"{random.randint(1000000000, 9999999999)}",
        1,
        round(random.uniform(0.1, 10.0), 2),
        1,
        10
    ), fetch=True)
    item_id = result[0]['id']

    # Удаляем сразу после создания
    manager.execute_query("DELETE FROM items WHERE id = %s", params=(item_id,))


def stress_read(manager, threads=100):
    print(f"\n[+] Стресс-тестирование чтения ({threads} потоков)...")
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(single_read, manager) for _ in range(1000)]
    print(f"[✓] Все SELECT-запросы завершены")


def stress_write(manager, threads=20):
    print(f"\n[+] Стресс-тестирование записи ({threads} потоков)...")
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(single_write, manager) for _ in range(500)]
    print(f"[✓] Все WRITE-запросы завершены")


if __name__ == "__main__":
    manager = PostgreSQLManager()
    stress_read(manager, threads=50)
    stress_write(manager, threads=20)
