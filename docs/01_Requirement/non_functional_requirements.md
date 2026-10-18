# Yêu cầu phi chức năng (NFR) — Phần Mềm Xem Ảnh

> Tách ra từ `requirements.md` (mục 3 — "Yêu cầu phi chức năng") theo ADR-0016 mục 3:
> nội dung và **cách đánh số NF1…NF8 giữ nguyên**, chỉ đổi chỗ ở. Sở hữu: **R6
> SW-Architect** (bảng quyền ghi: `../04_Process_Architecture/10_process_architecture_6_roles.md`).
>
> NFR của **quy trình làm việc** (6 vai, cổng, thời gian cổng…) nằm ở
> `../04_Process_Architecture/nfr_process.md` — đừng trộn hai bảng vào nhau.

## 1. Bảng NFR sản phẩm

| ID | Yêu cầu | Mô tả |
|----|---------|-------|
| NF1 | Hệ điều hành | Windows 7 trở lên. Chỉ chạy trên Windows (dùng Win32 API cho Aero, taskbar app-id). |
| NF2 | Ngôn ngữ / runtime | Python 3.10+, PySide6 >= 6.6.0. Quản lý dependencies bằng `uv` + `uv.lock`. |
| NF3 | Layout mã nguồn | Layout phẳng (không `src/`), không dùng `ruff` (dùng `pyflakes`). Mã app nằm trong `xemanh/`, `loc_nu.py`, `viewer_qt.py`. |
| NF4 | Hiệu năng | Không rò rỉ RAM khi chuyển ảnh lặp đi lặp lại. CPU khi rảnh thấp (< 1%). |
| NF5 | Độ phủ test | C0/C1 >= 80% (`--cov-fail-under=80`). Hiện tại đạt ~99.9%. |
| NF6 | Test offscreen | Chạy test trên CI không cần màn hình thật (Qt offscreen). Không tải model thật (giả lập/monkeypatch). |
| NF7 | Đóng gói .exe | Build onefile qua PyInstaller + spec lọc DLL xung đột. Kích thước ~115MB. Model lưu vào `%LOCALAPPDATA%\PhanMemXemAnh\models` hoặc `./models` cạnh .exe. |
| NF8 | Offline | Sau lần tải model đầu (~430MB), app hoạt động hoàn toàn offline. |

## 2. Cách xác minh (đo được, không cần đọc mã)

| NF | Lệnh / cách kiểm |
|----|------------------|
| NF1 | Chạy app trên Windows: `uv run python viewer_qt.py` (không có bản build cho hệ khác) |
| NF2 | `uv --version`, `uv run python -V`, `uv lock --check` |
| NF3 | `ls xemanh/*.py loc_nu.py viewer_qt.py` (không có thư mục `src/`); `uv run --with pyflakes python -m pyflakes …` |
| NF4 | `uv run python tools\measure_resources.py <thư-mục> -s 30` (RAM/CPU trung bình và đỉnh) |
| NF5 | `uv run pytest` — đọc bảng độ phủ ở cuối, sàn `--cov-fail-under=80` trong `pyproject.toml` |
| NF6 | `uv run pytest -m unit` / `-m functional` (offscreen, không mạng, không model thật) |
| NF7 | `build_exe.bat` rồi `uv run python tools\check_exe.py` (bundle sạch DLL lạ, app mở được) |
| NF8 | Ngắt mạng sau lần tải model đầu, mở thư mục ảnh và bấm lọc: kết quả không đổi |

## 3. Quy tắc sửa NFR

Nội dung NF1…NF8 chỉ **R6 SW-Architect** sửa; đổi chỉ số/nội dung phải đi kèm **ADR
mới** (đừng sửa thẳng số liệu). Thêm NFR mới thì đánh số tiếp `NF9`, `NF10`… và ghi
cách xác minh vào mục 2.
