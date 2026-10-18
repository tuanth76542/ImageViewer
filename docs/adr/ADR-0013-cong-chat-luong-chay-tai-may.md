# ADR-0013 — Cổng chất lượng chạy tại máy dev (CI chỉ tham chiếu)

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHỐT (người dùng chọn **phương án C** trong bảng phương án)
- **Liên quan**: `.github/workflows/ci.yml` (đã có trên `main` từ PR #2)

## Bối cảnh

Repo đã có CI GitHub Actions (`windows-latest`: `uv sync --group dev` → `uv run
pytest` → `pyflakes` → upload report) nhờ PR #2. Máy dev rất yếu. Câu hỏi: cổng
chất lượng nào là **điều kiện chặn merge**, và ai chạy nó?

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|----------|----------|
| A. CI là cổng bắt buộc + script local `tools/gate.py` chạy y hệt | một chuẩn duy nhất, log công khai trên GitHub | phải chờ CI (hàng đợi runner), máy yếu vẫn phải tự chạy để biết sớm |
| B. Chỉ local | nhanh nhất | không có log thứ ba; dễ quên |
| **C. Cổng chính thức chạy tại máy; CI giữ làm lớp tham chiếu (đã chọn)** | phù hợp máy yếu + thói quen hiện tại; CI vẫn bắt được hồi quy khi push | kỷ luật hoàn toàn do vai R4/R5 giữ; nếu quên chạy cổng thì không ai chặn |

## Quyết định

Chọn **C**:

1. **Cổng chính thức = bộ lệnh chạy tại máy dev**, ghi bằng chứng vào tệp task:
   `uv run pytest` (kèm `--cov-fail-under=80` có sẵn trong `pyproject.toml`),
   `uv run --with pyflakes python -m pyflakes <tệp đã sửa>`,
   `uv run python -m compileall -q <tệp đã sửa>`, và nếu đụng mã app:
   `build_exe.bat` + `uv run python tools\check_exe.py`.
2. **`tools/gate.py`** (R5 viết) gói đúng bộ lệnh trên thành **một lệnh duy nhất**
   để không quên bước nào. Đây vẫn là công cụ **local**, không phải CI.
3. **CI GitHub Actions giữ nguyên** như lớp tham chiếu: chạy khi push `main` /
   mở PR; đỏ **không** chặn merge nhưng phải được nêu trong báo cáo R4 nếu có.
4. Không bật branch protection (cần quyền GitHub + làm chậm máy yếu).

## Hệ quả

**Tốt**: vòng lặp nhanh (pytest ~16 s), không phụ thuộc mạng/runner; CI vẫn là lưới
an toàn khi push.

**Xấu (chấp nhận)**: `main` có thể chứa commit chưa từng qua CI xanh; nếu quên chạy
`tools/gate.py` thì lỗi chỉ lộ ra ở lần chạy sau. Giảm thiểu: R4 kiểm **bằng chứng
cổng** trong tệp task trước khi cho phát hành (NF-P2).

## Xác nhận thực hiện đúng

- Mỗi task có khối output cổng local trong mục *Kết quả thực hiện (R2)*.
- `tools/gate.py` cho kết quả **giống** CI (cùng lệnh, cùng ngưỡng).
