from uuid import UUID
from sqlalchemy.orm import Session
from src.app.db.models import Property


class PropertyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, property_id: UUID) -> Property | None:
        return self.db.query(Property).filter(Property.id == property_id).first()

    def get_by_property_code(self, property_code: str) -> Property | None:
        return self.db.query(Property).filter(Property.property_code == property_code).first()

    def get_active(self) -> list[Property]:
        return self.db.query(Property).filter(Property.is_active == True).all()

    def create(self, **kwargs) -> Property:
        prop = Property(**kwargs)
        self.db.add(prop)
        self.db.commit()
        self.db.refresh(prop)
        return prop
