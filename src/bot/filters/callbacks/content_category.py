from aiogram.filters.callback_data import CallbackData


class PickContentCategory(CallbackData, prefix="pick_content"):
    category_id: str


class ContentCategoriesMenu(CallbackData, prefix="content_categories_menu"):
    pass


class EditContentCategoryPath(CallbackData, prefix="edit_content_path"):
    category_id: str
