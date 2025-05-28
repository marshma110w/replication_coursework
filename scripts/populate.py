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
NUM_COURIERS = 10  # количество курьеров

# Реалистичные названия товаров по категориям
CATEGORY_PRODUCTS = {
    "Электроника": [
        "Смартфон", "Планшет", "Ноутбук", "Умные часы", "Наушники",
        "Мышь", "Клавиатура", "Монитор", "Роутер", "Пауэрбанк"
    ],
    "Одежда": [
        "Футболка", "Джинсы", "Куртка", "Шапка", "Перчатки",
        "Пальто", "Свитер", "Юбка", "Брюки", "Обувь"
    ],
    "Продукты": [
        "Хлеб", "Молоко", "Яйца", "Сыр", "Колбаса",
        "Овощной микс", "Фруктовый набор", "Йогурт", "Мясная нарезка", "Сок"
    ],
    "Книги": [
        "Роман", "Повесть", "Поэзия", "Учебник", "Энциклопедия",
        "Фэнтези", "Детектив", "Научпоп", "Комикс", "Журнал"
    ],
    "Спорттовары": [
        "Гантели", "Мяч", "Кроссовки", "Скакалка", "Мат для йоги",
        "Велосипед", "Рюкзак", "Гидратор", "Теннисная ракетка", "Лыжи"
    ],
    "Мебель": [
        "Стул", "Стол", "Диван", "Кровать", "Шкаф",
        "Полка", "Комод", "Кресло", "Тумба", "Вешалка"
    ],
    "Косметика": [
        "Крем", "Тональник", "Помада", "Тушь", "Лосьон",
        "Парфюм", "Маска для лица", "Карандаш для глаз", "Лак для ногтей", "Мужской одеколон"
    ],
    "Игрушки": [
        "Машинка", "Кукла", "Конструктор", "Мяч", "Пазл",
        "Мягкая игрушка", "Настольная игра", "Робот", "Кубики", "Фигурка"
    ],
    "Инструменты": [
        "Молоток", "Отвёртка", "Пила", "Шуруповёрт", "Дрель",
        "Рулетка", "Уровень", "Нож", "Паяльник", "Ключи"
    ],
    "Автозапчасти": [
        "Аккумулятор", "Фильтр масляный", "Тормозные колодки", "Свечи зажигания", "Ремень ГРМ",
        "Амортизатор", "Радиатор", "Стартер", "АКПП", "Топливный фильтр"
    ]
}

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
        self.courier_ids: List[int] = []

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
                """INSERT INTO warehouses (name, address, contact_phone, working_hours, capacity, is_active)
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
            result = self.cur.fetchone()
            if result and len(result) > 0:
                self.warehouse_ids.append(result[0])
            else:
                raise Exception("Не удалось создать склад")
        self.conn.commit()

    def generate_categories(self) -> None:
        """Генерация категорий товаров"""
        print("Генерация категорий товаров...")
        categories = list(CATEGORY_PRODUCTS.keys())
        for category in categories[:NUM_CATEGORIES]:
            self.cur.execute(
                """INSERT INTO item_categories (name, description)
                VALUES (%s, %s) RETURNING id""",
                (category, self.fake.sentence())
            )
            result = self.cur.fetchone()
            if result and len(result) > 0:
                self.category_ids.append(result[0])
            else:
                raise Exception(f"Не удалось создать категорию: {category}")
        self.conn.commit()

    def generate_employees(self) -> None:
        """Генерация сотрудников и курьеров"""
        print("Генерация сотрудников...")
        positions = [
            "Менеджер", "Кладовщик", "Грузчик", "Бухгалтер",
            "Администратор", "Логист", "Охранник"
        ]

        # Генерируем обычных сотрудников
        for _ in range(NUM_EMPLOYEES - NUM_COURIERS):
            warehouse_id = random.choice(self.warehouse_ids)
            position = random.choice(positions)
            self.cur.execute(
                """INSERT INTO Employees (first_name, last_name, email, phone, position, warehouse_id)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    self.fake.first_name(),
                    self.fake.last_name(),
                    self.fake.email(),
                    self.fake.phone_number(),
                    position,
                    warehouse_id
                )
            )
            result = self.cur.fetchone()
            if result:
                emp_id = result[0]
                self.employee_ids.append(emp_id)
            else:
                raise Exception("Не удалось создать сотрудника")

        # Генерируем курьеров
        for _ in range(NUM_COURIERS):
            warehouse_id = random.choice(self.warehouse_ids)
            self.cur.execute(
                """INSERT INTO Employees (first_name, last_name, email, phone, position, warehouse_id)
                VALUES (%s, %s, %s, %s, 'courier', %s) RETURNING id""",
                (
                    self.fake.first_name(),
                    self.fake.last_name(),
                    self.fake.email(),
                    self.fake.phone_number(),
                    warehouse_id
                )
            )
            result = self.cur.fetchone()
            if result:
                emp_id = result[0]
                self.employee_ids.append(emp_id)
                self.courier_ids.append(emp_id)  # ← сохраняем ID курьера
            else:
                raise Exception("Не удалось создать курьера")
        self.conn.commit()

    def generate_items(self) -> None:
        """Генерация товаров с реалистичными названиями"""
        print("Генерация товаров...")

        # Получаем категории из БД
        self.cur.execute("SELECT id, name FROM item_categories")
        categories = self.cur.fetchall()

        if not categories:
            raise Exception("Нет категорий для назначения товаров")

        category_map = {row[1]: row[0] for row in categories}  # {'Электроника': 1, ...}

        # Генерируем товары
        for category_name, product_list in CATEGORY_PRODUCTS.items():
            if category_name not in category_map:
                continue
            category_id = category_map[category_name]

            for _ in range(NUM_ITEMS // len(category_map)):
                name = random.choice(product_list)
                warehouse_id = random.choice(self.warehouse_ids)

                self.cur.execute(
                    """INSERT INTO Items (name, description, barcode, category_id, weight, warehouse_id, quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        name,
                        self.fake.text(max_nb_chars=200),
                        self.fake.ean(length=13),
                        category_id,
                        round(random.uniform(0.1, 50.0), 2),
                        warehouse_id,
                        random.randint(10, 100)
                    )
                )
        self.conn.commit()

    def generate_all_data(self) -> None:
        """Генерация всех данных"""
        self.generate_warehouses()
        self.generate_categories()
        self.generate_employees()
        self.generate_items()
        print("Все данные успешно сгенерированы!")



if __name__ == "__main__":
    generator = DataGenerator()
    generator.generate_all_data()
