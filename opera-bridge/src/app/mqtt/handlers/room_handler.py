import asyncio
import json
import uuid
import aiomqtt
from src.app.services import room_service, sync_service
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


async def handle_rcu_status(
    client: aiomqtt.Client, raw_topic: str, data: dict, project_id: str, room_id: str
) -> None:
    """Handler cho topic Legrand RCU: SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}

    Payload mẫu:
    {
      "floorList": [
        {
          "floorNo": 10,
          "roomList": [
            {"roomNo": "1001", "roomStatus": 2, "airMode": 9, "airNo": 0, "roomTypeNo": 10001}
          ]
        }
      ]
    }

    roomStatus mapping (Legrand → OPERA Cloud housekeeping status, theo khảo sát mục 13
    của GATEWAY_OVERVIEW.md — enum housekeeping status thật của OPERA Cloud là PascalCase):
      1 → OCCUPIED   (occupancy, không phải housekeeping — KHÔNG đẩy lên OPERA qua RCU,
                       occupancy do luồng check-in/check-out điều khiển)
      2 → Clean
      3 → Inspected
      4 → Dirty
      5 → OutOfOrder
      6 → OutOfService
    """
    trace_id = str(uuid.uuid4())
    logger.info("mqtt_rcu_status_received", project_id=project_id, room_id=room_id, trace_id=trace_id)

    RCU_HOUSEKEEPING_STATUS_MAP = {
        2: "Clean",
        3: "Inspected",
        4: "Dirty",
        5: "OutOfOrder",
        6: "OutOfService",
    }
    RCU_OCCUPANCY_ONLY_STATUSES = {1}  # OCCUPIED — không map sang housekeeping

    # Thu thập tất cả phòng từ toàn bộ tầng (full JSON có thể có hàng trăm phòng)
    rooms_to_sync: list[tuple[str, str]] = []  # [(room_no, housekeeping_status), ...]
    floor_list = data.get("floorList", [])
    for floor in floor_list:
        for room in floor.get("roomList", []):
            room_no = room.get("roomNo")
            rcu_status = room.get("roomStatus")
            if rcu_status in RCU_OCCUPANCY_ONLY_STATUSES:
                logger.info(
                    "mqtt_rcu_occupancy_status_skipped",
                    room_no=room_no, rcu_status=rcu_status, trace_id=trace_id,
                )
                continue
            housekeeping_status = RCU_HOUSEKEEPING_STATUS_MAP.get(rcu_status)
            if not room_no or housekeeping_status is None:
                logger.warning(
                    "mqtt_rcu_unknown_status",
                    room_no=room_no,
                    rcu_status=rcu_status,
                    trace_id=trace_id,
                )
                continue
            rooms_to_sync.append((room_no, housekeeping_status))

    failed_rooms: list[str] = []

    async def _sync_one(room_no: str, housekeeping_status: str) -> None:
        try:
            req = RoomStatusUpdateRequest(housekeeping_status=housekeeping_status)
            await room_service.update_room_status(room_no, req, trace_id, record_audit=False)
            logger.info("mqtt_rcu_status_synced", room_no=room_no, status=housekeeping_status, trace_id=trace_id)
        except Exception:
            logger.exception("mqtt_rcu_status_sync_failed", room_no=room_no, trace_id=trace_id)
            failed_rooms.append(room_no)

    # Xử lý song song tất cả phòng — tránh bottleneck khi có hàng trăm phòng
    await asyncio.gather(*(_sync_one(r, s) for r, s in rooms_to_sync))

    # Lỗi từng phòng tự retry tự nhiên ở lần publish tiếp theo (xem mục 5.4 GATEWAY_OVERVIEW.md),
    # ở đây chỉ ghi nhận sync_state để theo dõi tình trạng đồng bộ chung.
    if failed_rooms:
        sync_service.record_sync_result(
            "rcu_room_status",
            error_code="OPERA_ERROR",
            error_message=f"{len(failed_rooms)} phòng lỗi: {failed_rooms[:20]}",
        )
    else:
        sync_service.record_sync_result("rcu_room_status")


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
