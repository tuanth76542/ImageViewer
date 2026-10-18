# C4 Level 1 — System Context

## Tổng quan

Mô hình ngữ cảnh hệ thống cho "Phần Mềm Xem Ảnh" — ứng dụng desktop xem ảnh trên Windows.

## Các đối tượng (Actor)

| Actor | Mô tả |
|-------|-------|
| **Người dùng cuối** | Mở thư mục ảnh, xem ảnh, zoom/xoay, trình chiếu, lọc ảnh nữ, tùy chỉnh Aero. |

## Hệ thống (System)

| Hệ thống | Mô tả |
|----------|-------|
| **Phần Mềm Xem Ảnh** | Ứng dụng desktop PySide6, chạy trên Windows. Điểm vào là `viewer_qt.py`. Mã chính trong gói `xemanh/`. Bộ lọc ảnh nữ tách riêng trong `loc_nu.py`. |

## Hệ thống bên ngoài (External Systems)

| Hệ thống bên ngoài | Mô tả | Tương tác |
|-------------------|-------|-----------|
| **Thư mục ảnh cục bộ** | Thư mục chứa ảnh trên ổ cứng / SSD / USB của người dùng. | Đọc danh sách ảnh, mở file ảnh để hiển thị. |
| **Models AI** | File ONNX (YuNet, FairFace ResNet-34, FairFace ViT) lưu trong `models/`. | Tải lần đầu qua Internet, sau đó đọc cục bộ để suy luận giới tính khuôn mặt. |
| **Internet** | Mạng để tải model (~430MB) lần đầu sử dụng. | Tải model từ GitHub / Hugging Face. |
| **Windows OS** | Hệ điều hành Windows 7+. | Cung cấp API kính mờ Aero (DWM), thiết lập AppID taskbar, quản lý cửa sổ. |

## Sơ đồ tương tác (mô tả bằng văn bản)

```
Người dùng
    |
    | (mở thư mục, kéo-thả, phím tắt)
    v
+-----------------------------+
|   Phần Mềm Xem Ảnh          |
|   (PySide6 desktop app)     |
+-----------------------------+
    | (đọc ảnh)
    v
Thư mục ảnh cục bộ

    | (tải model lần đầu)
    v
Models AI (ONNX) <--- Internet

    | (Aero, AppID)
    v
Windows OS
```

## Ran Grenze (Boundary)

- Trong ran ran: UI (mainwindow, imageview, slideshow, helpdialog, theme, overlay), logic lọc ảnh nữ (filterthread, loc_nu), tiện ích Windows (winfx), đo tài nguyên (perf), tiện ích ảnh (imageutils).
- Ngoài ran ran: thư mục ảnh người dùng, file model ONNX, mạng Internet, Windows OS.
