# ADR-0014 — Phân chia viết test: R2 viết unit, R3 viết functional

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án A**)
- **Liên quan**: [`../04_Process_Architecture/10_process_architecture_6_roles.md`](../04_Process_Architecture/10_process_architecture_6_roles.md) mục 1

## Bối cảnh

Hiện nay **R2 (task-implementation) viết toàn bộ test** (unit + functional) rồi tự
chạy; vai R4 chỉ review lại báo cáo. Yêu cầu mới có thêm vai **R3 Task-V&V (System
Test Engineer)** chuyên viết **functional test case**, chạy và báo cáo. Bộ test hiện
có 224 test, 3 nhóm marker: `unit`, `functional`, `resources`; độ phủ C0/C1 ~99,9%
(ngưỡng `--cov-fail-under=80`).

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. R2 viết unit (`tests/unit/`), R3 viết + chạy functional (`tests/functional/`) + fixtures (đã chọn)** | tách "người viết code" khỏi "người kiểm chứng hành vi"; đúng vai System Test Engineer; giữ vòng lặp ngắn vì unit test vẫn do dev viết | một hành vi có thể cần cả 2 loại test → phải phối hợp qua tệp task |
| B. R3 viết toàn bộ test | độc lập cao nhất | dev không có test để tự kiểm khi code; vòng lặp dài, R3 thành nút cổ chai |
| C. Như hiện nay: R2 viết hết, R3 chỉ chạy lại | nhanh, ít thay đổi | "vừa đá bóng vừa thổi còi"; R3 gần như thừa |

## Quyết định

Chọn **A**:

| Vai | Vùng test | Nội dung |
|-----|-----------|----------|
| **R2** | `tests/unit/**`, `tools/bench_loc_nu.py` | unit test cho hàm/lớp vừa sửa; giữ test cũ xanh; cập nhật độ phủ |
| **R3** | `tests/functional/**`, `tests/conftest.py`, `tests/fixtures/**` | test chức năng chạy offscreen (Qt), test đầu-cuối trên thư mục ảnh giả lập, fixture dùng chung |
| **R4** | không viết test | chỉ review báo cáo (không chạy lại — quy tắc đã chốt với agent `sw-system-release`) |

Quy tắc phối hợp:

1. Mục *Tiêu chí nghiệm thu* trong tệp task là **hợp đồng** giữa R2 và R3: R3 viết
   test chức năng theo đúng các tiêu chí đó, **không** tự nghĩ thêm phạm vi.
2. R3 **không sửa** `tests/unit/**`; R2 **không sửa** `tests/functional/**`. Thiếu
   test ở vùng nào thì ghi yêu cầu vào tệp task cho vai đó.
3. Defect phát hiện ở G3 ghi mã `DEF-NNN` (mô tả + cách lặp lại) vào tệp task, trả
   về R2; R2 sửa xong thì R3 chạy lại.
4. Task rất nhỏ (sửa 1 dòng, đổi chữ) được phép ghi rõ trong tệp task là "R3 gộp
   vào G2, chỉ chạy lại bộ functional có sẵn" — phải được người dùng đồng ý tại G1.

## Hệ quả

**Tốt**: có người thứ hai thật sự kiểm hành vi; R2 vẫn tự kiểm nhanh bằng unit test;
phân vùng ghi rõ ràng nên không tranh chấp tệp.

**Xấu (chấp nhận)**: hai vai cùng chạm một hành vi → cần kỷ luật "hợp đồng là tiêu
chí nghiệm thu"; `tests/conftest.py` thuộc R3 nên khi R2 cần fixture mới phải yêu
cầu qua tệp task (chậm hơn một nhịp).

## Xác nhận thực hiện đúng

- `git diff --name-only` của một task cho thấy: R2 chỉ đụng `tests/unit/**`, R3 chỉ
  đụng `tests/functional/**` (+ `conftest.py`, `fixtures/`).
- Mỗi tiêu chí nghiệm thu trong tệp task có ít nhất một test chức năng trỏ về.
