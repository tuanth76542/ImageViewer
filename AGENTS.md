# Phần Mềm Xem Ảnh — hướng dẫn cho agent

Ứng dụng xem ảnh Qt/PySide6 (Windows). Chi tiết tính năng, cách chạy, cách test,
cách đóng gói: xem `README.md`.

## Quy trình: lập task trước khi code

Khi người dùng yêu cầu **một tính năng mới**, **sửa một lỗi**, hoặc **đổi hành vi
đang có**, việc đầu tiên là gọi subagent **`task-planning`** (Task planning):

```text
subagent(task-planning, "<chép nguyên văn yêu cầu của người dùng>")
```

Agent đó sẽ hỏi lại cho rõ rồi tạo `tasks/TASK-NNN-<tên-ngắn>.md`. Sau đó:

1. Đọc file task vừa tạo, trình bày ngắn cho người dùng và **chờ người dùng xác
   nhận** — không tự bắt tay vào code khi chưa có xác nhận.
2. Khi đã xác nhận: gọi subagent **`task-implementation`** để thực thi:
   ```text
   subagent(task-implementation, "Làm task TASK-NNN")
   ```
   Agent đó sẽ tạo nhánh `feature/task-NNN-…` hoặc `bugfix/task-NNN-…` từ `main`
   mới nhất, code + chạy test tới khi đạt các cổng chất lượng, rồi **tóm tắt kết
   quả và hỏi bạn xác nhận**. Bạn OK thì nó mới squash các commit và merge vào
   `main`. **Không dùng pull request.**
3. Bám theo mục "Tiêu chí nghiệm thu" và "Việc cần làm" trong task; xong thì đổi
   `Trạng thái` trong file task thành `xong` (việc này nằm trong nhánh được squash
   và merge vào `main`).
4. (Nên làm với thay đổi lớn) Kiểm định chất lượng phát hành: gọi subagent
   **`sw-release-qg-check`** để **review báo cáo của task-implementation** (không
   chạy lại test/đo đạc): đối chiếu với mô tả task, tóm tắt tài nguyên RAM/CPU/đĩa
   (trung bình và đỉnh), độ phủ + cảnh báo mã, kết quả kiểm thử chức năng
   Pass/Fail kèm lý do, rồi kết luận Đủ/Chưa đủ điều kiện phát hành:
   ```text
   subagent(sw-release-qg-check, "Kiểm định phát hành TASK-NNN")
   ```

Không cần tạo task cho: câu hỏi để hiểu code, đọc/in thông tin, việc vặt mà người
dùng đã nói rõ "khỏi cần task". Quy ước chi tiết: `tasks/README.md`.

## Cổng chất lượng (trước khi nói "xong")

- `uv run pytest` xanh toàn bộ, độ phủ không tụt dưới `--cov-fail-under` trong
  `pyproject.toml` (hiện là 80).
- `uv run --with pyflakes python -m pyflakes <tệp đã sửa>` sạch (dự án không dùng
  ruff; đừng đổi layout `src/` hay thêm thư viện ngoài phạm vi task).
- Sửa mã app (`xemanh/`, `loc_nu.py`, `viewer_qt.py`) thì build lại `.exe` và
  chạy `uv run python tools\check_exe.py`; chỉ sửa test/tài liệu thì bỏ qua và
  nói rõ lý do.

## Ghi danh commit (commit do máy tạo)

Khi agent/máy commit hộ, **đặt tên tác giả là tên model đang chạy** (ví dụ
`DeepSeek V4.1 Flash`) để phân biệt commit của máy với commit của người dùng:

```bat
git -c user.name="DeepSeek V4.1 Flash" commit -m "..."
git -c user.name="DeepSeek V4.1 Flash" commit -F <tệp-mô-tả>
```

Giữ nguyên email trong `git config` của máy. Không viết lại lịch sử commit cũ để
đổi tên tác giả (`--amend`/rebase/force push).

## Skill của dự án

- Skill nằm ở `.opencode/skills/<id>/SKILL.md`; gọi bằng `@<id>`, hoặc agent tự
  nạp khi thấy liên quan.
- Hiện có `python-pro` (quy ước viết code Python). Lưu ý: skill viết theo mẫu
  chung (Python 3.11+, layout `src/`, `ruff`), còn dự án này chạy **Python 3.10**,
  layout phẳng, không có ruff — **khi lệch thì quy ước của dự án thắng**.

## Agent của dự án

Danh sách agent hiện có: `agents/README.md` (sinh tự động từ chính các tệp agent).

- Bản gốc: `agents/agent-<tên>.md` — một tệp một agent, tên tệp = tên gọi agent.
- `.opencode/agents/<tên>.md` là **bản sinh tự động** cho OpenCode quét: không
  sửa tay, sửa bản gốc rồi chạy `sync`.
- Thêm agent mới:
  ```bat
  uv run python tools\agents.py new <tên>
  :: điền 'description' + phần thân, rồi:
  uv run python tools\agents.py sync
  uv run python tools\agents.py check
  ```
- `check` bắt: frontmatter sai, thiếu `description`, trường V1 của OpenCode cũ
  (`temperature`, `tools`, …), bản sinh bị sửa tay hoặc lệch, tệp lạ trong
  `agents/`. Hãy chạy `check` sau khi thêm/sửa agent.

## Môi trường & lệnh

- Windows, PowerShell. Python/PySide6 quản lý bằng **`uv`** — không dùng `pip`.
- Chạy app: `uv run python viewer_qt.py [đường-dẫn]`
- Test: `uv run pytest` (nhóm: `-m unit`, `-m functional`, `-m resources`)
- Đo tài nguyên: `uv run python tools\measure_resources.py <thư-mục> -s 30`
- Kiểm tra .exe sau khi build: `uv run python tools\check_exe.py <thư-mục>`
- Đóng gói: `build_exe.bat` (chạy `PhanMemXemAnh.spec`, không gọi
  `pyinstaller` trực tiếp vì spec lọc DLL lạ).

## Cấu trúc & quy ước

- Gói `xemanh/`: `theme`, `imageutils`, `winfx`, `imageview`, `slideshow`,
  `helpdialog`, `filterthread`, `mainwindow`, `perf`. `viewer_qt.py` chỉ là điểm
  chạy + re-export tên cũ (đừng đưa logic mới vào đây).
- `loc_nu.py` là bộ lọc ảnh nữ (model ~430MB tải lần đầu), tách riêng khỏi gói.
- Giao diện, chú thích, tài liệu, tên test: **tiếng Việt** (không dấu trong tên
  tệp/hàm test, có dấu trong chuỗi hiển thị và docstring).
- Test chạy ở chế độ offscreen, không tải mạng, không cần model thật — hãy giả
  lập (monkeypatch) thay vì tải model.
- Giữ test cũ xanh; thêm test mới cho hành vi mới. Đừng hạ ngưỡng độ phủ.
- Không sửa `dist/`, `build/`, `models/`, `reports/` bằng tay (đều là sản phẩm
  sinh ra, đã nằm trong `.gitignore`).
