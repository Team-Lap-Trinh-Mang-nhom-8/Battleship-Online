# Tổng hợp thành phần sử dụng kiến thức lập trình mạng

Tài liệu này tổng kết mọi điểm trong dự án tận dụng kiến thức về socket TCP, giao thức ứng dụng do người chơi định nghĩa, đa luồng và đồng bộ tài nguyên. Các tên lớp/hàm giữ nguyên để bạn thuận tiện theo dõi trong mã nguồn.

## Tầng server

### `server/network.py`

- Điều phối socket IPv4 (`socket.AF_INET`, `socket.SOCK_STREAM`), gán địa chỉ vào `Network.address`, gọi `listen()/accept()` và chấp nhận kết nối mới.
- Định nghĩa `SERVER_HOST`/`SERVER_PORT` làm biến môi trường để chứng minh kiến thức tham số hóa dịch vụ mạng.
- Với mỗi kết nối: khởi tạo một thể hiện `Network` (với `is_server=False`) rồi bắt một luồng riêng (`Thread`) thực thi `proceed_with_connection` → mô hình thread-per-connection.
- Khóa toàn cục (`Lock`) bảo vệ `game_list` khi nhiều luồng thao tác → thực hành đồng bộ dữ liệu và tránh race condition.
- `Room` duy trì danh sách client, phân luồng trận và phát thanh trạng thái, minh họa quản lý phiên (session/room).
- `send()`/`receive()` sử dụng length-prefix 4 byte big-endian trước payload JSON → làm rõ framing giao tiếp, giải mã và mã hóa dữ liệu, đảm bảo client/server đọc đúng số byte.
- Xử lý các thông điệp theo `category`: `CREATE`, `JOIN`, `BOARD`, `POSITION`, `CHAT`, `OVER`, `END` → áp dụng thiết kế giao thức ứng dụng tùy biến trên nền TCP thô.
- Chuyển tiếp chat/tọa độ sang đối thủ thông qua `player.opponent.conn.send(data)` → minh họa relay message và forwarding trong mô hình client-server.
- Bắt ngoại lệ khi mất kết nối và giải phóng phòng (đóng socket, xóa `Room` khỏi `game_list`) → thể hiện quản lý trạng thái kết nối và thu hồi tài nguyên.

### `server/__main__.py`

- điểm khởi hành của dịch vụ, khởi tạo `Network()` và lắng nghe trên thread chính → xác định entry point của ứng dụng mạng.

### `server/utils.py`

- `layout_ships()` tạo lưới tàu ngẫu nhiên (dữ liệu bạn gửi dưới dạng `BOARD`) → trình bày cách share dữ liệu game state giữa tầng server và client.

## Tầng client

### `client/misc/network.py`

- Khởi tạo TCP socket, kết nối tới `Network.address`, sử dụng zíc zắc `length-prefix + JSON` giống phía server → minh họa nguyên tắc thiết kế giao thức hai chiều.
- `send()`/`receive()` bảo đảm client và server dùng chung framing, thực thi reliable stream semantics.

### `client/__main__.py`

- Sau khi kết nối, tạo luồng `receiving_thread` chuyên nhận dữ liệu từ server để không chặn vòng lặp Pygame → chuẩn lập trình đa luồng cho giao diện không bị lag.
- Các thao tác menu gửi tin `CREATE`/`JOIN` và chờ phản hồi `ID`/`BOARD` rồi vào game → thể hiện handshake đơn giản và phân tách trách nhiệm UI/tương tác mạng.

### `client/interface/game.py`

- `receiving_thread()` giải mã JSON từ `Network.receive()`, cập nhật biến `player`, `opponent`, `waitting` → thể hiện xử lý sự kiện bất đồng bộ.
- Xử lý các `category`: `BOARD` truyền trạng thái ban đầu, `POSITION` cập nhật lượt bắn, `CHAT` cập nhật tin nhắn, `END` báo đối thủ rời phòng → minh họa xử lý protocol theo nội dung.
- Khi người chơi bắn: `self.n.send({"category": "POSITION", "payload": x})` → gửi sự kiện gameplay lên server.
- Chat thực hiện qua kênh TCP giống, đóng gói text vào `payload` → thực hành truyền dữ liệu text root.
- Nhận `END` từ server để hiển thị “Opponent Has Left” → trình bày thông báo lỗi mạng và thu hồi trạng thái.

### `client/interface/menu.py`

- `run()` gửi `CREATE` hoặc `JOIN` cùng mã phòng 6 ký tự đến server để tạo/nhập phòng → mô tả bước khởi tạo kết nối trực tiếp từ UI.

## Giao thức ứng dụng nội bộ

- Tất cả thông điệp là JSON có trường `category`/`payload`, giúp mở rộng để quản lý phòng, đồng bộ bản đồ, chat và kết thúc trận.
- Dòng dữ liệu TCP bắt đầu bằng chiều dài 4 byte big-endian → minh họa kỹ thuật framing, phòng tránh cắt/dồn gói (packet fragmentation/coalescing).
- ID phòng 6 ký tự ngẫu nhiên từ `generate_id()` → nêu kiến thức định danh session và tránh trùng lặp.
- Luồng “create room” → “join room” thể hiện handshake giữa client và server thông qua trung gian.

## Mô hình luồng và đồng bộ

- Mỗi client được phục vụ bởi một luồng riêng trên server (`Thread(target=self.proceed_with_connection, ...)`) → ví dụ thực hành đa luồng phía server.
- `Lock` toàn cục bảo vệ `game_list` khi thêm/xóa phòng → nhấn mạnh đồng bộ thread-safe.
- Client chạy luồng riêng để nhận server, tránh block khung hình Pygame → minh họa concurrency trên giao diện.

## Xử lý sự kiện mạng

- Ngoại lệ trong quá trình nhận/giải mã (`except: break`) giúp thread không crash khi mất dữ liệu → xử lý lỗi mạng cơ bản.
- Khi một người chơi rời (`"OVER"` hoặc mất kết nối), server gửi `END` để thông báo người chơi còn lại và giải phóng phòng → thực hành cleanup kết nối.

## Gợi ý kiểm thử liên quan mạng

- Chạy server trên máy riêng, mỗi client trên hai máy khác nhau hoặc hai cửa sổ Pythons để kiểm tra kết nối LAN.
- Dùng `netstat`/`Wireshark` phân tích gói JSON và các 4 byte độ dài → cụ thể hóa khái niệm giao thức.
- Đóng client một cách bất ngờ, quan sát `Opponent Has Left` → xác nhận logic phát hiện ngắt kết nối.
