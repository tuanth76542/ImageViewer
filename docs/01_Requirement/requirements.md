# Yêu cầu phần mềm — Phần Mềm Xem Ảnh

## 1. Mục đích

Xây dựng ứng dụng desktop xem ảnh trên Windows, giao diện tối (dark theme), điều khiển bằng thanh nổi, phím tắt và trình chiếu toàn màn hình. Bổ sung tính năng lọc chỉ ảnh có người nữ bằng mô hình AI chạy cục bộ.

## 2. Yêu cầu chức năng

| ID | Yêu cầu | Mô tả |
|----|---------|-------|
| F1 | Mở thư mục / ảnh | Chọn thư mục qua dialog hoặc kéo-thả thư mục/tệp ảnh vào cửa sổ. Hỗ trợ jpg, jpeg, png, bmp, gif, webp, tiff, tif, ico. |
| F2 | Điều hướng ảnh | Phím ←/→, lăn chuột, nút ◀/▶ trên thanh nổi. Chuyển ảnh lặp lại (vòng tròn). |
| F3 | Zoom / pan | Zoom bằng Ctrl + lăn chuột, pinch touchpad, nút ➖/➕, phím `+`/`-`. `0` = vừa màn hình, `1` = 100%. Kéo chuột để pan khi zoom to. |
| F4 | Xoay ảnh | Phím `R` hoặc nút ⟳ xoay 90°. |
| F5 | Slideshow | Cửa sổ toàn màn hình riêng (F5), tự chuyển ảnh theo tốc độ 3/5/10/20 giây, tạm dừng, ←/→ chuyển tay, Esc thoát. |
| F6 | Lọc ảnh nữ (F) | Quét thư mục, giữ ảnh có ít nhất 1 khuôn mặt đoán là Female. Hiện dần sau 5 ảnh đầu tiên. Cache theo (đường dẫn + kích thước + mtime) để quét lần sau tức thì. |
| F7 | Màn hình chào | Hiện khi chưa có ảnh nào; hướng dẫn kéo-thả hoặc bấm nút mở thư mục. |
| F8 | Thẻ thông tin | Hiển thị tên ảnh, vị trí, kích thước, số thứ tự; hiện nổi dưới trái. |
| F9 | Thông báo tự ẩn (toast) | Thông báo ngắn gọn tự ẩn sau 3 giây. |
| F10 | Trợ giúp phím tắt | Bấm ❔, `H` hoặc `F1` hiện bảng trợ giúp. |
| F11 | Toàn màn hình | F11 hoặc nháy đúp; thanh điều khiển tự ẩn khi rảnh, hiện lại khi di chuột. |
| F12 | Aero blur | Nền kính mờ kiểu Aero cho thanh tiêu đề (Ctrl+A); có thể tắt hẳn qua `AERO_BLUR = False` trong `xemanh/winfx.py`. |

## 3. Yêu cầu phi chức năng

Đã tách riêng ra **`non_functional_requirements.md`** (NF1…NF8 — giữ nguyên cách
đánh số, xem tệp đó để biết nội dung và cách xác minh từng NF).

## 4. Rang buộc

- Không sửa `dist/`, `build/`, `models/`, `reports/` bằng tay (sản phẩm sinh ra, trong `.gitignore`).
- Giao diện, chú thích, tài liệu, tên test: tiếng Việt (không dấu trong tên tệp/hàm test, có dấu trong chuỗi hiển thị).
- Commit do máy tạo gán tên tác giả là tên model đang chạy (ví dụ `Nemotron 3.5 Super VL Free`).
