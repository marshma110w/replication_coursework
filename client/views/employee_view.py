# views/employee_view.py
from views.base_view import BaseView


class EmployeeView(BaseView):
    def __init__(self, parent):
        super().__init__(parent, 'employees', [
            'id', 'first_name', 'last_name', 'email', 'phone', 'position', 'warehouse_id'
        ])

    def get_fields(self):
        return ['first_name', 'last_name', 'email', 'phone', 'position']

    def get_foreign_keys(self):
        return {
            'warehouse_id': ('warehouses', 'name')
        }
