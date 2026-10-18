# ADR-0009 — Kiến trúc quy trình: 6 vai trò agent làm việc song song trên 1 repo

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt — đây là trục thiết kế đặc thù
  của yêu cầu)
- **Link**: chi tiết đầy đủ `../10_process_architecture_6_roles.md`

## Bối cảnh

Yêu cầu của người dùng: port C++ phải **hỗ trợ 6 vị trí làm việc đồng thời
trên repo**, trong đó:

1. Task-Planning agent (PM / SE): nhận yêu cầu người dùng, viết FR, tạo task.
2. Task-Implementation agent (SW Dev): implement code change, unit test, fix
   bug, fix code warning.
3. Task-V&V agent (System Test Eng.): viết functional test case, chạy, report
   kết quả.
4. SW-Release-QA agent (QA Eng.): review kết quả các vai trò khác, tạo report
   để người dùng approve cho mỗi SW release.
5. SW-Integrator agent (Integrator / DevOps): thiết kế và implement git
   workflow.
6. SW-Architect agent (SW Architect): nhận SW requirement, tạo architecture
   design, làm ADR và xác nhận với người dùng phương án nào được lựa chọn,
   viết NFR.

Baseline Python đã có 3 agent (task-planning, task-implementation,
sw-release-qg-check) + coordinator (`AGENTS.md`); quy trình khá hiệu quả
nhưng chỉ dọc theo một task chạy lần lượt 3 vai, chưa có V&V, Integrator,
Architect độc lập, và chưa được thiết kế cho nhiều task song song.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **Quy trình 6-role theo artifact + gates (đề xuất)** — mỗi vai trò 1 tập quyền ghi phân vùng thư mục; giao tiếp bằng artifact trong git (FR/task/ADR/test code/report), không qua chat | Song song thật; ownership rõ; tự kiểm bằng CI; văn bản đủ để agent mới vào việc không hỏi lại | Cần kỷ luật điều phối (file `AGENTS.md` chuẩn) |
| Single coordinator làm mọi thứ trực tiếp (như hiện tại) | Đơn giản cho agent hiện có | Điều phối bị nghẽn; không thể chạy nhiều task song song |
| Các agent chạy chung một folder repo | Đơn giản | Conflict khi build/test cùng lúc; lock index; nhiễu `git status` |

## Quyết định (đề xuất)

Quy trình 6-role gồm 5 thành phần:

1. **Artifact Flow** — mỗi vai trò tạo/đọc artifact cụ thể (đường dẫn cố định,
   kiểm qua CI). Nguyên tắc "hợp tác về tài liệu, không chat".
2. **Ownership Matrix** — mỗi vai trò chỉ được **GHI** một tập thư mục/phạm vi
   cụ thể; nơi khác chỉ **ĐỌC**. Ranh giới để tránh merge conflict, được cài
   bền vào `CODEOWNERS` + CI.
3. **Git Workflow** — 1 task = 1 nhánh `feature|bugfix/task-NNN-*` từ `main`
   mới nhất; merge vào `main` chỉ qua **squash commit** sau khi người dùng
   đồng ý; `main` được bảo vệ bởi CI (chi tiết:
   `10_process_architecture_6_roles.md`).
4. **Quality gates** — cổng xanh bắt buộc giữa các vai: FR→TASK (G1) →
   implement (G2) → V&V (G3) → Release-QA (G4) → Integrate (G5). Mỗi gate có
   tiêu chí cụ thể + người xác nhận.
5. **Parallel protocol** — nhiều nhánh song song là bình thường; thứ tự merge
   do Integrator chốt; task đụng trùng component thì rebase theo thứ tự.

## Hệ quả

- Song song thật: 2 task không chạm cùng thư mục có thể chạy cùng lúc mà
  không cần người dùng điều phối.
- Rủi ro lớn: Integrator là vai mới — CI setup phải kỹ; merge chỉ qua squash,
  quy trình chặn cứng `git push --force`.

## Xác nhận thực hiện đúng

- Mô tả chi tiết 6 vai, artifact, gates (tài liệu
  `10_process_architecture_6_roles.md`) đủ để vai mới đọc một lần và chạy
  được một vòng lặp đầy đủ mà không phải hỏi lại.
