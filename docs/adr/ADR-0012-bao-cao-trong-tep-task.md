# ADR-0012 — Báo cáo của từng vai nằm trong tệp task

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án C** trong bảng phương án)
- **Liên quan**: [`../04_Process_Architecture/10_process_architecture_6_roles.md`](../04_Process_Architecture/10_process_architecture_6_roles.md) mục 2

## Bối cảnh

Các vai bàn giao cho nhau bằng artifact trong git. Câu hỏi: báo cáo kết quả của
từng vai (R2 thực thi, R3 V&V, R4 cổng phát hành) để ở đâu để (a) phiên/vai khác
đọc được, (b) người dùng review được, (c) không sinh hàng chục tệp nhỏ?

Hiện trạng: báo cáo R2 nằm ở mục `## 9b. Kết quả thực hiện` của tệp task; `reports/`
bị `.gitignore` (chứa HTML coverage, CSV, ảnh chụp).

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| A. Mục riêng cho từng vai **trong tệp task** (đã chọn); bằng chứng nặng ở `reports/` (không commit) | một tệp/task là nguồn sự thật duy nhất; review một chỗ; không sinh thêm mã hiệu | tệp task dài dần; `reports/` không nằm trong git nên chỉ máy hiện tại thấy |
| B. Tất cả báo cáo trong `reports/` | tệp task gọn | `reports/` bị gitignore → **vai khác / sau này không đọc được**, mất tính "artifact là hợp đồng" |
| C. Thư mục tracked `docs/records/`, mỗi vai một tệp | tách bạch, trích dẫn được | nhiều tệp + phải cấp mã hiệu; nặng nề cho dự án một người |

## Quyết định

Chọn **A** (thực chất là "C" trong bảng lựa chọn phiên — giữ đúng cách làm hiện
nay, có chuẩn hoá):

- Tệp `tasks/TASK-NNN-*.md` có thêm mục cố định:
  `## Kết quả thực hiện (R2)`, `## Kết quả V&V (R3)`, `## Cổng phát hành (R4)`.
- Mỗi vai **chỉ ghi vào mục của mình**; vai khác không sửa (append-only).
- Bằng chứng nặng (coverage HTML, CSV đo tài nguyên, ảnh chụp màn hình) để ở
  `reports/` và **được tham chiếu bằng đường dẫn** từ mục báo cáo.
- Báo cáo kết luận ngắn (verdict, số liệu chính) **bắt buộc** nằm trong tệp task —
  đó là thứ R4 và người dùng đọc.

## Hệ quả

**Tốt**: đọc một tệp là hiểu toàn bộ lịch sử task; `git log`/`git diff` cho thấy
đúng artifact đã bàn giao; không thêm hạ tầng.

**Xấu (chấp nhận)**: tệp task dài (TASK-002 hiện ~200 dòng); `reports/` chỉ có trên
máy đang chạy — muốn chia sẻ bằng chứng nặng thì phải dán số liệu vào tệp task
(đúng như bản review TASK-002 vừa yêu cầu).

## Xác nhận thực hiện đúng

- Mọi câu hỏi "task này đạt chưa?" trả lời được bằng **một** tệp task.
- R4 không cần mở `reports/` để kết luận (dù có thể đọc thêm nếu muốn).
