# C4 Level 1 — System Context (bản C++)

## Tổng quan

Mô hình ngữ cảnh hệ thống cho **Phần Mềm Xem Ảnh (C++ port)** — ứng dụng desktop
xem ảnh trên Windows, viết bằng C++20 + Qt 6 Widgets, với bộ lọc ảnh nữ chạy
ONNX Runtime cục bộ.

So với baseline Python (`../02_System_SW_Architecture/c4_context.md`): danh sách
actor và hệ thống bên ngoài **không đổi** — chỉ công nghệ của hệ thống trung tâm
đổi. Port có ý nghĩa kiến trúc nằm ở mức Container và Component, không ở mức
Context.

## Các đối tượng (Actor)

| Actor | Mô tả |
|-------|-------|
| **Người dùng cuối** | Mở thư mục ảnh, xem ảnh, zoom/xoay, trình chiếu, lọc ảnh nữ, bật/tắt Aero blur. |
| **Máy chủ tải model** *(trong suốt với người dùng)* | Nguồn tải YuNet + FairFace ONNX lần đầu; sau đó offline hoàn toàn (NF11). |

## Hệ thống (System)

| Hệ thống | Mô tả |
|----------|-------|
| **Phần Mềm Xem Ảnh (C++)** | Ứng dụng desktop single-process. Điểm vào `app/main.cpp`. Mã chính trong `src/xemanh/` (core/ai/gui/platform), engine AI trong `src/loc_nu/`. |

## Hệ thống bên ngoài (External Systems)

| Hệ thống bên ngoài | Mô tả | Tương tác |
|-------------------|-------|-----------|
| **Thư mục ảnh cục bộ** | Thư mục chứa ảnh trên ổ cứng / SSD / USB. | Đọc danh sách ảnh, đọc tệp ảnh để decode + hiển thị. |
| **Models AI (ONNX)** | 3 tệp ONNX: `face_detection_yunet_2023mar.onnx` (~230KB), FairFace ResNet-34 (~85MB), FairFace ViT (~343MB), tổng ~430MB, trong `models/`. | Tải lần đầu qua Internet, sau đó suy luận cục bộ. |
| **Internet** | Chỉ dùng để tải model lần đầu (GitHub / Hugging Face). | HTTPS GET, sau đó app offline hoàn toàn (NF11). |
| **Windows OS** | Windows 10 1809+ (Qt 6 chính thức hỗ trợ từ Win10 1607; dự án chốt 1809 vì vcpkg + onnxruntime runtime yêu cầu). | API DWM kính mờ Aero, AppID taskbar, quản lý cửa sổ, gesture touchpad/touch. |

## Sơ đồ tương tác (mô tả bằng văn bản)

```
Người dùng
    |
    | (mở thư mục, kéo-thả, phím tắt)
    v
+--------------------------------------+
|   Phần Mềm Xem Ảnh (C++ / Qt 6)      |
|   desktop app, 1 tiến trình          |
+--------------------------------------+
    | (đọc ảnh)                    | (Aero DWM, AppID, gesture)
    v                              v
Thư mục ảnh cục bộ            Windows OS 10 1809+

    | (tải model lần đầu)
    v
Models AI (ONNX, ~430MB) <--- Internet
```

## Ranh giới (Boundary)

- **Trong ranh giới**: toàn bộ mã C++ (`src/xemanh/core/*`, `src/xemanh/ai/*`,
  `src/xemanh/gui/*`, `src/xemanh/platform/*`, `src/loc_nu/*`), cache JSON do
  app tự ghi.
- **Ngoài ranh giới**: thư mục ảnh người dùng (chỉ đọc), tệp model ONNX, mạng
  Internet (một lần tải model), Windows OS API.
- **Khác baseline** (`../02_System_SW_Architecture/c4_context.md`): runtime
  Python + PySide6 được thay bởi nhị phân C++ tự đóng gói (không cần cài
  runtime), gọn hơn: bundle app + thư viện nằm gọn ≤ 200MB, riêng thư mục model
  ~430MB (mục tiêu NF10 trong `nfr_cpp.md`). Windows 7 không còn trong hỗ trợ
  (ADR-0001).
