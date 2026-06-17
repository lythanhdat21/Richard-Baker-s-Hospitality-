"""
Topic schema:

  [Nội bộ — hệ điều khiển gọi backend]
  REQUEST  hotel/{hotel_id}/reservation/search/request
           hotel/{hotel_id}/reservation/{id}/get/request
           hotel/{hotel_id}/reservation/{id}/checkin/request
           hotel/{hotel_id}/reservation/{id}/checkout/request
           hotel/{hotel_id}/room/{room_number}/status/get
           hotel/{hotel_id}/room/{room_number}/status/update
           hotel/{hotel_id}/sync/room_status

  RESULT   same path with /result suffix
           hotel/{hotel_id}/reservation/search/result
           hotel/{hotel_id}/reservation/{id}/checkin/result
           ...

  [Legrand RCU Server — publish trạng thái phòng thực tế]
  STATUS   SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}

           Payload mẫu:
           {
             "floorList": [
               {
                 "floorNo": 10,
                 "roomList": [
                   {"roomNo": "1001", "roomStatus": 2, "airMode": 9, "airNo": 0, "roomTypeNo": 10001},
                   {"roomNo": "1002", "roomStatus": 4, "airMode": 9, "airNo": 0, "roomTypeNo": 10002}
                 ]
               }
             ]
           }
"""

# Topic nội bộ (hệ điều khiển → backend)
SUBSCRIBE_PATTERN = "hotel/#"

# Topic Legrand RCU: SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}
# Dùng wildcard '+' để subscribe tất cả project và tất cả phòng
RCU_SUBSCRIBE_PATTERN = "SMARTHOTEL/STATUS/ROOMSTATUS/+/+"

# Prefix cố định của Legrand RCU
RCU_TOPIC_PREFIX = "SMARTHOTEL/STATUS/ROOMSTATUS"


def parse_rcu_topic(topic: str) -> tuple[str, str] | None:
    """Parse topic Legrand RCU: SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}
    Trả về (project_id, room_id), hoặc None nếu không khớp.
    """
    parts = topic.split("/")
    if len(parts) == 5 and "/".join(parts[:3]) == RCU_TOPIC_PREFIX:
        return (parts[3], parts[4])
    return None


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
