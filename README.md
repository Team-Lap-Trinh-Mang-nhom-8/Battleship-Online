# Battleship-Online

### Mô tả chung

`Battleship-Online` là phiên bản mạng của game Bắn tàu chiến cổ điển, xây dựng bằng Python và Pygame. Một máy chủ đơn giản điều phối các phòng chơi, trong khi hai client có giao diện đồ hoạ đẹp mắt, chat trực tiếp và hiệu ứng âm thanh khi bắn trúng hoặc hụt đạn.

### Tính năng nổi bật

- Giao diện menu phong cách retro với hiệu ứng tàu và hạt.
- Tạo phòng mới hoặc nhập mã phòng 6 ký tự để kết nối với đối thủ.
- Bảng chơi của người chơi và đối thủ cùng hiển thị trong một cửa sổ chia đôi.
- Thông báo lượt đi, trạng thái thắng/thua và xử lý đối thủ mất kết nối.
- Chat văn bản đơn giản giữa hai người chơi qua mạng.
- Hiệu ứng âm thanh khi đánh trúng, hụt và khi tàu bị đánh chìm.

### Kiến trúc dự án

- `server/`: socket TCP cho phép tạo/join phòng, gửi trạng thái bàn cờ và chuyển tiếp chat.
- `client/`: giao diện Pygame gồm menu, game, bảng người chơi và đối thủ, cùng các tài nguyên hình ảnh/âm thanh.

### Yêu cầu hệ thống

- Python 3.10 trở lên.
- Thư viện `pygame`.
- Kết nối mạng cục bộ (localhost) hoặc theo địa chỉ `HOST`/`PORT` nếu muốn mở rộng.



### Khởi chạy trò chơi

1. Chạy server trước để lắng nghe kết nối:

```powershell
python -m server
```

Điều này sẽ bật server ở `localhost:1234` và in `Started server...`.

2. Khởi tạo client đầu tiên để tạo phòng:

```powershell
python -m client
```

Tại menu chọn `NEW GAME`, server cung cấp mã phòng 6 ký tự và đợi đối thủ.

3. Chạy client thứ hai để tham gia phòng:

```powershell
python -m client
```

Chọn `JOIN GAME` rồi nhập mã phòng được cung cấp.

4. Sau khi cả hai bên kết nối, trận đấu bắt đầu tự động. Người đang lượt đánh được thông báo trên giao diện, chat có thể bật/tắt bằng nút `Chat`.

### Cấu trúc thư mục quan trọng

- `client/assets`: ảnh nền, chữ cái, sprite tàu, âm thanh.
- `client/interface`: logic menu, trò chơi, bảng người chơi.
- `client/misc`: màu sắc, mạng, tiện ích chung như lưới.
- `server`: quản lý kết nối, phòng chơi, sinh layout tàu (ô chia 10x10) và gửi trạng thái.

### Mở rộng hoặc đóng góp

- Có thể mở rộng bằng cách chuyển sang kết nối qua Internet bằng địa chỉ IP công khai.
- Có thể thêm xác thực người dùng/nhân vật bằng SQLite hoặc file JSON.
- Gửi pull request kèm mô tả thay đổi và cách kiểm tra tính năng mới.

### Hướng dẫn thử nghiệm nhanh

- Mỗi client hiển thị thông báo thắng/thua khi toàn bộ tàu bị đánh.
- Thử ngắt kết nối một client để kiểm tra thông báo `Opponent Has Left`.

Nếu cần, mình có thể giúp tạo thêm script tự động khởi động server + hai client hoặc bổ sung tài liệu kỹ thuật chi tiết hơn.
