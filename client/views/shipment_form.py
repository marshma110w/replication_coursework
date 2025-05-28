# views/shipment_form.py
import tkinter as tk
from tkinter import ttk, messagebox
from sql_manager import PostgreSQLManager


class ShipmentForm(ttk.Frame):
    def __init__(self, parent, shipment_id=None):
        super().__init__(parent)
        self.manager = PostgreSQLManager()
        self.shipment_id = shipment_id

        self.warehouse_var = tk.StringVar()
        self.item_vars = []  # (item_id, check_var, spin_var)

        self.create_widgets()

    def create_widgets(self):
        warehouses = self.get_warehouses()

        # Склад
        ttk.Label(self, text="Склад").pack(anchor='w', padx=10, pady=5)
        self.warehouse_combo = ttk.Combobox(
            self,
            textvariable=self.warehouse_var,
            state='readonly'
        )
        self.warehouse_combo['values'] = [f"{w[0]} - {w[1]}" for w in warehouses]
        self.warehouse_combo.pack(fill='x', padx=10, pady=5)
        self.warehouse_combo.bind("<<ComboboxSelected>>", lambda e: self.load_items())

        # Контейнер для списка товаров
        self.items_container = ttk.Frame(self)
        self.items_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.items_label_frame = None
        self.scrollable_items_frame = None

        # Кнопка "Сохранить"
        self.save_button = ttk.Button(self, text="Сохранить", command=self.save, state='disabled')
        self.save_button.pack(pady=10)

    def get_warehouses(self):
        query = "SELECT id, name FROM warehouses"
        return [(row['id'], row['name']) for row in self.manager.execute_query(query, use_replica=True, fetch=True)]

    def load_items(self):
        # Очищаем предыдущие виджеты
        if self.scrollable_items_frame:
            for widget in self.scrollable_items_frame.winfo_children():
                widget.destroy()

        warehouse_str = self.warehouse_combo.get()
        warehouse_id = int(warehouse_str.split(' ')[0])

        # Получаем товары на складе
        items = self.get_items_with_quantity(warehouse_id)

        if not items:
            if self.items_label_frame:
                self.items_label_frame.destroy()
            self.items_label_frame = ttk.Label(self.items_container, text="На этом складе нет товаров")
            self.items_label_frame.pack()
            self.save_button.config(state='disabled')
            return

        if self.items_label_frame:
            self.items_label_frame.destroy()
        self.items_label_frame = ttk.LabelFrame(self.items_container, text="Товары")
        self.items_label_frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(self.items_label_frame)
        scrollbar = ttk.Scrollbar(self.items_label_frame, orient="vertical", command=canvas.yview)
        self.scrollable_items_frame = ttk.Frame(canvas)

        self.scrollable_items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Товары
        self.item_vars = []

        for item_id, name, quantity in items:
            item_frame = ttk.Frame(self.scrollable_items_frame)
            item_frame.pack(fill='x', pady=2)

            check_var = tk.BooleanVar()
            spin_var = tk.IntVar(value=0)

            def on_check(item_frame=item_frame, check_var=check_var, spin_var=spin_var):
                item_frame.children['!spinbox'].config(state='normal' if check_var.get() else 'disabled')

            check = ttk.Checkbutton(
                item_frame,
                text=f"{name} (осталось: {quantity})",
                variable=check_var,
                command=on_check
            )
            check.pack(side='left', padx=5)

            spinbox = ttk.Spinbox(
                item_frame,
                from_=1,
                to=quantity,
                width=5,
                textvariable=spin_var,
                state='disabled'
            )
            spinbox.pack(side='right', padx=5)

            self.item_vars.append((item_id, check_var, spin_var))

        self.save_button.config(state='normal')

    def get_items_with_quantity(self, warehouse_id):
        query = """
        SELECT i.id, i.name, i.quantity
        FROM items i
        WHERE i.warehouse_id = %s AND i.quantity > 0
        ORDER BY i.name
        """
        return [(row['id'], row['name'], row['quantity']) for row in self.manager.execute_query(
            query, params=(warehouse_id,), use_replica=True, fetch=True)]

    def save(self):
        warehouse_str = self.warehouse_combo.get()
        if not warehouse_str:
            messagebox.showerror("Ошибка", "Выберите склад")
            return

        warehouse_id = int(warehouse_str.split(' ')[0])

        selected_items = [
            (item_id, spin_var.get()) 
            for item_id, check_var, spin_var in self.item_vars 
            if check_var.get()
        ]

        if not selected_items:
            messagebox.showerror("Ошибка", "Выберите хотя бы один товар")
            return

        # Создаем выдачу
        query = """
        INSERT INTO shipments (warehouse_id, status) VALUES (%s, 'PENDING') RETURNING id
        """
        result = self.manager.execute_query(query, params=(warehouse_id,), fetch=True)
        shipment_id = result[0]['id']

        # Добавляем товары
        for item_id, quantity in selected_items:
            query = """
            INSERT INTO shipment_items (shipment_id, item_id, quantity)
            VALUES (%s, %s, %s)
            """
            self.manager.execute_query(query, params=(shipment_id, item_id, quantity))

        messagebox.showinfo("Успех", "Выдача создана")
        self.master.destroy()
