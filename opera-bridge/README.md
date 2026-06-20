# Opera Bridge — Demo Project

Backend FastAPI cầu nối khách sạn ↔ Oracle OPERA Cloud. Bản demo này **chưa gọi OPERA Cloud** —
chỉ lưu/cập nhật dữ liệu nội bộ (`users`, `room_types`, `rooms`, `reservations`, `stays`,
`room_service_logs`) để test luồng nghiệp vụ Register/Login + Check-in/Check-out +
Do Not Disturb + Make-up-room, theo [`SKILLS/DATABASE_&_API.md`](../SKILLS/DATABASE_&_API.md).

## Chạy bằng Docker

```bash
cp .env.example .env
docker compose up --build
```

API chạy tại `http://localhost:8000`, OpenAPI docs tại `http://localhost:8000/docs`
(chỉ hiển thị khi `APP_ENV != production`). Migration Alembic chạy tự động khi container `api` start.

> Nếu đang nâng cấp từ schema cũ, cần xoá volume Postgres cũ trước:
> `docker compose down -v` rồi `docker compose up --build`.

## Chạy local (không Docker)

```bash
cp .env.example .env
# sửa DATABASE_URL trong .env thành postgresql+psycopg2://opera:opera@localhost:5432/opera_bridge
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --app-dir src
```

## Dữ liệu mẫu (seed sẵn trong migration `001_initial_schema`)

`room_types`: `PK` = Premium King, `DT` = Deluxe Twin, `JSK` = Junior Suite King.

| room_number | room_type | floor |
|---|---|---|
| 11 | Premium King | 1 |
| 15 | Premium King | 1 |
| 17 | Premium King | 1 |
| 202 | Deluxe Twin | 2 |
| 205 | Deluxe Twin | 2 |
| 209 | Deluxe Twin | 2 |
| 403 | Junior Suite King | 4 |
| 408 | Junior Suite King | 4 |
| 409 | Junior Suite King | 4 |

`room_id` (số) là khoá nội bộ, **không xuất hiện trong bất kỳ API request/response** —
mọi endpoint dùng `room_number` (string) làm định danh phòng.

## Luồng demo

1. `POST /api/auth/register` (multipart/form-data: `username, gender, phone_number, email,
   password, role, avatar`; `role` là `CUSTOMER` hoặc `RECEPTIONIST`)
   → tạo user, avatar lưu tại `./uploads/avatar_{id}.{ext}`, trả về `/uploads/avatar_{id}.{ext}`.
2. `POST /api/auth/login` (`phone_number`, `password`) → trả `access_token` (JWT).
3. Gọi các action với header `Authorization: Bearer <access_token>`:
   - `POST /api/stays/check-in` — chỉ `RECEPTIONIST`. Body: `room_number, room_name?(optional),
     username, gender, phone_number, number_of_guests, expected_arrival_date,
     expected_departure_date`. Không nhận `reservation_id` — backend tự tạo reservation mới
     mỗi lần check-in. `checked_in_by` lấy từ JWT.
   - `POST /api/stays/check-out` — chỉ `RECEPTIONIST`. Body: chỉ `{room_number}` — backend tự
     tìm lượt lưu trú đang `CHECKED_IN` của phòng đó. `checked_out_by` lấy từ JWT.
   - `PATCH /api/rooms/{room_number}/do-not-disturb` — `RECEPTIONIST` hoặc `CUSTOMER`. Body:
     `{"status": true|false}`.
   - `POST /api/rooms/{room_number}/make-up-room` — chỉ `CUSTOMER`. Không cần body.
   - `PATCH /api/rooms/{room_number}/service` — chỉ `RECEPTIONIST` (đóng vai trò Housekeeping),
     đánh dấu hoàn thành yêu cầu dọn phòng (`make_up_room = false`).

Mỗi lần gọi DND/Make-up-room đều ghi 1 dòng vào `room_service_logs` (ai gọi, role gì, lúc nào).

## Test bằng Postman

Import file [`postman/opera-bridge-demo.postman_collection.json`](postman/opera-bridge-demo.postman_collection.json).
Collection gồm: register 2 user (Receptionist + Customer), login (tự lưu token vào biến
`token`/`customer_token`), check-in/check-out, DND, make-up-room + các request kiểm chứng
403 khi gọi sai role.

## Giới hạn của bản demo

- Không gọi Oracle OPERA Cloud — đây là bản demo nghiệp vụ nội bộ, không phải bản tích hợp
  MQTT/OPERA Cloud thật (tài liệu mô tả kiến trúc đó đã bị xoá, xem `WORK_LOG.md` mục 11-12).
- Chưa có MQTT/Legrand RCU, `opera_cloud_client.py`, `room_status_sync.py` — các phần này
  sẽ phải build mới hoàn toàn khi bước vào giai đoạn tích hợp OPERA Cloud thật (bản code cũ
  có các phần này đã bị xoá, xem [`WORK_LOG.md`](../SKILLS/WORK_LOG.md)).
- Make-up-room không publish MQTT (quyết định: chỉ ghi log nội bộ).
- Sau Check-out, `rooms.status` chuyển thành `Cleaning` nhưng chưa có endpoint nào đưa phòng
  về lại `Vacant` — tài liệu đặc tả chưa định nghĩa endpoint này.
