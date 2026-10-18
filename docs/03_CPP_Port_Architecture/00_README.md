# Kiến trúc C++ (C++ Port) — Phần Mềm Xem Ảnh

## Phạm vi

Kiến trúc **mục tiêu** cho việc port ứng dụng từ Python/PySide6 sang **C++/Qt 6**,
cùng với **kiến trúc quy trình cho 6 vai trò agent làm việc song song** trên repo.

Kiến trúc này chốt ngày 2026-10-18, sau khi đối chiếu mã nguồn Python hiện tại
(xem `docs/02_System_SW_Architecture/` — bản C4 của baseline Python) và chốt 4
quyết định lớn với chủ dự án (đã ghi nhận trong từng ADR).

## Hai trục kiến trúc

| Trục | Mô tả | Tài liệu |
|------|-------|----------|
| **Sản phẩm** (mã C++) | Ứng dụng desktop Qt 6, kiến trúc 4 tầng core → ai → gui → platform | `c4_cpp_context.md`, `c4_cpp_container.md`, `c4_cpp_component.md` |
| **Quy trình** (6 agent) | PM/SE · Dev · V&V · QA · Integrator · Architect, làm song song qua basebranch + ownership matrix + CI gates | `10_process_architecture_6_roles.md` |
| **Quyết định kiến trúc** | 10 ADR, 4 quyết định đã chấp nhận, 6 đề xuất chờ duyệt | `adr/` |
| **Yêu cầu phi chức năng** | NFR đo được cho bản C++, thay thế NF của baseline Python | `nfr_cpp.md` |

## Tổng hợp quy trình (mô tả bằng văn bản)

```
Người dùng
  │
  │ (yêu cầu mới / báo lỗi)                    ┌─────────────────────┐
  ▼                                            │  6 SW-Architect      │
┌──────────────────────┐                       │  ADR + NFR           │
│ 1 Task-Planning (PM) │ ─── FR + TASK ───────►│  (khi task đụng      │
│  SE / Project Mgr    │     (tasks/)          │   kiến trúc)         │
└──────────┬───────────┘                       └─────────────────────┘
           │ task đã duyệt                            ▲
           ▼                                          │ (theo dõi, review kiến trúc)
┌──────────────────────┐   code + unit test   ┌──────────────────────┐
│ 2 Task-Implementation│ ────────────────────►│ 3 Task-V&V           │
│ (SW Developer)       │   (feature/task-NNN) │ (System Test Eng.)   │
└──────────┬───────────┘                      │ functional test case │
           │ summary báo cáo                  │ chạy + báo cáo        │
           ▼                                  └──────────┬───────────┘
┌──────────────────────┐  nhận report R2+R3  ┌──────────────────────┐
│ 4 SW-Release-QA      │ ◄───────────────────┘ (report V&V)         │
│ (QA Engineer)        │ ─── verdict ĐỦ/CHƯA ĐỦ PHÁT HÀNH ──► người dùng duyệt
└──────────┬───────────┘
           │ người dùng OK
           ▼
┌──────────────────────┐
│ 5 SW-Integrator      │  squash merge → main, tag, CI, build .exe,
│ (DevOps / Integrator)│  phát hành (release notes, changelog)
└──────────────────────┘
```

Mô tả chi tiết (input/output artifact, gates, quyền ghi) — xem
`10_process_architecture_6_roles.md`.

## Roadmap port (5 đợt)

| Đợt | Nội dung | Đầu ra |
|-----|----------|--------|
| **M0 — Nền móng** | Repo `PhanMemXemAnh-Cpp`, CMake + vcpkg, CI xanh (build + GoogleTest + coverage), 6 agent cùng pipeline mở, chuẩn hoá tiếng Việt trong code | CI xanh trên `main` rỗng |
| **M1 — Core không Qt** | `core/gallery`, `core/imaging`, phiên bản GoogleTest full coverage (không màn hình) | Tính được danh sách ảnh, decode + LRU cache |
| **M2 — UI tối thiểu** | `gui/mainwindow`, `gui/image_view`, phím tắt, zoom/pan/xoay, slideshow → thay được phần lớn chạy hàng ngày | .exe dùng được, đối chiếu hành vi với bản Python |
| **M3 — AI** | port `loc_nu`: YuNet + 2 classifier ONNX, giữ cache delta, `FilterWorker` thread | Lọc nữ đúng bằng bản Python trên cùng thư mục |
| **M4 — Hoàn thiện & phát hành** | Slideshow, help, Aero blur, fullscreen, toast, welcome, đóng gói CPack/NSIS, `check_exe.py`, QG report đầu tiên | Bản phát hành v1.0-cpp |

## Rủi ro lớn (register rút gọn)

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|--------|----------|------------|
| Qt 6 không chạy trên Windows 7 (baseline Python chạy được) | mất người dùng Win7 | Ghi nhận trong NFR: chấp nhận Windows 10 1809+; đã cân nhắc Qt 5.15 LTS trong ADR-0001 rồi loại vì ecosystem |
| Port sai hành vi lọc nữ (khác baseline: ngưỡng, resize, normalize) | lọc sai ảnh | ADR-0006: test so sánh giá trị với bản Python trên bộ ảnh mẫu cố định, chạy trong CI (mock model trong unit, model thật trong job định kỳ) |
| onnxruntime C++ API khác phức tạp hơn Python API | tốc độ port | ADR-0004: bọc `IGenderInference` interface, tách cache/delta khỏi engine để đối chiếu được |
| God class tái phát | khó test, khó review | ADR-0005: ràng buộc "component ≤ ~500 dòng, mỗi component một trách nhiệm" + kiểm include trong CI bằng clang-tidy |
| 6 agent đụng file | merge conflict chồng chất | ADR-0009: ownership matrix + 1 task 1 nhánh + CI gate |

## Tình trạng phê duyệt

- ADR-0001 … ADR-0004: **ĐÃ CHẤP NHẬN** (người dùng chốt ngày 2026-10-18).
- ADR-0005 … ADR-0010: **ĐỀ XUẤT** — chờ người dùng duyệt từng cái trước khi code theo hướng đó.
- Cập nhật kiến trúc: được nhằm chỉnh thay đổi ranh giới module đều phải bổ sung ADR mới (không sửa ADR cũ), rồi người dùng duyệt lại ADR mới đó.
