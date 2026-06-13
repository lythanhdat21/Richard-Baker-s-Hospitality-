from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from src.app.db.models import SyncState


class SyncStateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, property_id: UUID, sync_type: str) -> SyncState | None:
        return (
            self.db.query(SyncState)
            .filter(SyncState.property_id == property_id, SyncState.sync_type == sync_type)
            .first()
        )

    def mark_success(self, property_id: UUID, sync_type: str) -> SyncState:
        state = self.get(property_id, sync_type)
        now = datetime.utcnow()
        if state:
            state.last_synced_at = now
            state.last_success_at = now
            state.last_error_at = None
            state.last_error_code = None
            state.last_error_message = None
        else:
            state = SyncState(
                property_id=property_id,
                sync_type=sync_type,
                last_synced_at=now,
                last_success_at=now,
            )
            self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def mark_error(self, property_id: UUID, sync_type: str, error_code: str, error_message: str) -> SyncState:
        state = self.get(property_id, sync_type)
        now = datetime.utcnow()
        if state:
            state.last_synced_at = now
            state.last_error_at = now
            state.last_error_code = error_code
            state.last_error_message = error_message
        else:
            state = SyncState(
                property_id=property_id,
                sync_type=sync_type,
                last_synced_at=now,
                last_error_at=now,
                last_error_code=error_code,
                last_error_message=error_message,
            )
            self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state
