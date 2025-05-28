# views/base_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from sql_manager import PostgreSQLManager
import tkinter.font as tkfont


class BaseView(ttk.Frame):
    def __init__(self, parent, table_name, columns, editable_fields, foreign_keys=None):
        super().__init__(parent)
        self.manager = PostgreSQLManager()
        self.table_name = table_name
        self.columns = columns
        self.editable_fields = editable_fields
        self.foreign_keys = foreign_keys or {}

        self.font = tkfont.nametofont("TkDefaultFont")  # Используется для расчёта ширины текста
        self.min_column_width = 100
        self.max_column_width = 300

        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)

        self.tree.pack(fill='both', expand=True)

        self.load_data()

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5, fill='x')

        self.add_button = ttk.Button(button_frame, text="Добавить", command=self.open_add_window)
        self.add_button.pack(side='left', padx=5)

        self.edit_button = ttk.Button(button_frame, text="Редактировать", command=self.open_edit_window)
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

        self.adjust_column_widths()

    def adjust_column_width(self, column, data_samples):
        max_width = max(
            self.font.measure(str(value)) + 20  # добавляем отступ
            for value in [column] + [row[column] for row in data_samples]
        )
        max_width = max(max_width, self.min_column_width)
        max_width = min(max_width, self.max_column_width)
        self.tree.column(column, width=int(max_width))

    def adjust_column_widths(self):
        data_samples = []
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            data_samples.append({col: values[i] for i, col in enumerate(self.columns)})

        for col in self.columns:
            self.adjust_column_width(col, data_samples)

    def open_add_window(self):
        self.open_edit_window()

    def open_edit_window(self, item_id=None):
        edit_window = tk.Toplevel(self.winfo_toplevel())
        edit_window.title("Добавить/Редактировать запись")

        entries = {}
        data = None

        if item_id:
            edit_window.title("Редактировать запись")
            data = self.get_record(item_id)

        for i, field in enumerate(self.editable_fields):
            ttk.Label(edit_window, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            if data:
                entry.insert(0, data[field])
            entries[field] = entry

        for i, (fk_field, (table, display_field)) in enumerate(self.foreign_keys.items()):
            ttk.Label(edit_window, text=fk_field).grid(row=i + len(self.editable_fields), column=0, padx=5, pady=5)
            combo = ttk.Combobox(edit_window)
            combo.grid(row=i + len(self.editable_fields), column=1, padx=5, pady=5)
            combo['values'] = [str(x) for x in self.get_fk_values(table, display_field)]
            if data:
                combo.set(str(data[fk_field]))
            entries[fk_field] = combo

        def save():
            values = {k: v.get() for k, v in entries.items()}
            try:
                if item_id:
                    self.update_record(item_id, values)
                else:
                    self.insert_record(values)
                self.load_data()
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        ttk.Button(edit_window, text="Сохранить", command=save).grid(row=len(self.editable_fields) + len(self.foreign_keys), column=0, columnspan=2, pady=5)

    def get_record(self, item_id):
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        result = self.manager.execute_query(query, params=(item_id,), use_replica=True, fetch=True)
        if result:
            return result[0]
        return {}

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
