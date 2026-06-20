## Lưu ý khi build chương trình:
Không được đụng tới các folder sau:
BACKEND\graphql
BACKEND\postman-collections
BACKEND\rest-api-specs
BACKEND\.github

### Database và API:
#### API:
1. Register:
POST /api/auth/register
{
    "username": "Nguyễn Văn A",
    "gender": "Male",
    "phone_number": "0912345678",
    "email": "vana@gmail.com",
    "password": "123456",
    "role": "CUSTOMER",
    "avatar": "(file)"
}

Role có thể là:
- CUSTOMER
- RECEPTIONIST

Response:
{
    "message": "Register success",
    "status": "success",
    "data": {
        "id": 10,
        "username": "Nguyễn Văn A",
        "phone_number": "0912345678",
        "email": "vana@gmail.com",
        "role": "CUSTOMER",
        "avatar": "avatar.jpg",
        "created_at": "2026-06-18 16:20:11"
    }
}

Thời gian hiện tại gồm Năm-Tháng-Ngày và giờ phút giây. Thời gian này sẽ được lưu vào database. Thời gian thực tại Việt Nam.

2. Login
Customer và Receptionist dùng chung API
POST /api/auth/login

Request
{
    "phone_number":"0912345678",
    "password":"123456"
}

Response
{
    "message":"Login success",
    "status":"success",
    "data":{
        "id":10,
        "username":"Nguyễn Văn A",
        "role":"CUSTOMER",
        "avatar": "string",
        "created_at": "2026-06-18 16:20:11",
        "access_token": "string"
    }
}

3. Check-in
Chỉ Receptionist được gọi.
POST /api/stays/check-in

Request:
{
    "room_number": "205",
    "room_name": "Premium King",
    "username": "Tony Lee",
    "gender": "Male",
    "phone_number": "0123456789",
    "number_of_guests": 2,
    "expected_arrival_date": "2026-06-25",
    "expected_departure_date": "2026-06-30"
}

Trong đó:
room_number            : Số phòng — dùng để xác định phòng (bắt buộc).
room_name               : Tên loại phòng, vd "Premium King" — chỉ để hiển thị/log, không dùng để tra cứu.
username                : Tên khách
gender                  : Giới tính khách
phone_number            : Số điện thoại khách
number_of_guests        : Số khách
expected_arrival_date   : Ngày dự kiến nhận phòng
expected_departure_date : Ngày dự kiến trả phòng

Không có `reservation_id` trong request — backend **tự tạo một reservation mới** mỗi lần
check-in (không có khái niệm đặt phòng trước qua API này). `checked_in_by` cũng không nằm
trong request — backend lấy từ tài khoản Receptionist đang đăng nhập (qua access_token).

Response:
{
    "message": "Check-in thành công",
    "status": "success",
    "data": {
        "stay_id": 1,
        "reservation_id": 10001,
        "room_number": "205",
        "room_name": "Premium King",
        "username": "Tony Lee",
        "gender": "Male",
        "phone_number": "0123456789",
        "number_of_guests": 2,
        "expected_arrival_date": "2026-06-25",
        "expected_departure_date": "2026-06-30",
        "status": "CHECKED_IN",
        "checked_in_at": "2026-06-18 14:20:15",
        "checked_in_by": 2
    }
}

Trong đó:
stay_id        : Mã của một lần lưu trú (stay) của khách tại khách sạn — backend tự sinh.
reservation_id : Mã đặt phòng — backend tự sinh tại thời điểm check-in.
status         : Trạng thái của việc lưu trú. Có thể là:
                 - CHECKED_IN
                 - CHECKED_OUT

Sau khi API thành công:
- rooms.status đổi thành "Occupied".
- checked_in_at: thời gian hiện tại, giờ Việt Nam, dạng Năm-Tháng-Ngày Giờ:Phút:Giây.

4. API Check-out:
Chỉ Receptionist được gọi.
POST /api/stays/check-out

Request:
{
    "room_number": "205"
}

Chỉ cần `room_number` — backend tự tìm lượt lưu trú (stay) đang ở trạng thái CHECKED_IN
của phòng đó để check-out (không cần `stay_id` hay `username`). `checked_out_by` lấy từ
tài khoản Receptionist đang đăng nhập.

Response
{
    "message": "Check-out thành công",
    "status": "success",
    "data": {
        "stay_id": 1,
        "reservation_id": 10001,
        "room_number": "205",
        "room_name": "Premium King",
        "username": "Tony Lee",
        "gender": "Male",
        "phone_number": "0123456789",
        "number_of_guests": 2,
        "expected_arrival_date": "2026-06-25",
        "expected_departure_date": "2026-06-30",
        "status": "CHECKED_OUT",
        "checked_out_at": "2026-06-30 10:15:30",
        "checked_out_by": 3
    }
}

Sau khi API thành công:
- rooms.status đổi thành "Cleaning" (chưa có endpoint nào đưa phòng về lại "Vacant").
- checked_out_at: thời gian hiện tại, giờ Việt Nam, dạng Năm-Tháng-Ngày Giờ:Phút:Giây.

Nếu phòng không có lượt lưu trú nào đang CHECKED_IN, trả lỗi 404.

5. Do Not Disturb
Có thể gọi bởi Receptionist hoặc Customer.
PATCH /api/rooms/{room_number}/do-not-disturb

Request (bật):
{
    "status": true
}

Request (tắt):
{
    "status": false
}

Backend sẽ:
- Cập nhật rooms.do_not_disturb = status.
- Ghi log vào room_service_logs:
{
    "stay_id": 1,
    "service": "DO_NOT_DISTURB",
    "action": "ON",
    "requested_by": 2,
    "requested_role": "RECEPTIONIST"
}
(action là "OFF" khi tắt; requested_by/requested_role lấy từ tài khoản đang gọi — Customer
bật/tắt thì requested_role là "CUSTOMER".)

Response:
{
    "message": "Cập nhật trạng thái DND thành công. Không nên làm phiền khách.",
    "status": "success",
    "data": {
        "room_number": "205",
        "room_name": "Premium King",
        "do_not_disturb": true,
        "updated_at": "2026-06-18 14:40:05"
    }
}

(Khi tắt, message là "Đã tắt trạng thái Do Not Disturb.", `do_not_disturb: false`.)

6. Make Up Room

a) Khách yêu cầu dọn phòng — chỉ Customer được gọi.
POST /api/rooms/{room_number}/make-up-room
Không cần Request Body.

Backend sẽ:
- Cập nhật rooms.make_up_room = true.
- Ghi log vào room_service_logs:
{
    "stay_id": 1,
    "service": "MAKE_UP_ROOM",
    "action": "REQUEST",
    "requested_by": 15,
    "requested_role": "CUSTOMER"
}

Response:
{
    "message": "Đã gửi yêu cầu dọn phòng",
    "status": "success",
    "data": {
        "room_number": "205",
        "room_name": "Premium King",
        "make_up_room": true,
        "updated_at": "2026-06-18 15:00:00"
    }
}

b) Housekeeping hoàn thành — chỉ Receptionist được gọi (đóng vai trò Housekeeping).
PATCH /api/rooms/{room_number}/service
Không cần Request Body.

Backend sẽ:
- Cập nhật rooms.make_up_room = false.
- Ghi log vào room_service_logs:
{
    "stay_id": 1,
    "service": "MAKE_UP_ROOM",
    "action": "COMPLETE",
    "requested_by": 2,
    "requested_role": "RECEPTIONIST"
}

Response:
{
    "message": "Đã hoàn thành yêu cầu dọn phòng",
    "status": "success",
    "data": {
        "room_number": "205",
        "room_name": "Premium King",
        "make_up_room": false,
        "updated_at": "2026-06-18 15:30:00"
    }
}

Không publish MQTT cho Make Up Room — quyết định chỉ ghi log nội bộ (xem mục Lưu ý cuối file).

#### Database:
1. USERS:
id
username
gender
phone_number
email
password_hash
avatar
role
created_at
updated_at


2. stays (Check-in/Check-out)
POST /api/stays/check-in tạo 1 dòng reservations + 1 dòng stays.
POST /api/stays/check-out cập nhật dòng stays tương ứng.

Ví dụ dòng `stays` sau khi Check-in:
{
    "stay_id": 1,
    "reservation_id": 10001,
    "room_id": 5,

    "username": "Tony Lee",
    "gender": "Male",
    "phone_number": "0123456789",
    "number_of_guests": 2,

    "expected_arrival_date": "2026-06-25",
    "expected_departure_date": "2026-06-30",

    "checked_in_at": "2026-06-25 14:35:10",
    "checked_in_by": 2,

    "checked_out_at": null,
    "checked_out_by": null,

    "status": "CHECKED_IN"
}

Ví dụ dòng `stays` sau khi Check-out:
{
    "stay_id": 1,
    "reservation_id": 10001,
    "room_id": 5,

    "username": "Tony Lee",
    "gender": "Male",
    "phone_number": "0123456789",
    "number_of_guests": 2,

    "expected_arrival_date": "2026-06-25",
    "expected_departure_date": "2026-06-30",

    "checked_in_at": "2026-06-25 14:35:10",
    "checked_in_by": 2,

    "checked_out_at": "2026-06-30 10:15:30",
    "checked_out_by": 3,

    "status": "CHECKED_OUT"
}

Trong đó:
stay_id: Mã của một lần lưu trú (stay) của khách tại khách sạn.
reservation_id: Mã đặt phòng (backend tự sinh tại lúc check-in).
room_id: Khoá nội bộ trỏ tới bảng `rooms` — KHÔNG xuất hiện trong API request/response,
         chỉ dùng nội bộ. API dùng `room_number`/`room_name` (lấy qua join `rooms`+`room_types`,
         không lưu trùng lặp trên `stays`).
username: Tên khách
gender: Giới tính khách
phone_number: Số điện thoại khách
number_of_guests: Số khách
expected_arrival_date: Ngày dự kiến nhận phòng
expected_departure_date: Ngày dự kiến trả phòng
checked_in_at: Thời gian check-in
checked_in_by: ID Receptionist thực hiện Check-in
checked_out_at: Thời gian check-out
checked_out_by: ID Receptionist thực hiện Check-out
status: Trạng thái (CHECKED_IN, CHECKED_OUT)

3. ROOMS:
**1. room_types
-------------------------------
id              PK
code            VARCHAR(20)
name            VARCHAR(100)
max_guests      INT
description     TEXT

Ví dụ:
|  id | code     | name           |
| --: | -------- | -------------- |
|   1 | DISABLED | Disabled       |
|   2 | PK       | Premium King   |
|   3 | PK2      | Premium King 2 |
|   4 | PT       | Premium Twin   |
|   5 | DT       | Deluxe Twin    |
|   6 | DT2      | Deluxe Twin 2  |
| ... | ...      | ...            |


**rooms
-----------------------------------
room_id          PK (nội bộ, không lộ ra API)
room_number      VARCHAR(10)  -- định danh chính dùng trong mọi API
room_type_id     FK
floor
status
do_not_disturb
make_up_room
updated_at

Ví dụ:
| room_id | room_number | room_type_id | floor | status   | do_not_disturb | make_up_room | updated_at |
| ------: | ----------- | -----------: | ----: | -------- | -------------- | ------------ | ---------- |
|       1 | 101         |            5 |     1 | Vacant   | false          | false        | 2026-06-18 10:00:00 |
|       2 | 102         |            5 |     1 | Occupied | false          | false        | 2026-06-18 10:00:00 |
|       3 | 103         |            5 |     1 | Cleaning | false          | true         | 2026-06-18 10:00:00 |
|       4 | 104         |            2 |     1 | Vacant   | true           | false        | 2026-06-18 10:00:00 |

| Room Status  | Khi nào xảy ra?                         | Ai thực hiện?                                           |
| ------------ | --------------------------------------- | ------------------------------------------------------- |
| **Vacant**   | Phòng trống, sẵn sàng cho khách mới     | Sau khi dọn phòng xong hoặc khi khởi tạo hệ thống       |
| **Occupied** | Khách đã Check-in và đang ở             | Receptionist                                            |
| **Cleaning** | Khách đã Check-out, phòng đang được dọn | Receptionist (hoặc tự động sau Check-out). |


** reservations
-------------------------------------
reservation_id      PK (backend tự sinh)
username
gender
phone_number
number_of_guests
expected_departure_date
status

Ví dụ:
| reservation_id | username   | gender | phone_number | number_of_guests | expected_departure_date | status   |
| -------------: | ---------- | ------ | ------------ | ----------------: | ----------------------: | -------- |
|          10001 | Tony Lee   | Male   | 0123456789   |                 2 |              2026-06-30 | BOOKED   |
|          10002 | Mary Jane  | Female | 0987654321   |                 2 |              2026-06-25 | BOOKED   |


*** Bảng room_service_logs
Đây là bảng lưu lịch sử.

{
    "id": 1,
    "stay_id": 1,
    "room_id": 5,
    "service": "DO_NOT_DISTURB",
    "action": "ON",
    "requested_by": 2,
    "requested_role": "RECEPTIONIST",
    "requested_at": "2026-06-26 09:20:00"
}

Sau đó Customer tắt DND
{
    "id": 2,
    "stay_id": 1,
    "room_id": 5,
    "service": "DO_NOT_DISTURB",
    "action": "OFF",
    "requested_by": 15,
    "requested_role": "CUSTOMER",
    "requested_at": "2026-06-26 10:35:00"
}

Sau đó Customer yêu cầu dọn phòng
{
    "id": 3,
    "stay_id": 1,
    "room_id": 5,
    "service": "MAKE_UP_ROOM",
    "action": "REQUEST",
    "requested_by": 15,
    "requested_role": "CUSTOMER",
    "requested_at": "2026-06-26 13:15:00"
}

Sau đó Receptionist (đóng vai trò Housekeeping) hoàn thành dọn phòng
{
    "id": 4,
    "stay_id": 1,
    "room_id": 5,
    "service": "MAKE_UP_ROOM",
    "action": "COMPLETE",
    "requested_by": 2,
    "requested_role": "RECEPTIONIST",
    "requested_at": "2026-06-26 14:00:00"
}

### Lưu ý
- Build trong opera-bridge (thêm bảng users, room_types, rooms, reservations, stays, room_service_logs + route auth, stays, rooms) — không tách project riêng, không đụng 4 folder bị cấm.
- Không cần gọi OPERA CLOUD — chỉ lưu/cập nhật DB nội bộ cho demo, không gọi Oracle sandbox.
- Hash password bằng bcrypt (đã có sẵn thói quen dùng passlib/pwdlib trong FastAPI).
- Ảnh avatar lưu local disk (/uploads), trả về path dạng /uploads/avatar_1.jpg
- Make up room: chọn thiết kế boolean (`rooms.make_up_room`) + ghi log `room_service_logs`,
  KHÔNG publish MQTT. Receptionist đóng vai trò là Housekeeping (gọi `PATCH /service` để
  đánh dấu hoàn thành).
- Định danh phòng trong mọi API là `room_number` (string) — `room_id` chỉ dùng nội bộ
  (khoá ngoại trong DB), không xuất hiện trong request/response.
