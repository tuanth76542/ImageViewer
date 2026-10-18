# C4 Level 2 — Container

## Tổng quan

Mô hình container trình bày các thành phần kỹ thuật cao cấp của hệ thống.

## Các container

| Container | Công nghệ | Mô tả |
|-----------|-----------|-------|
| **Ứng dụng PySide6** | Python 3.10, PySide6 >= 6.6.0 | Single-process desktop application. Điểm vào `viewer_qt.py`. Chứa toàn bộ UI, điều hướng, zoom, slideshow, lọc ảnh nữ. |
| **Bộ lọc ảnh nữ (loc_nu)** | Python, OpenCV, onnxruntime, numpy | Chạy suy luận AI (YuNet phát hiện mặt, FairFace ResNet-34 + ViT đoán giới tính). Song song qua `ThreadPoolExecutor`. Cache kết quả vào JSON. |
| **Cache lọc** | File JSON (`loc_nu_cache_v2.json`) | Lưu kết quả suy luận theo (đường dẫn + kích thước + mtime). Tránh suy luận lại ảnh cũ. |
| **Models** | File ONNX (3 file, ~430MB) | YuNet (~230KB), FairFace ResNet-34 (~85MB), FairFace ViT (~343MB). Lưu trong `models/`. |
| **Thư mục ảnh người dùng** | File system (JPEG, PNG, …) | Nguồn ảnh đầu vào. Không do hệ thống quản lý, chỉ đọc. |

## Mối liên hệ giữa container

```
Ứng dụng PySide6 <──────────────┐
       │                        │
       │ (gọi lọc, nhận kết quả) │
       v                        │
Bộ lọc ảnh nữ (loc_nu)          │
       │                        │
       │ (đọc/ghi)              │
       v                        │
Cache lọc (JSON)                │
       │                        │
       │ (tải model)            │
       v                        │
Models (ONNX)                   │
                                │
Ứng dụng PySide6 ───────────────┘
       │ (đọc ảnh)
       v
Thư mục ảnh người dùng
```

## Ran Grenze (Boundary)

- Trong ran ran: Ứng dụng PySide6, Bộ lọc ảnh nữ, Cache lọc, Models.
- Ngoài ran ran: Thư mục ảnh người dùng, Internet (tải model lần đầu).

## Lưu ý triển khai

- Ứng dụng đóng gói thành `.exe` onefile (~115MB) qua PyInstaller + spec lọc DLL xung đột (tránh crash do DLL C++ runtime cũ của Java).
- Bản `.exe` lưu model vào `%LOCALAPPDATA%\PhanMemXemAnh\models` để không phải tải lại mỗi lần mở (thư mục giải nén onefile bị xoá khi thoát).
