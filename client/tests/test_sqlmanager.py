# test_sqlmanager.py
import time
import random
from sql_manager import PostgreSQLManager


def test_read(manager):
    """Тестирование скорости чтения"""
    print("\n[+] Начинаем тестирование чтения...")
    query = "SELECT * FROM items"
    iterations = 1000
    start_time = time.time()

    for i in range(iterations):
        manager.execute_query(query, use_replica=True, fetch=True)
        if i % 100 == 0:
            print(f"Выполнено {i} SELECT-запросов...")

    elapsed = time.time() - start_time
    qps = iterations / elapsed
    print(f"\n[✓] Выполнено {iterations} SELECT-запросов за {elapsed:.2f} секунд")
    print(f"[✓] QPS (запросов в секунду): {qps:.2f}")
    print(f"[✓] RPS (запросов в минуту): {qps * 60:.0f}")


def test_write(manager):
    """Тестирование скорости записи"""
    print("\n[+] Начинаем тестирование записи...")
    warehouse_id = 1
    category_id = 1
    base_name = "Тестовый товар"

    insert_query = """
    INSERT INTO items (name, description, barcode, category_id, weight, warehouse_id, quantity)
    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """

    update_query = """
    UPDATE items SET name = %s WHERE id = %s
    """

    delete_query = """
    DELETE FROM items WHERE id = %s
    """

    iterations = 500
    ids = []

    start_time = time.time()
    print("[~] Тестирование INSERT...")

    for i in range(iterations):
        name = f"{base_name}_{i}"
        desc = f"Описание {i}"
        barcode = f"{random.randint(1000000000, 9999999999)}"
        category = random.choice([1, 2])
        weight = round(random.uniform(0.1, 10.0), 2)
        warehouse = random.choice([1, 2])

        result = manager.execute_query(insert_query, params=(
            name, desc, barcode, category, weight, warehouse, 10
        ))

        # rowcount — это количество изменённых строк
        if result == 1:
            # Берём только что добавленный товар по штрихкоду или имени
            check_query = "SELECT id FROM items WHERE name = %s"
            fetched = manager.execute_query(check_query, params=(name,), fetch=True)
            if fetched:
                item_id = fetched[0]['id']
                ids.append(item_id)
            else:
                print(f"[!] Не удалось найти ID для {name}")
        else:
            print("[!] Ошибка при вставке")

    print(f"[~] Выполнено {len(ids)} вставок, начинаем UPDATE...")

    for i, item_id in enumerate(ids):
        new_name = f"Обновлённый товар {i}"
        manager.execute_query(update_query, params=(new_name, item_id))

        if i % 100 == 0:
            print(f"Выполнено {i} UPDATE-запросов...")

    print(f"[~] Выполнены UPDATE-запросы, начинаем DELETE...")

    for i, item_id in enumerate(ids):
        manager.execute_query(delete_query, params=(item_id,))
        if i % 100 == 0:
            print(f"Выполнено {i} DELETE-запросов...")

    elapsed = time.time() - start_time
    tps = len(ids) / elapsed
    print(f"\n[✓] Выполнено {len(ids)} операций записи (INSERT + UPDATE + DELETE) за {elapsed:.2f} секунд")
    print(f"[✓] TPS (операций в секунду): {tps:.2f}")
    print(f"[✓] TPM (операций в минуту): {tps * 60:.0f}")


if __name__ == "__main__":
    manager = PostgreSQLManager()

    print("🟢 Тестирование подключения...")
    master_status, master_ping = manager.check_connection(use_replica=False)
    replica_status, replica_ping = manager.check_connection(use_replica=True)

    print(f"Мастер: {'Доступен' if master_status else 'Недоступен'} ({master_ping or 0} мс)")
    print(f"Реплика: {'Доступна' if replica_status else 'Недоступна'} ({replica_ping or 0} мс)\n")

    test_read(manager)
    test_write(manager)
