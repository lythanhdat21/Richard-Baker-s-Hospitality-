"""
Topic schema:
  REQUEST  hotel/{hotel_id}/reservation/search/request
           hotel/{hotel_id}/reservation/{id}/get/request
           hotel/{hotel_id}/reservation/{id}/checkin/request
           hotel/{hotel_id}/reservation/{id}/checkout/request
           hotel/{hotel_id}/room/{room_number}/status/get
           hotel/{hotel_id}/room/{room_number}/status/update
           hotel/{hotel_id}/sync/room_status

  RESULT   same path with /result suffix (or replace trailing segment)
           hotel/{hotel_id}/reservation/search/result
           hotel/{hotel_id}/reservation/{id}/checkin/result
           ...
"""

SUBSCRIBE_PATTERN = "hotel/#"


def result_topic(request_topic: str) -> str:
    """Chuyển topic request → result bằng cách đổi đuôi cuối."""
    parts = request_topic.rsplit("/", 1)
    return f"{parts[0]}/result"


def parse_topic(topic: str) -> tuple[str, list[str]]:
    """Trả về (action_key, [hotel_id, ...parts]) để dispatch."""
    parts = topic.split("/")
    if len(parts) < 3 or parts[0] != "hotel":
        return ("unknown", parts)

    # hotel/{hotel_id}/reservation/search/request  → len=5
    # hotel/{hotel_id}/reservation/{id}/checkin/request → len=6
    # hotel/{hotel_id}/room/{room}/status/get  → len=6
    # hotel/{hotel_id}/sync/room_status → len=4
    action = "/".join(parts[2:])
    return (action, parts)
