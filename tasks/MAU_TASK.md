<!-- Mẫu task — NGUỒN DUY NHẤT (ADR-0015 mục 3).

     Agent R1 (`agents/agent-task-planning.md`) và công cụ `tools/task.py` đều dùng
     tệp này; đừng chép lại mẫu sang chỗ khác, `uv run python tools\agents.py check`
     sẽ bắt lỗi lệch nguồn.
     Cấp mã + tạo tệp: `uv run python tools\task.py new "<tên-ngắn>"`. -->

# TASK-NNN — <Tên việc>

- **Ngày tạo**: <YYYY-MM-DD>
- **Loại**: tính năng mới / sửa lỗi / cải tiến
- **Trạng thái**: chờ làm
- **Người yêu cầu**: <tên hoặc "chủ dự án">

Vòng đời `Trạng thái` (dòng trên đúng một giá trị):
`chờ làm` → `đang làm` → `chờ V&V` → `đang V&V` → `chờ release` → `xong`
(hoặc `tạm hoãn` / `bỏ`, kèm lý do ngắn).

## 1. Yêu cầu gốc

> <chép nguyên văn yêu cầu của người dùng>

## 2. Mục tiêu (đo được)

- <mỗi dòng một kết quả kiểm chứng được, tránh "cho đẹp hơn">

## 3. Phạm vi

- **Trong phạm vi**: …
- **Ngoài phạm vi**: … (nói rõ cái gì cố ý KHÔNG làm lần này)

## 4. Đã chốt với người dùng

| Câu hỏi | Chốt |
|---|---|
| … | … |

## 5. Còn mở

- <điểm chưa chốt, hoặc "không có">

## 6. Hướng làm & tệp dự kiến đụng tới

- `xemanh/<mô-đun>.py` — <sửa gì, vì sao>
- `tests/unit/<tệp>.py` — <thêm/sửa test gì>

## 7. Tiêu chí nghiệm thu

- [ ] <kiểm tra được: nhìn thấy gì, đo được gì>
- [ ] `uv run pytest` xanh (không làm hỏng test cũ)
- [ ] <nếu có đóng gói> `build_exe.bat` chạy được và `uv run python tools\check_exe.py` sạch

## 8. Kiểm thử

- Test mới/sửa: `tests/…`
- Lệnh: `uv run pytest` (thêm `-m functional` khi cần)
- Kiểm tra tay (nếu là việc giao diện): <các bước bấm/chuột cụ thể>

## 9. Việc cần làm

- [ ] <bước 1, nhỏ, làm được ngay>
- [ ] <bước 2>

## 10. Ghi chú / rủi ro

- <task liên quan, giới hạn đã biết, chỗ dễ vỡ>

## Kết quả thực hiện (R2)

- <R2 điền khi code xong: việc đã làm, tệp đã sửa, số liệu cổng chất lượng
  (pytest, độ phủ, pyflakes, `tools\gate.py`), lý do bỏ qua build `.exe` nếu có>

## Kết quả V&V (R3)

- <R3 điền khi chạy V&V: bảng test chức năng Pass/Fail kèm lý do; defect `DEF-NNN`
  kèm cách lặp lại; phần chưa kiểm được>

## Cổng phát hành (R4)

- <R4 điền khi kiểm định: kết luận `ĐỦ` / `ĐỦ NHƯNG CÓ ĐIỀU KIỆN` / `CHƯA ĐỦ`,
  kèm ≤5 điểm cần cải thiện theo thứ tự ưu tiên và bằng chứng đã đọc>
