# Kiến trúc quy trình: 6 vai trò làm việc trên repo (chế độ tuần tự)

> Trạng thái: **ĐÃ CHỐT** (ADR-0011 … ADR-0017, ngày 2026-10-18).
> Áp dụng cho repo Python này. Bản cho port C++: `../03_CPP_Port_Architecture/10_process_architecture_6_roles.md`.

## 0. Mục tiêu

Cho **6 vai trò** cùng làm việc trên **một repo**, mỗi vai có vùng ghi riêng và
artifact riêng, **giao tiếp bằng tệp trong git** (không qua chat), để:

- người khác (hoặc phiên agent khác) đọc artifact là làm tiếp được ngay;
- không vai nào giẫm lên việc của vai khác;
- người dùng chỉ phải duyệt **3 điểm**: task · phương án ADR · phát hành.

**Cách chạy: tuần tự** (ADR-0011). "Làm việc đồng thời" ở đây nghĩa là **6 vai
cùng tồn tại và luân phiên trên một checkout**, mỗi thời điểm chỉ **một vai chạy**.
Muốn song song vật lý (2 task cùng lúc) phải mở ADR mới để chuyển sang worktree.

## 1. Vai trò và quyền ghi

Nguyên tắc: **một đường dẫn chỉ có tối đa một vai được GHI**; vai khác chỉ đọc.

| # | Vai | Agent | Bản chất | Được GHI | Không được ghi |
|---|-----|-------|----------|----------|----------------|
| R1 | Task-Planning | `task-planning` | Project Manager / System Engineer | `tasks/TASK-*.md` (tạo mới), `docs/01_Requirement/requirements.md`, `docs/01_Requirement/fr/**` | mã, test, CI |
| R2 | Task-Implementation | `task-implementation` | SW Developer | `xemanh/**`, `loc_nu.py`, `viewer_qt.py`, `tests/unit/**`, `tools/bench_loc_nu.py` | `tests/functional/`, CI, tài liệu |
| R3 | Task-V&V | `task-vv` (mới) | System Test Engineer | `tests/functional/**`, `tests/conftest.py`, `tests/fixtures/**`, mục *Kết quả V&V* trong tệp task | mã app, `tests/unit/` |
| R4 | SW-System-Release | `sw-system-release` (đổi tên từ `sw-release-qg-check`) | QA Engineer | mục *Cổng phát hành* trong tệp task, `reports/release/**` | mã, test, CI |
| R5 | SW-Integrator | `sw-integrator` (mới) | Integrator / DevOps | `.github/workflows/**`, `tools/agents.py`, `tools/task.py`, `tools/board.py`, `tools/gate.py`, `AGENTS.md`, `agents/**`, `.opencode/agents/**`, `.gitignore`, `PhanMemXemAnh.spec`, `build_exe.bat`, `chay.bat`, `CHANGELOG.md` | mã app, test |
| R6 | SW-Architect | `sw-architect` (mới) | SW Architect | `docs/04_Process_Architecture/**`, `docs/adr/**`, `docs/02_System_SW_Architecture/**`, `docs/01_Requirement/non_functional_requirements.md` | mã, test, CI |

**Phiên chính không phải vai thứ 7** — nó là orchestrator theo `AGENTS.md`: chọn
vai kế tiếp theo trạng thái task, giữ "lượt", và là nơi người dùng ra quyết định.

## 2. Artifact là hợp đồng

| Artifact | Đường dẫn | Ai tạo/cập nhật | Ai đọc | Trong git? |
|----------|-----------|-----------------|--------|-----------|
| **FR** (yêu cầu chức năng) | `docs/01_Requirement/requirements.md` (+ `fr/FR-NN-*.md` khi cần chi tiết) | R1 | R2 R3 R4 R6, người dùng | ✅ |
| **NFR** (yêu cầu phi chức năng) | `docs/01_Requirement/non_functional_requirements.md` | R6 | R2 R3 R4 R5 | ✅ |
| **ADR** | `docs/adr/ADR-NNNN-*.md` | R6 | mọi vai, người dùng | ✅ |
| **Kiến trúc** (C4 + quy trình) | `docs/04_Process_Architecture/**`, `docs/02_System_SW_Architecture/**` | R6 | mọi vai | ✅ |
| **Tệp task** | `tasks/TASK-NNN-*.md` | R1 tạo; R2…R6 **chỉ ghi vào mục của mình** | mọi vai | ✅ |
| **Mã + unit test** | `xemanh/**`, `loc_nu.py`, `viewer_qt.py`, `tests/unit/**` | R2 | R3 R4 R6 | ✅ |
| **Test chức năng + fixture** | `tests/functional/**`, `tests/conftest.py`, `tests/fixtures/**` | R3 | R4 | ✅ |
| **Báo cáo V&V** | mục *Kết quả V&V* trong tệp task (+ mã test đã commit) | R3 | R4 | ✅ |
| **Cổng phát hành** | mục *Cổng phát hành* trong tệp task; bản đầy đủ `reports/release/REL-*.md` | R4 | người dùng, R5 | mục task ✅ / `reports/` ❌ |
| **Bằng chứng nặng** (coverage html, CSV, ảnh chụp) | `reports/**` | R2 R3 R4 | người dùng | ❌ (gitignored) |
| **Git workflow / CI / tooling** | `.github/**`, `tools/**`, `AGENTS.md`, `agents/**`, `CHANGELOG.md` | R5 | mọi vai | ✅ |
| **Bảng công việc** | `tasks/BOARD.md` (sinh bằng `tools/board.py`) | R5 | mọi vai, người dùng | ❌ (sinh lại) |

Nguyên tắc: **không có artifact → không qua cổng**. Nói miệng trong chat không
tính là đã bàn giao.

## 3. Vòng đời task và các cổng

```text
yêu cầu ─R1→ [G1 người dùng duyệt] ─R2→ implemented ─R3→ verified ─R4→ [G4 duyệt] ─R5→ released
```

`Trạng thái` trong tệp task (mở rộng so với 3 trạng thái cũ):

```text
chờ làm → đang làm → chờ V&V → đang V&V → chờ release → xong
                                   ↳ tạm hoãn / bỏ (kèm lý do ngắn)
```

Cổng nào đỏ → **quay lại đúng vai đó**, ghi danh sách việc cần sửa vào tệp task;
vai hiện tại **không tự sửa** phần của vai khác.

| Cổng | Vai chạy | Điều kiện qua | Bằng chứng nằm ở |
|------|----------|---------------|------------------|
| **G1** FR hợp lệ | R1 | FR có ID và đo được; task có *Mục tiêu (đo được)* + *Tiêu chí nghiệm thu* | người dùng OK trong chat |
| **G2** Code đủ chất lượng | R2 | `uv run pytest` xanh; độ phủ ≥ 80 (thực tế ~99,9%); `python -m pyflakes` sạch các tệp đã sửa; `python -m compileall` không lỗi; **nếu đụng mã app**: build `.exe` + `tools\check_exe.py` sạch | mục *Kết quả thực hiện* trong task |
| **G3** V&V đạt | R3 | mọi test chức năng của task PASS; defect ghi mã `DEF-NNN` kèm cách lặp lại | mục *Kết quả V&V* trong task |
| **G4** Đủ điều kiện phát hành | R4 | review **chỉ đọc** artifact của R1–R3 (không chạy lại), kết luận `ĐỦ / ĐỦ NHƯNG CÓ ĐIỀU KIỆN / CHƯA ĐỦ` + ≤5 điểm cần cải thiện | mục *Cổng phát hành* trong task |
| **G5** Đã phát hành | R5 | squash vào `main`, `git status` sạch, cổng local xanh, tag + `CHANGELOG.md` | log git + tag |
| **ADR** | R6 | ADR có ≥ 2 phương án, hệ quả tốt/xấu, được người dùng chọn | `docs/adr/` |

RACI rút gọn (R = chịu trách nhiệm chính):

| Cổng | R1 | R2 | R3 | R4 | R5 | R6 |
|------|----|----|----|----|----|----|
| G1 | **R** | C | C | I | I | C |
| G2 | I | **R** | C | I | I | C |
| G3 | C | C | **R** | I | I | C |
| G4 | I | I | C | **R** | I | C |
| G5 | I | I | I | C | **R** | I |
| ADR mới | I | I | I | I | I | **R** |

Người dùng là **Accountable** ở 3 điểm duyệt.

## 4. Quy chế chạy tuần tự (ADR-0011)

1. **Một checkout duy nhất** tại thư mục dự án; mọi vai dùng chung `.venv`,
   `models/`, `uv.lock` — không nhân bản gì.
2. **Mỗi thời điểm chỉ một vai chạy.** Phiên chính giữ "lượt": chỉ gọi vai kế tiếp
   khi vai trước đã kết thúc và **đã ghi artifact của mình**.
3. **Trước mỗi lượt: `git status` phải sạch.** Nếu bẩn → dừng, báo người dùng; vai
   đang chạy **không tự `stash`/`commit` hộ** thay đổi của người khác.
4. **Không mở hai phiên agent cùng lúc trên repo.** Sự cố ngày 2026-10-18 (một
   phiên ở nhánh `docs/c4-architecture` để cây bẩn + `docs/03_CPP_Port_Architecture/`
   chưa commit, trong khi phiên khác merge TASK-002 vào `main`) là ví dụ điển hình
   cho việc này. Muốn chạy song song thật → **mở ADR mới** xin chuyển sang worktree.
5. **Các bước nặng mặc nhiên tuần tự**: `pytest`, `build_exe.bat`, đo tài nguyên —
   không bao giờ chạy chồng.
6. **Một người ghi một mục**: trong tệp task, vai nào chỉ ghi vào mục của vai đó
   (kiểu append-only); cấm sửa mục của vai khác.
7. **Chỉ R5 merge vào `main`.** Quyền git của các vai:

   | Vai | `add`/`commit` trên nhánh của mình | `push` nhánh | merge `main` | `reset --hard` / `clean` / force push |
   |-----|-----|-----|-----|-----|
   | R1, R2, R3, R4, R6 | ✅ | ❌ | ❌ | ❌ |
   | R5 | ✅ | ✅ (chỉ `main` và nhánh hạ tầng) | ✅ | ❌ |

8. **Thứ tự khi có nhiều task**: R5 chốt thứ tự merge; nhánh đứng sau rebase lên
   `main` mới rồi mới vào cổng.

## 5. Trạng thái hiện tại / còn thiếu

| Hạng mục | Trạng thái |
|----------|-----------|
| R1, R2, R4 + orchestrator `AGENTS.md` | ✅ có |
| Cổng chất lượng local (pytest + pyflakes, `check_exe`) | ✅ có |
| `tools/agents.py` (quản lý vai + 18 test) | ✅ có |
| CI GitHub Actions (pytest + pyflakes) | ✅ có — nhưng chỉ là **tham chiếu** (ADR-0013) |
| R3 `task-vv`, R5 `sw-integrator`, R6 `sw-architect` | ❌ phải tạo |
| `tools/task.py` (cấp mã), `tools/board.py`, `tools/gate.py` | ❌ phải viết |
| Mẫu task: mục *Kết quả V&V*, *Cổng phát hành* + trạng thái mở rộng | ❌ phải sửa (R1) |
| `docs/01_Requirement/non_functional_requirements.md` tách riêng | ❌ phải tách (R6) |
| `CHANGELOG.md` | ❌ phải tạo (R5) |

## 6. Giao với kiến trúc C++

Kế thừa từ `../03_CPP_Port_Architecture/10_process_architecture_6_roles.md`:
6 vai trò, ownership matrix, artifact flow, 5 cổng, 3 điểm duyệt người dùng.

Khác ở chỗ (vì đây là repo Python đang chạy):
`pytest/pyflakes` thay `ctest/clang-tidy`; **tuần tự một checkout** thay worktree +
CI gates (ADR-0011, ADR-0013); báo cáo nằm trong tệp task (ADR-0012); không có
`CODEOWNERS` (chưa bật branch protection).
