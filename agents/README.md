<!-- SINH TỰ ĐỘNG từ tools/agents.py doc — đừng sửa tệp này: sửa bản gốc rồi chạy `uv run python tools/agents.py sync` -->

# agents/ — nơi chứa agent

Mỗi agent là một tệp `agent-<tên>.md` (một tệp một agent). Tên tệp chính là tên gọi agent, nên viết chữ thường không dấu: `agent-task-planning.md` → gọi `task-planning`.

Sửa xong thì chạy `uv run python tools/agents.py sync` để OpenCode thấy; `.opencode/agents/` là bản sinh tự động, không sửa tay.

| Agent | Chế độ | Quyền chặn | Mô tả |
|---|---|---|---|
| `sw-release-qg-check` | all | edit (trừ reports/*), shell (24 lệnh chặn), subagent | Cổng kiểm định chất lượng phát hành (SW release QG check) — REVIEW báo cáo của task-implementation: đối chiếu với task của task-planning và nêu ≤5 điểm cần cải thiện theo ưu tiên; tóm tắt tài nguyên (RAM/CPU/đĩa) trung bình và đỉnh; độ phủ + cảnh báo mã; kết quả kiểm thử chức năng Pass/Fail kèm lý do, rồi kết luận Đủ/Chưa đủ điều kiện phát hành. KHÔNG chạy lại test hay đo đạc. Gọi sau khi một task đã làm xong. |
| `task-implementation` | all | shell (6 lệnh chặn) +2 lệnh hỏi, subagent | Thực thi một task đã chốt trong tasks/ — tạo nhánh feature/… hoặc bugfix/… từ main mới nhất, code + chạy test tới khi đạt cổng chất lượng của dự án, tóm tắt kết quả và hỏi người dùng xác nhận, rồi squash và merge vào main (không tạo pull request). |
| `task-planning` | all | edit (trừ tasks/*), shell, subagent | Làm rõ yêu cầu trước khi code — dùng khi người dùng yêu cầu MỘT TÍNH NĂNG MỚI hoặc SỬA MỘT LỖI. Đặt câu hỏi cho rõ rồi tạo file task tasks/TASK-NNN-ten-ngan.md (không tự sửa code). |

## Lệnh quản lý

```bat
uv run python tools\agents.py list            :: xem danh sách
uv run python tools\agents.py new <tên>      :: tạo agent mới từ mẫu
uv run python tools\agents.py sync           :: sinh bản cho OpenCode
uv run python tools\agents.py check          :: kiểm tra hợp lệ + lệch bản
uv run python tools\agents.py rename <cũ> <mới>
uv run python tools\agents.py rm <tên>
```
