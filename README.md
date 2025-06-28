<div align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="100" />
  <h1>Discord PayOS Bot</h1>
  <p>Bot thanh toán PayOS cho Discord server, hỗ trợ quản lý đơn hàng, thống kê, tiện ích quản trị và nhiều hơn nữa.</p>
</div>

---

## 🚀 Cách sử dụng

### 1. Cài đặt

1. Clone repo này về máy:
   ```bash
   git clone <repo-url>
   ```
2. Cài đặt Python 3.10+ và các thư viện:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo file `.env` và điền các thông tin cần thiết:
   ```env
   TOKEN=YOUR_DISCORD_BOT_TOKEN
   PAYOS_CLIENT_ID=...
   PAYOS_API_KEY=...
   PAYOS_CHECKSUM_KEY=...
   LOG_PAYMENT_CHANNEL_ID=YOUR_CHANNEL_ID (Kênh logs thông tin thanh toán)
   DELAY=10 (Thời gian để check trạng thái thanh toán)
   ```

### 2. Chạy bot

```bash
python main.py
```

---

## 💡 Các lệnh chính

### Thanh toán

| Lệnh                     | Mô tả                                        |
| ------------------------ | -------------------------------------------- |
| `!pay <@user> <số tiền>` | Tạo đơn thanh toán cho user (hoặc chính bạn) |
| `!orders [trang]`        | Xem danh sách các đơn, phân trang            |

### Tiện ích quản trị

| Lệnh          | Mô tả                               |
| ------------- | ----------------------------------- |
| `!ping`       | Xem độ trễ bot                      |
| `!uptime`     | Xem thời gian hoạt động bot         |
| `!stats`      | Thống kê chi tiết về bot & hệ thống |
| `!serverinfo` | Thông tin server hiện tại           |
| `!userinfo`   | Thông tin chi tiết về user          |
| `!say <msg>`  | Bot gửi tin nhắn (quản trị)         |

---

## 📦 Tính năng nổi bật

- Tạo đơn thanh toán PayOS, sinh QR, theo dõi trạng thái tự động
- Quản lý, xem danh sách đơn hàng, phân trang
- Thống kê, uptime, ping, info server, info user
- Lệnh quản trị tiện lợi cho admin

---

## 📝 Ghi chú

- Đảm bảo bot có quyền gửi tin nhắn, quản lý tin nhắn ở các kênh cần thiết.
- Để đổi prefix hoặc thêm lệnh, chỉnh sửa trong code các file trong thư mục `commands/`.
- Nếu gặp lỗi, kiểm tra kỹ file `.env` và log terminal.

---

<div align="center">
  <b>nhatphong.xyz B)</b>
</div>
