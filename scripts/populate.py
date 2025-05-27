import psycopg2
from faker import Faker
import random
import json
from typing import List, Dict

# Настройки генерации
NUM_WAREHOUSES = 5
NUM_CATEGORIES = 10
NUM_EMPLOYEES = 100
NUM_ITEMS = 1000

class DataGenerator:
    def __init__(self):
        self.fake = Faker('ru_RU')  # Русские данные
        self.conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="admin",
            password="admin123",
            dbname="test_db"
        )
        self.cur = self.conn.cursor()
        
        # Кэш для хранения ID созданных записей
        self.warehouse_ids: List[int] = []
        self.category_ids: List[int] = []
        self.employee_ids: List[int] = []

    def generate_working_hours(self) -> Dict:
        """Генерация JSON с рабочими часами склада"""
        return {
            "monday": {"open": "08:00", "close": "20:00"},
            "tuesday": {"open": "08:00", "close": "20:00"},
            "wednesday": {"open": "08:00", "close": "20:00"},
            "thursday": {"open": "08:00", "close": "20:00"},
            "friday": {"open": "08:00", "close": "20:00"},
            "saturday": {"open": "10:00", "close": "18:00"},
            "sunday": {"open": "10:00", "close": "16:00"}
        }

    def generate_warehouses(self) -> None:
        """Генерация складов"""
        print("Генерация складов...")
        for _ in range(NUM_WAREHOUSES):
            working_hours = self.generate_working_hours()
            self.cur.execute(
                """INSERT INTO Warehouses (name, address, contact_phone, working_hours, capacity, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    f"Склад {self.fake.street_name()}",
                    self.fake.address(),
                    self.fake.phone_number(),
                    json.dumps(working_hours),
                    random.randint(1000, 5000),
                    random.choice([True, False])
                )
            )
            self.warehouse_ids.append(self.cur.fetchone()[0])
        self.conn.commit()

    def generate_categories(self) -> None:
        """Генерация категорий товаров"""
        print("Генерация категорий товаров...")
        categories = [
            "Электроника", "Одежда", "Продукты", "Книги", "Спорттовары",
            "Мебель", "Косметика", "Игрушки", "Инструменты", "Автозапчасти"
        ]
        
        for category in categories:
            self.cur.execute(
                """INSERT INTO Item_categories (name, description)
                   VALUES (%s, %s) RETURNING id""",
                (category, self.fake.sentence())
            )
            self.category_ids.append(self.cur.fetchone()[0])
        self.conn.commit()

    def generate_employees(self) -> None:
        """Генерация сотрудников"""
        print("Генерация сотрудников...")
        positions = [
            "Менеджер", "Кладовщик", "Грузчик", "Бухгалтер", 
            "Администратор", "Логист", "Охранник"
        ]
        
        for _ in range(NUM_EMPLOYEES):
            warehouse_id = random.choice(self.warehouse_ids)
            self.cur.execute(
                """INSERT INTO Employees (first_name, last_name, email, phone, position, warehouse_id)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    self.fake.first_name(),
                    self.fake.last_name(),
                    self.fake.email(),
                    self.fake.phone_number(),
                    random.choice(positions),
                    warehouse_id
                )
            )
            self.employee_ids.append(self.cur.fetchone()[0])
        self.conn.commit()

    def generate_items(self) -> None:
        """Генерация товаров"""
        print("Генерация товаров...")
        for _ in range(NUM_ITEMS):
            category_id = random.choice(self.category_ids)
            warehouse_id = random.choice(self.warehouse_ids)
            
            self.cur.execute(
                """INSERT INTO Items (name, description, barcode, category_id, weight, warehouse_id)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    self.fake.catch_phrase(),
                    self.fake.text(max_nb_chars=200),
                    self.fake.ean(length=13),
                    category_id,
                    round(random.uniform(0.1, 50.0), 2),
                    warehouse_id
                )
            )
        self.conn.commit()

    def generate_all_data(self) -> None:
        """Генерация всех данных"""
        try:
            self.generate_warehouses()
            self.generate_categories()
            self.generate_employees()
            self.generate_items()
            print("Все данные успешно сгенерированы!")
        except Exception as e:
            print(f"Ошибка при генерации данных: {e}")
            self.conn.rollback()
        finally:
            self.cur.close()
            self.conn.close()

if __name__ == "__main__":
    generator = DataGenerator()
    generator.generate_all_data()
