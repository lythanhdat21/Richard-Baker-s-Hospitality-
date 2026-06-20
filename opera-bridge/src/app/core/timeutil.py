from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def to_vn_str(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
