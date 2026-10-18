# ADR-0005 — Kiến trúc 4 tầng: core / ai / platform / gui

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt — trước khi code C++)
- **Link**: `../c4_cpp_component.md` (chi tiết từng component), baseline
  `../../02_System_SW_Architecture/c4_component.md`

## Bối cảnh

Baseline Python là layout phẳng một package (`xemanh/`) + một tệp AI riêng
(`loc_nu.py`). C4 review của baseline (`../02_System_SW_Architecture/c4_component.md`)
ghi rõ vấn đề: **God Class** (`mainwindow.py` ~573 dòng giữ UI, phím tắt, load
ảnh, zoom, slideshow, Aero, tiến độ lọc), **trộn domain vào UI**, thiếu cache
ảnh, xử lý lỗi yếu. Khi port sang C++, cần phân tầng lại ngay từ đầu — sửa về
sau tốn hơn nhiều.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| Chia `src/` theo kiểu baseline (flat, mỗi chức năng một tệp) | Đậm mùi dự án, port nhanh | God Class + bug cũ kiểu "import sai bị nuốt" dễ lặp lại; core khó test không màn hình |
| **4 tầng + DI tối giản** *(mỗi tầng một target CMake, chỉ tầng trên phụ thuộc tầng dưới)* | `core`/`ai` test được **không Qt widgets**, ranh giới nghiêm ngặt, CI kiểm được | Thêm cấu trúc thư mục + interface; số tệp tăng so với flat một chút |
| Tách tiến trình riêng (microservice/app service process) | Ranh giới cứng | Quá mức cần thiết cho 1 desktop app; triển khai chậm |

## Quyết định (đề xuất)

4 tầng + app entry, mỗi tầng một target CMake:

```
xemanh_app      (executable — main.cpp; link gui)
xemanh_gui      (QtWidgets — MainWindow, ImageView, Slideshow, Overlay, ...)
xemanh_ai       (loc_nu port — không Qt, chỉ dùng OpenCV + onnxruntime)
xemanh_core     (không Qt — GalleryCatalog, ImageLoader+LRU, SessionStore, Logger)
xemanh_platform (Win32 API — winfx; không Qt)
```

**Bắt buộc**: hướng phụ thuộc một chiều — `gui → ai → core`, `gui → core →
platform`. `core` và `ai` **không include header `QtWidgets`** nào (kiểm bằng
quy tắc clang-tidy + CI).

Kèm 5 quy tắc Component của `../c4_cpp_component.md` (quy tắc R1–R5).

## Hệ quả

- test offscreen không cần mở cửa sổ đối với `core`/`ai` (GoogleTest chạy thuần).
- Thêm thư mục `tests/fixture` chứa bộ ảnh mẫu đối chiếu.
- Lưu ý đặt tên: phân biệt rõ `xemanh_gui` (thư viện) và `xemanh_app`
  (executable) — tránh trùng lặp nhầm khi viết CMake.

## Xác nhận thực hiện đúng

- `clang-tidy check` báo 0 vi phạm phạm vi include.
- `cmake --build` từng tầng riêng thành công target `xemanh_core` (không cần build gui).
