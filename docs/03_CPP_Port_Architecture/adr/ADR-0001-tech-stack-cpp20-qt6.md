# ADR-0001 — Tech stack UI: C++20 + Qt 6 (Qt Widgets)

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHẤP NHẬN (người dùng chốt)
- **Link**: `00_README.md`, đối chiếu baseline `../../02_System_SW_Architecture/c4_component.md`

## Bối cảnh

App hiện tại viết bằng Python 3.10 + PySide6 (Qt Widgets). Cần port sang C++,
giữ nguyên hành vi, giao diện tối, phím tắt, bộ lọc nữ AI chạy cục bộ.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **C++20 + Qt 6 Widgets** | Port gần nhất: PySide6 → Qt 6 giữ nguyên mô hình widget, QSS, QGraphicsView, signal/slot; QT_QPA_PLATFORM=offscreen cho test CI | Qt 6 chính thức hỗ trợ từ Windows 10 1607 (dự án chốt 1809) — **mất Windows 7** |
| **Qt 5.15 LTS** | Giữ hỗ trợ Windows 7 | Framework cũ, ecosystem thu hẹp, ít năm hỗ trợ còn lại |
| **WinUI 3 / Win32 + Direct2D** | Native Windows 11 | Phải viết lại gần như toàn bộ UI + test offscreen khó |

## Quyết định

**C++20 + Qt 6 (Qt Widgets)**. Hỗ trợ chính thức Windows 10 1809+, thiết bị ở
baseline (PySide6 ≥ 6.6 yêu cầu Win10 1607 trước rồi) thực tế đã ở mức này.
Windows 7 không còn được hỗ trợ — người dùng đã được hiển thị trade-off và chốt
Qt 6.

## Hệ quả

- Điểm tốt: mô hình widget/port 1:1 từ PySide6; nâng cấp chính rõ ràng; dùng
  được Qt Test + offscreen cho CI (kiểm chứng cùng mức baseline).
- Rủi ro: mất người dùng trên Windows 7 — đã ghi vào NFR `nfr_cpp.md` (NF1)
  và rủi ro trong `00_README.md` (register rủi ro).
- Quy định hướng dẫn lint: dùng `clang-format` + `clang-tidy` (không dùng
  `pyflakes` như Python — đó chỉ áp dụng cho tooling giữ Python, xem ADR-0006).

## Xác nhận thực hiện đúng

- CI chạy được trên Windows (xem ADR-0002).
- Screenshot/behavior đối chiếu với bản Python trên 5 ảnh mẫu cố định.
