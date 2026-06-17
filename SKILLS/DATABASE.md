# Database Structure

## Mục tiêu

Database dùng PostgreSQL để hỗ trợ backend cầu nối giữa hệ điều khiển nội bộ của khách sạn và Oracle OPERA Cloud.

Database không dùng để sao chép toàn bộ dữ liệu từ OPERA Cloud. Nó chỉ lưu những dữ liệu cần thiết cho vận hành:

- Cấu hình khách sạn/property.
- Mapping ID giữa hệ nội bộ và OPERA Cloud.
- Trạng thái đồng bộ gần nhất.
- Log request quan trọng.
- Queue retry cho request lỗi tạm thời.
- Audit log cho các hành động nghiệp vụ quan trọng.

## Nguyên tắc thiết kế

- Không lưu access token, client secret hoặc dữ liệu thẻ thanh toán dạng plain text.
- Không lưu toàn bộ profile khách nếu không thật sự cần.
- Chỉ lưu metadata đủ để trace, retry và vận hành.
- Mỗi request nên có `trace_id` để theo dõi xuyên suốt.
- Các bảng nghiệp vụ nên có `created_at` và `updated_at`.
- Các dữ liệu linh hoạt có thể dùng `jsonb`, nhưng không lạm dụng nếu dữ liệu có cấu trúc rõ ràng.

## Sơ đồ bảng chính

```text
properties
  |
  |-- integration_mappings
  |-- sync_states
  |-- api_request_logs
  |-- retry_queue
  |-- audit_events
```

## Enum đề xuất

Có thể dùng PostgreSQL enum hoặc dùng `varchar` kèm check constraint. Với MVP, dùng `varchar` sẽ linh hoạt hơn khi nghiệp vụ thay đổi.

Các giá trị gợi ý:

```text
entity_type:
  reservation
  guest
  room

sync_type:
  room_status
  reservation_updates
  guest_status

retry_status:
  pending
  processing
  succeeded
  failed
  cancelled

operation_type:
  check_in
  check_out
  update_room_status
  sync_reservation
  sync_room_status

actor_type:
  system
  user
  job

audit_result:
  success
  failed
```

## Bảng `properties`

Lưu thông tin khách sạn/property được kết nối với OPERA Cloud.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `property_code` | `varchar(64)` | Có | Mã property nội bộ |
| `hotel_id` | `varchar(64)` | Có | Hotel ID dùng khi gọi OPERA Cloud |
| `name` | `varchar(255)` | Có | Tên khách sạn/property |
| `opera_base_url` | `text` | Có | Base URL của OPERA Cloud API |
| `is_active` | `boolean` | Có | Property còn được sử dụng hay không |
| `created_at` | `timestamptz` | Có | Thời điểm tạo |
| `updated_at` | `timestamptz` | Có | Thời điểm cập nhật |

### Index đề xuất

- Unique index trên `property_code`.
- Index trên `hotel_id`.
- Index trên `is_active`.

### DDL mẫu

```sql
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_code VARCHAR(64) NOT NULL,
    hotel_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    opera_base_url TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_properties_property_code UNIQUE (property_code)
);

CREATE INDEX idx_properties_hotel_id ON properties (hotel_id);
CREATE INDEX idx_properties_is_active ON properties (is_active);
```

## Bảng `integration_mappings`

Lưu mapping giữa ID nội bộ và ID của OPERA Cloud.

Bảng này giúp backend biết một reservation, guest hoặc room trong hệ nội bộ tương ứng với object nào trong OPERA Cloud.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `property_id` | `uuid` | Có | Liên kết tới `properties.id` |
| `entity_type` | `varchar(64)` | Có | Loại entity: reservation, guest, room |
| `internal_id` | `varchar(128)` | Có | ID từ hệ điều khiển nội bộ |
| `opera_id` | `varchar(128)` | Không | ID từ OPERA Cloud |
| `opera_confirmation_number` | `varchar(128)` | Không | Confirmation number của reservation nếu có |
| `created_at` | `timestamptz` | Có | Thời điểm tạo |
| `updated_at` | `timestamptz` | Có | Thời điểm cập nhật |

### Index đề xuất

- Unique index trên `property_id`, `entity_type`, `internal_id`.
- Index trên `property_id`, `entity_type`, `opera_id`.
- Index trên `opera_confirmation_number`.

### DDL mẫu

```sql
CREATE TABLE integration_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    entity_type VARCHAR(64) NOT NULL,
    internal_id VARCHAR(128) NOT NULL,
    opera_id VARCHAR(128),
    opera_confirmation_number VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_integration_mappings_internal
        UNIQUE (property_id, entity_type, internal_id)
);

CREATE INDEX idx_integration_mappings_opera_id
    ON integration_mappings (property_id, entity_type, opera_id);

CREATE INDEX idx_integration_mappings_confirmation
    ON integration_mappings (opera_confirmation_number);
```

## Bảng `sync_states`

Lưu trạng thái đồng bộ gần nhất của từng nhóm dữ liệu.

Ví dụ: lần cuối đồng bộ trạng thái phòng, lần cuối đồng bộ reservation update.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `property_id` | `uuid` | Có | Liên kết tới `properties.id` |
| `sync_type` | `varchar(64)` | Có | Loại đồng bộ |
| `last_synced_at` | `timestamptz` | Không | Lần gần nhất job chạy |
| `last_success_at` | `timestamptz` | Không | Lần gần nhất chạy thành công |
| `last_error_at` | `timestamptz` | Không | Lần gần nhất gặp lỗi |
| `last_error_code` | `varchar(128)` | Không | Mã lỗi gần nhất |
| `last_error_message` | `text` | Không | Nội dung lỗi gần nhất |
| `created_at` | `timestamptz` | Có | Thời điểm tạo |
| `updated_at` | `timestamptz` | Có | Thời điểm cập nhật |

### Index đề xuất

- Unique index trên `property_id`, `sync_type`.
- Index trên `last_success_at`.
- Index trên `last_error_at`.

### DDL mẫu

```sql
CREATE TABLE sync_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    sync_type VARCHAR(64) NOT NULL,
    last_synced_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_error_at TIMESTAMPTZ,
    last_error_code VARCHAR(128),
    last_error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_sync_states_property_sync
        UNIQUE (property_id, sync_type)
);

CREATE INDEX idx_sync_states_last_success_at ON sync_states (last_success_at);
CREATE INDEX idx_sync_states_last_error_at ON sync_states (last_error_at);
```

## Bảng `api_request_logs`

Lưu metadata của các request quan trọng giữa hệ nội bộ, backend cầu nối và OPERA Cloud.

Bảng này phục vụ trace lỗi, đo hiệu năng và audit kỹ thuật. Không nên lưu toàn bộ payload nếu payload chứa dữ liệu nhạy cảm.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `trace_id` | `varchar(128)` | Có | Mã trace của request |
| `property_id` | `uuid` | Không | Liên kết tới `properties.id` |
| `internal_endpoint` | `text` | Có | Endpoint nội bộ được gọi |
| `opera_endpoint` | `text` | Không | Endpoint OPERA Cloud tương ứng |
| `http_method` | `varchar(16)` | Có | HTTP method |
| `status_code` | `integer` | Không | HTTP status trả về |
| `success` | `boolean` | Có | Request thành công hay thất bại |
| `error_code` | `varchar(128)` | Không | Mã lỗi đã chuẩn hóa |
| `duration_ms` | `integer` | Không | Thời gian xử lý tính bằng millisecond |
| `created_at` | `timestamptz` | Có | Thời điểm ghi log |

### Index đề xuất

- Index trên `trace_id`.
- Index trên `property_id`, `created_at`.
- Index trên `success`, `created_at`.
- Index trên `error_code`.

### DDL mẫu

```sql
CREATE TABLE api_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id VARCHAR(128) NOT NULL,
    property_id UUID REFERENCES properties(id),
    internal_endpoint TEXT NOT NULL,
    opera_endpoint TEXT,
    http_method VARCHAR(16) NOT NULL,
    status_code INTEGER,
    success BOOLEAN NOT NULL,
    error_code VARCHAR(128),
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_api_request_logs_trace_id ON api_request_logs (trace_id);
CREATE INDEX idx_api_request_logs_property_created
    ON api_request_logs (property_id, created_at DESC);
CREATE INDEX idx_api_request_logs_success_created
    ON api_request_logs (success, created_at DESC);
CREATE INDEX idx_api_request_logs_error_code ON api_request_logs (error_code);
```

## Bảng `retry_queue`

Lưu các operation cần thử lại khi gặp lỗi tạm thời như timeout, rate limit hoặc lỗi mạng.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `property_id` | `uuid` | Có | Liên kết tới `properties.id` |
| `operation_type` | `varchar(64)` | Có | Loại operation cần retry |
| `payload` | `jsonb` | Có | Payload tối thiểu để thực hiện lại |
| `status` | `varchar(32)` | Có | Trạng thái retry |
| `attempt_count` | `integer` | Có | Số lần đã thử |
| `max_attempts` | `integer` | Có | Số lần thử tối đa |
| `next_retry_at` | `timestamptz` | Không | Thời điểm thử lại |
| `last_error_code` | `varchar(128)` | Không | Mã lỗi gần nhất |
| `last_error_message` | `text` | Không | Nội dung lỗi gần nhất |
| `created_at` | `timestamptz` | Có | Thời điểm tạo |
| `updated_at` | `timestamptz` | Có | Thời điểm cập nhật |

### Index đề xuất

- Index trên `status`, `next_retry_at`.
- Index trên `property_id`, `operation_type`.
- Index trên `created_at`.

### DDL mẫu

```sql
CREATE TABLE retry_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    operation_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    last_error_code VARCHAR(128),
    last_error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_retry_queue_status_next_retry
    ON retry_queue (status, next_retry_at);

CREATE INDEX idx_retry_queue_property_operation
    ON retry_queue (property_id, operation_type);

CREATE INDEX idx_retry_queue_created_at ON retry_queue (created_at);
```

## Bảng `audit_events`

Lưu audit log cho các hành động nghiệp vụ quan trọng.

Ví dụ: check-in, check-out, cập nhật trạng thái phòng.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `trace_id` | `varchar(128)` | Có | Mã trace liên quan |
| `property_id` | `uuid` | Có | Liên kết tới `properties.id` |
| `actor_type` | `varchar(32)` | Có | Loại tác nhân: system, user, job |
| `actor_id` | `varchar(128)` | Không | ID người dùng hoặc service |
| `action` | `varchar(128)` | Có | Hành động nghiệp vụ |
| `entity_type` | `varchar(64)` | Có | Loại entity bị tác động |
| `entity_id` | `varchar(128)` | Có | ID entity bị tác động |
| `result` | `varchar(32)` | Có | Kết quả: success hoặc failed |
| `metadata` | `jsonb` | Không | Metadata không nhạy cảm |
| `created_at` | `timestamptz` | Có | Thời điểm ghi audit |

### Index đề xuất

- Index trên `trace_id`.
- Index trên `property_id`, `created_at`.
- Index trên `entity_type`, `entity_id`.
- Index trên `action`, `created_at`.

### DDL mẫu

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id VARCHAR(128) NOT NULL,
    property_id UUID NOT NULL REFERENCES properties(id),
    actor_type VARCHAR(32) NOT NULL,
    actor_id VARCHAR(128),
    action VARCHAR(128) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    result VARCHAR(32) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_events_trace_id ON audit_events (trace_id);
CREATE INDEX idx_audit_events_property_created
    ON audit_events (property_id, created_at DESC);
CREATE INDEX idx_audit_events_entity
    ON audit_events (entity_type, entity_id);
CREATE INDEX idx_audit_events_action_created
    ON audit_events (action, created_at DESC);
```

## Bảng tùy chọn `opera_tokens`

Nếu triển khai cần cache token trong database, có thể thêm bảng này. Tuy nhiên, chỉ nên lưu token đã mã hóa hoặc dùng secret manager/cache an toàn thay vì lưu trực tiếp trong PostgreSQL.

Nếu hệ thống chỉ có một service instance, có thể cache token trong memory. Nếu có nhiều instance, nên cân nhắc Redis hoặc secret manager.

### Cột dữ liệu

| Cột | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | `uuid` | Có | Khóa chính |
| `property_id` | `uuid` | Có | Liên kết tới `properties.id` |
| `token_type` | `varchar(64)` | Có | Loại token |
| `encrypted_token` | `text` | Có | Token đã mã hóa |
| `expires_at` | `timestamptz` | Có | Thời điểm hết hạn |
| `created_at` | `timestamptz` | Có | Thời điểm tạo |
| `updated_at` | `timestamptz` | Có | Thời điểm cập nhật |

### DDL mẫu

```sql
CREATE TABLE opera_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    token_type VARCHAR(64) NOT NULL,
    encrypted_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_opera_tokens_property_type
        UNIQUE (property_id, token_type)
);

CREATE INDEX idx_opera_tokens_expires_at ON opera_tokens (expires_at);
```

## Extension cần bật

Để dùng `gen_random_uuid()`, PostgreSQL cần extension `pgcrypto`.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Trigger cập nhật `updated_at`

Có thể dùng một trigger chung để tự động cập nhật `updated_at`.

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_properties_updated_at
BEFORE UPDATE ON properties
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_integration_mappings_updated_at
BEFORE UPDATE ON integration_mappings
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_sync_states_updated_at
BEFORE UPDATE ON sync_states
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_retry_queue_updated_at
BEFORE UPDATE ON retry_queue
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_opera_tokens_updated_at
BEFORE UPDATE ON opera_tokens
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

## Quy tắc lưu log và dữ liệu nhạy cảm

Không lưu các dữ liệu sau trong database nếu không có cơ chế mã hóa và lý do nghiệp vụ rõ ràng:

- Access token.
- Client secret.
- Số thẻ.
- CVV.
- Dữ liệu thanh toán nhạy cảm.
- Toàn bộ request/response từ OPERA Cloud.
- Thông tin định danh cá nhân vượt quá nhu cầu vận hành.

Nếu cần lưu payload để retry, payload trong `retry_queue` chỉ nên chứa dữ liệu tối thiểu để thực hiện lại operation.

## Gợi ý migration ban đầu

Thứ tự tạo bảng:

1. Bật extension `pgcrypto`.
2. Tạo bảng `properties`.
3. Tạo bảng `integration_mappings`.
4. Tạo bảng `sync_states`.
5. Tạo bảng `api_request_logs`.
6. Tạo bảng `retry_queue`.
7. Tạo bảng `audit_events`.
8. Tạo bảng tùy chọn `opera_tokens` nếu cần.
9. Tạo function và trigger `updated_at`.

## Ghi chú cho MVP

Trong MVP, có thể bắt đầu với các bảng bắt buộc:

- `properties`
- `integration_mappings`
- `api_request_logs`
- `audit_events`

Sau đó thêm `sync_states` và `retry_queue` khi bắt đầu có job đồng bộ hoặc retry tự động.

`opera_tokens` chỉ nên thêm khi thật sự cần cache token ở database.

