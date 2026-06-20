## Lưu ý khi build chương trình:
Không được đụng tới các folder sau:
BACKEND\graphql
BACKEND\postman-collections
BACKEND\rest-api-specs
BACKEND\.github

## 14. Demo Project
1. Tạo danh sách người dùng bằng một file .json chứa các thông tin sau:
{
        your_name: string
        gender: Male/Female
        phone_number: number
        email: string
        password: string
        role: Receptionist/Customer
        userImage: (file)
}
Sau đó tôi nhấn nút Submit. Kết quả trả về:
{  
   "message": "Tạo tài khoản thành công",
   "status": "success",
   "data": {
      "id": 1,
      "username": "string",
      "email": "string",
      "phone": "string",
      "avatar": "string",
      "created_at": Thời gian hiện tại gồm Năm-Tháng-Ngày và giờ phút giây. Thời gian này sẽ được lưu vào database.
   }
}

Và tôi có thể add thêm người dùng, id sẽ là 2, 3, 4...

1.1. tạo Login
- Sử dụng phone_number và password để đăng nhập.
- Sau khi đăng nhập thành công, tôi sẽ nhận được:
{
   "message": "Đăng nhập thành công",
   "status": "success",
   "data": {
      "id": 1,
      "username": "string",
      "email": "string",
      "phone": "string",
      "avatar": "string",
      "created_at": Thời gian hiện tại gồm Năm-Tháng-Ngày và giờ phút giây. Thời gian này sẽ được lưu vào database.
      "access_token": string
   }
}

Login trả thêm token (JWT đơn giản); các action Check-in/out/DND/Make-up-room yêu cầu header Authorization: Bearer <token> để biết user + role

2. Tạo các nút Check in, Check out, Do not disturb, Make up room.
Thông tin trong check in gồm có:
- room_number: số phòng
- reservation_id: id đặt phòng
- room_type: Tên loại phòng
- guest_name: tên khách
- number_of_guests: số lượng khách
- expected_departure_date: ngày dự kiến trả phòng
Thông tin trong check out gồm có:
- room_number: số phòng
- reservation_id: id đặt phòng
Thông tin trong do not disturb gồm có:
- room_number: số phòng
Thông tin trong make up room gồm có:
- room_number: số phòng

Tên loại phòng cụ thể như sau:
- Premium King có số phòng là 11, 15, 17
- Deluxe Twin có số phòng là 202, 205, 209
- Junior Suite King có số phòng là 403, 408, 409

3. Cách sử dụng:
Nếu người dùng có role là Receptionist, tôi có thể nhấn vào các nút Check in, Check out, Do not disturb để thay đổi trạng thái phòng.

Nếu người dùng có role là Customer, tôi có thể nhấn vào các nút Do not disturb, Make up room để thay đổi trạng thái phòng.

Mỗi lần nhấn thì hãy in ra cho tôi kết quả:

#### A. Đối với Receptionist:

**1. Check-in:**
```json
{
  "message": "Check-in thành công!",
  "status": "success",
  "data": {
    "reservation_id": 101,
    "room_number": "11",
    "guest_name": "Nguyễn Văn A",
    "room_type": "Premium King",
    "number_of_guests": 2,
    "departure_date": "2026-12-30",
    "updated_at": "2026-06-19 10:00:00"
  }
}
```

**2. Check-out:**
```json
{
  "message": "Check-out thành công!",
  "status": "success",
  "data": {
    "reservation_id": 101,
    "room_number": "11",
    "guest_name": "Nguyễn Văn A",
    "room_type": "Premium King",
    "status": "Clean",
    "updated_at": "2026-06-19 10:05:00"
  }
}
```

**3. Do Not Disturb (DND):**
```json
{
  "message": "Cập nhật trạng thái DND thành công. Không nên làm phiền khách.",
  "status": "success",
  "data": {
    "room_number": "11",
    "is_dnd": true,
    "updated_at": "2026-06-19 10:10:00"
  }
}
```

#### B. Đối với Customer:

**1. Do Not Disturb (DND):**
```json
{
  "message": "Cập nhật trạng thái DND thành công. Không nên làm phiền khách.",
  "status": "success",
  "data": {
    "room_number": "11",
    "is_dnd": true,
    "updated_at": "2026-06-19 10:15:00"
  }
}
```

**2. Make up room:**
```json
{
  "message": "Yêu cầu dọn phòng đã được ghi nhận.",
  "status": "success",
  "data": {
    "room_number": "11",
    "housekeeping_requested": true,
    "updated_at": "2026-06-19 10:20:00"
  }
}
```

# 4 Cách test.
Hãy tạo giúp tôi một nút hoặc một giao diện để tôi có thể test các chức năng check in, check out, do not disturb, make up room trong Postman.

# 5. Lưu ý
- Build trong opera-bridge (thêm bảng users, rooms, reservations + route auth, users, action mới) — không tách project riêng, không đụng 4 folder bị cấm.
- Không cần gọi OPERA CLOUD — chỉ lưu/cập nhật DB nội bộ cho demo, không gọi Oracle sandbox.
- Hash password bằng bcrypt (đã có sẵn thói quen dùng passlib/pwdlib trong FastAPI).
- Ảnh userImage lưu local disk (/uploads), trả về path dạng /uploads/avatar_1.jpg
