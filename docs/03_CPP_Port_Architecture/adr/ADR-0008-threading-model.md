# ADR-0008 — Mô hình luồng: QThreadPool + LRU decode cache + delta scan bất đồng bộ

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt)
- **Link**: baseline `../../../xemanh/filterthread.py`, `../../../loc_nu.py` (dòng 315)

## Bối cảnh

Baseline Python có 2 điểm chạy nền:

1. `FilterThread` chạy `loc_nu.filter_female` trên 1 luồng nền, phát
   `progressed/found/done/failed` về UI ("quét vẫn chạy nền, cửa sổ vẫn chuyển
   ảnh/zoom được"; đóng hộp tiến độ không dừng quét).
2. `ThreadPoolExecutor(max_workers=workers)` trong `loc_nu.py` chạy 4 luồng
   suy luận song song (~950 ms/ảnh, trên máy 2 nhân/4 luồng).

Ngoài ra, vì thiếu cache ảnh: mỗi lần navigate đều decode lại từ đĩa.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **QThreadPool + QThread worker (đề xuất)** | Khớp 1:1 với 2 điểm nền của baseline; tạo được pool riêng cho decode và suy luận; giữ signal/slot Qt | Cần tự quản pool riêng cho decode; phải cẩn thận vòng đời worker |
| std::thread + mutex thủ công | Độc lập std thuần | Tự viết callback quản lý luồng phức tạp, dễ lỗi sync |
| QtConcurrent | API ngắn gọn | Ẩn việc ánh xạ, khó truyền lỗi lên UI rõ ràng; ít điều khiển pool theo từng loại công việc |

## Quyết định (đề xuất)

**Dùng luồng của Qt (QThread/QThreadPool), giữ signal/slot Qt cho sự kiện nền →
UI:**

1. **FilterWorker** (`QThread`/`moveToThread`) — bọc `IGenderInference`; phát
   tín hiệu Qt `progressed / found / done / failed`.
2. **Suy luận song song** — `QThreadPool`, `maxThreadCount` theo cùng quy tắc
   Python (4 luồng trên máy dev) để ngang baseline.
3. **Decode ảnh bất đồng bộ** (pool riêng, ưu tiên thấp) — decode nền các ảnh
   kề (±1) khi UI rảnh, để chuyển ảnh tức thì.
4. **Decode LRU cache trong RAM** (`ImageLRUCache`) — chặn theo bytes (mặc
   định 256MB), key path + mtime + rotation; **bắt buộc thread-safe** (mutex).
5. **UI thread không bao giờ block > 16 ms** (one frame @60fps): mọi tác nặng
   phải nằm trong worker; treo được phát hiện bằng test tiêu hao.
6. **Logic worker được GoogleTest gọi trực tiếp** (không qua QThread) để đo
   được độ phủ — bài học thật của baseline: `filterthread.run()` chạy trong
   luồng native Qt làm coverage không theo dõi được, phải gọi thẳng `run()`
   trên luồng chính. C++ thiết kế ngay từ đầu cho điều này.

## Hệ quả

- Kinh tế đúng: giữ hành vi không freeze (quét nền, cửa sổ vẫn chuyển ảnh).
- Rủi ro: pool tranh chấp. Kiểm bằng test `resources` (mở nhiều ảnh + lọc nữ
  song song, đo RAM đỉnh và CPU) — ngưỡng ghi trong NFR (`nfr_cpp.md`).
