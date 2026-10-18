# ADR-0015 — Cấp mã `TASK-NNN` bằng công cụ, chống trùng số

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (R6 đề xuất phương án A, người dùng không phản đối — ghi
  nhận là đã chốt cùng bộ ADR-0011…0017)
- **Liên quan**: `tasks/README.md`, `tools/agents.py` (mẫu công cụ tương tự)

## Bối cảnh

Quy ước hiện tại: `tasks/TASK-NNN-<tên-ngắn>.md`, `NNN` tăng dần, **không dùng
lại**. Khi có 6 vai và có thể có nhiều phiên/người cùng lập kế hoạch, hai người gõ
tay có thể chọn **cùng số** (TASK-002 hiện đã có 2 tệp cùng số ở hai thời điểm khác
nhau trong lịch sử repo, đúng kiểu nhầm này).

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. `tools/task.py new <tên>` cấp số kế tiếp bằng cách quét `tasks/` + mọi nhánh đang mở, rồi tạo tệp từ mẫu (đã chọn)** | không trùng số; tệp mới đúng mẫu; kiểm được bằng test | thêm một công cụ phải bảo trì |
| B. Gõ tay như hiện nay | không tốn công | vẫn có thể trùng; phải nhớ quy ước mẫu |
| C. Dùng ngày-giờ làm mã (`TASK-20261018-1`) | chắc chắn không trùng | tên dài, khó đọc, lệch quy ước `TASK-NNN` đang dùng trong mọi tài liệu |

## Quyết định

Chọn **A**:

1. Thêm `tools/task.py` với các lệnh:
   - `new <tên-ngắn>` — cấp số nhỏ nhất còn trống (quét `tasks/TASK-*.md` trên đĩa
     **và** trên các nhánh local/remote đang mở), tạo tệp từ mẫu chuẩn, in ra mã vừa cấp.
   - `list` — liệt kê task + trạng thái (đọc từ tệp).
2. `tools/board.py` sinh `tasks/BOARD.md` (bảng công việc, **không commit**) để
   phiên chính nhìn thấy hàng đợi mà không phải grep.
3. Tệp mẫu do `tools/task.py` dùng **cùng nguồn** với phần "Ghi file task" của agent
   `task-planning` (nếu lệch, `tools/agents.py check`/test sẽ bắt).
4. R1 vẫn là **vai duy nhất** được tạo `tasks/TASK-*.md`; công cụ chỉ giúp R1.

## Hệ quả

**Tốt**: hết trùng số kể cả khi có nhiều phiên; tệp task luôn đủ mục chuẩn (kể cả
mục mới *Kết quả V&V*, *Cổng phát hành*), giảm lỗi do quên mục.

**Xấu (chấp nhận)**: thêm 2 tệp tooling phải giữ tương thích khi mẫu task đổi; máy
yếu nên công cụ phải chạy tức thì (chỉ đọc/ghi tệp, không gọi mạng).

## Xác nhận thực hiện đúng

- Chạy `tools/task.py new` hai lần ở hai phiên khác nhau → hai mã khác nhau.
- `uv run pytest tests/unit/test_task_tool.py` xanh (bộ test mới cho công cụ).
