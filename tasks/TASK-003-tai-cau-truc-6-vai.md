# TASK-003 — Tái cấu trúc project theo 6 vai trò làm việc riêng rẽ

- **Ngày tạo**: 2026-10-18
- **Loại**: cải tiến (hạ tầng quy trình) — **bootstrap** (chạy bằng agent hiện có, xem mục 5)
- **Trạng thái**: xong
- **Người yêu cầu**: chủ dự án

## 1. Yêu cầu gốc

> "dua vao cac document da tao san trong project, hay tao lai cau truc project de cac agent co the lam viec rieng re nhu yeu cau"

(= dựa vào các tài liệu đã soạn sẵn trong project, tạo lại cấu trúc project để các agent
làm việc riêng rẽ như yêu cầu.)

Bản đặc tả **đã có sẵn, không mở lại**: `docs/04_Process_Architecture/00_README.md`,
`10_process_architecture_6_roles.md` (6 vai R1–R6, bảng quyền ghi, 5 cổng G1–G5),
`nfr_process.md` (NF-P1…NF-P12), `30_ke_hoach_ap_dung.md` (đợt 1–4) và
`docs/adr/ADR-0011…ADR-0017`. Task này **chỉ thi hành** các quyết định đó.

**Repo đích: `C:\Users\admin\Documents\Default Project\ImageViewer`** (bản mới, cây sạch,
tài liệu quy trình đã commit, đã push GitHub). Repo
`PhanMemXemAnh` **không** bị chạm trong task này (đang có cây bẩn của phiên agent khác).

## 2. Mục tiêu (đo được)

- `uv run python tools\agents.py list` hiện **đúng 6 vai**: `task-planning`,
  `task-implementation`, `task-vv`, `sw-system-release`, `sw-integrator`, `sw-architect`;
  `check` sạch. Không còn tên `sw-release-qg-check` ngoài ghi chú lịch sử.
- `tools/task.py new <tên>` cấp mã `TASK-NNN` **không trùng** (quét `tasks/` + các nhánh
  đang mở); chạy 2 lần liên tiếp cho 2 mã khác nhau; tệp sinh ra đủ mọi mục của mẫu.
- Mẫu task có thêm trạng thái `chờ V&V`, `đang V&V`, `chờ release` và 2 mục
  *Kết quả V&V* (R3), *Cổng phát hành* (R4); lệch giữa mẫu và agent R1 bị **test bắt**.
- `tools/board.py` sinh `tasks/BOARD.md` (nhóm theo trạng thái) và tệp đó **không được
  commit** (`git check-ignore tasks/BOARD.md` khớp).
- `tools/gate.py` = **một lệnh** chạy trọn cổng local (pytest → pyflakes → compileall),
  exit 0 khi sạch / exit ≠ 0 khi đỏ, thời gian **≤ 60 s** (NF-P5).
- `docs/01_Requirement/non_functional_requirements.md` tách riêng, **không mất NF nào**
  (đếm số NF trước/sau bằng nhau) và `requirements.md` trỏ sang tệp mới.
- `AGENTS.md` mô tả lượt chạy 5 vai **tuần tự** + 3 điểm duyệt của người dùng + chỉ R5
  merge `main`; trỏ tài liệu chi tiết về `docs/04_Process_Architecture/` (không chép lại).

## 3. Phạm vi

- **Trong phạm vi** (đợt 2 + phần còn lại của đợt 1): `agents/**`, `.opencode/agents/**`,
  `tools/agents.py`, `tools/task.py` (mới), `tools/board.py` (mới), `tools/gate.py` (mới),
  `tasks/MAU_TASK.md` (mới), `tasks/README.md`, `AGENTS.md`, `.gitignore`,
  `tests/unit/**`, `docs/01_Requirement/**`, `docs/adr/ADR-0018-*` (mới),
  `docs/04_Process_Architecture/30_ke_hoach_ap_dung.md`, `nfr_process.md`.
- **Ngoài phạm vi (cố ý không làm lần này)**: mã app `xemanh/**`, `loc_nu.py`,
  `viewer_qt.py`, `tests/functional/**`, `.github/workflows/**`; đợt 3 (`CHANGELOG.md`,
  tag thật, CI tham chiếu, `CODEOWNERS`/branch protection) và đợt 4 (chạy thử một vòng
  đủ 6 vai trên một yêu cầu thật); đồng bộ sang repo `PhanMemXemAnh` (làm ở task sau).
  Không đổi quy ước dự án (uv, PySide6, Python 3.10, layout phẳng, pyflakes, tiếng Việt).

## 4. Đã chốt với người dùng

| Câu hỏi | Chốt |
|---|---|
| Tái cấu trúc trên repo nào? | **Chỉ `ImageViewer`** (cây sạch, tài liệu đã commit). `PhanMemXemAnh` đồng bộ sau bằng cách chép nguyên bộ hạ tầng khi cây sạch — **không** stash/commit hộ cây bẩn. |
| Phạm vi đợt? | **Đợt 2 + phần còn lại đợt 1**. Đợt 3 (CHANGELOG/tag/CI) và đợt 4 (vòng vận hành 6 vai) = task sau. |
| Tag phiên bản + `CHANGELOG.md`? | **Có cả hai**: `CHANGELOG.md` + tag `v0.1.0`, `v0.1.1`… mỗi release. Chốt thành quyết định; **thi hành ở đợt 3**, task này chỉ ghi vào tài liệu/ADR. |
| Dùng pull request? | **Không PR cho task thường**; **được phép** PR khi người dùng muốn xem diff trên GitHub (ghi rõ trong tệp task). |

## 5. Còn mở

- **Ai chạy task này**: R5 `sw-integrator` chưa tồn tại → giai đoạn bootstrap dùng agent
  `task-implementation` hiện có (đóng vai R2+R5 tạm). Sau khi merge xong TASK-003 thì các
  task sau mới chạy đủ 6 vai. Ghi rõ lý do trong mục *Kết quả thực hiện*.
- Hai mục *Kết quả V&V* / *Cổng phát hành* của **chính task 003** để "không có" (R3/R4
  chưa tồn tại ở thời điểm làm) — ngoại lệ bootstrap, sẽ hết từ TASK-004.
- `CODEOWNERS` + branch protection có dùng không? — thuộc đợt 3, để task sau.

## 6. Hướng làm & tệp dự kiến đụng tới

**Đợt 1 (phần còn lại, chỉ tài liệu):**
- `docs/01_Requirement/non_functional_requirements.md` (mới) — tách mục NF1… khỏi
  `requirements.md`; tệp cũ giữ dòng trỏ sang, không đánh số lại NF.
- `docs/adr/ADR-0018-chinh-sach-phat-hanh-va-ngoai-le-pr.md` (mới) — ghi 2 quyết định vừa
  chốt (tag + `CHANGELOG.md`; PR là ngoại lệ có ghi chú).
- `docs/04_Process_Architecture/30_ke_hoach_ap_dung.md` (mục 2 "Điểm mở" → "đã chốt") và
  `nfr_process.md` (NF-P6 bỏ cột phụ thuộc treo).

**Đợt 2 (hạ tầng quy trình, không chạm mã app):**
- `agents/agent-task-vv.md`, `agents/agent-sw-integrator.md`, `agents/agent-sw-architect.md`
  (mới, bằng `uv run python tools\agents.py new …`); `sw-release-qg-check` →
  `sw-system-release` bằng `tools\agents.py rename`. Điền `description` + thân theo bảng
  quyền ghi mục 1 của `10_process_architecture_6_roles.md`; **chỉ `sw-integrator` được
  merge/push**, các vai khác bị chặn `push`/`merge`/`reset --hard`/`clean`/rebase.
- `tools/agents.py` — thêm luật kiểm cho `check`: đủ 6 vai, `sw-release-qg-check` không
  quay lại, mẫu task dùng chung nguồn chưa lệch.
- `tasks/MAU_TASK.md` (mới) = **nguồn duy nhất** của mẫu task (trạng thái mở rộng + mục
  *Kết quả V&V*, *Cổng phát hành*); sửa `agents/agent-task-planning.md` trỏ về tệp này
  thay vì chép mẫu trong prompt (ADR-0015 mục 3). Chi tiết kỹ thuật, không cần ADR.
- `tools/task.py` (mới): `new <tên>` cấp số nhỏ nhất còn trống (quét `tasks/TASK-*.md`
  trên đĩa **và** trên các nhánh local/remote), tạo tệp từ `tasks/MAU_TASK.md`, in mã;
  `list` liệt kê mã + trạng thái. Chỉ đọc/ghi tệp, không gọi mạng, chạy tức thì.
- `tools/board.py` (mới) sinh `tasks/BOARD.md` (bảng theo trạng thái + việc kế tiếp);
  `.gitignore` thêm `tasks/BOARD.md`.
- `tools/gate.py` (mới): pytest → pyflakes (tệp đã sửa/thêm) → `compileall`; cờ `--exe`
  mới thêm `build_exe.bat` + `tools\check_exe.py` (mặc định **tắt** để giữ ≤ 60 s).
- `AGENTS.md` (quy trình 6 vai, lượt tuần tự, 3 điểm duyệt, ai merge) và `tasks/README.md`
  (trạng thái mới, mục báo cáo mới, lệnh `tools\task.py`).

**Test (tests/unit — không cần màn hình, không tải model):**
- `tests/unit/test_task_tool.py` (mới — ADR-0015 nêu tên sẵn): cấp mã không trùng, quét
  được nhánh mở (dùng thư mục tạm/giả lập `git`), tệp sinh ra đủ mục, mẫu ↔ agent khớp.
- `tests/unit/test_board_tool.py`, `tests/unit/test_gate_tool.py` (mới; gate test bằng
  runner giả: sạch → 0, đỏ → ≠ 0).
- `tests/unit/test_agents_tool.py` (bổ sung): 6 vai, quyền của `sw-integrator` vs
  `task-vv`/`sw-architect`.

## 7. Tiêu chí nghiệm thu

- [x] `uv run python tools\agents.py list` hiện 6 vai đúng id; `check` in `OK`.
- [x] `grep -r "sw-release-qg-check" AGENTS.md tasks/README.md agents/README.md` **không** có kết quả.
- [x] `uv run python tools\task.py new "thu nghiem"` cấp **TASK-004** (không trùng 001–003),
      chạy lần hai cấp TASK-005; tệp sinh ra có đủ mọi mục của mẫu (xóa 2 tệp thử sau khi kiểm).
- [x] `uv run python tools\task.py list` hiện 3 task kèm trạng thái đọc từ tệp.
- [x] `uv run python tools\board.py` sinh `tasks/BOARD.md`; `git check-ignore tasks/BOARD.md` trả về đường dẫn đó.
- [x] `uv run python tools\gate.py` exit 0 và `Measure-Command` **≤ 60 s**; khi cố tình tiêm
      một lỗi pyflakes thì exit ≠ 0 (test đơn vị cũng phải phủ 2 nhánh này).
- [x] `docs/01_Requirement/non_functional_requirements.md` tồn tại, có đủ NF1…NFn như bản cũ.
- [x] `uv run pytest` xanh; độ phủ **không tụt** dưới mức hiện tại (sàn `--cov-fail-under=80`);
      `uv run --with pyflakes python -m pyflakes <tệp đã sửa/thêm>` sạch (ghi rõ cảnh báo có sẵn).
- [x] **Bỏ qua build `.exe` + `check_exe`**, kèm lý do: task chỉ chạm tài liệu/tooling/test,
      kiểm chứng bằng `git diff --name-only main..HEAD` không chứa `xemanh/`, `loc_nu.py`, `viewer_qt.py`.
- [x] Không có tệp nào ngoài danh sách mục 3 bị sửa; repo phía `PhanMemXemAnh` không bị chạm.

## 8. Kiểm thử

- Test mới/bổ sung: `tests/unit/test_task_tool.py`, `test_board_tool.py`, `test_gate_tool.py`,
  `test_agents_tool.py`.
- Lệnh: `uv run pytest` · `uv run pytest -m unit` · `uv run pytest tests/unit/test_task_tool.py`
  · `uv run python tools\agents.py check` · `uv run python tools\gate.py`.
- Kiểm tra tay (không có GUI, không cần build): `uv run python tools\task.py list`,
  `uv run python tools\board.py`, `git check-ignore tasks/BOARD.md`,
  `git diff --name-only main..HEAD`.
- Không cần kiểm tra giao diện: task không đụng mã app (nói rõ trong báo cáo).

## 9. Việc cần làm

- [x] (đợt 1) Tách `docs/01_Requirement/non_functional_requirements.md` + sửa liên kết trong `requirements.md`.
- [x] (đợt 1) Thêm `docs/adr/ADR-0018-…`; cập nhật `30_ke_hoach_ap_dung.md` mục 2 + `nfr_process.md` NF-P6.
- [x] `tools\agents.py new task-vv` / `new sw-integrator` / `new sw-architect`; điền description + thân theo bảng quyền.
- [x] `tools\agents.py rename sw-release-qg-check sw-system-release`; sửa tham chiếu cũ trong `AGENTS.md`.
- [x] Thêm `tasks/MAU_TASK.md` (mẫu đầy đủ, gồm trạng thái + 2 mục báo cáo mới); sửa `agents/agent-task-planning.md` trỏ về mẫu.
- [x] Viết `tools/task.py` (`new`, `list`) + test `tests/unit/test_task_tool.py`.
- [x] Viết `tools/board.py` + `.gitignore` (`tasks/BOARD.md`) + test.
- [x] Viết `tools/gate.py` (pytest → pyflakes → compileall, cờ `--exe`) + test.
- [x] Mở rộng `tools/agents.py check` (6 vai, tên cũ không quay lại, mẫu chưa lệch) + bổ sung test.
- [x] Cập nhật `AGENTS.md` + `tasks/README.md`; chạy `sync` + `check`; chạy cổng đầy đủ.
- [x] Ghi *Kết quả thực hiện* (số test, độ phủ, thời gian `gate.py`, lý do bỏ qua build `.exe`).

## 10. Ghi chú / rủi ro

- **Bootstrap**: chưa có R5/R3/R6 nên task này do `task-implementation` hiện có làm; ngoại lệ
  được ghi rõ trong tệp task (đúng tinh thần `30_ke_hoach_ap_dung.md` mục 3).
- `agents.py rename` xoá bản sinh `.opencode/agents/sw-release-qg-check.md` — phải chạy `sync`
  rồi `check`, và sửa mọi tham chiếu cũ (`AGENTS.md`, `tasks/README.md`, `README.md` nếu có).
- ADR-0015 mục 3: mẫu task phải **cùng nguồn** với phần "Ghi file task" của agent R1 — nếu để
  2 bản chép tay, sửa một bên là lệch; test phải bắt được.
- `tools/` không nằm trong `[tool.coverage.run]` → thêm tool không kéo độ phủ xuống, nhưng vẫn
  phải có test cho 3 công cụ mới (đừng để test rỗng).
- Đợt 3 (CHANGELOG, tag, CI) và đợt 4 (vòng 6 vai) **đừng lấn** trong task này.
- Repo `PhanMemXemAnh`: cây bẩn của phiên khác — tuyệt đối không stash/commit hộ/xoá.
- TASK liên quan: `TASK-001-tang-do-phu-test-len-90.md`, `TASK-002-hien-dan-ket-qua-loc-nu.md`
  (đều đã xong, không đụng). TASK-003 ở repo `PhanMemXemAnh` **không tồn tại** → mã này chỉ
  dùng cho repo `ImageViewer` (ADR-0015: cấp mã bằng công cụ để tránh trùng).

## Kết quả thực hiện (R2)

**Bối cảnh — ngoại lệ bootstrap (mục 5):** ở thời điểm làm, repo chưa có R3/R4/R5/R6; agent
`task-implementation` hiện có đóng **R2 + R5** tạm. Vì vậy task này **không** đi qua hai mục
*Kết quả V&V* / *Cổng phát hành* (R3/R4 chưa tồn tại) — ngoại lệ hết từ TASK-004.

**Nhánh:** `feature/task-003-tai-cau-truc-6-vai`, gốc `origin/main` @ `6d084b7`.

**Việc đã làm — đợt 1 (tài liệu):**
- `docs/01_Requirement/non_functional_requirements.md` (mới): tách nguyên NF1…NF8 khỏi
  `requirements.md` + bảng truy vết cách kiểm; `requirements.md` mục 3 chỉ còn dòng trỏ sang
  (không đánh số lại NF).
- `docs/adr/ADR-0018-chinh-sach-phat-hanh-va-ngoai-le-pr.md` (mới): chốt tag phiên bản +
  `CHANGELOG.md` mỗi release; PR chỉ là ngoại lệ có ghi chú.
- `docs/04_Process_Architecture/30_ke_hoach_ap_dung.md`: mục 2 "Điểm mở" → **ĐÃ CHỐT**, đợt 1
  và đợt 2 đánh dấu ✅ XONG, kèm ghi chú ngoại lệ bootstrap.
- `docs/04_Process_Architecture/nfr_process.md`: NF-P6 bỏ cột phụ thuộc "còn treo" → trỏ
  ADR-0011 + ADR-0018.

**Việc đã làm — đợt 2 (hạ tầng quy trình, KHÔNG chạm mã app):**
- `agents/agent-task-vv.md`, `agents/agent-sw-integrator.md`, `agents/agent-sw-architect.md`
  (mới) — description + thân theo bảng quyền ghi mục 1 của `10_process_architecture_6_roles.md`.
- `agents/agent-sw-release-qg-check.md` → `agents/agent-sw-system-release.md` (đổi tên, cập
  nhật description/thân/quyền review-only được ghi rõ là cố ý).
- `agents/agent-task-planning.md` viết lại: dùng `uv run python tools\task.py new …` và trỏ
  `tasks/MAU_TASK.md` thay vì chép mẫu trong prompt (ADR-0015 mục 3); được cấp **một** ngoại lệ
  shell cho đúng lệnh `uv run python tools\task.py*` (đây là lệnh shell, không phải sửa tệp).
- `tasks/MAU_TASK.md` (mới) = **nguồn duy nhất** của mẫu task: thêm trạng thái `chờ V&V`,
  `đang V&V`, `chờ release` và 2 mục *Kết quả V&V* (R3), *Cổng phát hành* (R4).
- `tools/task.py` (mới): `new <tên>` cấp số nhỏ nhất còn trống (quét `tasks/TASK-*.md` trên
  đĩa **và** trên các nhánh local/remote), tạo tệp từ `tasks/MAU_TASK.md`; `list` in mã +
  trạng thái. Chỉ đọc/ghi tệp, không gọi mạng.
- `tools/board.py` (mới): sinh `tasks/BOARD.md` nhóm theo trạng thái; `.gitignore` thêm
  `tasks/BOARD.md`.
- `tools/gate.py` (mới): một lệnh chạy cổng local pytest → pyflakes (tệp đã sửa/thêm) →
  `compileall`; cờ `--exe` mới thêm `build_exe.bat` + `tools\check_exe.py` (mặc định tắt).
- `tools/agents.py`: mở rộng `check` — đủ 6 vai chuẩn (ADR-0017), tên cũ `sw-release-qg-check`
  không quay lại, mẫu task cùng nguồn `tasks/MAU_TASK.md` chưa lệch; thêm `VAI_CHUAN`, `MAU_TASK`,
  `_la_du_an_that` (luật cấp dự án chỉ áp khi `NGUON` là `agents/` thật, tránh test thư mục tạm
  báo đỏ oan).
- `AGENTS.md`, `tasks/README.md` viết lại: 6 vai, lượt tuần tự R1→R5, 3 điểm duyệt, chỉ R5
  merge/push, trỏ chi tiết về `docs/04_Process_Architecture/`.

**Test mới/bổ sung:** `tests/unit/test_task_tool.py`, `test_board_tool.py`, `test_gate_tool.py`
(mới), `tests/unit/test_agents_tool.py` (bổ sung ca cấp dự án).

**Số liệu cổng chất lượng:**
- `uv run pytest`: **275 passed** (~17,7 s) — trước task 224 passed (+51 test).
- Độ phủ: **99,88 %** (1299 stmt, 1 miss `loc_nu.py:273`, 302 nhánh/1 miss) — **không đổi** so
  với trước task (trước: 99,88 %). `tools/` không nằm trong `[tool.coverage.run]` nên không kéo
  độ phủ xuống; sàn `--cov-fail-under=80` vượt xa.
- pyflakes 8 tệp `.py` đã sửa/thêm: **sạch** (không có cảnh báo có sẵn trên các tệp này).
- `uv run python tools\gate.py`: **exit 0**, **21,6 s** (≤ 60 s), cả 3 bước xanh.
- `uv run python tools\agents.py sync` + `check`: `OK: 6 agent hợp lệ, đủ 6 vai chuẩn
  (ADR-0017), bản OpenCode khớp bản gốc.`
- Kiểm tra tay: `tools\task.py new "thu nghiem"` → TASK-004 rồi TASK-005 (đã xoá 2 tệp thử);
  `tools\task.py list` → 3 task kèm trạng thái; `tools\board.py` ghi `tasks/BOARD.md`;
  `git check-ignore tasks/BOARD.md` khớp (exit 0).

**Bỏ qua build `.exe` + `tools\check_exe.py`** — có lý do: task chỉ chạm tài liệu/tooling/test,
không đụng mã app; kiểm chứng bằng `git diff --name-only main..HEAD` không chứa `xemanh/`,
`loc_nu.py`, `viewer_qt.py` (đúng tiêu chí nghiệm thu mục 7).

**Ngoài phạm vi (cố ý không làm):** mã app, `tests/functional/**`, `.github/workflows/**`;
đợt 3 (CHANGELOG/tag thật/CI/CODEOWNERS); đợt 4 (vòng 6 vai thật); đồng bộ sang
`PhanMemXemAnh` (repo đó không bị chạm).

## Kết quả V&V (R3)

- **Không có (ngoại lệ bootstrap)** — ở thời điểm làm TASK-003 chưa có vai R3 `task-vv`; agent
  `task-implementation` đóng R2+R5 tạm. Vai R3 bắt đầu hoạt động từ TASK-004 trở đi.

## Cổng phát hành (R4)

- **Không có (ngoại lệ bootstrap)** — ở thời điểm làm TASK-003 chưa có vai R4
  `sw-system-release`. Vai R4 bắt đầu hoạt động từ TASK-004 trở đi.
