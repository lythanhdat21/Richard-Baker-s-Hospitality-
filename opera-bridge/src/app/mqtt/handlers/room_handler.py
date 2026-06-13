import json
import uuid
import aiomqtt
from src.app.services import room_service
from src.app.schemas.internal.room import RoomStatusUpdateRequest
from src.app.mqtt.topics import result_topic
from src.app.core.logging import get_logger

logger = get_logger(__name__)


async def _publish(client: aiomqtt.Client, topic: str, payload: dict) -> None:
    await client.publish(topic, payload=json.dumps(payload, ensure_ascii=False))


async def handle_status_get(client: aiomqtt.Client, raw_topic: str, data: dict, room_number: str) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    logger.info("mqtt_room_status_get", room_number=room_number, trace_id=trace_id)
    try:
        status = await room_service.get_room_status(room_number, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": status.model_dump(),
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })


async def handle_status_update(client: aiomqtt.Client, raw_topic: str, data: dict, room_number: str) -> None:
    trace_id = data.get("trace_id") or str(uuid.uuid4())
    housekeeping_status = data.get("housekeeping_status", "")
    logger.info("mqtt_room_status_update", room_number=room_number, trace_id=trace_id)
    try:
        req = RoomStatusUpdateRequest(housekeeping_status=housekeeping_status)
        status = await room_service.update_room_status(room_number, req, trace_id)
        await _publish(client, result_topic(raw_topic), {
            "success": True,
            "trace_id": trace_id,
            "data": status.model_dump(),
        })
    except Exception as exc:
        await _publish(client, result_topic(raw_topic), {
            "success": False,
            "trace_id": trace_id,
            "code": getattr(exc, "detail", {}).get("code", "ERROR") if hasattr(exc, "detail") else "ERROR",
            "message": str(exc),
        })
