from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from src.app.db.models import RetryQueue


class RetryQueueRepository:
    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, property_id: UUID, operation_type: str, payload: dict, max_attempts: int = 3) -> RetryQueue:
        item = RetryQueue(
            property_id=property_id,
            operation_type=operation_type,
            payload=payload,
            status="pending",
            attempt_count=0,
            max_attempts=max_attempts,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_pending(self, limit: int = 50) -> list[RetryQueue]:
        now = datetime.utcnow()
        return (
            self.db.query(RetryQueue)
            .filter(
                RetryQueue.status == "pending",
                (RetryQueue.next_retry_at == None) | (RetryQueue.next_retry_at <= now),
            )
            .limit(limit)
            .all()
        )

    def mark_processing(self, item_id: UUID) -> None:
        item = self.db.query(RetryQueue).filter(RetryQueue.id == item_id).first()
        if item:
            item.status = "processing"
            self.db.commit()

    def mark_succeeded(self, item_id: UUID) -> None:
        item = self.db.query(RetryQueue).filter(RetryQueue.id == item_id).first()
        if item:
            item.status = "succeeded"
            self.db.commit()

    def mark_failed(self, item_id: UUID, error_code: str, error_message: str, next_retry_at: datetime | None = None) -> None:
        item = self.db.query(RetryQueue).filter(RetryQueue.id == item_id).first()
        if not item:
            return
        item.attempt_count += 1
        item.last_error_code = error_code
        item.last_error_message = error_message
        if item.attempt_count >= item.max_attempts:
            item.status = "failed"
        else:
            item.status = "pending"
            item.next_retry_at = next_retry_at
        self.db.commit()
