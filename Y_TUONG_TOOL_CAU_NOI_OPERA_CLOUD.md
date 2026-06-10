# Ý tưởng xây dựng tool cầu nối giữa hệ điều khiển khách sạn và Opera Cloud

## Mục tiêu

Xây dựng một backend nhỏ đóng vai trò cầu nối giữa hệ điều khiển đang dùng trong khách sạn và Oracle Hospitality OPERA Cloud thông qua Oracle Hospitality APIs.

Tool này không cần bao phủ toàn bộ hàng ngàn endpoint trong bộ API specs. Phạm vi ban đầu chỉ tập trung vào khoảng 20 endpoint thật sự cần thiết cho luồng vận hành của khách sạn, giúp hệ thống nhẹ, dễ bảo trì và dễ kiểm soát lỗi.

## Bối cảnh

Repository hiện tại cung cấp:

- Đặc tả REST API trong `rest-api-specs`.
- Postman collections trong `postman-collections`.
- Workflow mẫu cho các nghiệp vụ phổ biến như đặt phòng, check-in, check-out, block, event và rate plan.

Tool cầu nối sẽ sử dụng các tài liệu này làm nguồn tham chiếu để chọn endpoint, hiểu request/response schema và kiểm thử tích hợp bằng Postman trước khi hiện thực backend.

## Ý tưởng tổng thể

Tool hoạt động như một lớp trung gian:

```text
Hệ điều khiển khách sạn
        |
        v
Backend cầu nối nội bộ
        |
        v
Oracle Hospitality / OPERA Cloud APIs
```

Backend cầu nối chịu trách nhiệm:

- Nhận request từ hệ điều khiển khách sạn.
- Chuẩn hóa dữ liệu nội bộ sang format mà OPERA Cloud yêu cầu.
- Gọi đúng endpoint Oracle Hospitality API.
- Xử lý response, lỗi, retry và log.
- Trả kết quả đơn giản, ổn định về cho hệ điều khiển khách sạn.

## Phạm vi ban đầu

Phiên bản đầu nên giới hạn vào các nghiệp vụ có giá trị cao nhất, ví dụ:

- Kiểm tra thông tin đặt phòng.
- Tìm reservation theo mã đặt phòng, tên khách hoặc ngày đến.
- Lấy trạng thái phòng.
- Lấy thông tin khách đang lưu trú.
- Ghi nhận check-in.
- Ghi nhận check-out.
- Cập nhật một số thông tin reservation.
- Lấy thông tin folio hoặc thanh toán cơ bản nếu cần.
- Đồng bộ room status hoặc housekeeping status nếu hệ điều khiển có liên quan tới phòng.

Danh sách endpoint cụ thể nên được chọn sau khi xác định rõ hệ điều khiển khách sạn cần trao đổi những dữ liệu nào với OPERA Cloud.

## Nguyên tắc thiết kế

### Nhỏ và có kiểm soát

Không import hoặc generate toàn bộ API client từ tất cả specs nếu chưa cần. Chỉ tạo wrapper cho các endpoint được chọn.

Mỗi endpoint nên có:

- Một service function riêng.
- Request DTO nội bộ.
- Response DTO nội bộ.
- Mapping rõ ràng giữa dữ liệu nội bộ và dữ liệu OPERA Cloud.
- Test hoặc Postman sample để xác minh.

### Tách biệt domain nội bộ và OPERA Cloud

Không nên để format request/response của OPERA Cloud lan trực tiếp vào toàn bộ hệ thống nội bộ.

Backend cầu nối nên có lớp mapping:

```text
Internal Request
      -> Mapper
      -> OPERA Cloud Request
      -> OPERA Cloud API
      -> Mapper
      -> Internal Response
```

Cách này giúp hệ thống nội bộ ít bị ảnh hưởng nếu API của OPERA thay đổi version hoặc field.

### Ưu tiên luồng nghiệp vụ hơn endpoint rời rạc

Thay vì expose lại từng endpoint của OPERA Cloud, tool nên cung cấp các API nội bộ theo nghiệp vụ:

- `GET /reservations/search`
- `GET /reservations/{id}`
- `POST /reservations/{id}/check-in`
- `POST /reservations/{id}/check-out`
- `GET /rooms/{roomNumber}/status`
- `PATCH /rooms/{roomNumber}/status`

Bên trong mỗi API nội bộ có thể gọi một hoặc nhiều endpoint OPERA Cloud.

## Kiến trúc đề xuất

```text
src/
  config/
    opera-cloud.config
  controllers/
    reservation.controller
    room.controller
    guest.controller
  services/
    reservation.service
    room.service
    guest.service
  clients/
    opera-cloud.client
    opera-auth.client
  mappers/
    reservation.mapper
    room.mapper
    guest.mapper
  models/
    internal/
    opera/
  jobs/
    sync-room-status.job
  logs/
  tests/
```

Các thành phần chính:

- `controllers`: API nội bộ cho hệ điều khiển khách sạn gọi.
- `services`: xử lý nghiệp vụ và điều phối gọi API.
- `clients`: wrapper HTTP để gọi OPERA Cloud.
- `mappers`: chuyển đổi dữ liệu qua lại giữa hệ nội bộ và OPERA Cloud.
- `models`: định nghĩa DTO/schema.
- `jobs`: các tác vụ đồng bộ định kỳ nếu cần.

## Nhóm endpoint dự kiến

### Reservation

Các endpoint liên quan tới đặt phòng thường là nhóm quan trọng nhất:

- Tìm reservation.
- Lấy chi tiết reservation.
- Tạo hoặc cập nhật reservation nếu hệ điều khiển có quyền làm việc này.
- Check-in reservation.
- Check-out reservation.
- Lấy trạng thái reservation.

Specs tham khảo nằm trong nhóm `rest-api-specs/property/v1/rsv.json`.

### Guest / Profile

Nhóm này phục vụ việc lấy hoặc cập nhật thông tin khách:

- Tìm profile khách.
- Lấy thông tin liên hệ.
- Lấy thông tin định danh cơ bản.
- Gắn profile vào reservation nếu nghiệp vụ yêu cầu.

Specs tham khảo có thể nằm trong nhóm CRM/Profile của property APIs.

### Room / Housekeeping

Nhóm này phù hợp nếu hệ điều khiển khách sạn cần biết phòng nào đang trống, đang bẩn, đang có khách hoặc cần dọn:

- Lấy room status.
- Cập nhật housekeeping status.
- Lấy thông tin room assignment.
- Kiểm tra phòng theo ngày lưu trú.

Specs tham khảo có thể nằm trong các nhóm inventory, housekeeping hoặc reservation APIs.

### Cashiering / Folio

Chỉ nên đưa vào MVP nếu hệ điều khiển cần liên quan tới thanh toán hoặc trạng thái folio:

- Lấy folio cơ bản.
- Kiểm tra balance.
- Ghi nhận hoặc đọc thông tin thanh toán nếu được phép.

Nhóm này cần kiểm soát kỹ hơn vì liên quan tới dữ liệu nhạy cảm.

## Luồng xử lý mẫu

### Tìm reservation để check-in

```text
1. Hệ điều khiển gửi mã đặt phòng hoặc tên khách.
2. Backend cầu nối gọi endpoint tìm reservation của OPERA Cloud.
3. Backend chuẩn hóa response.
4. Hệ điều khiển hiển thị danh sách reservation phù hợp.
```

### Check-in khách

```text
1. Hệ điều khiển gửi yêu cầu check-in cho một reservation.
2. Backend kiểm tra reservation có hợp lệ không.
3. Backend gọi endpoint check-in của OPERA Cloud.
4. Backend ghi log kết quả.
5. Backend trả trạng thái thành công hoặc lỗi đã chuẩn hóa.
```

### Đồng bộ trạng thái phòng

```text
1. Job định kỳ hoặc webhook nội bộ được kích hoạt.
2. Backend lấy danh sách phòng cần đồng bộ.
3. Backend gọi API OPERA Cloud để lấy hoặc cập nhật room status.
4. Backend lưu trạng thái gần nhất để đối chiếu.
5. Nếu lỗi, backend retry hoặc đưa vào danh sách cần xử lý lại.
```

## Xử lý xác thực

Backend cầu nối nên chịu trách nhiệm quản lý authentication với OPERA Cloud:

- Lấy access token.
- Tự refresh token khi hết hạn.
- Không để hệ điều khiển khách sạn gọi trực tiếp OPERA Cloud token endpoint.
- Không log token, client secret hoặc thông tin nhạy cảm.
- Lưu credential bằng environment variables hoặc secret manager.

API nội bộ giữa hệ điều khiển khách sạn và backend cầu nối cũng nên có cơ chế bảo vệ riêng, ví dụ API key nội bộ, mutual TLS hoặc network allowlist.

## Xử lý lỗi

Backend nên chuẩn hóa lỗi từ OPERA Cloud thành format đơn giản:

```json
{
  "success": false,
  "code": "RESERVATION_NOT_FOUND",
  "message": "Không tìm thấy đặt phòng phù hợp.",
  "traceId": "..."
}
```

Cần phân loại lỗi:

- Lỗi xác thực.
- Lỗi thiếu dữ liệu.
- Lỗi validation từ OPERA Cloud.
- Lỗi timeout.
- Lỗi rate limit.
- Lỗi hệ thống tạm thời.

Với lỗi tạm thời, có thể áp dụng retry có giới hạn. Với lỗi nghiệp vụ, trả về ngay để người dùng xử lý.

## Logging và audit

Tool nên ghi log các thông tin sau:

- Thời điểm gọi API.
- Endpoint nội bộ được gọi.
- Endpoint OPERA Cloud tương ứng.
- Trạng thái thành công hoặc thất bại.
- Thời gian phản hồi.
- Trace ID hoặc correlation ID.

Không nên ghi log:

- Access token.
- Client secret.
- Số thẻ thanh toán.
- Dữ liệu cá nhân nhạy cảm nếu không cần thiết.

## Lưu trữ dữ liệu

Nếu backend chỉ là cầu nối trực tiếp, có thể không cần database ở MVP.

Tuy nhiên, nên cân nhắc database nhỏ nếu cần:

- Lưu mapping ID giữa hệ nội bộ và OPERA Cloud.
- Lưu trạng thái đồng bộ gần nhất.
- Lưu hàng đợi retry.
- Lưu audit log.
- Lưu cấu hình khách sạn, property hoặc chain.

Với phạm vi nhỏ, PostgreSQL hoặc SQLite có thể đủ tùy môi trường sử dụng.

## Khai triển

Một phương án xây dựng gọn nhẹ:

- Backend chạy như service nội bộ trong mạng khách sạn hoặc trên cloud riêng.
- Cấu hình qua environment variables.
- Có health check endpoint.
- Có log tập trung.
- Có timeout và retry rõ ràng khi gọi OPERA Cloud.

Endpoint nội bộ tối thiểu:

- `GET /health`
- `GET /reservations/search`
- `GET /reservations/{id}`
- `POST /reservations/{id}/check-in`
- `POST /reservations/{id}/check-out`
- `GET /rooms/{roomNumber}/status`
- `PATCH /rooms/{roomNumber}/status`

## Kế hoạch MVP

### Giai đoạn 1: Khảo sát

- Xác định hệ điều khiển khách sạn đang cần dữ liệu gì.
- Chọn khoảng 20 endpoint OPERA Cloud cần dùng.
- Test các endpoint bằng Postman collections.
- Ghi lại request/response mẫu cho từng endpoint.

### Giai đoạn 2: Thiết kế contract nội bộ

- Thiết kế API nội bộ cho hệ điều khiển gọi.
- Định nghĩa DTO nội bộ.
- Định nghĩa mã lỗi chuẩn.
- Xác định mapping dữ liệu giữa hai hệ thống.

### Giai đoạn 3: Xây backend cầu nối

- Implement authentication với OPERA Cloud.
- Implement HTTP client dùng chung.
- Implement từng service theo nhóm nghiệp vụ.
- Thêm logging, timeout và retry.
- Viết test cho mapper và service quan trọng.

### Giai đoạn 4: Kiểm thử tích hợp

- Chạy thử với môi trường test/sandbox.
- So sánh kết quả với Postman collection.
- Kiểm tra các lỗi thường gặp.
- Đo thời gian phản hồi.
- Hoàn thiện tài liệu vận hành.

## Kết quả mong muốn

Sau MVP, hệ thống sẽ có một backend nhỏ nhưng rõ ràng:

- Chỉ dùng các endpoint thật sự cần.
- Che giấu độ phức tạp của OPERA Cloud khỏi hệ điều khiển khách sạn.
- Có lớp mapping dữ liệu ổn định.
- Có logging và xử lý lỗi đủ để vận hành thực tế.
- Dễ mở rộng thêm endpoint khi nghiệp vụ phát sinh.

