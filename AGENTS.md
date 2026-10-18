# Phần Mềm Xem Ảnh — hướng dẫn cho agent

Ứng dụng xem ảnh Qt/PySide6 (Windows). Chi tiết tính năng, cách chạy, cách test,
cách đóng gói: xem `README.md`.

## Quy trình 6 vai — một checkout, các vai chạy TUẦN TỰ

Bản đặc tả đầy đủ nằm ở `docs/04_Process_Architecture/` (đừng chép lại vào đây):

| Tài liệu | Nội dung |
|---|---|
| `00_README.md` | sơ đồ tổng quan + danh sách ADR đã chốt |
| `10_process_architecture_6_roles.md` | 6 vai (R1…R6), **bảng quyền ghi**, 5 cổng G1…G5, quy chế tuần tự |
| `nfr_process.md` | NFR của quy trình (NF-P1…NF-P12) |
| `30_ke_hoach_ap_dung.md` | kế hoạch áp dụng theo đợt |
| `docs/adr/ADR-0011…` | các quyết định đã chốt (tuần tự, báo cáo trong task, cổng tại máy, phân chia test, cấp mã task, vị trí tài liệu, tên vai, chính sách phát hành) |

| Mã | Vai | Agent | Vùng ghi chính |
|----|-----|-------|----------------|
| R1 | Task-Planning | `task-planning` | `tasks/TASK-*.md` (tạo mới), `docs/01_Requirement/requirements.md` |
| R2 | Task-Implementation | `task-implementation` | `xemanh/**`, `loc_nu.py`, `viewer_qt.py`, `tests/unit/**` |
| R3 | Task-V&V | `task-vv` | `tests/functional/**`, `tests/conftest.py`, `tests/fixtures/**` |
| R4 | SW-System-Release | `sw-system-release` | mục *Cổng phát hành (R4)* trong tệp task, `reports/release/**` (review-only) |
| R5 | SW-Integrator | `sw-integrator` | `tools/**`, `agents/**`, `.opencode/agents/**`, `AGENTS.md`, `.github/workflows/**`, `.gitignore`, `CHANGELOG.md`, `PhanMemXemAnh.spec`, `build_exe.bat`, `chay.bat` |
| R6 | SW-Architect | `sw-architect` | `docs/adr/**`, `docs/04_Process_Architecture/**`, `docs/02_System_SW_Architecture/**`, `docs/01_Requirement/non_functional_requirements.md` |

**Phiên chính không phải vai thứ 7**: nó giữ "lượt" (mỗi thời điểm chỉ **một** vai
chạy), gọi vai kế tiếp theo `Trạng thái` của tệp task, và là nơi người dùng ra
quyết định.

### Một vòng chạy (tuần tự R1 → R2 → R3 → R4 → R5)

```text
R1 lập task ──► [duyệt 1: task]              (G1)
   └─► R2 code + unit test ──► G2 (pytest · độ phủ · pyflakes · compileall)
         └─► R3 viết + chạy test chức năng ──► G3
               └─► R4 review hồ sơ (chỉ đọc) ──► G4: ĐỦ / ĐỦ NHƯNG CÓ ĐIỀU KIỆN / CHƯA ĐỦ
                     └─► [duyệt 2: phát hành] ──► R5 squash 1 commit vào main + push (G5)

R6 chạy khi cần quyết định kiến trúc: ADR (≥ 2 phương án) ──► [duyệt 3: chọn phương án]
```

- Ba điểm duyệt của người dùng: **(1) task · (2) phát hành · (3) phương án ADR** —
  không điểm nào được bỏ qua, nói miệng trong chat không tính là đã bàn giao.
- Một task đi hết vòng lặp qua 3 trạng thái trung gian trong tệp task:
  `chờ làm` → `đang làm` → `chờ V&V` → `đang V&V` → `chờ release` → `xong`
  (nhánh phụ: `tạm hoãn` / `bỏ`, kèm lý do ngắn).
- Báo cáo của từng vai nằm **trong tệp task** (ADR-0012): R2 ghi *Kết quả thực hiện*,
  R3 ghi *Kết quả V&V*, R4 ghi *Cổng phát hành*. Mỗi vai **chỉ ghi mục của mình**.
- Cổng nào đỏ thì quay lại **đúng vai đó**, ghi việc cần sửa vào tệp task; vai đang
  chạy không tự sửa phần của vai khác.
- **Chỉ R5 `sw-integrator` được `git merge`/`git push`** (và chỉ push `main`). Các
  vai khác: được `git add`/`commit` trên nhánh của mình; **bị chặn** `push`, `merge`,
  `reset`, `clean`, `rebase`, force push. Không vai nào `reset --hard`/force push.
- **Không dùng pull request** cho task thường; PR chỉ là **ngoại lệ** khi người dùng
  muốn xem diff trên GitHub (ghi rõ trong tệp task) — ADR-0018.
- Trước mỗi lượt: `git status` phải **sạch**. Bẩn thì dừng, báo người dùng — không
  tự `stash`/`commit` hộ thay đổi của phiên khác. Trên repo này **không mở hai
  phiên agent cùng lúc** (ADR-0011).

### Lệnh gọi vai (subagent)

```text
subagent(task-planning, "<chép nguyên văn yêu cầu của người dùng>")
subagent(task-implementation, "Làm task TASK-NNN")
subagent(task-vv, "V&V task TASK-NNN")
subagent(sw-system-release, "Kiểm định phát hành TASK-NNN")
subagent(sw-integrator, "Phát hành TASK-NNN (đã duyệt)")
subagent(sw-architect, "Quyết định kiến trúc: <vấn đề>")
```

Không cần tạo task cho: câu hỏi để hiểu code, đọc/in thông tin, việc vặt mà người
dùng đã nói rõ "khỏi cần task". Quy ước chi tiết: `tasks/README.md`.

## Cổng chất lượng (trước khi nói "xong")

Cổng chính thức chạy **tại máy dev** (ADR-0013); CI GitHub Actions chỉ là lớp tham
chiếu. Một lệnh cho cả bộ cổng:

```bat
uv run python tools\gate.py          :: pytest → pyflakes (tệp đã sửa) → compileall
uv run python tools\gate.py --exe    :: thêm build .exe + tools\check_exe.py (chậm, khi đụng mã app)
```

- `uv run pytest` xanh toàn bộ, độ phủ không tụt dưới `--cov-fail-under` trong
  `pyproject.toml` (hiện là 80; thực tế ~99,9%).
- `uv run --with pyflakes python -m pyflakes <tệp đã sửa>` sạch (dự án không dùng
  ruff; đừng đổi layout `src/` hay thêm thư viện ngoài phạm vi task).
- Đụng `agents/` thì chạy `uv run python tools\agents.py sync` rồi `... check`.
- Sửa mã app (`xemanh/`, `loc_nu.py`, `viewer_qt.py`) thì build lại `.exe` và chạy
  `uv run python tools\check_exe.py`; chỉ sửa test/tài liệu/tooling thì bỏ qua và
  nói rõ lý do trong báo cáo.
- Bằng chứng (số test, độ phủ, thời gian cổng) ghi vào mục *Kết quả thực hiện (R2)*
  trong tệp task — R4 sẽ chỉ đọc báo cáo đó, **không chạy lại**.

## Ghi danh commit (commit do máy tạo)

Khi agent/máy commit hộ, **đặt tên tác giả là tên model đang chạy** (ví dụ
`DeepSeek V4.1 Flash`) để phân biệt commit của máy với commit của người dùng:

```bat
git -c user.name="DeepSeek V4.1 Flash" commit -m "..."
git -c user.name="DeepSeek V4.1 Flash" commit -F <tệp-mô-tả>
```

Giữ nguyên email trong `git config` của máy. Không viết lại lịch sử commit cũ để
đổi tên tác giả (`--amend`/rebase/force push).

## Công cụ quy trình

```bat
uv run python tools\task.py new "<tên-ngắn>"   :: cấp mã TASK-NNN không trùng + tạo tệp từ mẫu
uv run python tools\task.py list               :: task + trạng thái
uv run python tools\board.py                   :: sinh tasks/BOARD.md (KHÔNG commit)
uv run python tools\gate.py [--exe]            :: chạy trọn cổng chất lượng local
uv run python tools\agents.py list|new|sync|check|rename|rm
```

Mẫu task là **`tasks/MAU_TASK.md`** — nguồn duy nhất cho cả `tools/task.py` và agent
R1; đừng chép mẫu sang chỗ khác (`agents.py check` sẽ bắt lỗi lệch nguồn).

## Skill của dự án

- Skill nằm ở `.opencode/skills/<id>/SKILL.md`; gọi bằng `@<id>`, hoặc agent tự
  nạp khi thấy liên quan.
- Hiện có `python-pro` (quy ước viết code Python). Lưu ý: skill viết theo mẫu
  chung (Python 3.11+, layout `src/`, `ruff`), còn dự án này chạy **Python 3.10**,
  layout phẳng, không có ruff — **khi lệch thì quy ước của dự án thắng**.

## Agent của dự án

Danh sách agent hiện có: `agents/README.md` (sinh tự động từ chính các tệp agent).
Đủ **6 vai** theo ADR-0017: `task-planning`, `task-implementation`, `task-vv`,
`sw-system-release`, `sw-integrator`, `sw-architect`.

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
  `agents/`, **thiếu/thừa vai so với 6 vai chuẩn**, và **mẫu task lệch nguồn**.
  Hãy chạy `check` sau khi thêm/sửa agent.

## Môi trường & lệnh

- Windows, PowerShell. Python/PySide6 quản lý bằng **`uv`** — không dùng `pip`.
- Cài môi trường: `uv sync --group dev`
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
- Không sửa `dist/`, `build/`, `models/`, `reports/`, `tasks/BOARD.md` bằng tay
  (đều là sản phẩm sinh ra, đã nằm trong `.gitignore`).
