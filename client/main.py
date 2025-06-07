# main.py
import tkinter as tk
from tkinter import ttk

# Импортируем View-классы
from views.item_category_view import ItemCategoryView
from views.warehouse_view import WarehouseView
from views.item_view import ItemView
from views.employee_view import EmployeeView
from views.shipment_view import ShipmentView
from views.connection_status_bar import ConnectionStatusBar


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Распределение нагрузки через репликацию")
        self.root.geometry("800x600")

        # Статус подключения
        self.status_bar = ConnectionStatusBar(self.root)
        self.status_bar.pack(side='bottom', fill='x')

        # Центральная панель с кнопками
        self.create_main_buttons()

    def create_main_buttons(self):
        frame = ttk.Frame(self.root)
        frame.pack(expand=True, fill='both', padx=20, pady=20)

        ttk.Label(frame, text="Выберите раздел", font=("Arial", 14, "bold")).pack(pady=10)

        buttons = [
            ("Категории товаров", ItemCategoryView),
            ("Склады", WarehouseView),
            ("Товары", ItemView),
            ("Сотрудники", EmployeeView),
            ("Выдачи", ShipmentView),
        ]

        for name, view_class in buttons:
            button = ttk.Button(
                frame,
                text=name,
                command=lambda cls=view_class: self.open_window(cls)
            )
            button.pack(fill='x', pady=5)

    def open_window(self, view_class):
        window = tk.Toplevel(self.root)
        window.title(f"Работа с {view_class.__name__}")
        window.geometry("1000x600")

        view_class(window).pack(fill='both', expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
