# main.py
import tkinter as tk
from tkinter import ttk
from views.item_category_view import ItemCategoryView
from views.warehouse_view import WarehouseView
from views.item_view import ItemView
from views.employee_view import EmployeeView
from sql_manager import PostgreSQLManager


class ConnectionStatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.manager = PostgreSQLManager()

        self.master_label = ttk.Label(self, text="Master: ...", width=30)
        self.master_label.pack(side='left', padx=10)

        self.replica_label = ttk.Label(self, text="Replica: ...", width=30)
        self.replica_label.pack(side='left', padx=10)

        self.update_status()

    def update_status(self):
        self.check_and_update_label(self.master_label, use_replica=False)
        self.check_and_update_label(self.replica_label, use_replica=True)
        self.after(5000, self.update_status)  # обновление каждые 5 секунд

    def check_and_update_label(self, label, use_replica):
        success, ping = self.manager.check_connection(use_replica=use_replica)
        name = "Replica" if use_replica else "Master"
        if success:
            color = "green"
            text = f"{name}: ✔️ ({ping} ms)"
        else:
            color = "red"
            text = f"{name}: ✖️ (недоступна)"
        label.config(text=text, foreground=color)


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
