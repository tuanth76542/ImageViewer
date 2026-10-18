# Yêu cầu phi chức năng — bản C++ (NFR)

> Sở hữu: **R6 SW-Architect** (theo ADR-0009). Trạng thái: **BẢN THẢO** — số liệu
> mục tiêu sẽ khóa sau khi ADR-0005…ADR-0010 được người dùng duyệt; các NFR
> lệ thuộc ADR được đánh dấu trong cột "Depends on".

## 1. Bảng NFR

| ID | Yêu cầu | Chỉ số đo (mục tiêu) | Cách xác minh | Depends on |
|----|---------|---------------------|---------------|-----------|
| NF1 | Hệ điều hành | Windows 10 1809+ (x64); **Windows 7 không hỗ trợ** | CI chạy trên `windows-latest`; cài thực trên Win10 tại máy dev | ADR-0001 |
| NF2 | Ngôn ngữ/runtime dev | C++20; MSVC 2022 (≥ 19.30); Qt ≥ 6.8 LTS; onnxruntime pin theo `vcpkg.json`; OpenCV ≥ 4.9 | CI build từ máy sạch | ADR-0001, ADR-0002 |
| NF3 | Thời gian build | build Release từ máy sạch ≤ 6 phút trên CI (win-latest, vcpkg binary-cache hit); incremental ≤ 30 s máy dev | đo CI run + `cmake --build --preset release` | ADR-0002 |
| NF4 | Hiệu năng decode | mở ảnh 1600×1200 ≤ **60 ms** (baseline Python: PIL decode chậm hơn rõ); 60 lần navigate **không chạm đĩa** nhờ LRU cache | stopwatch trong test `resources` + `tools/measure_resources.py` | ADR-0008 |
| NF5 | Hiệu năng lọc nữ | suy luận ≤ **950 ms/ảnh** trên máy dev 2 nhân/4 luồng (ngang baseline Python); hiện sớm sau **5 ảnh nữ** đầu (`SHOW_AFTER = 5`, không chờ quét hết) | test đối chiếu trên bộ ảnh mẫu `tests/fixture/` + `tools/bench_loc_nu.py` (giữ Python) | ADR-0004, ADR-0008 |
| NF6 | Bộ nhớ | RAM rảnh ≤ **120 MB** (baseline ~87 MB; thêm khi mở ảnh); RAM đỉnh khi quét 345 ảnh ≤ **1.2 GB** | `tools/measure_resources.py` | ADR-0005, ADR-0008 |
| NF7 | CPU rảnh | ≤ **1%** CPU lúc idle (giữ đúng baseline NF4) | `tools/measure_resources.py` | ADR-0008 |
| NF8 | Độ phủ test | C0 (dòng lệnh) ≥ 80% trên `src/` (không tính tooling Python, không tính `tests/`) | OpenCppCoverage gắn vào ctest (ADR-0006) | ADR-0006 |
| NF9 | Test tự chứa | test không mạng, không model thật, không màn hình thật; chạy offscreen qua `QT_QPA_PLATFORM=offscreen`; mock tại `IGenderInference` | chạy unit trong CI headless PASS | ADR-0005, ADR-0006 |
| NF10 | Bundle `.exe` | tổng bundle app (không đếm `models/`) ≤ **200 MB**; không quá bùng nhờ KL của runtime | đo khi release bằng `tools/check_exe.py` | ADR-0007 |
| NF11 | Offline sau lần tải model đầu | model ~430MB tải 1 lần vào `%LOCALAPPDATA%\PhanMemXemAnh\models` (hoặc `./models` cạnh .exe); sau lần đầu app chạy offline hoàn toàn | `tools/check_exe.py` + test `model_store` | ADR-0004 |
| NF12 | Cache tương thích | file `loc_nu_cache_v2.json` sinh từ bản Python đọc được bằng bản C++ (không phải quét lại) | test unit với file cố định `tests/fixture/cache_v2_sample.json` | ADR-0010 |
| NF13 | Hành vi lọc nữ đúng | nhận diện đúng trên bộ ảnh mẫu cố định (bản Python làm oracle); sai lệch ≤ 1 ảnh / 350 | `bench_loc_nu.py` đối chiếu Python↔C++ mỗi lần port | ADR-0004, ADR-0006 |
| NF14 | CI tái lập được | CI trên Windows runner chỉ cần 2 công cụ: MSVC 2022 + CMake/vcpkg (không cài thêm gì khác) | CI xanh từ máy sạch → pass | ADR-0002 |
| NF15 | Lint & format | 0 cảnh báo clang-tidy mới trong tệp sửa; clang-format sạch | CI gate (ADR-0006); `NOLINT` phải kèm lý do | ADR-0006 |
| NF16 | Xử lý lỗi runtime | mọi lỗi được log với INFO/WARN/ERROR, file `%LOCALAPPDATA%\PhanMemXemAnh\logs\` quay vòng ≤ 15 MB; UI không crash khi ảnh hỏng/thư mục rỗng/mất model | test unit + test case lỗi | ADR-0005 |
| NF17 | Ngôn ngữ sản phẩm & code | giao diện tiếng Việt có dấu (giữ baseline); comment/tài liệu tiếng Việt có dấu; tên tệp/hàm test **không dấu** | review R4 + quy tắc từ AGENTS.md | ADR-0001 |
| NF18 | Luồng nền không block UI | event loop UI ≤ 16 ms/chu kỳ khi decode + lọc chạy song song | stopwatch trong test `resources` | ADR-0008 |
| NF19 | Quy trình 6-role được bảo đảm | CI chạy xanh trên `main` sau merge; 1 task = 1 nhánh = 1 commit squash; `main` protected | CI log; kiểm tra quy tắc nhánh khi merge | ADR-0009 |

## 2. NFR baseline Python không giữ lại (đã thay thế)

| Baseline NF | Nội dung cũ | Thay bằng | Lý do |
|-------------|-------------|-----------|-------|
| NF1 | Windows 7 trở lên | NF1 bản C++ (Win10 1809+) | Qt 6 bỏ Win7 — ADR-0001 (phương án Qt 5.15 đã cân nhắc rồi loại vì ecosystem) |
| NF2 | Python 3.10+, PySide6 ≥ 6.6, `uv` + `uv.lock` | NF2 bản C++ | port sang C++ |
| NF3 | Layout phẳng `xemanh/`, không `ruff`, dùng `pyflakes` | quy tắc mới (ADR-0002, ADR-0005): 5 target CMake, clang-format/tidy | C++ layout khác; **tooling Python giữ nguyên `uv` + `pyflakes`** cho `tools/` |
| NF5 | Độ phủ pytest-cov C0/C1 ≥ 80% | NF8 bản C++ (OpenCppCoverage) | tương đương cho C++ |
| NF6 | pytest offscreen, không model | NF9 bản C++ | tương đương cho C++ |
| NF7 | PyInstaller + spec lọc DLL | NF10 bản C++ (CPack, ADR-0007) | đóng gói C++ chuẩn hơn, hết rủi ro DLL PATH |

## 3. NFR mới không có ở baseline

| ID | Nội dung | Lý do xuất hiện ở kiến trúc C++ |
|----|----------|--------------------------------|
| NF3 | Thời gian build | C++ có bước compile mà Python không có |
| NF12 | Cache v2 tương thích | chỉ đúng khi giữ schema (ADR-0010) |
| NF14 | CI máy sạch tái lập được | bundle/runtime phụ thuộc native để không như Python |
| NF16 | Logging có (thay `try/except: pass`) | chặn kiểu hỏng "nuốt lỗi" gặp ở baseline |
| NF18 | UI không block | luồng là điểm mới của kiến trúc (ADR-0008) |
| NF19 | Quy trình 6-role | yêu cầu của người dùng |

> Sửa NFR: chỉ R6 SW-Architect sửa file này; thay đổi NFR phải đi kèm ADR mới
> (đừng ghi trực tiếp thay đổi lớn mà không có ADR để giải thích lý do).
> Số mục tiêu trong bảng là **đo được trên máy dev của dự án (i7-6600U,
> 2 nhân/4 luồng, 8 GB RAM)** — chỉ so sánh trong cùng điều kiện.
