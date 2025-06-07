# views/warehouse_view.py
from views.base_view import BaseView


class WarehouseView(BaseView):
    def __init__(self, parent):
        super().__init__(parent, 'warehouses', ['id', 'name', 'address', 'contact_phone', 'capacity', 'is_active'])

    def get_fields(self):
        return ['name', 'address', 'contact_phone', 'capacity', 'is_active']
