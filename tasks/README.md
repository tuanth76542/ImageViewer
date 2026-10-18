# tasks/ — Kế hoạch công việc

Mỗi yêu cầu (tính năng mới, sửa lỗi, cải tiến) được **R1 Task-Planning** làm rõ và
ghi thành một tệp riêng ở đây trước khi code (cổng **G1**: người dùng duyệt).

## Quy ước

- Tên tệp: `TASK-NNN-<tên-ngắn-không-dấu>.md`
  - `NNN` tăng dần, đủ 3 chữ số: `TASK-001`, `TASK-002`, …
  - ví dụ: `TASK-004-xem-anh-dang-luoi.md`
- Mã `TASK-NNN` **không dùng lại**, kể cả khi việc đã xong, và **không được trùng**
  giữa các phiên: cấp mã bằng công cụ, đừng gõ tay (ADR-0015).
- Một tệp = một việc. Việc gộp nhiều phần rời nhau thì tách nhiều tệp.
- Mẫu (các mục cần có): **`tasks/MAU_TASK.md`** — nguồn duy nhất của mẫu task, dùng
  chung cho `tools/task.py` và agent R1 (`uv run python tools\agents.py check` bắt
  lỗi nếu hai bên lệch).

## Trạng thái

Ghi trong tệp, ở dòng `Trạng thái`, theo vòng đời 6 vai:

```text
chờ làm → đang làm → chờ V&V → đang V&V → chờ release → xong
                                   ↳ tạm hoãn / bỏ (kèm lý do ngắn)
```

| Trạng thái | Ai chuyển tiếp | Cổng |
|---|---|---|
| `chờ làm` | R1 tạo task | G1: người dùng duyệt task |
| `đang làm` | R2 code + unit test | G2: pytest/độ phủ/pyflakes/compileall |
| `chờ V&V` → `đang V&V` | R3 viết + chạy test chức năng | G3 |
| `chờ release` | R4 review hồ sơ, kết luận | G4 + người dùng duyệt phát hành |
| `xong` | R5 squash vào `main`, push | G5 |

## Mục báo cáo trong tệp task (ADR-0012)

Cuối mỗi tệp task có 3 mục cố định; **mỗi vai chỉ ghi vào mục của mình**
(append-only, cấm sửa mục của vai khác):

| Mục | Vai ghi | Nội dung |
|---|---|---|
| `## Kết quả thực hiện (R2)` | R2 | việc đã làm, tệp đã sửa, số liệu cổng chất lượng |
| `## Kết quả V&V (R3)` | R3 | Pass/Fail từng hạng mục kèm lý do, defect `DEF-NNN`, phần chưa kiểm được |
| `## Cổng phát hành (R4)` | R4 | kết luận `ĐỦ` / `ĐỦ NHƯNG CÓ ĐIỀU KIỆN` / `CHƯA ĐỦ` + ≤5 điểm cần cải thiện |

Bằng chứng nặng (coverage HTML, CSV đo tài nguyên, ảnh chụp) để ở `reports/**`
(không commit) và tham chiếu bằng đường dẫn từ mục báo cáo.

## Cách tạo task

Nhờ agent chính:

```text
Lập task cho việc: <yêu cầu của bạn>
```

hoặc chọn trực tiếp agent **Task planning** trong danh sách agent.

## Lệnh công cụ

```bat
uv run python tools\task.py new "<tên-ngắn>"   :: cấp mã TASK-NNN không trùng + tạo tệp từ mẫu
uv run python tools\task.py list               :: liệt kê task + trạng thái
uv run python tools\board.py                   :: sinh tasks\BOARD.md (bảng theo trạng thái, KHÔNG commit)
```

- `task.py new` quét `tasks/TASK-*.md` trên đĩa **và** trên các nhánh local/remote
  rồi cấp **số nhỏ nhất còn trống**.
- `tasks/BOARD.md` là tệp sinh tự động, đã nằm trong `.gitignore` — đừng commit.
