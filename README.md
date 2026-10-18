# Phần Mềm Xem Ảnh (Windows) — giao diện Qt

Trình xem ảnh theme tối, viết bằng Python + PySide6 (Qt).
Môi trường được quản lý bằng [uv](https://docs.astral.sh/uv/) (nhanh hơn pip, tự khoá phiên bản).

## Cài đặt

Cài uv một lần (nếu chưa có):

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Rồi trong thư mục dự án:

```bat
uv sync
```

`uv sync` tự tạo `.venv` và cài đúng phiên bản ghi trong `uv.lock` — không cần `pip`/`venv` thủ công.

## Chạy

```bat
chay.bat
```

Hoặc:

```bat
uv run python viewer_qt.py "D:\ThuMucAnh"
```

(Mã nguồn chính nằm trong package `xemanh/`; `viewer_qt.py` chỉ là điểm chạy.)

## Tính năng

Giao diện tối, điều khiển dạng **thanh nổi** ngay trên ảnh (không chiếm chỗ hiển thị).

1. **Chuyển ảnh**: phím ←/→, lăn chuột, nút ◀/▶; **kéo-thả** thư mục hoặc tệp ảnh vào cửa sổ.
2. **Zoom**: pinch touchpad (= Ctrl + lăn chuột, zoom tại con trỏ), gesture
   cảm ứng, nút ➖/➕, phím `+`/`-`, `0` = vừa màn hình, `1` = 100%.
   Kéo chuột để pan khi zoom to.
3. **Slideshow** (nút 🎬, phím F5): cửa sổ toàn màn hình riêng (ẩn cửa sổ
   chính), tự chuyển ảnh; thanh điều khiển nổi tự ẩn — chọn tốc độ theo mốc
   3/5/10/20 giây mỗi ảnh, tạm dừng (bấm vào ảnh hoặc Space), ←/→ chuyển tay,
   Esc thoát.
4. **Lọc chỉ ảnh nữ** (nút 👩, phím F): xem chi tiết ở dưới.
5. **Màn hình chào** khi chưa mở ảnh; **thẻ thông tin** nổi (tên ảnh, vị trí,
   kích thước) và **thông báo tự ẩn**.
6. **Bảng trợ giúp phím tắt**: bấm ❔ hoặc phím `H` / `F1`.
7. **Toàn màn hình** (F11 / nháy đúp): thanh điều khiển tự ẩn khi rảnh, hiện lại khi di chuột.
8. **Thanh tiêu đề kính mờ (Aero)** trên Windows: nền mờ trong suốt kiểu Aero của
   Windows 7, chữ tiêu đề màu sáng cho hợp giao diện tối. Bật/tắt bằng `Ctrl+A`.
   Muốn tắt hẳn ngay từ đầu thì đặt `AERO_BLUR = False` trong `xemanh/winfx.py`
   (khi đó thanh tiêu đề trở về mặc định của Windows).

## Lọc chỉ ảnh nữ

- Quét toàn bộ thư mục, giữ ảnh có **ít nhất 1 khuôn mặt đoán là Female**.
- Tìm mặt bằng YuNet, đoán giới tính 2 vòng (ResNet nhanh + ViT phân xử ca khó).
- Ảnh không có mặt / chỉ có nam → ẩn tạm, bấm nút lần nữa để tắt lọc.
- **Hiện dần kết quả**: vừa tìm được **5 ảnh nữ đầu tiên** là danh sách đã cập nhật
  và xem được ngay, **không phải chờ quét hết** thư mục — quét vẫn chạy nền, cửa sổ
  vẫn chuyển ảnh/zoom được. Trong lúc quét, danh sách chỉ chứa ảnh nữ đã tìm được
  và ảnh đang xem được giữ nguyên (khớp theo đường dẫn); thư mục có **dưới 5 ảnh nữ**
  thì hiện khi quét xong như trước. Đóng hộp tiến độ **không** dừng việc quét.
  (Hằng số `SHOW_AFTER` trong `xemanh/mainwindow.py`.)
- **Quét delta**: kết quả từng ảnh được cache theo (đường dẫn + kích thước + mtime),
  nên bấm F lần hai trên thư mục không đổi thì **không suy luận lại** (kết quả hiện
  gần như tức thì); thêm ảnh mới vào thư mục thì **chỉ ảnh mới phải suy luận**.
- Lần đầu quét ~350 ảnh mất ~1,5 phút (máy 2 nhân/4 luồng, ~950 ms/ảnh), lần sau
  **tức thì** (cache).
- Đo lại trên máy yếu: `uv run python tools\bench_loc_nu.py "<thư mục ảnh>"` (thêm
  `--no-cache` để đo lần quét nguội mà **không** đụng cache thật).
- Lần đầu cần Internet tải model (~430MB vào `models/`), sau đó offline.
  Bản .exe lưu vào `%LOCALAPPDATA%\PhanMemXemAnh\models` (xem mục Đóng gói .exe).

## Phím tắt

| Phím | Chức năng |
|---|---|
| ← / → | Ảnh trước / tiếp |
| Ctrl + lăn / pinch | Zoom tại con trỏ |
| + / - | Zoom |
| 0 / 1 | Vừa màn hình / 100% |
| R | Xoay 90° |
| F5 | Slideshow |
| F | Bật/tắt lọc chỉ ảnh nữ |
| F11  ·  nháy đúp | Toàn màn hình |
| H / F1 | Bảng trợ giúp phím tắt |
| Kéo-thả tệp | Mở thư mục/ảnh vừa thả vào cửa sổ |
| Esc | Thoát fullscreen / đóng trợ giúp |
| Ctrl+O | Mở thư mục |
| Ctrl+A | Bật/tắt thanh tiêu đề kính mờ (Aero) |

Định dạng: jpg, jpeg, png, bmp, gif, webp, tiff, tif, ico.

## Kiểm thử

```bat
uv run pytest                     :: tất cả
uv run pytest -m unit             :: chỉ test đơn vị (nhanh nhất)
uv run pytest -m functional       :: test chức năng giao diện (offscreen)
uv run pytest -m resources        :: test đo tài nguyên (chậm hơn, ~5 giây)
uv run pytest tests/unit/test_filter.py     :: chạy một tệp
```

Sau mỗi lần chạy, pytest tự ghi **báo cáo HTML** vào `reports/test-report.html`
(một tệp duy nhất, mở bằng trình duyệt là xem được: tên từng test, thời gian,
thông báo lỗi, số liệu RAM/CPU của nhóm `resources`, và **bảng độ phủ C0/C1** ở
cuối). Báo cáo phản ánh **lần chạy gần nhất**, thư mục `reports/` không vào git.

**224 test chạy trong ~16 giây**, chia 3 nhóm (dùng `-m <nhóm>` để chọn):

| Nhóm | Nội dung |
|---|---|
| `unit` | logic lọc nữ (cache/delta, cascade 2 vòng, giữ thứ tự, tín hiệu `found`), tải/suy luận model (giả lập), đọc ảnh, chuyển PIL→QImage, các chỉ số đo tài nguyên, công cụ quản lý agent |
| `functional` | giao diện Qt: mở thư mục, điều hướng, zoom/xoay, lớp phủ, trợ giúp, phím tắt, slideshow, nút lọc nữ (hiện dần sau 5 ảnh, đóng tiến độ vẫn quét tiếp), icon |
| `resources` | RAM/CPU: mở 24 ảnh lớn, 60 lần chuyển ảnh, zoom/xoay, slideshow — không rò rỉ RAM, CPU lúc rảnh thấp |

Model nhận diện được **giả lập** nên test không cần tải 430MB model hay ảnh thật;
phần giao diện chạy ở chế độ `offscreen` nên không cần màn hình (chạy được trên CI).

Cấu trúc test:

```
tests/
  conftest.py                        ép offscreen + fixture (ảnh mẫu, cửa sổ, bơm sự kiện)
  unit/test_filter.py                logic loc_nu (cache/delta, cascade, giữ thứ tự, đọc ảnh)
  unit/test_loc_nu_models.py         tải model + _yunet/_ensure/_p_female*/_faces (giả lập cv2/onnxruntime)
  unit/test_filterthread.py          luồng nền lọc + tín hiệu `found` (gọi thẳng run() để đo được độ phủ)
  unit/test_loc_nu_paths.py          chỗ chứa models/cache (mã nguồn vs .exe)
  unit/test_viewer_main.py           viewer_qt.main() bằng đồ giả QApplication/MainWindow
  unit/test_imageutils.py            đọc thư mục, chuyển ảnh
  unit/test_perf.py                  bộ đo tài nguyên (kèm đường dự phòng thiếu psutil)
  unit/test_winfx.py                 icon app, hiệu ứng Aero, cấu trúc ACCENT_POLICY
  unit/test_agents_tool.py           công cụ quản lý agent (frontmatter, sync, check)
  functional/test_viewer.py          cửa sổ chính: mở/navigate/zoom/xoay/lớp phủ/trợ giúp
  functional/test_mainwindow_cov.py  phím tắt còn lại, nhánh lỗi/hủy của lọc nữ, Aero, closeEvent
  functional/test_imageview_events.py sự kiện chuột/kéo-thả/pinch của khung xem
  functional/test_slideshow.py       trình chiếu
  functional/test_filter_flow.py     luồng lọc nữ (thread + nút bấm + hiện dần + delta)
  functional/test_resources.py       ngưỡng RAM/CPU
```

### Độ phủ mã nguồn (C0 / C1)

Đã bật sẵn bằng `pytest-cov`: mỗi lần chạy test đều đo độ phủ của **chính mã app**
(`xemanh/`, `loc_nu.py`, `viewer_qt.py`; không tính `tests/`, `tools/`, thư viện ngoài).

| Loại | Ý nghĩa | Hiện tại |
|---|---|---|
| **C0** — dòng lệnh | bao nhiêu dòng lệnh đã chạy | 1236 / 1237 dòng ≈ **99.9%** |
| **C1** — nhánh | bao nhiêu nhánh `if/else`, `while`, `and/or` đã rẽ | 281 / 282 nhánh ≈ **99.6%** |
| Gộp | cột `Cover` trong bảng | **99.9%** |

Xem ở đâu:

- bảng in ra ngay khi chạy test (cột `Stmts`, `Miss`, `Branch`, `BrPart`, `Cover`,
  và danh sách số dòng còn thiếu);
- cuối `reports/test-report.html` — bảng độ phủ nằm chung với kết quả test;
- `reports/cov-html/index.html` — xem từng dòng: xanh = đã chạy, đỏ = chưa chạy,
  vàng = nhánh chỉ chạy một nửa.

Sàn độ phủ đã **chốt vào `pyproject.toml`** (`--cov-fail-under=80` trong
`addopts`), nên lần sau tụt sâu là `uv run pytest` đỏ ngay; muốn siết tạm thời thì
ghi đè trên dòng lệnh:

```bat
uv run pytest --cov-fail-under=95
```

Chỗ còn mỏng (cột `Missing`) và lý do:

| Tệp | Chưa chạy | Vì sao |
|---|---|---|
| `loc_nu.py` (99%) | dòng **273** (`continue` khi `face.size == 0`) | là **kiểm tra phòng vệ không thể chạy tới**: box mặt đã bị kẹp trong ảnh (`x1 ≥ 0`, `x2 ≤ w`, `y1 ≥ 0`, `y2 ≤ h`) và đã qua ngưỡng `MIN_FACE_SIZE`, nên lát cắt luôn khác rỗng. Để nguyên (không `# pragma`) cho an toàn nếu sau này đổi logic crop |
| tất cả các tệp khác | — | **100% C0 và C1** |

**Không thêm `# pragma: no cover` nào** trong lần này: mọi dòng khác đều chạy
tới được và đã được test thật (chủ yếu bằng giả lập/monkeypatch), kể cả các nhánh
`except` an toàn của `winfx.py`/`perf.py` và `main()` của `viewer_qt.py`.

Một chỗ thấp bất thường đáng nhớ: `filterthread.py` từng báo **36%** dù đã có 4 test,
vì `run()` chạy trên luồng do Qt tạo (luồng native) nên coverage **không theo dõi
được**; `tests/unit/test_filterthread.py` gọi thẳng `run()` trên luồng chính nên
giờ đo được 100%.

Nhờ đi soi mấy chỗ thấp đó mà phát hiện một **lỗi thật**: `imageview.event()` nhập
`QPinchGesture` từ `QtGui` (sai — lớp gesture nằm ở `QtWidgets`) và để trong
`try/except` nên lỗi import bị nuốt ⇒ **zoom bằng pinch touchpad không bao giờ
chạy**. Đã sửa (nhập ở đầu tệp để lỗi không bị nuốt) và thêm test
`test_pinch_nhap_dung_module` để không tái phát.

## Agent OpenCode của dự án

Dự án có sẵn vài agent để làm việc theo quy trình (ví dụ: làm rõ yêu cầu trước khi
code). Bản gốc nằm ở `agents/`, mỗi agent một tệp `agent-<tên>.md`;
`.opencode/agents/<tên>.md` là **bản sinh tự động** cho OpenCode quét (tên tệp =
tên gọi agent) — đừng sửa tay, sửa bản gốc rồi chạy `sync`.

| Lệnh | Việc |
|---|---|
| `uv run python tools\agents.py list` | xem danh sách (chế độ, quyền chặn, bản sinh đã khớp chưa) |
| `uv run python tools\agents.py new <tên>` | tạo agent mới từ mẫu rồi đồng bộ luôn |
| `uv run python tools\agents.py sync` | sinh lại `.opencode/agents/` và bảng `agents/README.md` |
| `uv run python tools\agents.py check` | bắt lỗi: frontmatter sai, thiếu `description`, trường V1 của bản cũ, bản sinh bị sửa tay/lệch, tệp lạ |
| `uv run python tools\agents.py rename <cũ> <mới>` · `rm <tên>` | đổi tên · xoá (cả bản sinh) |

Thêm agent mới: `new <tên>` → điền `description` + phần thân → `sync` → `check`.
Danh sách agent hiện có: `agents/README.md`. Công cụ này có 18 test ở
`tests/unit/test_agents_tool.py`.

## Đo tài nguyên (RAM, CPU)

Công cụ mở app, đo theo thời gian rồi in báo cáo (cần `uv sync` để có `psutil`):

```bat
uv run python tools/measure_resources.py "D:\ThuMucAnh"
uv run python tools/measure_resources.py "D:\ThuMucAnh" -s 30 -i 0.5
uv run python tools/measure_resources.py --pid 1234        :: đo app đang chạy
uv run python tools/measure_resources.py "D:\Anh" --csv ket-qua.csv
```

Trong lúc đo, cứ thao tác bình thường (chuyển ảnh, zoom, trình chiếu) để xem RAM/CPU
thay đổi. Số liệu **cộng cả tiến trình con** (vì `python.exe` trong `.venv` chỉ là
vỏ khởi chạy), in từng mẫu và tổng kết ở cuối: thấp nhất / trung bình / cao nhất.

Số đo tham khảo trên máy dev (chỉ PySide6, chưa dùng lọc nữ, 4 ảnh mở sẵn):

| Trạng thái | RAM | CPU |
|---|---|---|
| Vừa lên giao diện (rảnh) | ~87 MB | ~0% |
| Mở 24 ảnh 1600×1200 | ~+18 MB | |
| 60 lần chuyển ảnh | ~+0,2 MB (không rò rỉ) | |
| Dùng lọc nữ (nạp OpenCV + onnxruntime) | ~+200 MB | |
| Đang quét nguội 345 ảnh thật (`tools\bench_loc_nu.py`, 4 luồng) | đỉnh ~0,96 GB | CPU ~4 nhân |

## Đóng gói .exe

```bat
build_exe.bat
```

Lấy `dist\PhanMemXemAnh.exe` (~115MB, chạy độc lập, không cần cài Python).

Kiểm tra lại .exe sau khi build (mở thử, đo RAM, soi bundle, tự tạo ảnh mẫu nếu
không truyền thư mục ảnh; trả mã thoát 1 nếu có vấn đề nên dùng được trong CI):

```bat
uv run python tools/check_exe.py
uv run python tools/check_exe.py "D:\ThuMucAnh"
```

Việc đóng gói dùng `PhanMemXemAnh.spec` (không gọi `pyinstaller` trực tiếp) vì một
lỗi thật đã gặp: PyInstaller tìm DLL phụ thuộc **theo PATH**, nên khi máy có cài
Java (Adoptium JRE) nó gom bản runtime C++ **cũ của JRE** (`msvcp140.dll` 14.27,
`vcruntime140.dll`, cả `ucrtbase.dll`) vào app ⇒ .exe crash `0xC0000005` trong
`MSVCP140.dll` ngay khi mở. Spec lọc bỏ các DLL đó, chỉ giữ bản mới nhất đi kèm
PySide6 và không đóng gói `ucrtbase.dll` / `api-ms-win-*` của Windows.

Lưu ý khi chạy bản .exe:

- Model lọc nữ được tải vào `%LOCALAPPDATA%\PhanMemXemAnh\models` (thư mục giải nén
  của onefile bị xoá sau mỗi lần thoát, để cạnh module thì lần nào mở app cũng phải
  tải lại ~430MB). Muốn bản "portable" thì copy thêm thư mục `models\` ra cạnh
  file .exe — app sẽ dùng luôn thư mục đó.
- Nếu .exe không mở được, chạy lại build với `console=True` trong spec (hoặc tạm
  bỏ `--windowed`) để thấy thông báo lỗi.

## Phụ thuộc & cấu trúc

- Khai báo phụ thuộc trong `pyproject.toml`; `uv.lock` khoá phiên bản chính xác.
  Nhóm `dev` chỉ dùng khi phát triển/test: `pytest`, `pytest-html` (báo cáo HTML),
  `pytest-cov` (độ phủ C0/C1), `psutil` (đo RAM/CPU trong test và
  `tools/measure_resources.py`); app chạy thật không cần các gói này.
- `models/` (~430MB) và cache được tải/ghi khi chạy, đã loại khỏi git.
- `viewer_qt.py` là **điểm chạy** (mỏng); mã nguồn chính nằm trong package `xemanh/`:

  | Tệp | Việc |
  |---|---|
  | `xemanh/theme.py` | bảng màu/QSS dùng chung cho giao diện tối |
  | `xemanh/imageutils.py` | liệt kê ảnh trong thư mục, chuyển PIL → QImage |
  | `xemanh/winfx.py` | tiện ích Windows: icon app, app-id taskbar, kính mờ Aero |
  | `xemanh/imageview.py` | khung xem ảnh (zoom, pan, kéo-thả) |
  | `xemanh/slideshow.py` | cửa sổ trình chiếu toàn màn hình |
  | `xemanh/helpdialog.py` | bảng trợ giúp phím tắt |
  | `xemanh/filterthread.py` | luồng nền chạy bộ lọc ảnh nữ |
  | `xemanh/mainwindow.py` | cửa sổ chính, nối mọi thứ lại |
  | `xemanh/perf.py` | đo tài nguyên (RAM, CPU, thread, handle) |

- `loc_nu.py` (nhận diện nữ) · `tests/` (test tự động) · `tools/` (tạo icon, đo tài
  nguyên, đo tốc độ lọc nữ `bench_loc_nu.py`, kiểm tra .exe, quản lý agent).
- `agents/` là **bản gốc** các agent OpenCode (một tệp `agent-<tên>.md`);
  `.opencode/agents/` là bản sinh tự động cho OpenCode quét; `tasks/` chứa task đã
  chốt với người dùng trước khi code; `AGENTS.md` là hướng dẫn cho agent. Quản lý
  bằng `uv run python tools\agents.py` (xem mục *Agent OpenCode của dự án*).
- `assets/app.ico` là icon của app (thanh tiêu đề + taskbar). Muốn đổi icon:
  sửa `tools/make_icon.py` rồi chạy `uv run python tools/make_icon.py`,
  hoặc thay thẳng `assets/app.ico` bằng tệp .ico của bạn (nhớ có cỡ 16×16).
