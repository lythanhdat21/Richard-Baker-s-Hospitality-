# Tổng hợp README dự án Oracle Hospitality APIs

## Tổng quan

Dự án này là kho lưu trữ tài liệu kỹ thuật cho Oracle Hospitality APIs. Nội dung chính bao gồm đặc tả REST API, bộ sưu tập Postman và các tài liệu hỗ trợ để developer hoặc đối tác có thể tích hợp với Oracle Hospitality Integration Platform.

Các API trong dự án phục vụ nhiều nghiệp vụ của ngành khách sạn, đặc biệt là các chức năng liên quan đến OPERA Cloud, chẳng hạn như đặt phòng, check-in, check-out, quản lý khách, phân phối phòng, giá phòng, tồn kho và báo cáo dữ liệu.

## Cấu trúc chính

### `README.md`

File README ở thư mục gốc giới thiệu mục đích chung của repository:

- Lưu trữ đặc tả REST API cho Oracle Hospitality APIs.
- Cung cấp các Postman collections đi kèm để thử nghiệm và tham khảo cách gọi API.
- Dẫn tới Oracle Hospitality Integration Platform để xem thêm thông tin chính thức.
- Cung cấp thông tin đóng góp, bảo mật, giấy phép và kênh hỗ trợ.

Theo README gốc, đặc tả REST API nằm trong thư mục `rest-api-specs`, còn Postman collections nằm trong thư mục `postman-collections`.

### `rest-api-specs/README.md`

Thư mục `rest-api-specs` chứa các đặc tả REST API theo chuẩn OAS 2.0, còn gọi là Swagger 2.0.

Các file trong thư mục này mô tả chi tiết:

- Endpoint API.
- Phương thức HTTP.
- Request parameters.
- Request body và response body.
- Mã lỗi và cấu trúc dữ liệu.
- Các module nghiệp vụ khác nhau của Oracle Hospitality.

Đây là phần phù hợp để developer đọc khi cần hiểu chính xác API hoạt động như thế nào hoặc khi muốn sinh client SDK, tài liệu API, mock server, hoặc kiểm tra contract API.

### `postman-collections/README.md`

Thư mục `postman-collections` chứa các bộ sưu tập Postman dùng để gọi thử API và tham khảo các luồng nghiệp vụ phổ biến.

Nội dung chính gồm:

- Các Postman collections với nhiều request mẫu.
- Postman Environment chứa các biến môi trường cần thiết khi gọi API.
- Tài liệu workflow mô tả các luồng nghiệp vụ được hỗ trợ.
- Liên kết tới Postman workspace online của Oracle Hospitality APIs.

Các collection này hữu ích khi developer muốn thử API nhanh, kiểm tra cách truyền header, token, biến môi trường, body request và thứ tự gọi API trong một quy trình thực tế.

## Các workflow được hỗ trợ trong Postman

Tài liệu workflow trong `postman-collections/property/WORKFLOWS.md` mô tả một số luồng nghiệp vụ thường dùng, bao gồm:

- Kiểm tra phòng trống và đặt phòng.
- Check-in khách.
- Upsell đặt phòng.
- Xử lý khách đang lưu trú.
- Check-out khách.
- Tạo block.
- Tạo event.
- Tạo rate plan mới.

Các workflow này giúp người tích hợp hiểu thứ tự gọi API trong các tình huống nghiệp vụ thực tế của khách sạn.

## Mục đích sử dụng

Repository này phù hợp cho:

- Developer tích hợp hệ thống bên ngoài với Oracle Hospitality hoặc OPERA Cloud.
- Đối tác cần kiểm tra API contract trước khi phát triển tích hợp.
- Nhóm QA dùng Postman để kiểm thử API.
- Nhóm kỹ thuật cần tra cứu endpoint, schema, request mẫu và workflow.
- Người mới tìm hiểu Oracle Hospitality APIs.

## Cách đọc dự án

Nếu mới bắt đầu, nên đọc theo thứ tự:

1. Đọc `README.md` để hiểu mục tiêu chung của repository.
2. Đọc `postman-collections/README.md` để biết cách dùng Postman collections và environment.
3. Xem `postman-collections/property/WORKFLOWS.md` nếu cần hiểu các quy trình nghiệp vụ mẫu.
4. Tra cứu `rest-api-specs/README.md` và các file JSON trong `rest-api-specs` khi cần chi tiết kỹ thuật của từng API.

## Hỗ trợ, đóng góp và bảo mật

Dự án có hướng dẫn đóng góp trong `CONTRIBUTING.md` và hướng dẫn báo cáo lỗ hổng bảo mật trong `SECURITY.md`.

Nếu có câu hỏi về Oracle Hospitality APIs, README gốc hướng dẫn liên hệ qua email hỗ trợ của Oracle Hospitality APIs.

## Giấy phép

Toàn bộ nội dung trong dự án được phát hành theo Universal Permissive License v1.0. Thông tin chi tiết nằm trong file `LICENSE.txt`.

