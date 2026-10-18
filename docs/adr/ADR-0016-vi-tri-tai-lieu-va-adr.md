# ADR-0016 — Vị trí tài liệu quy trình và nơi đặt ADR

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án A**)
- **Liên quan**: [`../04_Process_Architecture/00_README.md`](../04_Process_Architecture/00_README.md)

## Bối cảnh

Repo đã có hệ tài liệu đánh số:

| Thư mục | Nội dung |
|---------|----------|
| `docs/01_Requirement/` | `requirements.md` (F1…F12, NF1…NF8) |
| `docs/02_System_SW_Architecture/` | C4 của **baseline Python** (context/container/component) |
| `docs/03_CPP_Port_Architecture/` | kiến trúc **mục tiêu bản C++** + 10 ADR (`docs/03_.../adr/ADR-0001…0010`) — hiện chưa commit |

Kiến trúc 6 vai trò vừa chốt áp cho **repo Python đang chạy**, nên không được trộn
vào `docs/03` (phạm vi C++). Cũng cần chỗ cho ADR mới, tránh đánh số đè lên
ADR-0001…0010 của bản C++.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| **A. `docs/04_Process_Architecture/` cho quy trình Python; ADR mới ở `docs/adr/` đánh số tiếp 0011+ (đã chọn)** | tách bạch Python/C++; một dãy số ADR liền mạch về sau (bản C++ chuyển 0001…0010 vào `docs/adr/` khi port) | thêm một thư mục |
| B. Gộp vào `docs/03_CPP_Port_Architecture/` | một chỗ duy nhất | lẫn phạm vi; tài liệu C++ chưa commit, dễ rối |
| C. Thư mục `docs/process/` không đánh số | ngắn | phá vỡ quy ước đánh số `01/02/03` đang dùng |

## Quyết định

Chọn **A**:

1. `docs/04_Process_Architecture/` chứa:
   `00_README.md`, `10_process_architecture_6_roles.md`, `nfr_process.md`,
   `30_ke_hoach_ap_dung.md`.
2. ADR của repo này đặt ở **`docs/adr/`**, đánh số **tiếp dãy chung**: bắt đầu
   `ADR-0011`. ADR-0001…0010 (bản C++) giữ nguyên ở `docs/03_.../adr/` cho tới khi
   port; khi port xong sẽ chuyển vào `docs/adr/` (đã ghi trong checklist của bản C++).
3. NFR quy trình ở `docs/04_.../nfr_process.md`; NFR sản phẩm tách riêng ra
   `docs/01_Requirement/non_functional_requirements.md` (việc của đợt 1).
4. Thay đổi kiến trúc quy trình sau này → **ADR mới** (0018, 0019…), không sửa ADR cũ.

## Hệ quả

**Tốt**: đọc `docs/` là thấy rõ hai phạm vi; R6 có vùng ghi riêng, không đụng mã.

**Xấu (chấp nhận)**: người mới phải biết `docs/03` là C++ (chưa thực thi) còn
`docs/04` mới là quy trình đang chạy → đã ghi rõ ở `00_README.md` của cả hai.

## Xác nhận thực hiện đúng

- Không có tệp ADR nào trùng số giữa `docs/adr/` và `docs/03_.../adr/`.
- `docs/04_Process_Architecture/00_README.md` trỏ đúng đường dẫn tới từng ADR.
