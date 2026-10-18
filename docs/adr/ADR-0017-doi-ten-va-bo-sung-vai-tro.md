# ADR-0017 — Đổi tên vai R4 và bổ sung ba vai còn thiếu

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án A**)
- **Liên quan**: `agents/`, `tools/agents.py`, `AGENTS.md`

## Bối cảnh

Yêu cầu đặt tên 6 vai theo chuẩn: Task-Planning, Task-Implementation,
Task-**Verification-Validation**, SW-**System-Release**, SW-**Integrator**,
SW-**Architect**. Hiện repo có 3 agent: `task-planning`, `task-implementation`,
`sw-release-qg-check` (tên cũ do tôi đặt hôm nay, mô tả "Quality Gate check").

Cần quyết: đổi tên agent cũ cho khớp chuẩn, hay giữ id cũ để khỏi cập nhật tham
chiếu? Và các vai mới dùng id nào?

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. Đổi `sw-release-qg-check` → `sw-system-release`; thêm `task-vv`, `sw-integrator`, `sw-architect` (đã chọn)** | tên khớp chuẩn 6 vai, đọc là hiểu vai | phải cập nhật tham chiếu cũ trong `AGENTS.md`, `agents/README.md`, tài liệu |
| B. Giữ id `sw-release-qg-check`, chỉ đổi mô tả | không phải sửa gì | tên lệch chuẩn; về sau tài liệu phải giải thích "vì sao tên khác" |
| C. Đổi hết thành `role-1…role-6` | gọn | mất ngữ nghĩa; khó đọc |

## Quyết định

Chọn **A**:

| Mã | Tên chuẩn | Agent id | Ghi chú |
|----|-----------|----------|---------|
| R1 | Task-Planning | `task-planning` | giữ nguyên |
| R2 | Task-Implementation | `task-implementation` | giữ nguyên |
| R3 | Task-V&V | `task-vv` | **mới** |
| R4 | SW-System-Release | `sw-system-release` | **đổi tên** từ `sw-release-qg-check` bằng `uv run python tools\agents.py rename` |
| R5 | SW-Integrator | `sw-integrator` | **mới** |
| R6 | SW-Architect | `sw-architect` | **mới** |

Chi tiết khi tạo (đợt 2 của `30_ke_hoach_ap_dung.md`):

1. Dùng `uv run python tools\agents.py new <id>` rồi điền `description` + thân theo
   bảng quyền ghi ở `../04_Process_Architecture/10_process_architecture_6_roles.md`
   mục 1; sau đó `sync` + `check`.
2. Quyền của vai mới (least privilege, khớp ADR-0011 mục 4.7): được `git add/commit`
   trên nhánh của mình; **chặn** `git push`, `git merge`, `git reset`, `git clean`,
   `git rebase`, force push. R4 (release) là **review-only**: không chạy lại test,
   không đo đạc (quy tắc đã chốt với agent hiện tại).
3. R5 là vai duy nhất có `git merge`/`push` (merge vào `main`).

## Hệ quả

**Tốt**: 6 vai đọc lên là hiểu ngay; tài liệu C++ và Python dùng cùng bộ tên (bản
C++ cũng gọi R4 là SW-Release-QA — lệch nhẹ, đã ghi nhận, sẽ đồng bộ khi port).

**Xấu (chấp nhận)**: `sw-release-qg-check` xuất hiện trong commit cũ và trong
`agents/README.md` lịch sử — không viết lại lịch sử, chỉ đổi về sau.

## Xác nhận thực hiện đúng

- `uv run python tools\agents.py list` hiện đủ **6 agent** với id đúng bảng trên.
- `uv run python tools\agents.py check` sạch; `agents/README.md` sinh lại khớp.
- Không còn tham chiếu `sw-release-qg-check` trong `AGENTS.md` (trừ ghi chú lịch sử).
