# views/warehouse_view.py
from .base_view import BaseView


class WarehouseView(BaseView):
    def __init__(self, parent):
        columns = ['id', 'name', 'address', 'contact_phone', 'capacity', 'is_active']
        editable_fields = ['name', 'address', 'contact_phone', 'capacity', 'is_active']
        super().__init__(parent, 'warehouses', columns, editable_fields)
