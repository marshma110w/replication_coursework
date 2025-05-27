# views/employee_view.py
from .base_view import BaseView


class EmployeeView(BaseView):
    def __init__(self, parent):
        columns = ['id', 'first_name', 'last_name', 'email', 'phone', 'position', 'warehouse_id']
        editable_fields = ['first_name', 'last_name', 'email', 'phone', 'position']
        foreign_keys = {
            'warehouse_id': ('warehouses', 'name')
        }
        super().__init__(parent, 'employees', columns, editable_fields, foreign_keys)
