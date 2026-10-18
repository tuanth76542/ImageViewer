# Kiến trúc quy trình — 6 vai trò trên repo Python (bản đang chạy)

## Phạm vi

Kiến trúc **quy trình làm việc** cho **chính repo này** (`PhanMemXemAnh`, Python +
PySide6): 6 vai trò (agent) cùng làm việc trên một repo, giao tiếp bằng **artifact
trong git**, cổng chất lượng chạy **tại máy dev**.

> Phân biệt: `../03_CPP_Port_Architecture/` là kiến trúc **mục tiêu cho bản port
> C++** (chưa thực thi). Thư mục này (`04_Process_Architecture/`) là bản **áp dụng
> cho repo Python đang chạy**, cùng tinh thần 6 vai trò nhưng khác công cụ
> (pytest/pyflakes/PyInstaller thay cho CMake/ctest/clang) và khác quy chế chạy.

## Người dùng đã chốt gì (2026-10-18)

| ADR | Quyết định đã chốt |
|-----|--------------------|
| [ADR-0011](../adr/ADR-0011-che-do-chay-tuan-tu-mot-checkout.md) | **Một checkout, các vai chạy TUẦN TỰ** (không worktree, không song song vật lý) |
| [ADR-0012](../adr/ADR-0012-bao-cao-trong-tep-task.md) | Báo cáo của từng vai nằm **trong tệp task**; bằng chứng nặng ở `reports/` (không commit) |
| [ADR-0013](../adr/ADR-0013-cong-chat-luong-chay-tai-may.md) | **Cổng chất lượng chạy tại máy dev**; CI GitHub Actions chỉ là lớp tham chiếu |
| [ADR-0014](../adr/ADR-0014-phan-chia-viet-test.md) | **R2 viết unit test**, **R3 viết + chạy functional test** + fixtures |
| [ADR-0015](../adr/ADR-0015-cap-ma-task-bang-cong-cu.md) | Cấp mã `TASK-NNN` bằng công cụ `tools/task.py` (chống trùng số giữa các phiên) |
| [ADR-0016](../adr/ADR-0016-vi-tri-tai-lieu-va-adr.md) | Tài liệu quy trình ở `docs/04_Process_Architecture/`, ADR ở `docs/adr/` (tiếp số 0011+) |
| [ADR-0017](../adr/ADR-0017-doi-ten-va-bo-sung-vai-tro.md) | Đổi tên `sw-release-qg-check` → `sw-system-release`; thêm `task-vv`, `sw-integrator`, `sw-architect` |

## Ba trục

| Trục | Nội dung | Tài liệu |
|------|----------|----------|
| **Quy trình** (6 vai) | Vai trò, quyền ghi, artifact, cổng, quy chế tuần tự | `10_process_architecture_6_roles.md` |
| **Yêu cầu phi chức năng** | NFR đo được cho quy trình (thời gian cổng, traceability, số lần duyệt…) | `nfr_process.md` |
| **Kế hoạch áp dụng** | Việc cần làm theo đợt + checklist | `30_ke_hoach_ap_dung.md` |

## Sơ đồ

```text
                    NGƯỜI DÙNG  (Accountable — duyệt đúng 3 điểm)
                        │ yêu cầu / báo lỗi
                        ▼
        ┌───────────────────────────────────────────┐
        │ PHIÊN CHÍNH (orchestrator theo AGENTS.md)  │ ← không phải vai thứ 7
        │ giữ "lượt": mỗi thời điểm chỉ 1 vai chạy   │
        └───────┬───────────────────────────────────┘
                ▼
   ┌────────────────────────┐  FR + TASK   ┌──────────────────────────┐
   │ R1 Task-Planning       │─────────────►│ R6 SW-Architect           │
   │ PM / System Engineer   │◄─────────────│ ADR · C4 · NFR            │
   └────────────┬───────────┘              └──────────────────────────┘
                │ [G1: người dùng duyệt task]        ▲ [ADR: người dùng chọn phương án]
                ▼                                     │
   ┌────────────────────────┐  code+unit test  ┌──────┴───────────────────┐
   │ R2 Task-Implementation │─────────────────►│ R3 Task-V&V               │
   │ SW Developer           │◄─────────────────│ System Test Engineer      │
   └────────────┬───────────┘  [G3]            └──────────┬───────────────┘
                │ [G2]                                    │
                ▼                                         ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ R4 SW-System-Release (QA) — review artifact R1..R3 (chỉ ĐỌC)     │
   │ verdict: ĐỦ / ĐỦ NHƯNG CÓ ĐIỀU KIỆN / CHƯA ĐỦ           [G4]      │
   └───────────────────────────────┬───────────────────────────────────┘
                                   │ người dùng duyệt phát hành
                                   ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ R5 SW-Integrator (DevOps) — squash vào main, cổng xanh, tag, note │
   └───────────────────────────────────────────────────────────────────┘
```

## Trạng thái phê duyệt

- **ADR-0011 … ADR-0017: ĐÃ CHỐT** ngày 2026-10-18 (người dùng chọn phương án
  trực tiếp trong phiên làm việc).
- Thay đổi ranh giới module, quyền ghi, hay cách chạy → **phải mở ADR mới** (đừng
  sửa ADR cũ), rồi người dùng duyệt ADR mới đó.
- Còn treo (chưa đủ để thành ADR, xem `30_ke_hoach_ap_dung.md` mục "Điểm mở"):
  dùng pull request hay không, có tag phiên bản mỗi release hay không.
