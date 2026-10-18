# C4 Level 2 — Container (bản C++)

## Tổng quan

Mô hình container trình bày các thành phần kỹ thuật cao cấp của hệ Phần Mềm Xem
Ảnh **bản C++**. So với baseline Python (`../02_System_SW_Architecture/c4_container.md`):

1. Runtime Python + PySide6 virtualenv **bị thay** bằng một thư viện thực thi
   C++ duy nhất (Qt 6 / onnxruntime / OpenCV **static-link hoặc bundled DLL**
   theo ADR-0007).
2. Bộ lọc ảnh nữ từ "tệp lẻ `loc_nu.py`" được nâng lên **thư viện riêng `ai`
   chạy trong tiến trình app** — kết nối qua interface, không còn "import tùy
   tình huống" như trong `mainwindow.py` cũ.
3. Thêm container **Cache ảnh decode trong RAM** (LRU) — là một điểm yếu được
   ghi nhận ở baseline (xem `c4_component.md`: "Thiếu cache ảnh") và được giải
   quyết hẳn bằng kiến trúc mới.

## Các container

| Container | Công nghệ | Mô tả |
|-----------|-----------|-------|
| **Ứng dụng C++ (gui)** | C++20, Qt 6 Widgets (≥ 6.8), ADR-0001 | Single-process desktop app, điểm vào `app/main.cpp`. Chứa MainWindow, ImageView, Slideshow, HelpDialog, Overlay (topbar/toast/info pill), theme QSS tối. |
| **Thư viện lõi (core)** | C++20, không phụ thuộc Qt (chỉ `std::`) | GalleryCatalog (liệt kê, lọc, index ảnh), ImageLoader (decode và đưa QImage/QPixmap), ImageLRUCache, SessionStore (lưu trạng thái phiên), FilterCoordinatorState. |
| **Thư viện AI `loc_nu`** | C++20, onnxruntime C++ API, OpenCV 4.9 (`cv::FaceDetectorYN`) | Port trực diện của `loc_nu.py`: phát hiện mặt (YuNet), phân loại giới tính 2 vòng (ResNet + ViT), kết quả JSON cache theo (đường dẫn + kích thước + mtime), delta scan, push kết quả `found` thực-thời qua callback (ADR-0004). |
| **Thư viện platform** | C++20, Win32 API | `src/xemanh/platform/winfx.cpp`: AppID taskbar, kính mờ Aero (DWM), icon app. Tách riêng để unit test được và thay đổi win32 không đụng core/gui. |
| **Bộ tải model & cache** | thư viện trung tâm `ai/model_store` | Download lần đầu từ GitHub/HuggingFace vào `models/` (app chạy từ sources) hoặc `%LOCALAPPDATA%\PhanMemXemAnh\models` (.exe), hoặc `./models` cạnh .exe. |
| **Cache kết quả lọc** | File JSON (`loc_nu_cache_v2.json`) | **Giữ nguyên schema v2 của baseline Python** — kết quả cache có thể tái sử dụng khi người dùng nâng cấp từ bản Python lên bản C++ mà không phải quét lại từ đầu (ADR-0010). |
| **Models (ONNX)** | 3 tệp ONNX, ~430MB, trong `models/` | **Không đổi** — là artifact của hành vi lọc nữ được đảm bảo bằng test so sánh với baseline Python (ADR-0006). |
| **Thư mục ảnh người dùng** | File system (JPEG, PNG, …) | Nguồn ảnh đầu vào. Không do hệ thống quản lý, chỉ đọc. |
| **Bộ test tự vận hành** | CMake + GoogleTest + Qt Test | Dùng CTest, chạy offscreen (`QT_QPA_PLATFORM=offscreen`), không cần mạng, không cần model thật (bọc interface + mock) — giữ đúng chuẩn của baseline (`tests/` + conftest ở bản Python). |

## Mối liên hệ giữa container

```
Ứng dụng C++ (gui) ◄──── quyền điều khiển người dùng ────► Windows OS
        │  (interface: IGenderFilter, IWindowEffects)
        ▼
Thư viện lõi (core) ──── decode + cache/QImage ────► Thư mục ảnh người dùng
        │  (interface: IGenderInference)             (chỉ đọc)
        ▼
Thư viện AI loc_nu ────── đọc model ONNX ──────► Models (ONNX, ~430MB)
        │                                            ▲
        │ (đọc/ghi cache v2 JSON)                    │ tải lần đầu
        ▼                                            │ Internet
Cache lọc (loc_nu_cache_v2.json) ───────────────────┘
```

## Ranh giới (Boundary)

- **Trong ranh giới**: gui, core, ai, platform (các mục trong `src/`), cache JSON,
  models, tests, công cụ đo (`tools/`). Tất cả do người dùng điều phối, trong
  phạm vi repo mới `PhanMemXemAnh-Cpp` (ADR-0003).
- **Ngoài ranh giới**: thư mục ảnh người dùng, Internet (tải model lần đầu),
  Windows OS.

## Lý do tách core / ai / platform khỏi gui

Cơ sở: port C++ cho phép **biên dịch chạy được từ dòng lệnh mà không cần mở
 cửa sổ** (chạy offscreen trên CI) — nhưng điều mới thật sự là **core/ai
 không phụ thuộc Qt widget**:

- `core` không include `QWidget`/`QMainWindow` — chỉ dùng thư viện chuẩn C++,
  decode ảnh bằng `QtGui` độc lập (QImage), không dùng `QtWidgets`. Điều này
  giúp GoogleTest chạy không màn hình mà không cần chế độ offscreen.
- `ai` không include bất kỳ Qt nào; interface thuần `IGenderInference` +
  callback, GoogleTest mô phỏng ONNX bằng dữ liệu mô phỏng có ghi sẵn.
- Chỉ `gui` phụ thuộc `QtWidgets` (cửa sổ, phím tắt, overlay).

Vì sao: baseline Python có lỗi thật "import gesture sai module bị nuốt lặng lẽ
trong try/except" và God class `mainwindow.py` (~573 dòng). Port C++ tách tầng
chặn cả hai kiểu hỏng cấu trúc đó ngay từ đầu.

Giới hạn: mọi container **không đọc trực tiếp file system của model** trừ
container `ai/model_store`, tránh lặp lại cách baseline Python từng cần.
