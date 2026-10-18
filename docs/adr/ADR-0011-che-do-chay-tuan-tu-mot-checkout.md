# ADR-0011 — Chế độ chạy: một checkout, các vai chạy tuần tự

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án B**)
- **Liên quan**: [`../04_Process_Architecture/10_process_architecture_6_roles.md`](../04_Process_Architecture/10_process_architecture_6_roles.md) mục 4

## Bối cảnh

Yêu cầu: 6 vai trò làm việc **đồng thời** trên cùng một repo. Máy dev rất yếu
(i7-6600U 2 nhân/4 luồng, 8 GB RAM), `.venv` và `models/` (409 MB) dùng chung.
Thực tế ngày 2026-10-18 đã xảy ra sự cố: hai phiên agent cùng dùng một checkout —
một phiên để cây bẩn ở nhánh `docs/c4-architecture` (`docs/03_CPP_Port_Architecture/`
chưa commit) trong khi phiên khác đang merge vào `main`.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| A. 1 task = 1 `git worktree`, `.venv` dùng chung qua `UV_PROJECT_ENVIRONMENT`, model ở `%LOCALAPPDATA%` | song song thật; cách ly cây làm việc | phải quản nhiều thư mục; `uv`/pytest dễ lẫn môi trường; máy 2 nhân chạy 2 pytest là nghẽn |
| **B. Một checkout, các vai chạy tuần tự (đã chọn)** | không conflict, không tốn đĩa, dễ hiểu, hợp máy yếu | không song song vật lý; phải kỷ luật "một phiên một lúc" |
| C. Clone riêng mỗi vai | cách ly tuyệt đối | ~1,5 GB mỗi bản; quá nặng với máy 8 GB |

## Quyết định

Chọn **B**:

1. **Một checkout duy nhất** cho mọi vai; dùng chung `.venv`, `uv.lock`, `models/`.
2. **Mỗi thời điểm chỉ một vai chạy**; phiên chính giữ "lượt", chỉ gọi vai kế tiếp
   khi vai trước đã xong và đã ghi artifact.
3. **`git status` phải sạch đầu mỗi lượt**; bẩn thì dừng, báo người dùng — không tự
   `stash`/`commit` hộ thay đổi của phiên khác.
4. **Không mở hai phiên agent cùng lúc** trên repo này.
5. Các bước nặng (`pytest`, `build_exe.bat`, đo tài nguyên) mặc nhiên tuần tự.

## Hệ quả

**Tốt**: không có nguy cơ conflict/lock; không phát sinh dung lượng; thời gian vào
việc của vai mới thấp; phù hợp máy yếu.

**Xấu (chấp nhận)**:

- Không có song song vật lý → hai task độc lập vẫn phải xếp hàng; tổng thời gian
  bằng tổng các bước.
- Nếu người dùng vẫn mở thêm phiên (như sự cố 18/10), kiến trúc không tự chặn được
  — chỉ có kỷ luật + `git status` đầu lượt phát hiện.
- Khi cần song song thật (nhiều task độc lập) phải **mở ADR mới** để chuyển sang
  worktree; thiết kế phương án A đã có sẵn trong ADR này để dùng lại.

## Xác nhận thực hiện đúng

- Kiểm được: trong một vòng 6 vai, mọi lượt đều bắt đầu bằng `git status` sạch và
  chỉ có một vai ghi tệp.
- Kiểm được: dung lượng repo không tăng thêm ngoài `dist/` và `reports/`.
