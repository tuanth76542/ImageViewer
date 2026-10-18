# ADR-0007 — Đóng gói & phát hành: CPack (ZIP portable) + NSIS tùy chọn

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt)
- **Link**: baseline `../../../README.md` (mục Đóng gói .exe), `../../../PhanMemXemAnh.spec`

## Bối cảnh

Baseline Python đóng gói bằng PyInstaller onefile (~115MB, riêng ~430MB model
tải theo thời gian chạy). Vấn đề thật từng gặp: PyInstaller nhặt DLL runtime
C++ cũ từ PATH (JRE trên máy dev) → `0xC0000005`; spec phải lọc thủ công DLL
xung đột. Với bản C++, đóng gói chuẩn hơn rất nhiều.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **CPack: ZIP portable (one-dir bundle) — chính** | Đơn giản; runtime DLL gọn bằng `windeployqt`; không có vấn đề DLL bản cũ trên PATH kiểu PyInstaller | Kích thước lớn hơn onefile chút (giải nén ở máy người dùng) |
| NSIS / Inno Setup installer | Cài đặt chuẩn Windows, shortcut menu | Thêm công cụ, release phức tạp hơn |
| MSIX | Gắn với ký số | Layering phức tạp + yêu cầu ký số |
| Static link Qt / onnxruntime | Một .exe duy nhất | License Qt LGPL + static của onnxruntime có ràng buộc; mất khả năng thay DLL version |

## Quyết định (đề xuất)

**CPack "portable" (one-dir bundle) là hình thức chính; NSIS installer chỉ là
lựa chọn phụ nếu cần cài đặt kiểu chuẩn.** Runtime DLL Qt, OpenCV,
onnxruntime được gom nhịp vào thư mục output bằng `windeployqt` +
`CMAKE_RUNTIME_OUTPUT_DIRECTORY` — hết rủi ro DLL từ PATH như PyInstaller từng
gặp (vấn đề thật đó đã ghi trong `README.md` mục "Đóng gói .exe").

Kích thước dự kiến: bundle app ≈ 70–90MB (Qt Core/Gui/Widgets + OpenCV +
onnxruntime), nhỏ hơn PyInstaller 115MB và chưa tính `models/` (mục tiêu NFR
NF10 ≤ 200MB).

Model ONNX ~430MB **không đóng trong bundle** — chỉ tải lần đầu vào
`%LOCALAPPDATA%\PhanMemXemAnh\models` (giữ như baseline); muốn "portable" thì
copy `models/` ra cạnh .exe (giữ như baseline).

Tool giữ nguyên: `tools/check_exe.py` (Python, giữ như baseline: mở thử .exe,
đo RAM, kiểm tra bundle, tự tạo ảnh mẫu khi không truyền thư mục ảnh) chỉ cần
đổi đường dẫn; thêm kiểm C++ (chạy .exe không nạp DLL lỗi PATH).

## Hệ quả

- Trước release: `tools/measure_resources.py` vẫn dùng được (Python dev
  tooling, ADR-0002).
- Lệnh "cách đóng gói release" ghi trong `docs/git_work_flow/` của repo mới —
  SW-Integrator sẽ hoàn thành khi ADR-0009 được duyệt.
