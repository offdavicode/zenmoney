from sqlalchemy.orm import Session

from schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_category(self, payload: CategoryCreate):
        raise NotImplementedError("Category creation has not been implemented yet.")

    def list_categories(self):
        raise NotImplementedError("Category listing has not been implemented yet.")

    def update_category(self, category_id: int, payload: CategoryUpdate):
        raise NotImplementedError("Category update has not been implemented yet.")

    def delete_category(self, category_id: int):
        raise NotImplementedError("Category deletion has not been implemented yet.")

