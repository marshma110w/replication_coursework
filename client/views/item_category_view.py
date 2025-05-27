# views/item_category_view.py
from .base_view import BaseView


class ItemCategoryView(BaseView):
    def __init__(self, parent):
        columns = ['id', 'name', 'description']
        editable_fields = ['name', 'description']
        super().__init__(parent, 'item_categories', columns, editable_fields)
