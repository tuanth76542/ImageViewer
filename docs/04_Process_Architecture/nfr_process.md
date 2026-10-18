# Yêu cầu phi chức năng cho QUY TRÌNH (NFR quy trình)

> Sở hữu: **R6 SW-Architect**. Trạng thái: **đã viết theo ADR-0011 … ADR-0018**
> (chốt 2026-10-18); **không còn điểm mở** treo ở cột "Phụ thuộc" — quyết định nào
> mới thay đổi chỉ số thì phải mở ADR mới và cập nhật cả bảng dưới đây.

Đây là NFR cho **cách làm việc** (quy trình), không phải cho sản phẩm. NFR của sản
phẩm nằm ở `../01_Requirement/non_functional_requirements.md` (NF1…).

## 1. Bảng NFR quy trình

| ID | Yêu cầu | Chỉ số đo (mục tiêu) | Cách xác minh | Phụ thuộc |
|----|---------|----------------------|---------------|-----------|
| NF-P1 | Mọi bàn giao giữa các vai đều để lại **artifact trong git** (không chỉ nói trong chat) | 100% task có mục báo cáo của vai đã chạy; `git log` khớp nội dung báo cáo | đọc tệp task + `git diff main..HEAD` | ADR-0012 |
| NF-P2 | **Cổng chất lượng chạy tại máy dev** và phải xanh trước khi merge | `uv run pytest` xanh + pyflakes sạch **trước** mỗi lần merge; CI chỉ tham chiếu, không chặn | log phiên chạy cổng trong tệp task | ADR-0013 |
| NF-P3 | **Chỉ một vai chạy tại một thời điểm**; không chạy chồng 2 `pytest`/2 `build_exe` | 0 lần chồng tiến trình nặng; `git status` sạch đầu mỗi lượt | `tasks/BOARD.md` + mắt thường khi chạy | ADR-0011 |
| NF-P4 | Không nhân bản tài nguyên nặng (`.venv`, `models/`) | đĩa tăng mỗi release < 200 MB (chủ yếu `.exe` trong `dist/`) | `Get-ChildItem` đo dung lượng | ADR-0011 |
| NF-P5 | Bộ cổng local chạy nhanh trên máy yếu (i7-6600U 2 nhân) | `tools\gate.py` ≤ **60 s** (hiện pytest ~16 s + pyflakes < 5 s) | `Measure-Command` | ADR-0013 |
| NF-P6 | Lịch sử `main` sạch: 1 task = **1 commit squash**; mỗi release có dấu vết | `git log --first-parent main` có đúng 1 commit/task; mỗi release có tag `vX.Y.Z` + mục `CHANGELOG.md` | `git log`, `git tag`, `CHANGELOG.md` | ADR-0011, ADR-0018 |
| NF-P7 | **Traceability**: mọi FR có ≥ 1 test chức năng trỏ về nó | bảng F↔test trong `docs/01_Requirement/requirements.md` đầy đủ | review của R4 | ADR-0014 |
| NF-P8 | Cổng không tải mạng, không dùng model thật, không cần màn hình | `uv run pytest` xanh khi offscreen, không mạng | chạy `pytest -m unit` / `-m functional` | ADR-0014 |
| NF-P9 | Không vai nào ghi ra ngoài vùng sở hữu (mục 1 của tài liệu quy trình) | 0 vụ vi phạm bị R4 bắt trong review | `git diff --name-only` đối chiếu bảng quyền ghi | ADR-0016 |
| NF-P10 | Người dùng chỉ phải duyệt **3 điểm** (task · ADR · phát hành) | số lần agent hỏi duyệt ≤ 3 cho một task trọn vẹn | đếm trong phiên | — |
| NF-P11 | Không có 2 phiên cùng ghi vào một checkout | 0 sự cố "cây bẩn khi sang lượt"; phát hiện bằng `git status` đầu lượt | `git status` + ghi chú trong `tasks/BOARD.md` | ADR-0011 |
| NF-P12 | Mỗi vai **không đọc quá nhiều** để vào việc | vai mới chỉ cần: `AGENTS.md` + tệp task + tài liệu quy trình này (< 500 dòng) | đọc thử và đo | ADR-0016 |

## 2. NFR bị thay thế so với bản C++ (`../03_CPP_Port_Architecture/nfr_cpp.md`)

| NFR bản C++ | Thay bằng ở đây | Lý do |
|-------------|-----------------|-------|
| NF3 "thời gian build ≤ 6 phút" | NF-P5 "cổng local ≤ 60 s" | Python không có bước compile; cổng là pytest + pyflakes |
| NF14 "CI tái lập trên runner" | NF-P2 "cổng chạy tại máy dev" | ADR-0013: CI chỉ tham chiếu |
| NF19 "main protected by CI" | NF-P6 + NF-P2 | Không bật branch protection; kỷ luật do R5 + cổng local |
| Cơ chế worktree cho song song | NF-P3 + NF-P11 (tuần tự 1 checkout) | ADR-0011 phương án B |

## 3. Quy tắc sửa NFR

Chỉ **R6 SW-Architect** sửa tệp này. Thay đổi lớn (đổi chỉ số, bỏ yêu cầu) phải đi
kèm **ADR mới** nêu lý do — đừng sửa thẳng số liệu.
