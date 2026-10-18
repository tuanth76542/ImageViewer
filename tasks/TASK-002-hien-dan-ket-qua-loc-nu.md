# TASK-002 — Hiện dần kết quả lọc nữ + quét delta (cải thiện cảm nhận tốc độ)

- **Ngày tạo**: 2026-10-18
- **Loại**: cải tiến (hành vi/giao diện)
- **Trạng thái**: xong
- **Người yêu cầu**: chủ dự án

## 1. Yêu cầu gốc
> "hay giup toi cai thien performance cua thuat toan loc anh nu"

Khi hỏi lại, người dùng chốt rõ mong muốn thực tế là **cảm nhận tốc độ khi dùng**:
> "lan bam filter dau tien thi toi da 1 phut, cac lan sau chi quet theo kieu delta,
> ghi filter dc 5 tam hinh thi bat dau hien thi, task detect chay back ground"
> và chọn: *"Làm UI/hành vi trước, tốc độ sau"*.

## 2. Mục tiêu (đo được)
- Bấm nút 👩/phím `F`: **ngay khi đã lọc được 5 ảnh nữ đầu tiên** thì danh sách hiển
  thị đã cập nhật và xem được, **không chờ quét hết** thư mục.
- Quét vẫn chạy nền; cửa sổ không đứng (vẫn chuyển ảnh/zoom được trong lúc quét).
- Bấm `F` lần thứ hai trên **cùng thư mục không đổi**: không suy luận lại ảnh đã có
  cache; kết quả hiện **gần như tức thì** (đo được: số lần suy luận = 0 cho ảnh cũ).
- Thêm ảnh mới vào thư mục rồi bấm `F`: **chỉ suy luận ảnh mới**, ghép với kết quả cũ.
- Kết quả cuối cùng **y hệt hiện tại**: cùng tập ảnh nữ, cùng thứ tự thư mục.

## 3. Phạm vi
- **Trong phạm vi**: `xemanh/filterthread.py`, `xemanh/mainwindow.py`, thêm công cụ đo
  `tools/bench_loc_nu.py`, test tương ứng, cập nhật `README.md`.
- **Ngoài phạm vi**: tối ưu tốc độ suy luận trong `loc_nu.py` (WORKERS,
  `intra_op_num_threads`, dùng chung phiên ONNX, dừng sớm, đổi ngưỡng/model/quantize)
  — đó là **TASK-003** (tối ưu tốc độ), chưa tạo. Không dùng GPU, không đổi cache key.

## 4. Đã chốt với người dùng
| Câu hỏi | Chốt |
|---|---|
| Ưu tiên lần này? | **Giao diện/hành vi trước, tối ưu tốc độ thuật toán sau** |
| Được đánh đổi độ chính xác? | **Không** — kết quả lọc phải y hệt |
| Được đổi kiến trúc chạy song song? | **Không** trong task này; giữ nguyên phần suy luận của `loc_nu.py` |
| Số liệu lấy làm mốc? | Thời gian suy luận/ảnh + tổng thời gian bộ ảnh (~345 ảnh), kèm RAM đỉnh |
| Mục tiêu tốc độ đã nêu | ≤ 1 giây/ảnh, lần đầu ≤ 1 phút — **tiêu chí của TASK-003**, task này chỉ đo baseline |

## 5. Còn mở
- "5 tấm" hiểu là **5 ảnh nữ đầu tiên được giữ** (không phải 5 ảnh bất kỳ đã quét) —
  cần xác nhận.
  -> **Chốt: đúng, 5 ảnh NỮ đầu tiên** (hằng số `SHOW_AFTER = 5` đếm ảnh được kết
  luận là nữ).
- Trong lúc hiện dần, danh sách chỉ chứa ảnh nữ tìm được (khuyến nghị) hay vẫn kèm
  ảnh chưa quét?
  -> **Chốt: chỉ chứa ảnh nữ đã tìm được.**
- Khi danh sách được bổ sung mà người dùng đang xem 1 ảnh: **giữ nguyên ảnh đang xem**
  (khuyến nghị, khớp theo đường dẫn chứ không theo chỉ số).
  -> **Chốt: giữ nguyên theo đường dẫn** (cả lúc hiện dần lẫn lúc quét xong).
- Thư mục có < 5 ảnh nữ: hiển thị khi quét xong như hiện tại (khuyến nghị).
  -> **Chốt: chờ quét xong mới hiện như trước.**

## 6. Hướng làm & tệp dự kiến đụng tới
Thứ tự ưu tiên: ý 1 rẻ và ít rủi ro nhất, làm trước rồi mới tới ý 2.

1. **Tín hiệu kết quả từng phần** — `xemanh/filterthread.py`: thêm
   `found = Signal(int)` (hoặc `Signal(list)`) phát danh sách ảnh nữ **tích luỹ** sau
   mỗi ảnh nữ mới. Giữ nguyên `progressed`/`done`/`failed` để không vỡ test cũ.
   Lợi ích: UI có dữ liệu để hiện dần. Rủi ro thấp, không đụng `loc_nu.py`.
   **Lưu ý thứ tự**: cache phát tiến độ trước ảnh mới quét, nên phải **sắp lại theo
   thứ tự `paths` gốc** khi phát — nếu không, thứ tự hiển thị sẽ lệch kết quả cuối.
2. **Hiện dần khi đã có 5 ảnh nữ** — `xemanh/mainwindow.py`: hằng số `SHOW_AFTER = 5`
   (chú thích tiếng Việt), slot `_filter_found` cập nhật `image_list` (giữ ảnh đang
   xem theo đường dẫn), `_refresh_filter_btn()` + `show_current()` + `status_msg`
   ("đã tìm thấy N ảnh nữ, đang quét tiếp..."). Giữ `QProgressDialog`; đóng tiến độ
   không được dừng quét. Lợi ích lớn nhất về cảm nhận; rủi ro trung bình (chạm luồng
   Qt + test functional cũ).
3. **Đo baseline** — `tools/bench_loc_nu.py` **(mới)**: in thời gian/ảnh, tổng thời
   gian, RAM đỉnh; cờ `--no-cache` để đo lần **quét nguội** mà **không xoá cache thật**
   của người dùng (dùng đường dẫn cache tạm). Cần cho cả TASK-003.
4. **Tài liệu** — `README.md`: mô tả hành vi hiện dần + delta ở mục "Lọc chỉ ảnh nữ".

## 7. Tiêu chí nghiệm thu
- [x] Test chứng minh: khi mới có 5 ảnh nữ, `win.image_list` đã có ≥ 5 ảnh **dù thread chưa xong**.
      (`test_hien_dan_du_5_anh_nu_khi_luong_chua_quet_xong`: đúng 5 ảnh, `isRunning()` vẫn `True`.)
- [x] Khi quét xong, `image_list` **y hệt** hành vi cũ (cùng tập, cùng thứ tự thư mục).
      (`_dat_quy_tac_nu` trong test + kiểm tra thật đầu-cuối: thứ tự khớp `all_images`.)
- [x] Lần bấm thứ hai (thư mục không đổi): **0 lần suy luận** cho ảnh cũ, danh sách có ngay.
      (`test_bam_lan_hai_khong_suy_luan_lai_va_chi_quet_anh_moi` + `test_filter_female_bao_tien_do_cho_anh_lay_tu_cache`.)
- [x] Thêm ảnh mới rồi bấm `F`: chỉ suy luận ảnh mới, kết quả cũ giữ nguyên.
      (test nêu trên + `test_filter_female_them_anh_moi_chi_quet_anh_moi`.)
- [x] Có **baseline ghi lại trong task** (số liệu nguội + delta) trước khi sửa. (mục 8)
- [x] `uv run pytest` xanh; C0/C1 **không tụt** dưới mức hiện tại (ghi số trước khi sửa).
      (trước: 1236/1237 C0 · 281/282 C1 — sau: 1285/1286 · 299/300; tỉ lệ gộp giữ 99.87%.)
- [x] `uv run --with pyflakes python -m pyflakes <tệp đã sửa>` sạch.
      (1 cảnh báo `'cv2' imported but unused` tại `mainwindow.py` là **có sẵn trên `main`**,
      không do thay đổi này — xem mục 9b.)
- [x] `build_exe.bat` rồi `uv run python tools\check_exe.py` sạch (đụng `xemanh/`).
- [x] `README.md` mô tả đúng hành vi mới.

## 8. Kiểm thử
- **Baseline (làm TRƯỚC khi sửa)**, bộ ảnh `C:\Users\admin\Downloads\TikTok\@heocon.ttn` (~345 ảnh):
  ```bat
  uv run python tools\bench_loc_nu.py "C:\Users\admin\Downloads\TikTok\@heocon.ttn" --no-cache
  uv run python tools\bench_loc_nu.py "C:\Users\admin\Downloads\TikTok\@heocon.ttn"
  uv run python tools\measure_resources.py "C:\Users\admin\Downloads\TikTok\@heocon.ttn" -s 30
  ```
  Ghi lại: giây/ảnh, tổng giây (nguội), tổng giây (delta), RAM đỉnh — chép vào đây
  để TASK-003 so sánh sau này.

### 8a. Số đo BASELINE (trước khi sửa, máy i7-6600U 2 nhân/4 luồng)
Bộ ảnh: `C:\Users\admin\Downloads\TikTok\@heocon.ttn` — **345 ảnh**, giữ lại **243 ảnh nữ**.

| Chỉ số (quét NGUỘI, 345 ảnh) | Trước khi sửa |
|---|---|
| Số ảnh phải suy luận | 345 / 345 (cache hit 0) |
| **Tổng thời gian** | **86,49 giây** (3,99 ảnh/giây → ~250 ms/ảnh tính cả 4 luồng) |
| Giây/ảnh suy luận | TB **952 ms** · trung vị 647 ms · p95 2 302 ms · nhanh nhất 239 ms · chậm nhất 8 623 ms |
| RAM đỉnh (RSS) khi quét | **963 MB** |
| **Thời gian tới 5 ảnh nữ đầu tiên** | **5,90 giây** (lúc đó mới quét xong 8/345 ảnh) |

| Chỉ số (lần bấm thứ hai — DELTA) | Trước khi sửa |
|---|---|
| Số ảnh phải suy luận | **0** / 345 (cache hit 345) |
| Tổng thời gian | **0,05 giây** (kết quả y hệt: 243 ảnh nữ) |

- App khi mở thư mục này (chưa lọc): RAM đỉnh **92,5 MB** (TB 90,0 MB; +32,5 MB so với
  lúc rảnh), CPU TB 1,2% · cao nhất 36,4%, 17 thread, 1384 handle.
- `uv run pytest`: **209 test** xanh trong ~19,6 giây; C0 1236/1237 = 99,9%,
  C1 281/282 = 99,6%, cột gộp **99,87%**.
- Lệnh đo baseline đã chạy (dùng cache tạm để không đụng cache thật):
  ```bat
  uv run python tools\bench_loc_nu.py "<thư mục>" --cache "%TEMP%\bench_t002_cache.json" --detail --json "%TEMP%\bench_t002_nguoi.json"
  uv run python tools\bench_loc_nu.py "<thư mục>" --cache "%TEMP%\bench_t002_cache.json" --json "%TEMP%\bench_t002_delta.json"
  ```

### 8b. Số đo SAU khi sửa
Phần suy luận (`loc_nu.py`) **cố ý không đụng** nên các số về model **giữ nguyên** như
8a — đó chính là mốc để TASK-003 so sánh. Cái đổi là **lúc nào người dùng thấy kết quả**:

| Chỉ số | Trước | Sau |
|---|---|---|
| Thấy 5 ảnh nữ đầu tiên (345 ảnh thật) | sau khi quét xong hết **86,49 s** | **5,90 s** (mốc dữ liệu) — nhanh hơn ~14× |
| Đo thật đầu-cuối, 12 ảnh nữ (offscreen, model thật) | chỉ hiện khi quét xong ~7,6 s | hiện lúc **6,33 s** khi luồng còn chạy; tổng 7,57 s |
| Lần bấm thứ hai (delta) | 0,05 s (nhưng UI chỉ cập nhật lúc xong) | 12 ảnh: hiện lúc **0,06 s**, tổng 0,13 s |
| `uv run pytest` | 209 test · 19,6 s | **224 test** · 16,3 s |
| C0 / C1 | 1236/1237 · 281/282 | **1285/1286 · 299/300** (tỉ lệ gộp vẫn 99,87%) |

- Test mới/sửa: `tests/unit/test_filterthread.py` (tín hiệu `found`, đúng thứ tự gốc,
  có ca cache phát trước), `tests/functional/test_filter_flow.py` (hiện dần sau 5 ảnh,
  đóng tiến độ vẫn quét, giữ ảnh đang xem, delta không quét lại, kết quả cuối không đổi),
  `tests/functional/test_mainwindow_cov.py` (các nhánh mới của `_filter_found`/
  `_filter_done`/`_filter_failed`/`_anh_dang_xem`/`_refresh_filter_meta`),
  `tests/unit/test_loc_nu_models.py` (thêm ảnh mới → chỉ quét ảnh mới).
- Lệnh: `uv run pytest` · `uv run pytest -m unit` · `uv run pytest -m functional`.
- Kiểm tra tay: mở thư mục ~345 ảnh → bấm `F`: ảnh nữ đầu tiên phải hiện **trước khi**
  tiến độ đạt 100%; vẫn chuyển ảnh/zoom được trong lúc quét; đóng hộp tiến độ thì quét
  vẫn tiếp tục; bấm `F` lần hai thấy kết quả gần như ngay.
  -> Kiểm tra bằng script **đầu-cuối, model thật, offscreen** (12 ảnh thật copy ra thư mục
  tạm) vì agent không thao tác được giao diện thật: kết quả ở bảng 8b — mốc hiện dần đến
  khi luồng còn chạy, thứ tự đúng, không crash.

## 9. Việc cần làm
- [x] Thêm `tools/bench_loc_nu.py` và **ghi baseline** vào mục 8.
- [x] Thêm tín hiệu `found` trong `xemanh/filterthread.py` (sắp theo thứ tự gốc).
- [x] Thêm `SHOW_AFTER = 5` + slot `_filter_found` trong `xemanh/mainwindow.py`.
- [x] Thêm test unit cho tín hiệu `found`; thêm test functional cho hiện dần + delta.
- [x] Chạy 3 nhóm test, so độ phủ với số ghi trước khi sửa; chạy `pyflakes`.
- [x] Chạy lại app tay theo mục 8; cập nhật `README.md`.
      -> Thay bằng script đầu-cuối model thật offscreen (xem 8b) + `tools\check_exe.py`.
- [x] `build_exe.bat` + `uv run python tools\check_exe.py`.
- [x] Ghi số liệu sau khi sửa (để TASK-003 có mốc so sánh).

## 9b. Kết quả thực hiện (điền khi xong)

| Chỉ số | Trước | Sau |
|---|---|---|
| Số test | 209 (unit 118 · functional 84 · resources 7) | **224** (unit 123 · functional 94 · resources 7) |
| Thời gian chạy | ~19,6 giây | **~16,3 giây** |
| **C0** — dòng lệnh | 1236 / 1237 ≈ 99,9% | **1285 / 1286 ≈ 99,9%** |
| **C1** — nhánh | 281 / 282 ≈ 99,6% | **299 / 300 ≈ 99,7%** |
| Cột `Cover` gộp | 99,87% | **99,87%** (không tụt) |
| `xemanh/mainwindow.py` | 471 dòng / 130 nhánh — 100% | **509 / 144 — 100%** |
| `xemanh/filterthread.py` | 25 dòng / 0 nhánh — 100% | **36 / 4 — 100%** |
| Thấy 5 ảnh nữ đầu (345 ảnh thật) | sau khi quét xong (**86,49 s**) | **5,90 s** (đo thật 12 ảnh: 6,33 s) |

- **Tệp mới**: `tools/bench_loc_nu.py` (đo tốc độ + RAM + mốc "hiện dần"; cờ
  `--no-cache` dùng cache tạm nên **không** xoá cache thật của người dùng, cờ `--cache`
  để đo nguội rồi delta trên cùng dữ liệu, `--json` để TASK-003 so sánh).
- **Tệp sửa**: `xemanh/filterthread.py` (tín hiệu `found` + `_tien_do`, sắp theo thứ tự
  `paths` gốc để cache phát trước không làm lệch thứ tự), `xemanh/mainwindow.py`
  (`SHOW_AFTER = 5`, slot `_filter_found`, `_anh_dang_xem`, `_refresh_filter_meta`,
  `_filter_done` giữ ảnh đang xem, `_filter_failed` nói rõ khi dừng giữa chừng),
  `README.md`, và 4 tệp test.
- **Không đụng** `loc_nu.py`, `WORKERS`, `intra_op_num_threads`, cache key, `pyproject.toml`
  (đúng phạm vi). Phần tối ưu tốc độ vẫn để cho TASK-003.
- **Chi tiết đáng chú ý**: khi danh sách dài thêm mà ảnh đang xem không đổi thì **không**
  gọi `show_current()` (hàm đó giải mã lại ảnh từ đĩa); chỉ cập nhật chữ bằng
  `_refresh_filter_meta()` — nếu không, một lần quét 345 ảnh (243 ảnh nữ) sẽ giải mã lại
  ảnh hàng trăm lần và làm chậm cả quét lẫn giao diện.
- **pyflakes**: sạch với mọi tệp/dòng **do thay đổi này**. Còn 1 cảnh báo
  `mainwindow.py: 'cv2' imported but unused` — **có sẵn trước khi sửa**: đã kiểm chứng
  bằng cách chạy pyflakes trên chính tệp `mainwindow.py` lấy từ `origin/main`
  (cùng cảnh báo, dòng 499). Đó là `import cv2` để kiểm tra OpenCV có sẵn (có `# noqa:
  F401`); pyflakes không hiểu `noqa`. Cố ý **không** sửa vì nằm ngoài phạm vi task
  (`find_spec()` sẽ đổi hành vi khi cv2 cài hỏng) — nêu ở đây để người dùng quyết.
- **`build_exe.bat`** + `uv run python tools\check_exe.py`:
  `KẾT QUẢ: .exe chạy tốt, bundle sạch.` (RAM 80,9 MB, 4 thread, 29 DLL, exit 0).
- **Điểm cần biết khi viết test**: test functional **không** nên để
  `loc_nu.filter_female` thật chạy (nó mở `ThreadPoolExecutor` bên trong luồng Qt) rồi
  bơm sự kiện Qt liên tục — như vậy pytest **abort cả tiến trình**
  (`Fatal Python error: Aborted`, GC ở luồng chính va vào lúc luồng pool tạo thread).
  Đã kiểm chứng: test đó chạy **một mình thì xanh**, chỉ chết khi chạy sau các test khác
  → đổi sang đồ giả `filter_female` có cache; phần cache thật được kiểm ở
  `tests/unit/test_loc_nu_models.py` (không có Qt). App thật chạy đầu-cuối với model
  thật thì không thấy hiện tượng này (xem 8b).

## 10. Ghi chú / rủi ro
- **TASK-003** (tối ưu tốc độ `loc_nu.py`, mục tiêu ≤ 1s/ảnh) sẽ tạo sau; đừng lấn
  sang việc của nó trong task này.
- `tests/functional/test_filter_flow.py` và `test_mainwindow_cov.py` hiện giả định
  "chờ `win.filter_female` thành True rồi mới xem danh sách" — sửa `mainwindow.py` dễ
  làm vỡ các test này; phải giữ chúng xanh (có thể chỉnh test nhưng không hạ độ chặt).
- Bài học cũ: coverage **không theo dõi được luồng do Qt tạo** — test cho
  `FilterThread` phải gọi thẳng `run()`, còn luồng thật để ở `test_filter_flow.py`.
- Thứ tự hiển thị là chỗ dễ sai nhất (cache phát tiến độ trước ảnh mới quét).
- Không đụng `WORKERS` / `intra_op_num_threads` / cache key trong task này.
- TASK liên quan đã có: `TASK-001-tang-do-phu-test-len-90.md` (test/độ phủ).
