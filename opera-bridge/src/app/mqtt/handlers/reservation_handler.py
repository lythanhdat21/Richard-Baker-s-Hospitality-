import json
import uuid
import aiomqtt
from src.app.services import reservation_service
from src.app.schemas.internal.reservation import ReservationSearchRequest
from src.app.mqtt.topics import result_topic
from src.app.core.logging import get_logger

logger = get_logger(__name__)


async def _publish(client: aiomqtt.Client, topic: str, payload: dict) -> None:
    await client.publish(topic, payload=json.dumps(payload, ensure_ascii=False))


async def handle_search(client: aiomqtt.Client, raw_topic: str, data: dict) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    logger.info("mqtt_reservation_search", trace_id=trace_id)
    try:
        req = ReservationSearchRequest(
            confirmation_number=data.get("confirmation_number"),
            guest_name=data.get("guest_name"),
            arrival_date=data.get("arrival_date"),
            departure_date=data.get("departure_date"),
        )
        results = await reservation_service.search_reservations(req, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": [r.model_dump() for r in results],
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })


async def handle_get(client: aiomqtt.Client, raw_topic: str, data: dict, reservation_id: str) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    logger.info("mqtt_reservation_get", reservation_id=reservation_id, trace_id=trace_id)
    try:
        detail = await reservation_service.get_reservation(reservation_id, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": detail.model_dump(),
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })


async def handle_checkin(client: aiomqtt.Client, raw_topic: str, data: dict, reservation_id: str) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    logger.info("mqtt_checkin", reservation_id=reservation_id, trace_id=trace_id)
    try:
        result = await reservation_service.check_in(reservation_id, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": result.model_dump(),
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })


async def handle_checkout(client: aiomqtt.Client, raw_topic: str, data: dict, reservation_id: str) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    logger.info("mqtt_checkout", reservation_id=reservation_id, trace_id=trace_id)
    try:
        result = await reservation_service.check_out(reservation_id, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": result.model_dump(),
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })
