# Kiến trúc quy trình: 6 vai trò agent làm việc song song

## 0. Mục tiêu

Cho phép **6 vai trò** làm việc đồng thời trên 1 repo (bản C++ mới — ADR-0003)
mà không đụng nhau, giao tiếp bằng **artifact trong git** (không chat), các cổng
chất lượng kiểm bằng CI, người dùng chỉ duyệt vào đúng 3 thời điểm.

Các vai trò:

| # | Vai trò | Bản chất đội ngũ | Agent OpenCode (tệp `agents/agent-<tên>.md`) |
|---|---------|------------------|---------------------------------------------|
| 1 | **Task-Planning** | Project Manager / System Engineer | `agent-task-planning.md` (đã có ở baseline) |
| 2 | **Task-Implementation** | SW Developer | `agent-task-implementation.md` (đã có ở baseline) |
| 3 | **Task-V&V** | System Test Engineer (Verification & Validation) | `agent-task-vv.md` (mới) |
| 4 | **SW-Release-QA** | QA Engineer | `agent-sw-release-qg-check.md` (baseline gọi là QG check; đổi tên) |
| 5 | **SW-Integrator** | SW Integrator / DevOps Engineer | `agent-sw-integrator.md` (mới) |
| 6 | **SW-Architect** | SW Architect | `agent-sw-architect.md` (mới) |

Vai trò "điều phối" (orchestrator) **không phải vai trò thứ 7** — nó là phiên
chính chạy theo `AGENTS.md` (giữ như baseline), nhiệm vụ duy nhất là chọn vai
trò nào tiếp theo theo trạng thái task.

## 1. Artifact flow — ai tạo gì, ở đâu

Mỗi vai trò giao tiếp **qua file trong git**, theo đường dẫn cố định. Quy tắc
"artifact là hợp đồng": không có artifact → không qua cổng.

| Artifact | Đường dẫn (repo mới) | Tạo / cập nhật bởi | Được đọc bởi |
|----------|----------------------|--------------------|--------------|
| **FR** (Functional Requirement) | `requirements/functional_requirements.md` + `requirements/FR-NN-*.md` | **R1 Task-Planning** | R2 R3 R4 R6, Người dùng |
| **NFR** (Non-Functional Requirement) | `requirements/non_functional_requirements.md` | **R6 SW-Architect** | R2 R3 R4, Người dùng |
| **Task file** | `tasks/TASK-NNN-*.md` | **R1 tạo**; R2, R3, R4 cập nhật **chỉ mục "Trạng thái" + mục "Kết quả" phần của mình** | mọi vai |
| **ADR** | `docs/adr/ADR-NNNN-*.md` | **R6 SW-Architect** | mọi vai, Người dùng |
| **C4 docs + kiến trúc** | `docs/architecture/` | **R6 SW-Architect** | mọi vai |
| **Code + unit test** | `src/`, `app/`, `tests/unit/` | **R2 Task-Implementation** | R3 R4 R6 |
| **Functional test case + QtTest** | `tests/vnv/cases/TC-NNN-*.md`, `tests/vnv/*.cpp` | **R3 Task-V&V** | R4, Người dùng |
| **Báo cáo thực thi (R2)** | mục `Kết quả thực hiện` trong `tasks/TASK-NNN-*.md` + `reports/impl/task-NNN.md` | **R2** | R3 R4 |
| **Báo cáo V&V (R3)** | `reports/vnv/task-NNN.md` | **R3** | R4 |
| **Báo cáo QG / release report** | `reports/qg/release/vM.N.md` | **R4 SW-Release-QA** | Người dùng (approve), R5 |
| **Workflow git + CI + tooling** | `.github/workflows/*`, `tools/*`, `CMakePresets.json`, thiết kế trong `docs/git_work_flow/` | **R5 SW-Integrator** | mọi vai |
| **Traceability matrix** | `requirements/traceability_matrix.md` | **R1 duy trì** (FR↔TC↔code); R3 điền cột TC | mọi vai |
| **Báo cáo đo tài nguyên** | `reports/resources/*.md` | **R3** (chạy `tools/measure_resources.py`) | R4 |

Cơ chế "ai được ghi file nào" (ownership matrix) — R5 cài vào `CODEOWNERS` +
CI check tên nhánh; chi tiết mục 3.

## 2. State machine của task

```
requested ──► [R1] viết FR, chốt FR ──► planned (TASK-NNN, Trạng thái: chờ làm)
planned   ──► [R2] tạo nhánh, Trạng thái: đang làm ──► implemented (R2 báo cáo + xin duyệt)
implemented ──► [R3] viết + chạy test case ──► verified (R3 báo cáo, ghi rõ lỗi nếu có)
verified  ──► [R4] release report ──► release_gate (Người dùng duyệt)
release_gate ──► [R5] squash merge + tag ──► released
```

Nhánh phụ (vòng sửa): bất kỳ cổng nào chưa đạt → quay lại vai trước với danh
sách việc cần sửa (ghi vào task file + report tương ứng), KHÔNG sửa code/phần
của vai khác.

**Người dùng chỉ duyệt tại 3 điểm** — giữ tinh thần baseline:

1. Duyệt **task** (sau R1, trước khi R2 code) — như baseline.
2. Duyệt **phương án ADR** (chỉ khi R6 mở phương án kiến trúc mới, ví dụ việc
   chọn framework) — điểm mới so với baseline, thêm cho R6.
3. Duyệt **merge vào main** (sau khi R4 kết luận "ĐỦ ĐIỀU KIỆN PHÁT HÀNH").

## 3. Ownership matrix (quyền GHI theo đường dẫn)

Quy tắc: **một đường dẫn có tối đa 1 vai trò được ghi**; vai khác chỉ đọc.
CI check qua `CODEOWNERS`.

| Đường dẫn | R1 | R2 | R3 | R4 | R5 | R6 |
|-----------|----|----|----|----|----|----|
| `requirements/functional_requirements.md`, `FR-*.md` | **GHI** | Đ | Đ | Đ | Đ | Đ |
| `requirements/non_functional_requirements.md`, `docs/adr/`, `docs/architecture/` | Đ | Đ | Đ | Đ | Đ | **GHI** |
| `tasks/TASK-NNN-*.md` | **GHI (tạo mới)** | GHI (chỉ mục Trạng thái + Kết quả của mình) | GHI (chỉ mục Trạng thái + Kết quả của mình) | GHI (chỉ mục Trạng thái + Kết quả của mình) | Đ | Đ |
| `src/`, `app/`, `tests/unit/`, `tests/fixtures-dev/` | Đ | **GHI** | Đ | Đ | Đ | Đ |
| `tests/vnv/`, `reports/vnv/`, `reports/resources/` | Đ | Đ | **GHI** | Đ | Đ | Đ |
| `reports/qg/` | Đ | Đ | Đ | **GHI** | Đ | Đ |
| `.github/workflows/`, `tools/`, `CMakePresets.json`, `docs/git_work_flow/`, `CODEOWNERS`, `vcpkg.json` | Đ | Đ | Đ | Đ | **GHI** | Đ |
| `CMakeLists.txt` | Đ | GHI (chỉ thêm target con, không đổi cấu trúc gốc) | Đ | Đ | **GHI (thay đổi cấu trúc)** | Đ |
| `README.md`, `AGENTS.md`, `agents/agent-*.md` | Đ | Đ | Đ | Đ | **GHI** (docs quy trình thuộc DevOps) | Đ |
| `reports/` (ngoài các mục trên) | Đ | Đ | Đ | Đ | Đ | Đ |

Giải quyết "đụng nhau" giữa các task:

- **Trùng component**: hai task đều sửa `src/xemanh/gui/mainwindow.*` → R5
  (Integrator) quyết thứ tự merge: cái trước merge trước, cái sau rebase trên
  `main` mới rồi mới vào cổng. Đây là lý do duy nhất cho phép R5 chặn merge.
- **Lệ thuộc khi một task cần kết quả của task khác**: ghi rõ vào mục "Ghi chú
  / rủi ro" của task file; task sau không được bắt trước khi task trước merge.

*(quy tắc chi tiết được đóng trong `docs/git_work_flow/merge_protocol.md` — R5
hoàn thành sau khi ADR-0009 được duyệt.)*

## 4. Git workflow (thiết kế do R5 phụ trách)

### 4.1 Các nhánh

| Mẫu nhánh | Ai tạo | Mục đích | Merge kiểu |
|-----------|--------|----------|------------|
| `main` | — | trunk, được CI chặn | không commit trực tiếp |
| `feature/task-NNN-<ten-ngan>` | R2 | tính năng mới / cải tiến | squash chỉ khi Người dùng OK |
| `bugfix/task-NNN-<ten-ngan>` | R2 | sửa lỗi | squash |
| `test/task-NNN-<ten-ngan>` | R3 (hiếm: khi test case độc lập với nhánh R2) | làm việc thí điểm song song với nhánh R2 | squash sau merge nhánh R2 |
| `ci/<ten-viec>` | R5 | thay đổi workflow git/CI/tooling | squash |
| `adr/adr-NNNN` | R6 | thêm ADR mới | squash (sau khi Người dùng duyệt phương án) |
| `docs/req-<ten>` | R1 | thêm FR | squash |

Baseline Python quy định "không dùng pull request; nhánh là việc nội bộ máy,
không push nhánh lên remote". Bản C++ giữ tinh thần đó: **nhánh làm việc
local, không push nhánh; merge vào main bằng squash**:

```
git checkout main; git pull --ff-only origin main      # BẮT BUỘC
git checkout -b feature/task-NNN-<ten-ngan> origin/main
... làm việc ...
[trình bày tóm tắt cho Người dùng, xin duyệt]
git checkout main && git merge --squash feature/task-NNN-<ten-ngan>
git -c user.name="<tên model agent đang chạy>" commit -m "TASK-NNN: ..."
git push origin main                                   # CI tự chạy full gate
```

Ràng buộc giữ nguyên từ baseline:

- Không `git push --force`, không `git reset --hard`, không rebase nhánh đã
  push, không tạo pull request.
- Commit do máy tạo: `user.name` là **tên model đang chạy** (giữ baseline).

### 4.2 CI gates (R5 cài đặt; vai khác không sửa file CI)

CI trên `main` (và cho phép chạy thủ công trên nhánh) phải xanh để task được
phát hành:

| Gate | Lệnh | Điều kiện xanh |
|------|------|----------------|
| Build | `cmake --preset release && cmake --build --preset release` | không lỗi |
| Unit test | `ctest --preset unit` | 100% PASS |
| Functional test (offscreen) | `QT_QPA_PLATFORM=offscreen ctest --preset functional` | 100% PASS |
| Coverage | OpenCppCoverage gắn từ ctest | ≥ 80% (sàn ADR-0006) |
| Lint | clang-format --dry-run + clang-tidy | 0 cảnh báo mới |
| Bundle smoke | `tools/check_exe.py` | sạch (giữ baseline) |
| Resources smoke | `tools/measure_resources.py` (không hard-fail, chỉ ghi trend) | RAM/CPU ngưỡng theo NFR |

## 5. Bảng gate tổng hợp

| Gate | Vai trigger | Ý nghĩa | Điều kiện qua |
|------|-------------|---------|---------------|
| **G1 — FR hợp lệ** | R1 | Người dùng duyệt task/FR mới | FR có ID, đo được; task có "Mục tiêu (đo được)", "Tiêu chí nghiệm thu" |
| **G2 — Code đủ chất lượng** | R2 | Unit + coverage + lint xanh | đạt mọi CI gates mục 4.2 |
| **G3 — V&V đạt** | R3 | Functional test case chạy đạt, defect được ghi | các TC liên quan PASS; defect (nếu có) có mã `DEF-NNN` và được theo dõi |
| **G4 — Đủ điều kiện phát hành** | R4 | Kết luận định lượng ("ĐỦ / ĐỦ NHƯNG CÓ ĐIỀU KIỆN / CHƯA ĐỦ") | release report của R4 đủ mục, số liệu có bằng chứng |
| **G5 — Released** | R5 | Merge thành công, tag `vX.Y` | CI trên main xanh, tag đã push, changelog cập nhật |

Ma trận RACI (ai chịu trách nhiệm gì ở từng gate):

| Gate | R1 | R2 | R3 | R4 | R5 | R6 |
|------|----|----|----|----|----|----|
| G1 | **R** | Consulted | Consulted | Informed | Informed | Consulted |
| G2 | Informed | **R** | Consulted | Informed | Informed | Consulted |
| G3 | Consulted | Consulted | **R** | Informed | Informed | Consulted |
| G4 | Informed | Informed | Consulted | **R** | Informed | Consulted |
| G5 | Informed | Informed | Informed | Consulted | **R** | Informed |
| ADR (mới) | Informed | Informed | Informed | Informed | Informed | **R** |

Người dùng là **Accountable** ở 3 điểm duyệt (mục 2), tức Gene quyết cuối cùng
dù vai nào chạy gate.

## 6. Làm việc song song — quy chế cụ thể

1. **Mỗi nhánh = một worktree riêng** (OpenCode `worktree_create`) khi chạy
   song song >1 task — tránh lock build/index, không dùng chung checkout.
2. **Task file là nguồn sự thật** cho mọi vai trong task đó; mỗi vai chỉ sửa
   mục của mình (Trạng thái / Kết quả / Báo cáo), không sửa mục vai khác.
3. Conflict component: R5 xếp thứ tự; phía sau rebase rồi merge.
4. Hai task cùng chạm "incompatible component" (ghi trong ADR) → phải đợi task
   trước xong (R5 quyết, người dùng biết).
5. Việc thuộc vai khác thì vai hiện tại KHÔNG tự làm — cập nhật artifact đúng
   vai (vd. defect phát hiện lúc R2 → ghi `DEF-NNN` vào task, để R3 rót test
   case; ADR lệch khi code → dừng, nhờ R6 mở ADR mới).

## 7. Giao với baseline Python

Kế thừa từ repo `PhanMemXemAnh` (Python):

1. `AGENTS.md`, 3 agent hiện có, tooling `tools/agents.py` (+18 test của tool)
   — copy sang repo mới rồi chỉnh scope, **thêm 3 agent mới**.
2. Quy ước commit (tác giả là tên model), "không PR / không force", merge khi
   người dùng OK — giữ nguyên (điểm duyệt đã liệt kê mục 2).
3. Bộ ảnh mẫu + cache JSON v2 cứng (`tests/fixture/`) — sao từ baseline (mục
   tiêu: giúp test đối chiếu Python↔C++ đúng kết quả, xem ADR-0006, ADR-0010).

## 8. Checklist khởi tạo (R5 chạy khi ADR-0009 được duyệt)

- [ ] Tạo repo `PhanMemXemAnh-Cpp` (ADR-0003)
- [ ] Copy `tools/` + `agents/` + `AGENTS.md` từ repo này, chỉnh lại đường dẫn
- [ ] Tạo 3 agent mới: `agent-task-vv.md`, `agent-sw-integrator.md`,
      `agent-sw-architect.md` + cập nhật description của `sw-release-qg-check`
      thành vai R4 (chạy `tools/agents.py new` + `sync` + `check`)
- [ ] Đặt `CODEOWNERS` theo ownership matrix mục 3
- [ ] Cài `.github/workflows/ci.yml` theo mục 4.2
- [ ] Chuyển 10 ADR từ `docs/03_CPP_Port_Architecture/adr/` sang `docs/adr/`
- [ ] Bootstrap `requirements/`, `tasks/`, `tests/fixture/`
