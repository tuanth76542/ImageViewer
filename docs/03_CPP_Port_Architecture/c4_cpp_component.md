# C4 Level 3 — Component (bản C++)

## Tổng quan

Mô hình component trình bày các thành phần bên trong **Ứng dụng C++**.
Mỗi component bảng dưới đây trực tiếp tương ứng 1:1 với component baseline
Python (trừ `MainWindow`, được chia tách — giải quyết "God Class" được ghi nhận
ở `../02_System_SW_Architecture/c4_component.md`).

## Quy tắc kiến trúc ràng buộc (component-level)

| R1 | `gui` **không** include trực tiếp mã của `core`, `ai`, `platform` — chỉ include interface header (`include/xemanh/*.h`) |
| R2 | `core` và `ai` **không** include `QtWidgets` (`QMainWindow`, dialog…) — chỉ dùng `QtGui` (QImage), `QtCore` (signal/slot, QThreadPool) nếu cần |
| R3 | `platform` chỉ dùng Win32 API thuần, không Qt |
| R4 | Mỗi component ≤ ~500 dòng (CI kiểm bằng clang-tidy, không chờ review) |
| R5 | Mọi lỗi được log bằng `xemanh::Logger` (không nuốt lỗi kiểu `try/except: pass` của baseline), UI nhận qua `LogSink` |

## Các component

| Component | C++ | Tương ứng Python | Trách nhiệm chính |
|-----------|-----|------------------|-------------------|
| **AppEntry** | `app/main.cpp` | `viewer_qt.py` | Điểm chạy mỏng: khởi tạo QApplication, dựng các factory class, mở MainWindow, mở thư mục nếu có argv. |
| **MainWindow** | `src/xemanh/gui/mainwindow.{h,cpp}` | `xemanh/mainwindow.py` *(chia tách)* | Cửa sổ chính: dựng layout + Overlay + phím tắt; UI shell mỏng, mọi hành vi delegate xuống controller (`GalleryController`, `ZoomController`, `FilterController`). Mục tiêu: **≤ 250 dòng**, phần còn lại rời sang controller riêng. |
| **GalleryController** | `src/xemanh/gui/gallery_controller.{h,cpp}` | *(phần của mainwindow.py: index, open dir, drag-drop list)* | Trạng thái selector: index đang xem, vòng lặp ←/→, thêm/xóa khi filter đổi danh sách; duyệt qua `GalleryCatalog`. |
| **ZoomController** | `src/xemanh/gui/zoom_controller.{h,cpp}` | *(phần của mainwindow.py: zoom/xoay)* | Zoom tại con trỏ (pinch = Ctrl+wheel), fit/100%, pan, rotate 90° (state image + cache gate của bộ decode). |
| **FilterController** | `src/xemanh/gui/filter_controller.{h,cpp}` | *(phần của mainwindow.py: toggle filter, progress dialog)* | Bật/tắt lọc nữ, giao tiếp `FilterWorker` (thread nền), chạy hộp tiến độ, xử lý tín hiệu `found/progress/done/failed`, hiện dần sau `SHOW_AFTER = 5` ảnh (giữ đúng hằng số baseline). |
| **GalleryCatalog** | `src/xemanh/core/gallery_catalog.{h,cpp}` | `xemanh/imageutils.py` | Liệt kê ảnh theo đuôi tệp hỗ trợ, giữ thứ tự đĩa; lọc danh sách theo tiêu chí; thuần logic (không Qt Widgets). |
| **ImageLoader + ImageLRUCache** | `src/xemanh/core/image_loader.{h,cpp}`, `image_lru_cache.{h,cpp}` | `xemanh/imageutils.py` *(PIL→QImage)* + *(mới — giải quyết "thiếu cache ảnh" của baseline)* | Decode file → QImage (Qt image plugin), bọc LRU theo bytes (mặc định 256MB, cấu hình được), preload ảnh lân cận khi idle (mức ưu tiên thấp). |
| **SessionStore** | `src/xemanh/core/session_store.{h,cpp}` | *(mới — giải quyết "không lưu trạng thái phiên" của baseline)* | Ghi/đọc trạng thái phiên: thư mục cuối, zoom mode, tốc độ slideshow, trạng thái filter, trạng thái Aero (JSON trong `%APPDATA%`). |
| **Logger** | `src/xemanh/core/logger.{h,cpp}` | *(mới — thay cho `try/except: pass` của baseline)* | Log mức INFO/WARN/ERROR có context, ghi ra `%LOCALAPPDATA%\PhanMemXemAnh\logs\`, quay vòng 5MB × 3 tệp. |
| **IGenderInference** | `include/xemanh/gender_inference.h` | *(phần private của loc_nu.py)* | Interface thuần: `bool isFemale(const std::string& path, const FaceBox& face[])`. Cho phép mock trong unit test (ADR-0006). |
| **GenderFilterEngine** | `src/loc_nu/gender_filter_engine.{h,cpp}` | `loc_nu.py` | Bọc suy luận: YuNet detect mặt (OpenCV `cv::FaceDetectorYN`) → 2 vòng phân loại (ResNet nhanh rồi ViT phân xử ca khó), giữ **đúng pre/post-processing của baseline** (resize, fmt, thresh). |
| **ResultCache + DeltaScanner** | `src/loc_nu/result_cache.{h,cpp}`, `delta_scanner.{h,cpp}` | `loc_nu.py` *(cache JSON theo đường dẫn + kích thước + mtime)* | Cache theo (path + size + mtime); scan delta chỉ suy luận ảnh mới/thay đổi; **giữ schema JSON v2** để cache cũ của bản Python còn dùng được (ADR-0010). |
| **FilterWorker** | `src/xemanh/gui/filter_worker.{h,cpp}` | `xemanh/filterthread.py` | `QThread`/`QThreadPool` chạy `GenderFilterEngine`, phát tín hiệu Qt `progressed/found/done/failed`; logic giờ không còn UI phụ thuộc (ADR-0008). |
| **NetworkModelFetcher** | `src/loc_nu/model_fetcher.{h,cpp}` | `loc_nu.py` *(download model)* | Tải model lần đầu (HTTPS), kiểm tra file size, lưu `models/` hoặc `%LOCALAPPDATA%`. |
| **ImageView** | `src/xemanh/gui/image_view.{h,cpp}` | `xemanh/imageview.py` | Khung QGraphicsView: pan, pinch gesture, wheel, drag-drop, resize; **nhập gesture đúng module** (bài học từ baseline: nhập sai bị nuốt → pinch không chạy). |
| **SlideshowDialog** | `src/xemanh/gui/slideshow_dialog.{h,cpp}` | `xemanh/slideshow.py` | Cửa sổ toàn màn hình riêng, tốc độ 3/5/10/20 giây, thanh điều khiển nổi tự ẩn, tạm dừng nháy chuột. |
| **HelpDialog** | `src/xemanh/gui/help_dialog.{h,cpp}` | `xemanh/helpdialog.py` | Bảng trợ giúp phím tắt. |
| **Overlay & Theme** | `src/xemanh/gui/overlay.{h,cpp}`, `src/xemanh/gui/theme.{h,cpp}` + `resources/dark.qss` | `xemanh/theme.py` | QSS dark theme, hiệu ứng kính mờ `_glass`, welcome screen, toast, info pill, topbar. |
| **WinFx (platform)** | `src/xemanh/platform/winfx.{h,cpp}` | `xemanh/winfx.py` | AppID taskbar, kính mờ Aero (DWM `ACCENT_POLICY`), icon app; không Qt. |
| **ResourceMonitor** | `src/xemanh/core/resource_monitor.{h,cpp}` | `xemanh/perf.py` | Đo RAM/CPU/thread/handle của tiến trình (Windows API), dùng cho test `resources` và `tools/measure_resources.py`. |

## Sơ đồ luồng chính

```
AppEntry ──► MainWindow (gui, mỏng)
              ├─► GalleryController ──► GalleryCatalog (core, không Qt)
              ├─► ZoomController ──► ImageLoader + ImageLRUCache (core)
              ├─► SlideshowDialog / HelpDialog / Overlay (gui)
              └─► FilterController ──► FilterWorker (gui, QThread)
                                          │ async callback
                                          ▼
                                     GenderFilterEngine (ai) ──► ResultCache JSON v2
                                          │                         ├─► FaceDetector (YuNet/OpenCV)
                                          │ decode sẵn khi nhàn rỗi ├─► GenderClassifier (onnxruntime)
                                          ▼                         └─► ModelFetcher → Network
MainWindow ──► WinFx (platform: Aero, AppID) ──► Windows OS
```

## Khác baseline Python (điểm thay đổi kiến trúc)

| Vấn đề baseline | Giải pháp trong bản C++ |
|-----------------|--------------------------|
| God Class `mainwindow.py` ~573 dòng | Chia tách → MainWindow + GalleryController + ZoomController + FilterController, mỗi cái một trách nhiệm |
| Trộn domain vào UI (toggle filter import `loc_nu` trực tiếp) | `FilterController` chỉ biết interface `IGenderInference`, engine nằm sau interface |
| Thiếu cache ảnh decode | Bổ sung `ImageLRUCache` (đây là lỗi thật gặp ở baseline: chuyển ảnh là `Image.open` lại từ đĩa) |
| Xử lý lỗi yếu (`try/except: pass`) | `xemanh::Logger` + quy tắc R5 kiểm trong CI (clang-tidy bugprone-unused-return…) |
| Không lưu trạng thái phiên | `SessionStore` JSON |
| Import gesture sai module bị nuốt (lỗi thật đã gặp) | Không bọc include trong `try`; quy tắc R2 kiểm sẵn bằng lint |
| `filterthread.run()` chạy trên thread native làm coverage không đo được | GoogleTest gọi trực tiếp logic filter (không qua QThread) cho coverage; QThread chỉ wrap run |
