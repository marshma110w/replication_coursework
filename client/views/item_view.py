# views/item_view.py
from .base_view import BaseView


class ItemView(BaseView):
    def __init__(self, parent):
        columns = ['id', 'name', 'description', 'barcode', 'category_id', 'weight', 'warehouse_id']
        editable_fields = ['name', 'description', 'barcode', 'weight']
        foreign_keys = {
            'category_id': ('item_categories', 'name'),
            'warehouse_id': ('warehouses', 'name')
        }
        super().__init__(parent, 'items', columns, editable_fields, foreign_keys)
