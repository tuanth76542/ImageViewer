<!-- SINH TỰ ĐỘNG từ tools/agents.py doc — đừng sửa tệp này: sửa bản gốc rồi chạy `uv run python tools/agents.py sync` -->

# agents/ — nơi chứa agent

Mỗi agent là một tệp `agent-<tên>.md` (một tệp một agent). Tên tệp chính là tên gọi agent, nên viết chữ thường không dấu: `agent-task-planning.md` → gọi `task-planning`.

Sửa xong thì chạy `uv run python tools/agents.py sync` để OpenCode thấy; `.opencode/agents/` là bản sinh tự động, không sửa tay.

| Agent | Chế độ | Quyền chặn | Mô tả |
|---|---|---|---|
| `sw-architect` | all | edit (trừ docs/adr/*, docs/04_Process_Architecture/*, docs/02_System_SW_Architecture/*, docs/01_Requirement/non_functional_requirements.md), shell (5 lệnh chặn), subagent | Kiến trúc & quy trình (R6, SW Architect) — viết ADR (≥2 phương án, hệ quả tốt/xấu) ở docs/adr/, tài liệu kiến trúc ở docs/04_Process_Architecture/** và docs/02_System_SW_Architecture/**, NFR sản phẩm ở docs/01_Requirement/non_functional_requirements.md. Gọi khi cần quyết định kiến trúc, ranh giới module, quyền ghi hay chỉ số chất lượng. |
| `sw-integrator` | all | edit (trừ tools/*, agents/*, .opencode/agents/*, .github/workflows/*, .gitignore, AGENTS.md, CHANGELOG.md, PhanMemXemAnh.spec, build_exe.bat, chay.bat, tasks/*), shell (5 lệnh chặn) +2 lệnh hỏi, subagent | Tích hợp & phát hành (R5, Integrator/DevOps) — squash nhánh của task thành MỘT commit trên main, giữ lịch sử main sạch, chạy cổng local xanh trước khi merge, viết/tag CHANGELOG khi phát hành, và quản hạ tầng quy trình (tools/**, agents/**, AGENTS.md, .github/workflows/**, build_exe.bat, .gitignore). Gọi ở bước cuối (G5) sau khi người dùng duyệt phát hành. |
| `sw-system-release` | all | edit (trừ reports/release/*, tasks/*), shell (24 lệnh chặn), subagent | Cổng kiểm định chất lượng phát hành (R4, SW-System-Release) — REVIEW báo cáo của R2/R3 (chỉ ĐỌC, không chạy lại test/đo đạc) rồi ghi kết luận ĐỦ / ĐỦ NHƯNG CÓ ĐIỀU KIỆN / CHƯA ĐỦ vào mục *Cổng phát hành (R4)* trong tệp task: đối chiếu với task của task-planning và nêu ≤5 điểm cần cải thiện theo ưu tiên; tài nguyên (RAM/CPU/đĩa) trung bình và đỉnh; độ phủ + cảnh báo mã; kết quả kiểm thử chức năng Pass/Fail kèm lý do. Gọi sau khi task-implementation (R2) và task-vv (R3) đã xong. |
| `task-implementation` | all | shell (6 lệnh chặn) +2 lệnh hỏi, subagent | Thực thi một task đã chốt trong tasks/ — tạo nhánh feature/… hoặc bugfix/… từ main mới nhất, code + chạy test tới khi đạt cổng chất lượng của dự án, tóm tắt kết quả và hỏi người dùng xác nhận, rồi squash và merge vào main (không tạo pull request). |
| `task-planning` | all | edit (trừ tasks/*), shell (trừ uv run python tools\task.py*, uv run python tools/task.py*), subagent | Làm rõ yêu cầu trước khi code — dùng khi người dùng yêu cầu MỘT TÍNH NĂNG MỚI hoặc SỬA MỘT LỖI. Đặt câu hỏi cho rõ rồi tạo task bằng lệnh uv run python tools\task.py new (mã TASK-NNN không trùng, tệp sinh ra từ mẫu tasks/MAU_TASK.md; không tự sửa code). |
| `task-vv` | all | edit (trừ tests/functional/*, tests/conftest.py, tests/fixtures/*, tasks/*), shell (5 lệnh chặn), subagent | V&V (R3, System Test Engineer) — viết và CHẠY test chức năng (tests/functional/**, conftest.py, fixtures) theo đúng "Tiêu chí nghiệm thu" của tệp task, rồi ghi kết quả Pass/Fail kèm lý do và defect DEF-NNN vào mục *Kết quả V&V* trong tệp task. Gọi sau khi task-implementation (R2) báo xong. |

## Lệnh quản lý

```bat
uv run python tools\agents.py list            :: xem danh sách
uv run python tools\agents.py new <tên>      :: tạo agent mới từ mẫu
uv run python tools\agents.py sync           :: sinh bản cho OpenCode
uv run python tools\agents.py check          :: kiểm tra hợp lệ + lệch bản
uv run python tools\agents.py rename <cũ> <mới>
uv run python tools\agents.py rm <tên>
```
