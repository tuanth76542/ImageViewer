# C4 Level 3 — Component

## Tổng quan

Mô hình component trình bày các thành phần bên trong **Ứng dụng PySide6** (container cấp cao nhất).

## Các component

| Component | Mô tả | Trách nhiệm chính |
|-----------|-------|-------------------|
| **MainWindow** | `xemanh/mainwindow.py` | Cửa sổ chính: UI, thanh nổi, overlay, phím tắt, điều hướng, zoom/xoay, slideshow, lọc nữ, Aero, fullscreen. |
| **ImageView** | `xemanh/imageview.py` | Khung xem ảnh (QGraphicsView): pan, pinch gesture, lăn chuột, kéo-thả, resize. |
| **FilterThread** | `xemanh/filterthread.py` | Luồng nền chạy `loc_nu.filter_female`, phát tín hiệu tiến độ / tìm thấy / hoàn thành / thất bại về UI. |
| **loc_nu** | `loc_nu.py` (ngoài gói) | Bộ lọc ảnh nữ: phát hiện mặt (YuNet), đoán giới tính (2 vòng ResNet + ViT), cache JSON, tải model. |
| **ImageCache** | *(nên có, chưa có)* | LRU cache ảnh đã decode để tránh giải mã lại khi quay lại ảnh cũ. |
| **FilterService** | *(nên có, chưa có)* | Ứng dụng dịch vụ đóng gói logic gọi `loc_nu`, quản lý cache, trả về pure data; tách khỏi UI. |
| **Slideshow** | `xemanh/slideshow.py` | Cửa sổ trình chiếu toàn màn hình, tốc độ 3/5/10/20 giây, nút điều khiển nổi. |
| **HelpDialog** | `xemanh/helpdialog.py` | Bảng trợ giúp phím tắt. |
| **Overlay** | `xemanh/theme.py`, `mainwindow.py` | Topbar (thanh nổi), toast (thông báo tự ẩn), info pill (thẻ thông tin), welcome screen. |
| **winfx** | `xemanh/winfx.py` | Tiện ích Windows: icon app, AppID taskbar, kính mờ Aero (DWM). |
| **theme** | `xemanh/theme.py` | Bảng màu QSS dark theme, hiệu ứng kính mờ `_glass`. |
| **imageutils** | `xemanh/imageutils.py` | Liệt kê ảnh trong thư mục, chuyển PIL → QImage. |
| **perf** | `xemanh/perf.py` | Đo tài nguyên: RAM, CPU, thread, handle. |

## Mối liên hệ và luồng dữ liệu chính

```
Người dùng
    │ (phím tắt, chuột)
    ▼
MainWindow ◄───────────────┐
    │                      │
    │ (gọi lọc)            │ (tín hiệu: progressed/found/done/failed)
    ▼                      │
FilterThread               │
    │                      │
    │ (gọi suy luận)       │
    ▼                      │
loc_nu                     │
    │                      │
    │ (đọc/ghi)            │
    ▼                      │
Cache (JSON)               │
    │                      │
    ▼                      │
Models (ONNX)              │
                           │
MainWindow ◄───────────────┘
    │ (hiển thị)
    ▼
ImageView (zoom, pan, render)

MainWindow ──► Slideshow (toàn màn hình)
MainWindow ──► HelpDialog (trợ giúp)
MainWindow ──► winfx (Aero, taskbar)
```

## Các vấn đề kiến trúc đã biết (nên cải thiện)

| Vấn đề | Mô tả | Độ ưu tiên |
|--------|-------|------------|
| **God Class** | `MainWindow` (~636 dòng) giữ quá nhiều trách nhiệm (UI, phím tắt, load ảnh, zoom, slideshow, Aero, tiến độ lọc, tiêu đề). | Cao |
| **Trộn domain vào UI** | `MainWindow.toggle_female_filter()` trực tiếp import `loc_nu`, hiển thị `QMessageBox`, `QProgressDialog`. | Cao |
| **Thiếu cache ảnh** | Mỗi lần chuyển ảnh đều `Image.open` từ đĩa, chưa có LRU cache ảnh đã decode. | Trung bình |
| **Xử lý lỗi yếu** | Nhiều `try/except: pass` không log, không thông báo người dùng. | Trung bình |
| **Không lưu trạng thái phiên** | Thư mục mở lần cuối, zoom, lọc nữ… mất khi đóng app. | Thấp |
