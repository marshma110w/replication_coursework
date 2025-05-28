# views/shipment_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from sql_manager import PostgreSQLManager
from .shipment_form import ShipmentForm


class ShipmentView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.manager = PostgreSQLManager()

        self.status_var = tk.StringVar(value="PENDING")

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        top_bar = ttk.Frame(self)
        top_bar.pack(fill='x', pady=5)

        ttk.Label(top_bar, text="Фильтр по статусу:").pack(side='left', padx=5)

        status_options = ["PENDING", "PREPARED", "COMPLETED"]
        ttk.Combobox(top_bar, textvariable=self.status_var, values=status_options, state='readonly').pack(side='left', padx=5)

        ttk.Button(top_bar, text="Обновить", command=self.load_data).pack(side='left', padx=5)
        ttk.Button(top_bar, text="Создать выдачу", command=self.open_create_window).pack(side='right', padx=5)

        self.tree = ttk.Treeview(self, show='headings', selectmode='browse')
        self.tree["columns"] = ("id", "warehouse", "status", "courier", "created_at", "completed_at")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100)

        self.tree.pack(fill='both', expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.action_frame = ttk.Frame(self)
        self.action_frame.pack(fill='x', pady=5)

        self.prepare_button = ttk.Button(self.action_frame, text="Собрать выдачу", command=self.prepare_shipment)
        self.complete_button = ttk.Button(self.action_frame, text="Завершить выдачу", command=self.complete_shipment)

        self.prepare_button.pack(side='left', padx=5)
        self.complete_button.pack(side='left', padx=5)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        status = self.status_var.get()
        query = """
        SELECT s.id, w.name AS warehouse, s.status, e.first_name || ' ' || e.last_name AS courier,
               s.created_at, s.completed_at
        FROM shipments s
        LEFT JOIN warehouses w ON s.warehouse_id = w.id
        LEFT JOIN employees e ON s.courier_id = e.id
        WHERE s.status = %s
        ORDER BY s.created_at DESC
        """

        rows = self.manager.execute_query(query, params=(status,), use_replica=True, fetch=True)
        for row in rows:
            self.tree.insert('', 'end', values=[row[col] for col in self.tree["columns"]], tags=(row['id'],))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        shipment_id = self.tree.item(selected[0], 'tags')[0]
        self.current_shipment_id = shipment_id

        # Обновляем доступные действия
        query = "SELECT status FROM shipments WHERE id = %s"
        result = self.manager.execute_query(query, params=(shipment_id,), use_replica=True, fetch=True)
        status = result[0]['status']

        self.prepare_button.config(state='normal' if status == 'PENDING' else 'disabled')
        self.complete_button.config(state= 'normal' if status == 'PREPARED' else 'disabled')

    def prepare_shipment(self):
        if not hasattr(self, 'current_shipment_id'):
            return

        # Получаем товары и количество из shipment_items
        query = "SELECT item_id, quantity FROM shipment_items WHERE shipment_id = %s"
        items = self.manager.execute_query(query, params=(self.current_shipment_id,), use_replica=True, fetch=True)

        # Списываем товары со склада
        try:
            for item in items:
                update_query = """
                UPDATE items SET quantity = quantity - %s
                WHERE id = %s AND quantity >= %s
                """
                updated = self.manager.execute_query(update_query, params=(
                    item['quantity'],
                    item['item_id'],
                    item['quantity']
                ), fetch=False)

                if updated != 1:
                    raise Exception(f"Недостаточно товара ID {item['item_id']} на складе")

            # Обновляем статус выдачи
            query = "UPDATE shipments SET status = 'PREPARED' WHERE id = %s"
            self.manager.execute_query(query, params=(self.current_shipment_id,))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось собрать выдачу: {e}")

    def complete_shipment(self):
        if not hasattr(self, 'current_shipment_id'):
            return

        # Создаем новое окно
        courier_window = tk.Toplevel(self.winfo_toplevel())
        courier_window.title("Выбор курьера")
        courier_window.geometry("600x400")
        courier_window.resizable(False, False)

        ttk.Label(courier_window, text="Выберите курьера:", padding=10).pack(anchor='w')

        # Таблица курьеров
        columns = ("id", "name", "phone", "warehouse")
        tree = ttk.Treeview(courier_window, columns=columns, show="headings", selectmode="browse")
        tree.heading("id", text="ID")
        tree.heading("name", text="Имя")
        tree.heading("phone", text="Телефон")
        tree.heading("warehouse", text="Склад")

        tree.column("id", width=50)
        tree.column("name", width=150)
        tree.column("phone", width=120)
        tree.column("warehouse", width=180)

        scrollbar = ttk.Scrollbar(courier_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y")

        selected_courier_id = None  # Переменная для хранения выбранного ID

        def on_select(event):
            nonlocal selected_courier_id
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                selected_courier_id = item['values'][0]

        tree.bind("<<TreeviewSelect>>", on_select)

        # Получаем курьеров
        query = """
            SELECT e.id, e.first_name || ' ' || e.last_name AS name, e.phone, w.name AS warehouse
            FROM employees e
            JOIN warehouses w ON e.warehouse_id = w.id
            WHERE e.position = 'courier'
        """
        couriers = self.manager.execute_query(query, use_replica=True, fetch=True)

        if not couriers:
            ttk.Label(courier_window, text="Нет доступных курьеров").pack(pady=10)
            ttk.Button(courier_window, text="Закрыть", command=courier_window.destroy).pack(pady=5)
            return

        for courier in couriers:
            tree.insert('', 'end', values=(courier['id'], courier['name'], courier['phone'], courier['warehouse']))

        # Кнопка подтверждения (всегда видна внизу)
        def confirm():
            if not selected_courier_id:
                messagebox.showwarning("Ошибка", "Выберите курьера")
                return
            try:
                query = """
                    UPDATE shipments 
                    SET courier_id = %s, status = 'COMPLETED', completed_at = NOW()
                    WHERE id = %s
                """
                self.manager.execute_query(query, params=(selected_courier_id, self.current_shipment_id))
                courier_window.destroy()
                self.load_data()
                messagebox.showinfo("Успех", "Выдача завершена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось завершить выдачу: {e}")

        ttk.Button(courier_window, text="Подтвердить", command=confirm).pack(pady=10)

    def open_create_window(self):
        window = tk.Toplevel(self.winfo_toplevel())
        window.title("Создать выдачу")
        window.geometry("600x400")
        ShipmentForm(window).pack(fill='both', expand=True)
