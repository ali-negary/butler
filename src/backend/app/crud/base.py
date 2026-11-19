from typing import Optional, List, TypeVar, Generic
from sqlmodel import SQLModel, Session, select, update, delete
from datetime import date

T = TypeVar("T", bound=SQLModel)


class CRUDBase:
    """Generic CRUD operations shared across all domain models."""

    def __init__(self, model: type[T]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[T]:
        return db.get(self.model, id)

    def get_by_date(self, db: Session, model_date: date, model_class: Optional[type] = None) -> Optional[T]:
        cls = model_class or self.model
        stmt = select(cls).where(getattr(cls, "date") == model_date)
        return db.exec(stmt).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.exec(stmt).all())

    def create(self, db: Session, *, obj_in: T) -> T:
        db_obj = self.model.model_validate(obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: T, obj_in: T) -> T:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, obj: T) -> None:
        db.delete(obj)
        db.commit()


# ── Date-based CRUD (for models with date as PK) ──────────────────────────

class CRUDByDate:
    """CRUD for models where the primary key is a date field (e.g. DailyVitals, NutritionLog)."""

    def __init__(self, model: type[SQLModel]):
        self.model = model

    def get(self, db: Session, date_value: date) -> Optional[SQLModel]:
        stmt = select(self.model).where(getattr(self.model, "date") == date_value)
        return db.exec(stmt).first()

    def create(self, db: Session, *, obj_in: SQLModel) -> SQLModel:
        db_obj = self.model.model_validate(obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, date_value: date, obj_in: SQLModel) -> SQLModel:
        stmt = (
            update(self.model)
            .where(getattr(self.model, "date") == date_value)
            .values(obj_in.model_dump(exclude_unset=True))
        )
        db.exec(stmt)
        db.commit()
        return self.get(db, date_value)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[SQLModel]:
        stmt = select(self.model)
        if start_date:
            stmt = stmt.where(getattr(self.model, "date") >= start_date)
        if end_date:
            stmt = stmt.where(getattr(self.model, "date") <= end_date)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.exec(stmt).all())

    def delete(self, db: Session, *, date_value: date) -> bool:
        stmt = delete(self.model).where(getattr(self.model, "date") == date_value)
        result = db.exec(stmt)
        db.commit()
        return result.rowcount > 0
