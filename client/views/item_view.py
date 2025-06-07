# views/item_view.py
from views.base_view import BaseView


class ItemView(BaseView):
    def __init__(self, parent):
        super().__init__(parent, 'items', ['id', 'name', 'description', 'barcode', 'category_id', 'weight', 'warehouse_id'])

    def get_fields(self):
        return ['name', 'description', 'barcode', 'weight']

    def get_foreign_keys(self):
        return {
            'category_id': ('item_categories', 'name'),
            'warehouse_id': ('warehouses', 'name')
        }
