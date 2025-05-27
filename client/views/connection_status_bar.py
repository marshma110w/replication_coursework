from tkinter import ttk
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
