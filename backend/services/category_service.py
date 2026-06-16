from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from models.budget_alert import BudgetAlert
from models.budget_limit import BudgetLimit
from models.category import Category
from models.recurrence import Recurrence
from models.transaction import Transaction
from models.user import User
from schemas.category import CategoryCreate, CategoryUpdate
from utils.category_rules import UNSPECIFIED_CATEGORY_NAME


class CategoryServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_category(self, current_user: User, payload: CategoryCreate) -> Category:
        parent = self._resolve_parent_category(
            current_user=current_user,
            parent_id=payload.parent_id,
            category_type=payload.type,
        )
        self._ensure_name_available(
            current_user=current_user,
            name=payload.name,
            category_type=payload.type,
        )

        category = Category(
            name=payload.name,
            type=payload.type,
            is_default=False,
            is_essential=payload.is_essential,
            user_id=current_user.id,
            parent_id=parent.id if parent is not None else None,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_categories(self, current_user: User) -> list[Category]:
        statement = (
            select(Category)
            .where(
                (Category.user_id == current_user.id) | (Category.user_id.is_(None))
            )
            .order_by(
                Category.type.asc(),
                Category.is_default.desc(),
                Category.name.asc(),
            )
        )
        return list(self.db.scalars(statement))

    def update_category(
        self,
        current_user: User,
        category_id: int,
        payload: CategoryUpdate,
    ) -> Category:
        category = self._get_mutable_category(current_user, category_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data:
            self._ensure_name_available(
                current_user=current_user,
                name=update_data["name"],
                category_type=category.type,
                ignore_category_id=category.id,
            )
            category.name = update_data["name"]

        if "parent_id" in update_data:
            if update_data["parent_id"] == category.id:
                raise CategoryServiceError("A category cannot be its own parent.", 400)

            parent = self._resolve_parent_category(
                current_user=current_user,
                parent_id=update_data["parent_id"],
                category_type=category.type,
            )
            if parent is not None and self._would_create_parent_cycle(category, parent):
                raise CategoryServiceError("Category hierarchy cannot contain cycles.", 400)
            category.parent_id = parent.id if parent is not None else None

        if "is_essential" in update_data:
            category.is_essential = update_data["is_essential"]

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, current_user: User, category_id: int) -> None:
        category = self._get_mutable_category(current_user, category_id)
        unspecified_category = self._get_unspecified_category(category.type)

        self.db.execute(
            update(Transaction)
            .where(
                Transaction.user_id == current_user.id,
                Transaction.category_id == category.id,
            )
            .values(category_id=unspecified_category.id)
        )
        self.db.execute(
            update(Recurrence)
            .where(
                Recurrence.user_id == current_user.id,
                Recurrence.category_id == category.id,
            )
            .values(category_id=unspecified_category.id)
        )
        self.db.execute(
            delete(BudgetAlert).where(
                BudgetAlert.user_id == current_user.id,
                BudgetAlert.category_id == category.id,
            )
        )
        self.db.execute(
            delete(BudgetLimit).where(
                BudgetLimit.user_id == current_user.id,
                BudgetLimit.category_id == category.id,
            )
        )
        self.db.delete(category)
        self.db.commit()

    def _get_accessible_category(self, current_user: User, category_id: int) -> Category:
        statement = select(Category).where(
            Category.id == category_id,
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        category = self.db.scalar(statement)
        if category is None:
            raise CategoryServiceError("Category not found.", 404)
        return category

    def _get_mutable_category(self, current_user: User, category_id: int) -> Category:
        category = self._get_accessible_category(current_user, category_id)
        if category.is_default or category.user_id is None:
            raise CategoryServiceError("Default categories cannot be modified.", 403)
        return category

    def _get_unspecified_category(self, category_type: str) -> Category:
        statement = select(Category).where(
            Category.name == UNSPECIFIED_CATEGORY_NAME,
            Category.type == category_type,
            Category.is_default.is_(True),
            Category.user_id.is_(None),
        )
        category = self.db.scalar(statement)
        if category is None:
            raise CategoryServiceError(
                "Default unspecified category is not configured.",
                500,
            )
        return category

    def _resolve_parent_category(
        self,
        current_user: User,
        parent_id: int | None,
        category_type: str,
    ) -> Category | None:
        if parent_id is None:
            return None

        parent = self._get_accessible_category(current_user, parent_id)
        if parent.type != category_type:
            raise CategoryServiceError(
                "Parent category must have the same type as the category.",
                400,
            )
        return parent

    def _ensure_name_available(
        self,
        current_user: User,
        name: str,
        category_type: str,
        ignore_category_id: int | None = None,
    ) -> None:
        statement = select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.type == category_type,
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        if ignore_category_id is not None:
            statement = statement.where(Category.id != ignore_category_id)

        existing_category = self.db.scalar(statement)
        if existing_category is not None:
            raise CategoryServiceError(
                "A category with this name already exists for this type.",
                409,
            )

    def _would_create_parent_cycle(self, category: Category, parent: Category) -> bool:
        current_parent = parent
        while current_parent is not None:
            if current_parent.id == category.id:
                return True
            current_parent = current_parent.parent
        return False
