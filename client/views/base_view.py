# views/base_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from sql_manager import PostgreSQLManager


class BaseView(ttk.Frame):
    def __init__(self, parent, table_name, columns):
        super().__init__(parent)
        self.manager = PostgreSQLManager()
        self.table_name = table_name
        self.columns = columns

        self.create_widgets()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись для редактирования")
            return
        item_id = self.tree.item(selected[0], 'tags')[0]
        self.open_edit_window(item_id=item_id)

    def create_widgets(self):
        # Таблица
        self.tree = ttk.Treeview(self, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill='both', expand=True)

        self.load_data()

        # Кнопки
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5, fill='x')

        self.add_button = ttk.Button(button_frame, text="Добавить", command=self.open_edit_window)
        self.add_button.pack(side='left', padx=5)

        self.edit_button = ttk.Button(button_frame, text="Редактировать", command=self.edit_selected)
        self.edit_button.pack(side='left', padx=5)

        self.delete_button = ttk.Button(button_frame, text="Удалить", command=self.delete_record)
        self.delete_button.pack(side='left', padx=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = f"SELECT * FROM {self.table_name}"
        result = self.manager.execute_query(query, use_replica=True, fetch=True)
        for record in result:
            self.tree.insert('', 'end', values=tuple(record[col] for col in self.columns), tags=(record['id'],))

    def get_fields(self):
        """
        Шаблонный метод: должен возвращать список полей, доступных для редактирования
        Например: ['name', 'description']
        """
        raise NotImplementedError("Метод get_fields() должен быть переопределён")

    def get_foreign_keys(self):
        """
        Шаблонный метод: возвращает словарь с внешними ключами.
        Например: {'category_id': ('item_categories', 'name')}
        """
        return {}

    def open_edit_window(self, item_id=None):
        edit_window = tk.Toplevel(self.winfo_toplevel())
        edit_window.title("Добавить/Редактировать запись")

        entries = {}
        data = None

        if item_id:
            edit_window.title("Редактировать запись")
            data = self.get_record(item_id)
            print("Данные записи:", data)

        editable_fields = self.get_fields()
        foreign_keys = self.get_foreign_keys()

        for i, field in enumerate(editable_fields):
            ttk.Label(edit_window, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=5)

            # Заполняем значение из data, если это режим редактирования
            if data and field in data:
                entry.insert(0, str(data[field]))
            entries[field] = entry

        fk_vars = {}
        fk_values_map = {}  # для хранения (id, name) для Combobox

        for i, (fk_field, (table, display_field)) in enumerate(foreign_keys.items()):
            ttk.Label(edit_window, text=fk_field).grid(
                row=i + len(editable_fields), column=0, padx=5, pady=5
            )

            values = self.get_fk_values(table, display_field)
            combo = ttk.Combobox(edit_window, values=[v[1] for v in values], state='readonly')
            combo.grid(row=i + len(editable_fields), column=1, padx=5, pady=5)

            # Сохраняем список значений в виджете
            combo.values = values

            # Если это режим редактирования — устанавливаем текущее значение
            if data and fk_field in data:
                current_id = data[fk_field]
                try:
                    idx = next(i for i, v in enumerate(values) if v[0] == current_id)
                    combo.current(idx)
                except StopIteration:
                    combo.set('')  # или можно установить пустой выбор
            else:
                combo.set('')

            fk_vars[fk_field] = combo
            fk_values_map[fk_field] = values

        def save():
            try:
                values = {k: v.get() for k, v in entries.items()}
                fk_values = {
                    fk: combo.values[combo.current()][0]
                    for fk, combo in fk_vars.items()
                }

                combined = {**values, **fk_values}
                if item_id:
                    self.update_record(item_id, combined)
                else:
                    self.insert_record(combined)
                self.load_data()
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        ttk.Button(edit_window, text="Сохранить", command=save).grid(
            row=len(editable_fields) + len(foreign_keys), column=0, columnspan=2, pady=5
        )

    def get_record(self, item_id):
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        result = self.manager.execute_query(query, params=(item_id,), use_replica=True, fetch=True)
        return result[0] if result else {}

    def get_fk_values(self, table, display_field):
        query = f"SELECT id, {display_field} FROM {table}"
        result = self.manager.execute_query(query, use_replica=True, fetch=True)
        return [(row['id'], row[display_field]) for row in result]

    def insert_record(self, values):
        fields = ', '.join(values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        query = f"INSERT INTO {self.table_name} ({fields}) VALUES ({placeholders})"
        self.manager.execute_query(query, params=tuple(values.values()))

    def update_record(self, item_id, values):
        set_clause = ', '.join([f"{k} = %s" for k in values])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s"
        params = tuple(values.values()) + (item_id,)
        self.manager.execute_query(query, params=params)

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        item_id = self.tree.item(selected[0], 'tags')[0]
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            query = f"DELETE FROM {self.table_name} WHERE id = %s"
            self.manager.execute_query(query, params=(item_id,))
            self.load_data()
