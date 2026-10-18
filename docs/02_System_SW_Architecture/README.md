# Kiến trúc hệ thống / phần mềm — Phần Mềm Xem Ảnh

## Phạm vi

Tài liệu này mô tả kiến trúc phần mềm theo **mô hình C4** (Context → Container → Component) cho ứng dụng desktop "Phần Mềm Xem Ảnh".

## Các mức tài liệu

| Mức | File | Nội dung |
|-----|------|----------|
| C4 Level 1 — System Context | `c4_context.md` | Hệ thống, người dùng, hệ thống bên ngoài |
| C4 Level 2 — Container | `c4_container.md` | Các container (ứng dụng PySide6, loc_nu, cache, models) |
| C4 Level 3 — Component | `c4_component.md` | Các component bên trong ứng dụng (MainWindow, ImageView, FilterThread, …) |
| Tổng hợp | `../architecture_summary.html` | Bảng tóm tắt cả 3 mức |

## Lý do chọn C4

- Dễ hiểu cho cả SW Architect, SW Project Manager và SW QA.
- Phân tách rõ khoảng cách giữa business context và chi tiết triển khai.
- Hỗ trợ nhận diện sớm các điểm rủi ro (God Class, trộn domain vào UI, thiếu cache ảnh, xử lý lỗi yếu).

## Lưu ý

Tài liệu phản ánh trạng thái mã nguồn tại thời điểm tạo. Khi có thay đổi cấu trúc lớn (ví dụ tách `MainWindow`, tách `FilterService`), cần cập nhật lại các file C4 tương ứng.

> **Lưu ý (2026-10-18)**: kiến trúc **mục tiêu cho bản port C++** (khác baseline
> Python của tài liệu này) đã soạn riêng ở
> [`../03_CPP_Port_Architecture/00_README.md`](../03_CPP_Port_Architecture/00_README.md)
> kèm bộ 10 ADR (`../03_CPP_Port_Architecture/adr/`), NFR
> (`../03_CPP_Port_Architecture/nfr_cpp.md`) và kiến trúc quy trình 6 agent
> (`../03_CPP_Port_Architecture/10_process_architecture_6_roles.md`). Tài liệu
> trong thư mục này tiếp tục phản ánh **baseline Python** đang chạy.
