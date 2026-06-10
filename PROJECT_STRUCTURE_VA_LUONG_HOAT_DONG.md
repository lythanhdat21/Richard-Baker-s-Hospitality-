# Project Structure và luồng hoạt động

## Mục tiêu

Project này là một backend nhỏ làm cầu nối giữa hệ điều khiển nội bộ của khách sạn và Oracle OPERA Cloud.

Backend không dùng toàn bộ Oracle Hospitality APIs, mà chỉ chọn một nhóm endpoint cần thiết, khoảng 20 endpoint, để phục vụ các nghiệp vụ chính như tìm đặt phòng, check-in, check-out, lấy thông tin khách và đồng bộ trạng thái phòng.

## Project Structure đề xuất

```text
src/
  app/
    app.module
    main

  config/
    opera-cloud.config
    app.config

  controllers/
    reservation.controller
    room.controller
    guest.controller
    health.controller

  services/
    reservation.service
    room.service
    guest.service
    sync.service

  clients/
    opera-cloud.client
    opera-auth.client

  mappers/
    reservation.mapper
    room.mapper
    guest.mapper

  models/
    internal/
      reservation.dto
      room.dto
      guest.dto
      error.dto
    opera/
      opera-reservation.dto
      opera-room.dto
      opera-guest.dto

  jobs/
    room-status-sync.job
    reservation-sync.job

  middlewares/
    auth.middleware
    request-logging.middleware

  utils/
    retry.util
    logger.util
    error-normalizer.util

  tests/
    reservation.service.test
    room.service.test
    mapper.test
```

## Stack đề xuất

Vì backend chỉ đóng vai trò cầu nối nhỏ, dùng khoảng 20 endpoint từ OPERA Cloud, stack nên ưu tiên đơn giản, dễ vận hành và dễ mở rộng.

### Backend

Ngôn ngữ và framework đề xuất:

- Python 3.11 hoặc mới hơn.
- FastAPI để xây REST API nội bộ.
- Uvicorn hoặc Gunicorn + Uvicorn worker để chạy service.
- Pydantic để định nghĩa DTO, validate request và chuẩn hóa response.
- HTTPX để gọi OPERA Cloud API.
- SQLAlchemy hoặc SQLModel để làm việc với PostgreSQL.
- Alembic để quản lý database migration.

FastAPI phù hợp vì nhẹ, nhanh, dễ viết API rõ ràng và có sẵn OpenAPI documentation cho API nội bộ.

### Database

Database đề xuất:

- PostgreSQL.

PostgreSQL dùng để lưu các dữ liệu cần thiết cho vận hành, không dùng để copy toàn bộ dữ liệu từ OPERA Cloud.

Nên lưu:

- Cấu hình property/hotel.
- Mapping ID giữa hệ điều khiển nội bộ và OPERA Cloud.
- Log request quan trọng.
- Trạng thái đồng bộ gần nhất.
- Queue retry cho các request lỗi tạm thời.
- Audit log cho các nghiệp vụ nhạy cảm như check-in, check-out hoặc cập nhật room status.

Không nên lưu:

- Access token dạng plain text.
- Client secret dạng plain text.
- Dữ liệu thẻ thanh toán.
- Toàn bộ profile khách nếu không thật sự cần.
- Dữ liệu cá nhân nhạy cảm vượt quá mục đích tích hợp.

### Thư viện phụ trợ

Một số thư viện nên cân nhắc:

- `python-dotenv` hoặc cơ chế environment variables của môi trường deploy.
- `structlog` hoặc logging chuẩn của Python để ghi log có cấu trúc.
- `tenacity` để retry có kiểm soát.
- `pytest` để viết test.
- `pytest-asyncio` nếu service dùng async.
- `ruff` để lint và format code.

### Triển khai

Phương án triển khai gọn:

- Docker cho backend Python.
- Docker hoặc managed PostgreSQL cho database.
- Environment variables cho cấu hình.
- Health check endpoint tại `GET /health`.
- Migration chạy bằng Alembic.
- Log xuất ra stdout để hệ thống vận hành thu thập.

## Database Structure đề xuất

Với MVP, database chỉ cần một số bảng nhỏ.

### `properties`

Lưu thông tin khách sạn/property được kết nối với OPERA Cloud.

```text
id
property_code
hotel_id
name
opera_base_url
is_active
created_at
updated_at
```

### `integration_mappings`

Lưu mapping giữa ID nội bộ và ID của OPERA Cloud.

```text
id
property_id
entity_type
internal_id
opera_id
opera_confirmation_number
created_at
updated_at
```

Ví dụ `entity_type` có thể là:

- `reservation`
- `guest`
- `room`

### `sync_states`

Lưu trạng thái đồng bộ gần nhất của từng nhóm dữ liệu.

```text
id
property_id
sync_type
last_synced_at
last_success_at
last_error_at
last_error_code
last_error_message
created_at
updated_at
```

Ví dụ `sync_type`:

- `room_status`
- `reservation_updates`
- `guest_status`

### `api_request_logs`

Lưu log các request quan trọng giữa hệ nội bộ, backend cầu nối và OPERA Cloud.

```text
id
trace_id
property_id
internal_endpoint
opera_endpoint
http_method
status_code
success
error_code
duration_ms
created_at
```

Bảng này chỉ nên lưu metadata, không nên lưu toàn bộ request/response chứa dữ liệu nhạy cảm.

### `retry_queue`

Lưu các request cần thử lại khi gặp lỗi tạm thời.

```text
id
property_id
operation_type
payload
status
attempt_count
max_attempts
next_retry_at
last_error_code
last_error_message
created_at
updated_at
```

Ví dụ `operation_type`:

- `check_in`
- `check_out`
- `update_room_status`
- `sync_reservation`

### `audit_events`

Lưu audit log cho các hành động nghiệp vụ quan trọng.

```text
id
trace_id
property_id
actor_type
actor_id
action
entity_type
entity_id
result
created_at
```

Ví dụ `action`:

- `reservation.check_in`
- `reservation.check_out`
- `room.status_update`

## Python Project Structure đề xuất

Nếu dùng Python + FastAPI, cấu trúc có thể điều chỉnh như sau:

```text
src/
  main.py

  app/
    api/
      routes/
        health.py
        reservations.py
        rooms.py
        guests.py

    core/
      config.py
      security.py
      logging.py

    clients/
      opera_auth_client.py
      opera_cloud_client.py

    services/
      reservation_service.py
      room_service.py
      guest_service.py
      sync_service.py

    mappers/
      reservation_mapper.py
      room_mapper.py
      guest_mapper.py

    schemas/
      internal/
        reservation.py
        room.py
        guest.py
        error.py
      opera/
        reservation.py
        room.py
        guest.py

    db/
      session.py
      models.py
      repositories/
        property_repository.py
        mapping_repository.py
        sync_state_repository.py
        retry_queue_repository.py

    jobs/
      room_status_sync.py
      reservation_sync.py

    utils/
      retry.py
      error_normalizer.py

tests/
  test_reservation_service.py
  test_room_service.py
  test_mappers.py

alembic/
  versions/
```

## Vai trò từng thành phần

### `controllers`

Đây là lớp API nội bộ để hệ điều khiển khách sạn gọi vào.

Ví dụ:

- `GET /reservations/search`
- `GET /reservations/{id}`
- `POST /reservations/{id}/check-in`
- `POST /reservations/{id}/check-out`
- `GET /rooms/{roomNumber}/status`
- `PATCH /rooms/{roomNumber}/status`
- `GET /health`

Controller không nên chứa logic phức tạp. Nó chỉ nhận request, validate dữ liệu cơ bản và gọi service tương ứng.

### `services`

Đây là lớp xử lý nghiệp vụ chính.

Service quyết định cần gọi endpoint nào của OPERA Cloud, có cần kiểm tra dữ liệu trước không, có cần gọi nhiều API liên tiếp không và kết quả cuối cùng trả về cho hệ điều khiển khách sạn là gì.

Ví dụ:

- `reservation.service`: tìm reservation, lấy chi tiết reservation, check-in, check-out.
- `room.service`: lấy trạng thái phòng, cập nhật trạng thái phòng.
- `guest.service`: lấy hoặc chuẩn hóa thông tin khách.
- `sync.service`: xử lý các luồng đồng bộ định kỳ.

### `clients`

Đây là lớp chuyên gọi API bên ngoài.

- `opera-auth.client`: lấy access token, refresh token hoặc quản lý token.
- `opera-cloud.client`: gọi REST API của OPERA Cloud.

Lớp client chịu trách nhiệm:

- Gắn header cần thiết.
- Gắn token.
- Xử lý timeout.
- Retry lỗi tạm thời.
- Trả response thô về cho service.

### `mappers`

Mapper chuyển đổi dữ liệu giữa format nội bộ và format của OPERA Cloud.

Ví dụ:

```text
InternalReservationSearchRequest
        -> reservation.mapper
        -> OperaReservationSearchRequest
```

Và chiều ngược lại:

```text
OperaReservationResponse
        -> reservation.mapper
        -> InternalReservationResponse
```

Lớp này giúp hệ điều khiển khách sạn không phải phụ thuộc trực tiếp vào cấu trúc phức tạp của OPERA Cloud.

### `models`

Chứa định nghĩa dữ liệu.

- `models/internal`: DTO/schema mà API nội bộ sử dụng.
- `models/opera`: DTO/schema gần với request/response của OPERA Cloud.

Tách riêng hai nhóm model giúp dễ bảo trì khi API của OPERA thay đổi.

### `jobs`

Chứa các tác vụ chạy nền hoặc chạy theo lịch.

Ví dụ:

- Đồng bộ trạng thái phòng mỗi vài phút.
- Đồng bộ reservation mới hoặc reservation thay đổi.
- Retry các request từng thất bại.

### `middlewares`

Chứa logic xử lý request trước khi vào controller.

Ví dụ:

- Xác thực request nội bộ bằng API key.
- Ghi log request.
- Gắn correlation ID để trace request từ đầu đến cuối.

### `utils`

Chứa các hàm dùng chung như retry, logging và chuẩn hóa lỗi.

## Luồng hoạt động tổng thể

```text
Hệ điều khiển khách sạn
        |
        v
Internal API Controller
        |
        v
Service nghiệp vụ
        |
        v
Mapper request
        |
        v
OPERA Cloud Client
        |
        v
Oracle OPERA Cloud API
        |
        v
OPERA Cloud Client
        |
        v
Mapper response
        |
        v
Service nghiệp vụ
        |
        v
Internal API Controller
        |
        v
Hệ điều khiển khách sạn
```

## Luồng 1: Tìm reservation

```text
1. Hệ điều khiển gửi mã đặt phòng, tên khách hoặc ngày đến.
2. Controller nhận request tại /reservations/search.
3. Reservation service kiểm tra dữ liệu đầu vào.
4. Reservation mapper đổi request nội bộ sang request OPERA Cloud.
5. Opera cloud client gọi endpoint tìm reservation.
6. OPERA Cloud trả danh sách reservation phù hợp.
7. Mapper đổi response OPERA Cloud về format nội bộ.
8. Controller trả kết quả đơn giản cho hệ điều khiển.
```

Kết quả trả về nên chỉ gồm dữ liệu cần thiết:

```json
{
  "success": true,
  "data": [
    {
      "reservationId": "12345",
      "confirmationNumber": "ABC123",
      "guestName": "Nguyen Van A",
      "arrivalDate": "2026-06-10",
      "departureDate": "2026-06-12",
      "status": "RESERVED"
    }
  ]
}
```

## Luồng 2: Check-in khách

```text
1. Hệ điều khiển gửi reservationId cần check-in.
2. Controller nhận request tại /reservations/{id}/check-in.
3. Reservation service lấy thông tin reservation hiện tại nếu cần.
4. Service kiểm tra reservation có đủ điều kiện check-in không.
5. Mapper tạo request check-in theo format OPERA Cloud.
6. Opera cloud client gọi endpoint check-in.
7. OPERA Cloud trả kết quả.
8. Service ghi log kết quả check-in.
9. Controller trả trạng thái check-in cho hệ điều khiển.
```

Kết quả mẫu:

```json
{
  "success": true,
  "data": {
    "reservationId": "12345",
    "status": "CHECKED_IN",
    "roomNumber": "1208"
  }
}
```

## Luồng 3: Check-out khách

```text
1. Hệ điều khiển gửi reservationId cần check-out.
2. Controller nhận request tại /reservations/{id}/check-out.
3. Reservation service kiểm tra trạng thái reservation.
4. Nếu cần, service kiểm tra folio hoặc balance.
5. Mapper tạo request check-out theo format OPERA Cloud.
6. Opera cloud client gọi endpoint check-out.
7. OPERA Cloud trả kết quả.
8. Service chuẩn hóa response.
9. Controller trả kết quả cho hệ điều khiển.
```

Nếu còn balance chưa xử lý, backend nên trả lỗi nghiệp vụ rõ ràng:

```json
{
  "success": false,
  "code": "BALANCE_NOT_CLEARED",
  "message": "Không thể check-out vì reservation vẫn còn balance."
}
```

## Luồng 4: Lấy trạng thái phòng

```text
1. Hệ điều khiển gửi roomNumber.
2. Controller nhận request tại /rooms/{roomNumber}/status.
3. Room service gọi OPERA Cloud để lấy trạng thái phòng.
4. Mapper chuẩn hóa trạng thái phòng.
5. Controller trả trạng thái phòng về cho hệ điều khiển.
```

Kết quả mẫu:

```json
{
  "success": true,
  "data": {
    "roomNumber": "1208",
    "occupancyStatus": "OCCUPIED",
    "housekeepingStatus": "CLEAN"
  }
}
```

## Luồng 5: Đồng bộ trạng thái phòng

```text
1. Job đồng bộ chạy theo lịch.
2. Job lấy danh sách phòng cần kiểm tra.
3. Room service gọi OPERA Cloud để lấy trạng thái mới nhất.
4. Service so sánh với trạng thái đang lưu nội bộ.
5. Nếu có thay đổi, service cập nhật dữ liệu hoặc gửi sự kiện sang hệ điều khiển.
6. Nếu lỗi tạm thời, job đưa request vào retry.
```

## Xác thực và bảo mật

Backend có hai lớp xác thực:

```text
Hệ điều khiển khách sạn -> Backend cầu nối
Backend cầu nối -> OPERA Cloud
```

Với lớp nội bộ, có thể dùng:

- API key.
- IP allowlist.
- Mutual TLS nếu môi trường yêu cầu bảo mật cao.

Với OPERA Cloud, backend tự quản lý:

- Client ID.
- Client secret.
- Access token.
- Refresh token hoặc token renewal.

Không để hệ điều khiển khách sạn gọi trực tiếp token endpoint của OPERA Cloud.

## Xử lý lỗi

Backend nên chuẩn hóa mọi lỗi về một format thống nhất:

```json
{
  "success": false,
  "code": "OPERA_TIMEOUT",
  "message": "Không thể kết nối OPERA Cloud trong thời gian cho phép.",
  "traceId": "req-20260610-0001"
}
```

Các nhóm lỗi chính:

- `AUTH_FAILED`: lỗi xác thực.
- `VALIDATION_ERROR`: dữ liệu đầu vào không hợp lệ.
- `RESERVATION_NOT_FOUND`: không tìm thấy đặt phòng.
- `ROOM_NOT_FOUND`: không tìm thấy phòng.
- `OPERA_TIMEOUT`: OPERA Cloud phản hồi quá lâu.
- `OPERA_RATE_LIMIT`: bị giới hạn số request.
- `OPERA_ERROR`: lỗi chung từ OPERA Cloud.

## Logging và trace

Mỗi request nên có `traceId` hoặc `correlationId`.

Log nên ghi:

- API nội bộ được gọi.
- Endpoint OPERA Cloud tương ứng.
- Thời gian bắt đầu và kết thúc.
- HTTP status.
- Mã lỗi nếu có.
- Thời gian phản hồi.

Không ghi log:

- Access token.
- Client secret.
- Dữ liệu thẻ thanh toán.
- Dữ liệu cá nhân nhạy cảm nếu không cần thiết.

## Nguyên tắc triển khai

- Chỉ implement endpoint thật sự cần.
- Không expose nguyên xi API OPERA Cloud ra bên ngoài.
- Luôn có mapper giữa dữ liệu nội bộ và dữ liệu OPERA Cloud.
- Luôn có timeout khi gọi API bên ngoài.
- Retry chỉ áp dụng cho lỗi tạm thời.
- Log đủ để vận hành nhưng không làm lộ dữ liệu nhạy cảm.
- Thiết kế sao cho có thể thêm endpoint mới mà không phải sửa toàn bộ hệ thống.
