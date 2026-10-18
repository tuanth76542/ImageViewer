# TASK-001 — Tăng độ phủ test lên tối thiểu 90% (C0 và C1)

- **Ngày tạo**: 2026-10-18
- **Loại**: cải tiến (chất lượng test)
- **Trạng thái**: xong
- **Người yêu cầu**: chủ dự án

## 1. Yêu cầu gốc
> "giup toi tang code coverage cua project len toi thieu 90%"

## 2. Mục tiêu (đo được)
- Sau khi xong, `uv run pytest` báo **C0 ≥ 90%** (hiện 1049/1237 = 85%) và
  **C1 ≥ 90%** (hiện 240/282 = 85%).
- Bộ test vẫn **chạy offline, không tải model, không cần màn hình**, tổng thời
  gian không vượt ~30 giây (hiện ~14 giây).
- Không hạ ngưỡng/độ chặt của test cũ; 138 test cũ vẫn xanh.
- `pyproject.toml` có `--cov-fail-under=80` để lần sau tụt sâu là pytest đỏ.

## 3. Phạm vi
- **Trong phạm vi**: thêm test (chủ yếu là **giả lập/monkeypatch**), chỉnh
  `pyproject.toml`, cập nhật mục "Độ phủ mã nguồn" trong `README.md`.
- **Ngoài phạm vi**: tải model thật, test cần mạng, sửa logic sản phẩm trong
  `xemanh/`/`loc_nu.py` (trừ khi thấy lỗi thật — khi đó báo lại, đừng tự sửa
  rộng), build lại `.exe` (thay đổi chỉ ở test + pyproject).

## 4. Đã chốt với người dùng
| Câu hỏi | Chốt |
|---|---|
| "90%" là chỉ số nào? | **Cả C0 và C1 đều ≥ 90%** (cột Cover gộp khi đó cũng ≥ 90%) |
| Cho phép `# pragma: no cover` / exclude? | **Cho phép, nhưng chỉ cho phần thật sự không test được, và mỗi chỗ phải có chú thích ngắn giải thích vì sao**; ưu tiên giả lập/mock |
| Có được bỏ offline / chạy chậm hơn? | **Không** — giữ offline + nhanh, chỉ dùng giả lập/mock |
| Chốt ngưỡng vào pyproject? | **Có**, đặt `--cov-fail-under=80` (thấp hơn lần chạy gần nhất 85%) |

## 5. Còn mở
- Sau khi đã đạt 90%, có nâng `--cov-fail-under` lên 90 không? (lần này giữ 80
  theo ý người dùng).
  -> **Chưa nâng**, giữ 80 như đã chốt. Số thực đạt ~99.87% nên có thể nâng lên 90
  hoặc 95 bất cứ lúc nào; để người dùng quyết ở lần sau.

## 6. Hướng làm & tệp dự kiến đụng tới
- `tests/unit/test_loc_nu_models.py` **(mới)** — chỗ hụt lớn nhất (81 dòng):
  - `download_models` (86-99): monkeypatch `urllib.request.urlretrieve`, `MODEL_DIR` trỏ `tmp_path`; test bỏ qua khi model đã có, gọi `progress`, và `.tmp → replace`.
  - `_yunet` (143-151), `_ensure` (153-182): thay `cv2.FaceDetectorYN`/`sys.modules["onnxruntime"]` bằng đồ giả; test cả nhánh thiếu `FaceDetectorYN` (158-160) và nhánh vòng 1 lỗi → `self.fast = None` (180-181).
  - `_p_female_fast` (184-199), `_p_female` (201-212): session giả trả mảng numpy cố định, kiểm tra softmax ≈ giá trị mong đợi.
  - `_faces` (234-255): detector giả; test nhánh ảnh lớn bị thu nhỏ (`DET_MAX_SIDE`), `faces is None`, và sắp xếp mặt to nhất trước.
  - `_save_cache` nhánh `OSError` (126-127): monkeypatch `open`/`os.replace` cho lỗi.
- `tests/functional/test_mainwindow_cov.py` **(mới)** — `mainwindow.py` hụt 66 dòng:
  - `keyPressEvent` các phím chưa test: Up, Down/Space, Plus/Equal, Minus, F5, F11, Esc khi `_f11_full`, F, H, F1, Ctrl+O, Ctrl+A, nhánh `else`.
  - `MainWindow(start_path=<tệp ảnh>)` (56-57); `choose_folder` (254-256, monkeypatch `QFileDialog`); `open_folder` thư mục rỗng (271-274, monkeypatch `QMessageBox`).
  - `show_current` khi `Image.open` lỗi (305-307); nhánh `filter_female` còn bật (318-319); `_compute_fit`/`_apply_view` khi chưa có ảnh (327-328, 335-336).
  - `_step` khi rỗng (352-353); các hàm zoom/rotate khi chưa có ảnh (367-368, 382-383, 389-390, 396-397, 403-404, 410-411).
  - `showEvent` khi `_aero_on` (419-420), `toggle_aero` cả hai nhánh (424-433, monkeypatch `aero_available`/`enable_window_blur`/`disable_window_blur`).
  - `toggle_slideshow` đóng khi đang mở (449-451) và khi chưa có ảnh (452-453); `_on_slideshow_closed` hai nhánh (463-466).
  - `toggle_female_filter`: đang chạy thì thoát (483-484), chưa mở ảnh (485-487), tắt lọc (488-497), thiếu cv2 (498-505), bỏ qua tải model (507-513) — monkeypatch `QMessageBox`.
  - `_filter_tick` (533-538), `_close_progress` nhánh lỗi (544-545), `_filter_failed` (548-550), `_filter_done` khi không giữ ảnh nào (554-558), `closeEvent` khi luồng còn chạy (570-571).
- `tests/functional/test_slideshow.py` (thêm test) — 119-126 (chuột di/chuyển), 139 (`show_slide` khi rỗng), 145-146 (ảnh đọc lỗi), 166 (`step` khi rỗng), 196 (phím lạ).
- `tests/unit/test_winfx.py` (thêm test) — 27→23 (vòng lặp chọn icon), 40-41, 69-70, 102-103, 121-122: các nhánh `except` an toàn, giả lập `ctypes`/`QApplication.platformName` cho lỗi.
- `tests/unit/test_perf.py` (thêm test) — 26-27 (không có psutil), 74 (`GetProcessMemoryInfo` lỗi), 140-141 (tiến trình con đã tắt), 146→151 (`dt <= 0`).
- `tests/functional/test_viewer.py` (thêm test) — `helpdialog.py` 63-66 (Esc/H/F1 và phím lạ) và 59→exit; `imageview.py` 20-21 (monkeypatch `grabGesture` cho lỗi).
- `tests/unit/test_viewer_main.py` **(mới)** — `viewer_qt.main()` 46-54: monkeypatch `QApplication`/`MainWindow`/`sys.exit` bằng đồ giả để `app.exec()` không thật sự chạy; `pytest.raises(SystemExit)`.
- `pyproject.toml` — thêm `--cov-fail-under=80` vào `addopts` (kèm chú thích lý do).
- `README.md` — cập nhật bảng C0/C1 (số mới), bảng "chỗ còn mỏng", và ghi rõ dòng nào
  phải `# pragma: no cover` + vì sao.

## 7. Tiêu chí nghiệm thu
- [x] `uv run pytest` xanh; bảng coverage in ra **C0 ≥ 90%** và **C1 ≥ 90%**.
- [x] `pytest --cov-fail-under=80` (đã nằm trong `addopts`) không làm đỏ bộ test.
- [x] Số test tăng, toàn bộ test cũ giữ nguyên hành vi; tổng thời gian ≤ ~30 giây.
- [x] Không có test nào cần mạng/model thật; `uv run pytest -m unit` và `-m functional` vẫn chạy offline.
- [x] Mọi `# pragma: no cover` mới đều có chú thích ngắn lý do và được liệt kê trong README.
      (Lần này **không thêm `# pragma: no cover` nào** — mọi dòng đều chạy tới được và
      đã có test thật; README ghi rõ dòng duy nhất còn hụt là phòng vệ không chạy tới.)
- [x] `uv run python tools\agents.py check` vẫn sạch (không đụng agent, chỉ để chắc).
- [x] Không cần `build_exe.bat` lần này (không đổi mã app) — ghi rõ trong kết quả.

## 8. Kiểm thử
- Test mới/sửa: `tests/unit/test_loc_nu_models.py`, `tests/unit/test_viewer_main.py`,
  `tests/functional/test_mainwindow_cov.py`, cùng các tệp test hiện có nêu ở mục 6.
- Lệnh: `uv run pytest` · `uv run pytest -m unit` · `uv run pytest -m functional` ·
  xem `reports/cov-html/index.html` để soi dòng còn đỏ/vàng.
- Kiểm tra tay: mở `reports/test-report.html`, kéo xuống bảng độ phủ, xác nhận
  C0/C1 ≥ 90%; đối chiếu `loc_nu.py`, `mainwindow.py` không còn dòng đỏ vô lý.

## 9. Việc cần làm
- [x] Thêm `tests/unit/test_loc_nu_models.py` (giả lập cv2/onnxruntime) — ưu tiên cao nhất vì hụt nhiều nhất.
- [x] Thêm `tests/unit/test_viewer_main.py` cho `main()` bằng đồ giả.
- [x] Thêm `tests/functional/test_mainwindow_cov.py` phủ phím tắt/nhánh lỗi/lọc nữ.
- [x] Bổ sung test cho `slideshow.py`, `winfx.py`, `perf.py`, `helpdialog.py`, `imageview.py`.
- [x] Chạy lại, soi `cov-html`; chỗ nào vẫn hụt thì hoặc viết thêm test, hoặc thêm `# pragma: no cover` + chú thích lý do.
      -> Viết thêm test là đủ; **không phải thêm `# pragma: no cover` nào**.
- [x] Thêm `--cov-fail-under=80` vào `pyproject.toml` (có chú thích).
- [x] Cập nhật bảng độ phủ + danh sách dòng exclude trong `README.md`.
- [x] Chạy lại toàn bộ 3 nhóm test, xác nhận thời gian và độ phủ.

## 9b. Kết quả thực hiện (điền khi xong)

| Chỉ số | Trước | Sau |
|---|---|---|
| Số test | 138 | **209** (unit 118 · functional 84 · resources 7) |
| Thời gian chạy | ~14 giây | **~15 giây** |
| **C0** — dòng lệnh | 1049 / 1237 ≈ 85% | **1236 / 1237 ≈ 99.9%** |
| **C1** — nhánh | 240 / 282 ≈ 85% | **281 / 282 ≈ 99.6%** |
| Cột `Cover` gộp | 82% | **99.87%** |

- Tệp mới: `tests/unit/test_loc_nu_models.py`, `tests/unit/test_viewer_main.py`,
  `tests/functional/test_mainwindow_cov.py`.
- Tệp sửa: `tests/unit/test_perf.py`, `tests/unit/test_winfx.py`,
  `tests/functional/test_slideshow.py`, `tests/functional/test_viewer.py`,
  `pyproject.toml`, `README.md`.
- **Không đụng mã app** (`xemanh/`, `loc_nu.py`, `viewer_qt.py`) và **không thêm
  `# pragma: no cover`** nào. Dòng duy nhất còn hụt là `loc_nu.py:273` — kiểm tra
  phòng vệ **không thể chạy tới** (box mặt đã bị kẹp trong ảnh và đã qua ngưỡng
  `MIN_FACE_SIZE`, nên lát cắt `img[y1:y2, x1:x2]` luôn khác rỗng).
- Vì chỉ sửa test + `pyproject.toml` + tài liệu nên **cố ý bỏ qua `build_exe.bat`
  và `tools\check_exe.py`**: mã app không đổi, `.exe` đang có vẫn đúng.
- `uv run --with pyflakes python -m pyflakes <các tệp đã sửa>`: sạch.
- `uv run python tools\agents.py check`: `OK: 2 agent hợp lệ, bản OpenCode khớp bản gốc.`
- Ghi chú: lần này **không phát hiện lỗi thật** nào trong mã app; độ phủ tăng thuần
  bằng test + giả lập, không phải sửa logic sản phẩm.

## 10. Ghi chú / rủi ro
- `loc_nu.py` khó nhất: các hàm `_ensure`/`_yunet`/`_p_female*` `import` bên trong
  hàm nên phải monkeypatch `sys.modules["onnxruntime"]` / thuộc tính của `cv2`;
  nhớ `monkeypatch` sẽ tự hoàn tác, đừng `setattr` trực tiếp lên `cv2`.
- Đừng lặp lại lỗi cũ: coverage **không theo dõi được luồng do Qt tạo** — test cho
  `FilterThread` phải gọi thẳng `run()`, không dựa vào `start()`.
- `mainwindow.toggle_female_filter` dựng `ProgressDialog` thật; nên monkeypatch
  `QMessageBox`/`QProgressDialog` để không treo ở chế độ offscreen.
- Đã có tiền lệ soi coverage phát hiện **lỗi thật** (pinch zoom import sai module)
  — khi thấy dòng tối nghĩa, đọc kỹ trước khi exclude, có thể là lỗi thật.
