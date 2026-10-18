# tasks/ — Kế hoạch công việc

Mỗi yêu cầu (tính năng mới hoặc sửa lỗi) được **task planning agent** làm rõ và
ghi thành một tệp riêng ở đây trước khi code.

## Quy ước

- Tên tệp: `TASK-NNN-<tên-ngắn-không-dấu>.md`
  - `NNN` tăng dần, đủ 3 chữ số: `TASK-001`, `TASK-002`, …
  - ví dụ: `TASK-004-xem-anh-dang-luoi.md`
- Mã `TASK-NNN` **không dùng lại**, kể cả khi việc đã xong.
- Một tệp = một việc. Việc gộp nhiều phần rời nhau thì tách nhiều tệp.
- Tệp mẫu (các mục cần có): xem phần "Ghi file task" trong
  `agents/agent-task-planning.md` (bản OpenCode dùng để chạy nằm ở
  `.opencode/agents/task-planning.md`, sinh tự động — đừng sửa tay).

## Trạng thái

Ghi trong tệp, ở dòng `Trạng thái`: `chờ làm` → `đang làm` → `xong`
(hoặc `tạm hoãn` / `bỏ` kèm lý do ngắn).

## Cách tạo task

Nhờ agent chính:

```text
Lập task cho việc: <yêu cầu của bạn>
```

hoặc chọn trực tiếp agent **Task planning** trong danh sách agent.
