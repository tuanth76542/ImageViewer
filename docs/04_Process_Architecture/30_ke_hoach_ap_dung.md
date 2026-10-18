# Kế hoạch áp dụng kiến trúc quy trình 6 vai trò

> Trạng thái: **chờ người dùng mở task** (theo ADR-0011 … ADR-0017).
> Mọi thay đổi hành vi (tạo agent, sửa mẫu task, thêm công cụ) đều phải đi qua
> quy trình task của dự án: `task-planning` → người dùng xác nhận → `task-implementation`.

## 0. Việc dọn dẹp phải làm trước

| # | Việc | Lý do |
|---|------|-------|
| 1 | `git pull` cho `main` (đang behind `origin/main` = `3a58783` — CI đã vào main qua PR #2) | tránh merge trên nền cũ |
| 2 | Commit phần đang treo của phiên `docs/c4-architecture`: `docs/03_CPP_Port_Architecture/**` (chưa commit) + `docs/02_System_SW_Architecture/README.md` (sửa dở) | đang có công sức chưa lưu trong git |
| 3 | Xác nhận **không còn phiên agent nào khác** đang chạy trên repo | ADR-0011: chỉ một phiên |

## 1. Các đợt áp dụng (đề xuất thành task)

### Đợt 1 — Tài liệu kiến trúc (R6)
- Đầu ra: `docs/04_Process_Architecture/**` + `docs/adr/ADR-0011…0017` (đã soạn xong
  trong lần này) + tách `docs/01_Requirement/non_functional_requirements.md`.
- Điều kiện xong: `tools/agents.py check` vẫn sạch; không đụng mã app.

### Đợt 2 — Hạ tầng quy trình (R5 + R1)
- Tạo 3 agent mới: `task-vv`, `sw-integrator`, `sw-architect`; đổi tên
  `sw-release-qg-check` → `sw-system-release` (`uv run python tools\agents.py rename`).
- Viết `tools/task.py` (cấp mã `TASK-NNN` không trùng), `tools/board.py` (sinh
  `tasks/BOARD.md`), `tools/gate.py` (chạy đúng bộ cổng local).
- Sửa mẫu task + `tasks/README.md`: thêm trạng thái `chờ V&V`, `đang V&V`,
  `chờ release`; thêm mục *Kết quả V&V*, *Cổng phát hành*.
- Cập nhật `AGENTS.md` (quy trình 6 vai + 3 điểm duyệt + ai merge).
- Điều kiện xong: `uv run pytest` xanh; `tools/agents.py check` sạch; 6 agent hiện
  trong `agents/README.md`.

### Đợt 3 — Integrator (R5)
- Thêm `CHANGELOG.md`; cài quy chế nhánh (mục 4 tài liệu quy trình) vào `AGENTS.md`.
- (Tùy chọn) mở rộng CI: cache `uv`, job build `.exe` + `check_exe` khi có tag —
  chỉ mang tính tham chiếu (ADR-0013).
- (Tùy chọn) `CODEOWNERS` + branch protection trên GitHub nếu người dùng muốn.

### Đợt 4 — Vận hành thử một vòng đủ 6 vai
- Chọn một yêu cầu nhỏ thật (ví dụ: chặn luồng lọc cũ khi mở thư mục khác), chạy
  đủ R1 → R2 → R3 → R4 → R5 và đo lại các NFR quy trình.

## 2. Điểm mở (chưa chốt — cần người dùng quyết)

| # | Câu hỏi | Đề xuất của R6 |
|---|---------|----------------|
| (a) | Có dùng **pull request** cho thay đổi lớn (CI, quy trình) như PR #1/#2 vừa rồi? | Không PR cho task thường (theo `AGENTS.md`); **được phép** PR khi bạn muốn xem diff trên GitHub — ghi rõ trong task |
| (b) | Có **tag phiên bản** + `CHANGELOG.md` mỗi release? | Có: `v0.1.0`, `v0.1.1`… rẻ, giúp truy vết bản `.exe` đã phát |
| (c) | `reports/` giữ gitignored? | Giữ (ADR-0012); chỉ báo cáo kết luận nằm trong tệp task |

## 3. Rủi ro khi áp dụng

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Chế độ tuần tự làm mất tính "song song" người dùng mong đợi | Nói rõ trong `00_README.md`; khi cần song song thật thì mở ADR mới chuyển sang worktree (đã có thiết kế sẵn ở ADR-0011 phương án A) |
| Chia việc test cho R3 làm chậm vòng lặp nhỏ | Cho phép task nhỏ ghi rõ "R3 gộp vào G2" nếu người dùng đồng ý trong tệp task |
| Cổng chỉ chạy local → quên chạy trước khi merge | `tools/gate.py` một lệnh duy nhất + R4 kiểm bằng chứng trong tệp task |
| Thêm 3 agent làm `AGENTS.md` phình to | Tài liệu quy trình đặt ở `docs/04_Process_Architecture/`, `AGENTS.md` chỉ trỏ tới |
