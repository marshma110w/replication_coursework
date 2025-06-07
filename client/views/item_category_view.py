# views/item_category_view.py
from views.base_view import BaseView


class ItemCategoryView(BaseView):
    def __init__(self, parent):
        super().__init__(parent, 'item_categories', ['id', 'name', 'description'])

    def get_fields(self):
        return ['name', 'description']
