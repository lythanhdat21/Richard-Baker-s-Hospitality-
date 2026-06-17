import asyncio
import json
import aiomqtt
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.mqtt.topics import SUBSCRIBE_PATTERN, RCU_SUBSCRIBE_PATTERN, parse_topic, parse_rcu_topic
from src.app.mqtt.handlers import reservation_handler, room_handler
from src.app.services import sync_service
import uuid

logger = get_logger(__name__)

RECONNECT_DELAY = 5  # giây chờ trước khi reconnect


async def _dispatch(client: aiomqtt.Client, topic: str, data: dict) -> None:
    # Legrand RCU: SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}
    rcu = parse_rcu_topic(topic)
    if rcu is not None:
        project_id, room_id = rcu
        await room_handler.handle_rcu_status(client, topic, data, project_id=project_id, room_id=room_id)
        return

    action, parts = parse_topic(topic)

    # hotel/{hotel_id}/reservation/search/request
    if action == "reservation/search/request":
        await reservation_handler.handle_search(client, topic, data)

    # hotel/{hotel_id}/reservation/{id}/get/request
    elif len(parts) == 6 and parts[2] == "reservation" and parts[4] == "get" and parts[5] == "request":
        await reservation_handler.handle_get(client, topic, data, reservation_id=parts[3])

    # hotel/{hotel_id}/reservation/{id}/checkin/request
    elif len(parts) == 6 and parts[2] == "reservation" and parts[4] == "checkin" and parts[5] == "request":
        await reservation_handler.handle_checkin(client, topic, data, reservation_id=parts[3])

    # hotel/{hotel_id}/reservation/{id}/checkout/request
    elif len(parts) == 6 and parts[2] == "reservation" and parts[4] == "checkout" and parts[5] == "request":
        await reservation_handler.handle_checkout(client, topic, data, reservation_id=parts[3])

    # hotel/{hotel_id}/room/{room_number}/status/get
    elif len(parts) == 6 and parts[2] == "room" and parts[4] == "status" and parts[5] == "get":
        await room_handler.handle_status_get(client, topic, data, room_number=parts[3])

    # hotel/{hotel_id}/room/{room_number}/status/update
    elif len(parts) == 6 and parts[2] == "room" and parts[4] == "status" and parts[5] == "update":
        await room_handler.handle_status_update(client, topic, data, room_number=parts[3])

    # hotel/{hotel_id}/sync/room_status
    elif action == "sync/room_status":
        trace_id = data.get("trace_id") or str(uuid.uuid4())
        await sync_service.sync_room_statuses(trace_id)

    else:
        logger.warning("mqtt_unhandled_topic", topic=topic)


async def _process_message(client: aiomqtt.Client, message: aiomqtt.Message) -> None:
    topic = str(message.topic)
    try:
        raw = message.payload
        data = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, ValueError):
        logger.warning("mqtt_invalid_json", topic=topic)
        return

    try:
        await _dispatch(client, topic, data)
    except Exception:
        logger.exception("mqtt_dispatch_error", topic=topic)


async def run_subscriber() -> None:
    """Chạy vòng lặp subscribe MQTT, tự reconnect khi mất kết nối."""
    while True:
        try:
            logger.info("mqtt_connecting", host=settings.mqtt_host, port=settings.mqtt_port)
            async with aiomqtt.Client(
                hostname=settings.mqtt_host,
                port=settings.mqtt_port,
                identifier=settings.mqtt_client_id,
            ) as client:
                await client.subscribe(SUBSCRIBE_PATTERN)
                await client.subscribe(RCU_SUBSCRIBE_PATTERN)
                logger.info("mqtt_subscribed", patterns=[SUBSCRIBE_PATTERN, RCU_SUBSCRIBE_PATTERN])

                async for message in client.messages:
                    # Mỗi message chạy trong task riêng, không block subscriber loop
                    asyncio.create_task(_process_message(client, message))

        except aiomqtt.MqttError as exc:
            logger.warning("mqtt_disconnected", error=str(exc), retry_in=RECONNECT_DELAY)
            await asyncio.sleep(RECONNECT_DELAY)
        except asyncio.CancelledError:
            logger.info("mqtt_subscriber_stopped")
            return
        except Exception:
            logger.exception("mqtt_unexpected_error", retry_in=RECONNECT_DELAY)
            await asyncio.sleep(RECONNECT_DELAY)
