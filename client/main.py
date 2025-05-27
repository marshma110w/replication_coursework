# main.py
import tkinter as tk
from tkinter import ttk
from views.item_category_view import ItemCategoryView
from views.warehouse_view import WarehouseView
from views.item_view import ItemView
from views.employee_view import EmployeeView
from views.connection_status_bar import ConnectionStatusBar


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Инвентаризация")
        self.root.geometry("800x600")

        self.create_menu()

    def create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        entities_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Сущности", menu=entities_menu)

        entities_menu.add_command(label="Категории товаров", command=self.open_item_category)
        entities_menu.add_command(label="Склады", command=self.open_warehouse)
        entities_menu.add_command(label="Товары", command=self.open_item)
        entities_menu.add_command(label="Сотрудники", command=self.open_employee)

        # Статус подключения
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side='bottom', fill='x')
        self.status_bar = ConnectionStatusBar(status_frame)
        self.status_bar.pack()

    def open_item_category(self):
        window = tk.Toplevel(self.root)
        ItemCategoryView(window).pack(fill='both', expand=True)

    def open_warehouse(self):
        window = tk.Toplevel(self.root)
        WarehouseView(window).pack(fill='both', expand=True)

    def open_item(self):
        window = tk.Toplevel(self.root)
        ItemView(window).pack(fill='both', expand=True)

    def open_employee(self):
        window = tk.Toplevel(self.root)
        EmployeeView(window).pack(fill='both', expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
