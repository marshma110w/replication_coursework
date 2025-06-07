# views/shipment_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
        cb = ttk.Combobox(top_bar, textvariable=self.status_var, values=status_options, state='readonly')
        cb.pack(side='left', padx=5)
        cb.bind("<<ComboboxSelected>>", func=lambda x: self.load_data())

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
        self.complete_button.config(state='normal' if status == 'PREPARED' else 'disabled')
        
        # Добавляем кнопку редактирования состава
        if not hasattr(self, 'edit_content_button'):
            self.edit_content_button = ttk.Button(self.action_frame, text="Редактировать состав", command=self.open_edit_content_window)
            self.edit_content_button.pack(side='left', padx=5)

        self.edit_content_button.config(state='normal' if status == 'PENDING' else 'disabled')

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

        # Получаем данные о выдаче, чтобы знать, к какому складу она относится
        query = "SELECT warehouse_id FROM shipments WHERE id = %s"
        shipment_data = self.manager.execute_query(query, params=(self.current_shipment_id,), use_replica=True, fetch=True)
        if not shipment_data:
            messagebox.showerror("Ошибка", "Не удалось получить данные выдачи")
            return

        warehouse_id = shipment_data[0]['warehouse_id']

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

        # Получаем только курьеров с того же склада, что и выдача
        query = """
            SELECT e.id, (e.first_name || ' ' || e.last_name) AS name, e.phone, w.name AS warehouse
            FROM employees e
            JOIN warehouses w ON e.warehouse_id = w.id
            WHERE e.position = 'courier' AND e.warehouse_id = %s
        """

        couriers = self.manager.execute_query(query, params=(warehouse_id,), use_replica=True, fetch=True)

        if not couriers:
            ttk.Label(courier_window, text="Нет доступных курьеров на этом складе").pack(pady=10)
            ttk.Button(courier_window, text="Закрыть", command=courier_window.destroy).pack(pady=5)
            return

        for courier in couriers:
            tree.insert('', 'end', values=(courier['id'], courier['name'], courier['phone'], courier['warehouse']))

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

    def open_edit_content_window(self):
        if not hasattr(self, 'current_shipment_id'):
            return

        # Получаем warehouse_id выдачи
        query = "SELECT warehouse_id FROM shipments WHERE id = %s"
        shipment_data = self.manager.execute_query(query, params=(self.current_shipment_id,), use_replica=True, fetch=True)
        warehouse_id = shipment_data[0]['warehouse_id']

        # Получаем товары из выдачи и склада
        query_in_shipment = """
            SELECT i.id, i.name, si.quantity AS in_shipment_quantity
            FROM shipment_items si
            JOIN items i ON si.item_id = i.id
            WHERE si.shipment_id = %s
            ORDER BY i.name
        """
        in_shipment = self.manager.execute_query(query_in_shipment, params=(self.current_shipment_id,), use_replica=True, fetch=True)
        in_shipment_dict = {row['id']: row for row in in_shipment}

        query_on_warehouse = """
            SELECT id, name, quantity
            FROM items
            WHERE warehouse_id = %s AND quantity > 0
            ORDER BY name
        """
        on_warehouse = self.manager.execute_query(query_on_warehouse, params=(warehouse_id,), use_replica=True, fetch=True)

        # Создаём окно редактирования состава
        edit_window = tk.Toplevel(self.winfo_toplevel())
        edit_window.title("Редактировать состав выдачи")
        edit_window.geometry("800x500")

        # Левый список: товары в выдаче
        left_frame = ttk.LabelFrame(edit_window, text="В выдаче")
        left_list = tk.Listbox(left_frame, selectmode=tk.SINGLE, exportselection=False)
        left_list.pack(fill='both', expand=True, padx=5, pady=5)
        left_frame.pack(side='left', fill='both', expand=True, padx=10)

        # Правый список: товары на складе
        right_frame = ttk.LabelFrame(edit_window, text="На складе")
        right_list = tk.Listbox(right_frame, selectmode=tk.SINGLE, exportselection=False)
        right_list.pack(fill='both', expand=True, padx=5, pady=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=10)

        # Сохраняем ссылки на данные
        left_list.data = {}
        right_list.data = {}

        def refresh_lists():
            left_list.delete(0, tk.END)
            right_list.delete(0, tk.END)
            left_list.data.clear()
            right_list.data.clear()

            # Заполняем левый список
            for item in in_shipment:
                display = f"{item['name']} ({item['in_shipment_quantity']})"
                left_list.insert(tk.END, display)
                left_list.data[left_list.size() - 1] = item

            # Заполняем правый список
            for item in on_warehouse:
                available = item['quantity']
                display = f"{item['name']} (осталось: {available})"
                right_list.insert(tk.END, display)
                right_list.data[right_list.size() - 1] = item

        refresh_lists()

        # Контейнер для кнопок
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(side='left', padx=5)

        def move_right():
            idx = left_list.curselection()
            if not idx:
                return
            item = left_list.data[idx[0]]
            item_id = item['id']

            # Убираем из выдачи
            left_list.delete(idx)
            del left_list.data[idx[0]]

            # Обновляем данные в памяти
            in_shipment[:] = [i for i in in_shipment if i['id'] != item_id]

            # Отправляем обратно на склад
            query = "DELETE FROM shipment_items WHERE shipment_id = %s AND item_id = %s"
            self.manager.execute_query(query, params=(self.current_shipment_id, item_id))

            refresh_lists()

        def move_left():
            idx = right_list.curselection()
            if not idx:
                return
            item = right_list.data[idx[0]]
            item_id = item['id']
            current_quantity = item['quantity']

            # Предлагаем выбрать количество
            qty = simpledialog.askinteger("Количество", f"Сколько взять {item['name']}?", minvalue=1, maxvalue=current_quantity)
            if not qty:
                return

            # Добавляем в выдачу
            query = """
                INSERT INTO shipment_items (shipment_id, item_id, quantity)
                VALUES (%s, %s, %s)
            """
            self.manager.execute_query(query, params=(self.current_shipment_id, item_id, qty))

            # Обновляем данные
            in_shipment.append({
                'id': item_id,
                'name': item['name'],
                'in_shipment_quantity': qty
            })

            refresh_lists()

        ttk.Button(button_frame, text="Удалить →", command=move_right).pack(pady=5)
        ttk.Button(button_frame, text="← Добавить", command=move_left).pack(pady=5)

        ttk.Button(edit_window, text="Закрыть", command=edit_window.destroy).pack(pady=10)