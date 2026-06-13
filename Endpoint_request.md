Listed directory hospitality-api-docs

Searched for "endpoint"

Viewed Y\_TUONG\_TOOL\_CAU\_NOI\_OPERA\_CLOUD.md:1-358

Viewed PROJECT\_STRUCTURE\_VA\_LUONG\_HOAT\_DONG.md:1-671



Dựa vào các tài liệu trong dự án (đặc biệt là file `Y\_TUONG\_TOOL\_CAU\_NOI\_OPERA\_CLOUD.md` và `PROJECT\_STRUCTURE\_VA\_LUONG\_HOAT\_DONG.md`), khách hàng \*\*không yêu cầu bao phủ toàn bộ\*\* hàng ngàn endpoint của Oracle Hospitality API. 



Thay vào đó, phạm vi ban đầu được khách hàng giới hạn ở \*\*khoảng 20 endpoint thật sự cần thiết\*\* để phục vụ luồng vận hành của khách sạn. Việc giới hạn này nhằm mục đích giúp hệ thống nhẹ, dễ bảo trì và dễ kiểm soát lỗi.



Cụ thể, các nhóm endpoint nội bộ tối thiểu (đóng vai trò cầu nối với OPERA Cloud) được đề xuất ban đầu bao gồm:



1\. \*\*Tìm kiếm và kiểm tra đặt phòng:\*\*

&#x20;  - `GET /reservations/search` (Tìm reservation theo mã, tên hoặc ngày đến)

&#x20;  - `GET /reservations/{id}` (Lấy chi tiết reservation)



2\. \*\*Xử lý nghiệp vụ Check-in / Check-out:\*\*

&#x20;  - `POST /reservations/{id}/check-in`

&#x20;  - `POST /reservations/{id}/check-out`



3\. \*\*Quản lý trạng thái phòng (Room / Housekeeping):\*\*

&#x20;  - `GET /rooms/{roomNumber}/status` (Lấy thông tin room status/housekeeping status)

&#x20;  - `PATCH /rooms/{roomNumber}/status` (Đồng bộ/cập nhật trạng thái dọn phòng)



4\. \*\*Quản lý hệ thống:\*\*

&#x20;  - `GET /health` (Endpoint kiểm tra trạng thái hoạt động của backend)



Ngoài ra, tài liệu cũng dự phòng thêm một số nhóm tính năng khác có thể cần tuỳ theo yêu cầu trao đổi dữ liệu chi tiết giữa hệ thống điều khiển và OPERA Cloud:

\- \*\*Guest/Profile:\*\* Lấy và cập nhật thông tin khách.

\- \*\*Cashiering/Folio:\*\* Lấy folio cơ bản hoặc kiểm tra thanh toán (nhóm này ưu tiên kiểm soát kỹ vì là dữ liệu nhạy cảm).



\*\*Tóm lại:\*\* Khách yêu cầu tạo một danh sách các API nội bộ chuẩn hoá phục vụ các luồng trên. Backend sẽ tự map các API nội bộ này sang các endpoint tương ứng của OPERA Cloud, không để hệ điều khiển nội bộ phụ thuộc trực tiếp vào cấu trúc phức tạp của OPERA Cloud. Danh sách chính xác khoảng 20 endpoint của OPERA Cloud sẽ được chọn chi tiết trong \*Giai đoạn 1: Khảo sát\* sau khi đã thống nhất hoàn toàn nhu cầu dữ liệu.

