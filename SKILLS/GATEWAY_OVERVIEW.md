# Hospitality Integration Gateway — Tổng quan dự án

> **MQTT (Legrand RCU) ↔ Backend cầu nối ↔ Oracle OPERA Cloud**

---

## 1. Kiến trúc tổng thể

```
┌─────────────────────┐     MQTT      ┌──────────────────────────────────────┐   HTTPS/OAuth 2.0   ┌──────────────────────┐
│  Legrand RCU System │ ────────────▶ │      Backend cầu nối nội bộ          │ ──────────────────▶ │   Oracle OPERA Cloud │
│                     │               │  (Linux Server / Docker Container)   │                     │   OHIP-FOUNDATION    │
│  • RCU Server       │               │                                      │                     │   ~20 API Endpoints  │
│  • RCU Units        │               │  [aiomqtt]  [Mapper]  [httpx+async]  │                     │                      │
└─────────────────────┘               │  Mosquitto MQTT Broker (port 1883)   │                     └──────────────────────┘
                                      └──────────────────────────────────────┘
```

**Nguyên tắc cốt lõi:**
- RCU gửi sự kiện (room status, check-in, check-out) qua **MQTT**.
- Backend subscribe MQTT, xử lý và gọi đúng endpoint **Oracle OPERA Cloud** qua HTTPS.
- Hệ điều khiển nội bộ không tiếp xúc trực tiếp với API Oracle — toàn bộ complexity được che giấu sau Backend.
- OAuth token với OPERA Cloud do Backend tự quản lý, tự refresh — không để lộ ra ngoài.

---

## 2. Luồng dữ liệu (Workflow)

### 2.1 Luồng MQTT → OPERA Cloud

```
RCU Unit gửi sự kiện
        │
        ▼ (MQTT publish)
Mosquitto Broker (port 1883)
        │
        ▼ (aiomqtt subscribe)
mqtt/subscriber.py
        │
        ▼
mqtt/handlers/  (reservation_handler | room_handler)
        │
        ▼
services/       (reservation_service | room_service)
        │
        ▼
mappers/        (Internal DTO → OPERA Cloud DTO)
        │
        ▼
clients/opera_cloud_client.py  (httpx + asyncio)
        │
        ▼ (HTTPS + Bearer token)
Oracle OPERA Cloud API
        │
        ▼
mappers/        (OPERA Cloud response → Internal response)
        │
        ▼
Ghi log + cập nhật DB (sync_state, audit_events)
```

### 2.2 Luồng REST API nội bộ

```
Hệ điều khiển  ──(X-Internal-API-Key)──▶  api/routes/  ──▶  services/  ──▶  clients/  ──▶  OPERA Cloud
```

### 2.3 Đồng bộ định kỳ trạng thái phòng

```
jobs/room_status_sync.py  ──▶  room_service  ──▶  OPERA Cloud  ──▶  cập nhật sync_state
```

---

## 3. Cấu trúc thư mục

```
opera-bridge/
│
├── src/
│   └── app/
│       ├── main.py                        # Entrypoint FastAPI
│       │
│       ├── api/routes/                    # REST endpoints nội bộ
│       │   ├── health.py                  # GET /health
│       │   ├── reservations.py            # GET|POST /reservations/...
│       │   ├── rooms.py                   # GET|PATCH /rooms/...
│       │   └── guests.py                  # GET /guests/...
│       │
│       ├── mqtt/                          # MQTT layer
│       │   ├── subscriber.py              # aiomqtt subscriber chính
│       │   ├── topics.py                  # Định nghĩa MQTT topics
│       │   └── handlers/
│       │       ├── reservation_handler.py
│       │       └── room_handler.py
│       │
│       ├── services/                      # Business logic
│       │   ├── reservation_service.py
│       │   ├── room_service.py
│       │   ├── guest_service.py
│       │   ├── folio_service.py
│       │   └── sync_service.py
│       │
│       ├── mappers/                       # Chuyển đổi Internal ↔ OPERA Cloud
│       │   ├── reservation_mapper.py
│       │   ├── room_mapper.py
│       │   ├── guest_mapper.py
│       │   └── folio_mapper.py
│       │
│       ├── clients/                       # HTTP client gọi OPERA Cloud
│       │   ├── opera_cloud_client.py      # httpx AsyncClient
│       │   └── opera_auth_client.py       # OAuth2 token + auto-refresh
│       │
│       ├── schemas/                       # Pydantic DTOs
│       │   ├── internal/                  # DTO dùng trong hệ thống nội bộ
│       │   │   ├── reservation.py
│       │   │   ├── room.py
│       │   │   ├── guest.py
│       │   │   ├── folio.py
│       │   │   └── error.py
│       │   └── opera/                     # DTO map với OPERA Cloud API
│       │       ├── reservation.py
│       │       └── room.py
│       │
│       ├── db/                            # Database layer
│       │   ├── models.py                  # SQLAlchemy models
│       │   ├── session.py
│       │   └── repositories/
│       │       ├── mapping_repository.py
│       │       ├── property_repository.py
│       │       ├── retry_queue_repository.py
│       │       └── sync_state_repository.py
│       │
│       ├── core/                          # Cấu hình lõi
│       │   ├── config.py                  # Settings từ .env
│       │   ├── logging.py                 # structlog setup
│       │   └── security.py               # X-Internal-API-Key validation
│       │
│       ├── middlewares/
│       │   └── request_logging.py
│       │
│       ├── jobs/
│       │   └── room_status_sync.py        # Sync định kỳ room status
│       │
│       └── utils/
│           ├── retry.py                   # Retry logic (tenacity)
│           └── error_normalizer.py        # Chuẩn hóa lỗi từ OPERA Cloud
│
├── alembic/                               # Database migrations
│   └── versions/
│       └── 001_initial_schema.py
│
├── Dockerfile
├── docker-compose.yml
├── mosquitto.conf                         # Cấu hình Mosquitto MQTT Broker
├── pyproject.toml
├── requirements.txt
└── .env                                   # Credentials (không commit)
```

---

## 4. API Endpoints nội bộ

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/health` | Kiểm tra trạng thái service |
| `GET` | `/reservations/search` | Tìm đặt phòng theo mã, tên, ngày |
| `GET` | `/reservations/{id}` | Lấy chi tiết một đặt phòng |
| `POST` | `/reservations/{id}/check-in` | Ghi nhận check-in |
| `POST` | `/reservations/{id}/check-out` | Ghi nhận check-out |
| `GET` | `/rooms/{room_number}/status` | Lấy trạng thái phòng |
| `PATCH` | `/rooms/{room_number}/status` | Cập nhật housekeeping status |
| `GET` | `/guests/{profile_id}` | Lấy thông tin khách |

**Xác thực:** Header `X-Internal-API-Key` cho tất cả endpoint.

---

## 5. MQTT — Legrand RCU Topic & Payload

### 5.1 Cấu trúc Topic

```
SMARTHOTEL/STATUS/ROOMSTATUS/{project_id}/{room_id}
                               ────────    ─────────
                               Cố định     Thay đổi
                               theo dự án  theo từng phòng
```

- `project_id` (vd: `8888`): định danh dự án, cấu hình trong `.env` theo từng công trình.
- `room_id` (vd: `1253044848`): ID phòng do Legrand RCU cấp, mỗi phòng một topic riêng.

Backend subscribe bằng wildcard: `SMARTHOTEL/STATUS/ROOMSTATUS/+/+`

### 5.2 Cấu trúc Payload JSON

Mỗi message chứa **toàn bộ trạng thái khách sạn** — tập hợp hàng trăm phòng trải qua nhiều tầng:

```json
{
  "floorList": [
    {
      "floorNo": 10,
      "roomList": [
        { "roomNo": "1001", "roomStatus": 2, "airMode": 9, "airNo": 0, "roomTypeNo": 10001 },
        { "roomNo": "1002", "roomStatus": 4, "airMode": 9, "airNo": 0, "roomTypeNo": 10002 }
      ]
    },
    {
      "floorNo": 11,
      "roomList": [ "..." ]
    }
  ]
}
```

> Đây chỉ là ví dụ rút gọn. Full JSON thực tế gồm **hàng trăm phòng** trải qua nhiều tầng.

### 5.3 Mapping roomStatus → OPERA Cloud

| `roomStatus` (Legrand) | Ý nghĩa | OPERA Cloud Housekeeping Status |
|------------------------|---------|----------------------------------|
| `1` | OCCUPIED | _Không map_ — đây là occupancy, không phải housekeeping. Occupancy do luồng check-in/check-out điều khiển, RCU không đẩy giá trị này lên OPERA. |
| `2` | CLEAN | `Clean` |
| `3` | INSPECT | `Inspected` |
| `4` | DIRTY | `Dirty` |
| `5` | OUT OF ORDER | `OutOfOrder` |
| `6` | OUT OF SERVICE | `OutOfService` |

> Enum housekeeping status thật của OPERA Cloud (API `PUT /hsk/v1/hotels/{hotelId}/rooms/status`)
> là PascalCase: `Clean`, `Dirty`, `Pickup`, `Inspected`, `OutOfOrder`, `OutOfService`.

### 5.4 Đặc điểm publish của Legrand RCU

> **Confirmed:** MQTT của Legrand RCU là **event-driven** — publish **tức thời** khi có thay đổi trạng thái phòng, không theo chu kỳ cố định.  
> Mỗi lần publish là **full JSON chứa toàn bộ phòng** — không phải delta.

Hệ quả thiết kế:

| Vấn đề | Hệ quả |
|--------|--------|
| **Retry** | Nếu sync 1 phòng lỗi, lần publish tiếp theo (khi bất kỳ phòng nào thay đổi) sẽ gửi lại full JSON → phòng lỗi được retry tự nhiên, không cần retry queue riêng cho MQTT |
| **Idempotent** | `update_room_status` phải an toàn khi gọi nhiều lần với cùng giá trị (không tạo duplicate record) |
| **Debounce** | Không cần — mỗi publish là sự kiện có ý nghĩa thực sự, không phải polling lặp lại |

### 5.5 Xử lý hiệu năng

Vì payload chứa hàng trăm phòng, backend dùng `asyncio.gather()` để **sync song song toàn bộ phòng** thay vì tuần tự:

```
parse floorList → collect tất cả (room_no, status)
        │
        ▼
asyncio.gather(sync phòng 1, sync phòng 2, ..., sync phòng N)  ← song song
        │
        ▼
update_room_status → OPERA Cloud (idempotent, mỗi phòng một request)
```

---

## 6. Database — 6 bảng chính

| Bảng | Mục đích |
|------|----------|
| `properties` | Thông tin khách sạn / property |
| `integration_mappings` | Mapping ID nội bộ ↔ OPERA Cloud ID |
| `sync_states` | Trạng thái đồng bộ gần nhất |
| `api_request_logs` | Log từng lần gọi API |
| `retry_queue` | Hàng đợi retry khi gặp lỗi tạm thời |
| `audit_events` | Audit log nghiệp vụ |

---

## 7. Stack công nghệ

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python 3.11, FastAPI |
| MQTT | aiomqtt, Mosquitto Broker |
| HTTP Client | httpx + asyncio |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| Logging | structlog |
| Retry | tenacity |
| Deploy | Docker, docker-compose |

---

## 8. Lộ trình MVP

| Giai đoạn | Nội dung |
|-----------|----------|
| **1 — Khảo sát** | Xác định dữ liệu RCU cần trao đổi, chọn ~20 endpoint OPERA Cloud, test bằng Postman |
| **2 — Thiết kế contract** | Định nghĩa DTO nội bộ, mã lỗi chuẩn, mapping schema |
| **3 — Build backend** | Implement auth, HTTP client, services, MQTT handlers, retry/log |
| **4 — Kiểm thử tích hợp** | Chạy với OPERA Cloud sandbox, đo thời gian phản hồi, hoàn thiện docs vận hành |

---

## 9. Sơ đồ nguyên lý

Xem file: [hospitality_gateway_diagram.svg](hospitality_gateway_diagram.svg)

## 10. Sao chép cấu hình
cp .env.example .env
# Điền OPERA_CLIENT_ID, OPERA_CLIENT_SECRET, OPERA_BASE_URL, OPERA_HOTEL_ID

## 11.1 Chạy bằng Docker
wsl
cd opera-bridge
docker compose up --build

## 11.2 Hoặc chạy local
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload

## 12 Chạy test
pytest
API docs tại http://localhost:8000/docs (chỉ khi APP_ENV != production).

## 13. Các câu hỏi khảo sát:
roomStatus = 2 (CLEAN) và roomStatus = 4 (DIRTY), các giá trị khác có thể xuất hiện là gì? Ý nghĩa của từng giá trị là gì?"
Các giá trị khác có thể là: 1=OCCUPIED, 3=INSPECT, 5=OUT OF ORDER, 6=OUT OF SERVICE