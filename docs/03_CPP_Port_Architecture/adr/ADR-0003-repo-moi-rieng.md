# ADR-0003 — Tổ chức repo: repo mới riêng cho bản C++

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHẤP NHẬN (chủ dự án chốt — lựa chọn khác so với đề xuất
  "cùng repo" được cân nhắc)
- **Link**: `00_README.md`, đối chiếu baseline `../../02_System_SW_Architecture/c4_context.md`

## Bối cảnh

Port C++ được làm song song với baseline Python đang sống trong repo
`PhanMemXemAnh` (Python). Cần quyết định tổ chức mã.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| Cùng repo, thêm `app/` | Diff/so sánh trực tiếp với Python, commit cùng lịch sử | Lịch sử repo rối giữa 2 công nghệ; tooling CI kết hợp 2 hệ sinh khó tách |
| **Repo mới riêng `PhanMemXemAnh-Cpp`** *(chọn)* | Lịch sử git tách bạch; CI tách riêng; tooling của 2 công nghệ không lẫn nhau | Mất khả năng diff/so sánh trực tiếp với Python |

## Quyết định

**Repo mới riêng** với tên đề xuất `PhanMemXemAnh-Cpp`. Baseline Python giữ
nguyên trong repo này (`PhanMemXemAnh`) và đóng vai trò **nguồn đối chiếu**
cho tính đúng đắn của port (đặc biệt mục lọc nữ — ADR-0006 dùng nó làm
oracle). Khi bản C++ giữ được hành vi đủ mức (tests + NFR đều PASS), baseline
Python được archive (README đánh dấu "legacy, không tiếp tục phát triển tính
năng mới" và ghim tag kết thúc bảo trì).

## Cấu trúc repo mới

```
PhanMemXemAnh-Cpp/
├── AGENTS.md             # hướng dẫn cho 6 agent (copy + chỉnh từ repo này)
├── agents/               # 6 tệp agent-*.md (bản gốc; .opencode/agents/ là bản sinh — Không sửa tay)
├── tasks/                # TASK-NNN theo quy ước templates mới (10_process_architecture_6_roles.md)
├── requirements/         # FR (Task-Planning) + NFR (SW-Architect) + traceability matrix
│   ├── functional_requirements.md      # ≈ docs/01_Requirement/requirements.md của baseline
│   ├── non_functional_requirements.md  # ≈ docs/03_CPP_Port_Architecture/nfr_cpp.md
│   └── traceability_matrix.md          # FR ↔ ADR ↔ Component ↔ V&V Test ID
├── docs/
│   ├── architecture/     # C4 3 mức bản C++ (copy từ docs/03_CPP_Port_Architecture/)
│   ├── adr/              # ADR mới nhất
│   └── git_work_flow/    # thiết kế workflow (SW-Integrator phụ trách)
├── src/
│   ├── xemanh/core/      # thư viện lõi — không Qt
│   ├── xemanh/ai/        # port loc_nu.py (engine AI)
│   ├── xemanh/platform/  # winfx port
│   ├── xemanh/gui/       # Qt widget port
│   └── loc_nu/           # engine AI (port loc_nu.py)
├── app/                  # main.cpp (entry mỏng — vai trò viewer_qt.py)
├── tests/
│   ├── unit/             # GoogleTest (chỉ được Task-Implementation ghi)
│   ├── vnv/              # Qt Test functional (Task-V&V) + test case dạng MD
│   └── fixture/          # bộ ảnh mẫu cố định dùng cho test đối chiếu Python↔C++
├── tools/                # giữ như baseline: agents.py, measure_resources.py, check_exe.py (giữ Python)
├── .github/workflows/    # CI (SW-Integrator)
└── reports/              # báo cáo QG, coverage, tài nguyên (bản .gitignore)
```

## Hệ quả

- Tái dụng "tooling-dev bằng Python" của baseline (ADR-0002, ADR-0006) — đồng
  thời giữ chuẩn "tiếng Việt, không dấu trong tên tệp/hàm test" của dự án.
- Model ONNX ~430MB và `models/` không đưa vào git (như baseline); trong CI,
  mỗi job chỉ tải model khi cần (test của `ai/model_fetcher` toàn mock).
