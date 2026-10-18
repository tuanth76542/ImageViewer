# ADR-0006 — Chiến lược kiểm thử và cổng chất lượng bản C++

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt)
- **Link**: baseline `../../../README.md` (mục Kiểm thử), `../../../pyproject.toml`

## Bối cảnh

Baseline Python có nền test mạnh: 224 test, độ phủ C0/C1 ~99.9%, sàn 80%
chốt trong `pyproject.toml`; 3 nhóm test `unit`/`functional`/`resources`;
test chạy offscreen, không mạng, không model thật (giả lập/monkeypatch);
`pytest-html` ghi `reports/test-report.html`; một lỗi thật từng được phát
hiện nhờ soi độ phủ (pinch gesture import sai module bị nuốt). Quy trình
6-role mới cần một chiến lược test tương đương sức mạnh trên C++.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **GoogleTest (unit) + Qt Test (functional) + CTest** | GTest = chuẩn de-facto C++, mock thoải mái; Qt Test native cho widget/signal; vcpkg có sẵn cả hai (ADR-0002) | Fixture cần tự viết, không tiện lợi như pytest fixtures |
| Catch2 + Qt Test | Cú pháp BDD gọn | Ecosystem nhỏ hơn; mock và GoogleMock mạnh hơn Catch2 |
| doctest only | Nhẹ nhất | Không có mock mạnh, thiếu Qt test integration |

## Quyết định (đề xuất)

**GoogleTest + GMock cho `core`/`ai` (unit, không cần màn hình); Qt Test cho
`gui` (functional, `QT_QPA_PLATFORM=offscreen`); CTest tổng hợp và chạy trên
CI; coverage bằng OpenCppCoverage trên Windows, sàn ≥ 80%, báo cáo cobertura/
HTML vào `reports/cov/`.**

Nhóm test (giữ 3 nhóm như baseline — `CTest labels` để chọn nhóm):

| Nhóm | Tương ứng baseline | Nội dung | Ai sở hữu |
|------|-------------------|----------|-----------|
| `unit` | `tests/unit/*` (~100+ test) | logic lọc nữ (cache/delta), cascade, đọc ảnh, SessionStore, Logger… (không màn hình) | Task-Implementation |
| `functional` | `tests/functional/*` (~100+ test) | cửa sổ chính: mở/navigate/zoom/xoay/lớp phủ/trợ giúp; slideshow; filter flow (hiện dần sau 5 ảnh); sự kiện chuột/kéo-thả/pinch; **đối chiếu hành vi Python↔C++** | Task-V&V |
| `resources` | `tests/resources/*` (4 test) | RAM/CPU: mở 24 ảnh lớn, 60 lần navigate, slideshow — không rò rỉ, CPU idle < 1% (như baseline, ngưỡng theo `nfr_cpp.md`) | Task-V&V |

Nguyên tắc giữ nguyên từ baseline:

- Test **không mạng, không model thật, không màn hình** — mock qua
  `IGenderInference` (ADR-0004/ADR-0005).
- Giữ test cũ xanh; thêm test mới cho hành vi port; **không hạ sàn độ phủ**.
- Báo cáo test (XML/HTML) ghi vào `reports/` — tương đương `reports/test-report.html`.

Cổng chất lượng C++ (thay `uv run pytest` + `pyflakes` ở baseline):

1. `cmake --build` + `ctest` xanh toàn bộ (không lỗi link, không test thất bại).
2. Coverage ≥ 80% (chỉ đo `src/`, không đo tooling, không đo `tests/`).
3. **clang-format** sạch (lệch format = fail).
4. **clang-tidy** không có cảnh báo mới ở tệp sửa (nếu có phải `NOLINT` kèm lý
   do được ghi).
5. Nếu sửa mã app: build .exe (CPack) rồi `tools/check_exe.py` sạch (tool
   Python giữ nguyên, chỉ cần điều chỉnh đường dẫn .exe — ADR-0002).

## Hệ quả

- Điểm tốt: port kiểm chứng thu được tính đúng đắn được đo bằng dữ liệu,
  không bằng mắt.
- Rủi ro: tooling C++ (ctest) khác tooling Python (pytest), nên tệp template
  `tasks/*.md` phải ghi đúng lệnh cổng chất lượng để Task-Implementation
  chạy trúng (spec nằm trong `10_process_architecture_6_roles.md`).
