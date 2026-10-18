# ADR-0018 — Chính sách phát hành (tag + `CHANGELOG.md`) và ngoại lệ pull request

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng trả lời hai điểm mở ở
  `../04_Process_Architecture/30_ke_hoach_ap_dung.md` mục 2: **có** tag phiên bản +
  `CHANGELOG.md` mỗi release; **không** PR cho task thường, PR chỉ là ngoại lệ khi
  người dùng muốn xem diff)
- **Liên quan**: `../04_Process_Architecture/nfr_process.md` (NF-P6),
  `../04_Process_Architecture/30_ke_hoach_ap_dung.md` (đợt 3),
  `../../AGENTS.md`, ADR-0011, ADR-0013

## Bối cảnh

Kiến trúc quy trình 6 vai (ADR-0011…0017) đã chốt cách làm việc, nhưng còn **hai
điểm mở** phải người dùng quyết vì chúng đổi hành vi phát hành:

1. **Có tag phiên bản + `CHANGELOG.md` mỗi release không?** Hiện `main` chỉ có
   commit squash (1 commit/task, ADR-0011), không dấu vết nào cho biết "bản `.exe`
   đang phát hành là code ở thời điểm nào". NF-P6 ghi yêu cầu này nhưng cột "Phụ
   thuộc" còn treo vì chưa có quyết định.
2. **Có dùng pull request cho thay đổi lớn không?** Lịch sử repo có PR #1/#2 (CI,
   sao chép repo), nhưng máy dev yếu và quy trình hiện chạy thuần local (ADR-0013:
   cổng chính thức tại máy, CI chỉ tham chiếu) — nếu bắt buộc PR cho mọi task thì
   vòng lặp chậm và tốn thao tác GitHub.

## Phương án đã cân nhắc

### Điểm mở 1 — dấu vết phát hành

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. `CHANGELOG.md` + tag `vX.Y.Z` mỗi release (đã chọn)** | truy vết được bản `.exe` đã phát ↔ commit; `git tag` rẻ, không cần hạ tầng; NF-P6 hết treo | phải nhớ tăng số + viết 1 dòng changelog mỗi lần phát hành |
| B. Chỉ dựa vào `git log` trên `main` | không thêm việc gì | không biết commit nào ứng với bản phát hành/bản `.exe` người dùng đang có; NF-P6 không thoả |
| C. Tag tự động theo CI khi push `main` | không phải gõ tay | máy yếu + CI chỉ tham chiếu (ADR-0013) → tag sinh ra cả khi cổng local chưa từng chạy; khó sửa khi sai |

### Điểm mở 2 — pull request

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. Không PR cho task thường; PR là ngoại lệ có ghi chú trong tệp task (đã chọn)** | vòng lặp nhanh trên máy local; diff vẫn xem được bằng `git diff main..HEAD`; khi cần review trên GitHub thì vẫn mở được PR | không có "cổng" review tự động trên GitHub cho thay đổi lớn |
| B. Bắt buộc PR cho thay đổi lớn (CI, quy trình) | có chỗ bình luận/diff công khai | chờ runner + thao tác GitHub cho mỗi lần; lệch với "cổng chạy tại máy" (ADR-0013) |
| C. Cấm PR hoàn toàn | đơn giản nhất | mất khả năng review diff trên GitHub khi người dùng muốn |

## Quyết định

Chọn **A** ở cả hai điểm mở:

1. **Phát hành có dấu vết**: mỗi lần phát hành thật (người dùng duyệt ở G4 → R5
   merge ở G5) thì
   - ghi một mục vào `CHANGELOG.md` (ngày, mã task, thay đổi người dùng thấy được);
   - tạo tag **`vX.Y.Z`** (`v0.1.0`, `v0.1.1`, …) trên commit squash đó.
   Chỉ **R5 `sw-integrator`** làm việc này, cùng lúc với `git push origin main`.
   Chi tiết thi hành nằm ở **đợt 3** của `30_ke_hoach_ap_dung.md` (`CHANGELOG.md` được
   tạo ở đợt 3; task nào cũng vậy — quyết định đã có hiệu lực từ ADR này).
2. **PR là ngoại lệ**: quy trình mặc định **không dùng pull request** (nhánh là việc
   nội bộ trên máy, không push nhánh). Ngoại lệ được phép khi **người dùng muốn xem
   diff trên GitHub** — khi đó tệp task phải ghi rõ "có PR" và lý do; PR vẫn không
   thay cổng local (ADR-0013: cổng chính thức chạy tại máy dev).
3. `nfr_process.md` NF-P6 bỏ cột "Phụ thuộc" treo: từ nay phụ thuộc **ADR-0011 +
   ADR-0018**, và cách xác minh là `git tag` + `git log --first-parent main`.

## Hệ quả

**Tốt**: mỗi bản phát hành có dấu vết kiểm được bằng `git tag` và `CHANGELOG.md`;
`main` vẫn sạch 1 commit/task; người dùng giữ được quyền xem PR khi cần mà không
phải chờ runner cho mọi task.

**Xấu (chấp nhận)**: thêm một bước thủ công cho R5 mỗi release (dễ quên → NF-P6 và
review của R4 là lưới bắt); khi có PR thì nội dung trên GitHub có thể lệch thời điểm
với commit squash cuối cùng trên `main` (PR là để xem, không phải nguồn sự thật).

## Xác nhận thực hiện đúng

- `AGENTS.md` ghi rõ: chỉ R5 merge `main`, không PR cho task thường, PR là ngoại lệ
  có ghi chú; phát hành kèm tag + `CHANGELOG.md`.
- `30_ke_hoach_ap_dung.md` mục 2 đánh dấu hai điểm mở **đã chốt** (trỏ về ADR này);
  không còn mục "cần người dùng quyết" treo.
- `nfr_process.md` NF-P6 trỏ về ADR-0018, không còn phụ thuộc chưa chốt.
- Khi đợt 3 làm xong: `git tag` có `v0.1.x` và `CHANGELOG.md` có mục tương ứng.
