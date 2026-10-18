# ADR-0010 — Tương thích cache v2: giữ schema `loc_nu_cache_v2.json`

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐỀ XUẤT (chờ người dùng duyệt)
- **Link**: baseline `../../../loc_nu.py` (cache JSON theo path+size+mtime)

## Bối cảnh

Bộ lọc nữ ở baseline cache kết quả JSON theo key (đường dẫn + kích thước +
mtime) → lần quét thứ hai trên thư mục không đổi **tức thì**, chỉ ảnh
mới/thay đổi phải suy luận lại (quét delta). Người dùng nâng cấp Python → C++
mang theo cache cũ chạy vẫn nhanh được nếu schema giữ nguyên.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **Giữ schema v2 (đề xuất)** | Người dùng nâng cấp không phải quét lại 350 ảnh (~1,5 phút máy yếu + 430MB suy luận lãng phí); dễ đối chiếu A/B Python↔C++ | Schema cũ sinh ra theo thói quen Python (field bool, path theo kiểu Windows) — hơi bất tiện khi parse ở C++ |
| Schema v3 (định dạng mới, ví dụ msgpack / SQLite) | Parse C++ tiện hơn | Mất cache cũ; test đối chiếu khó; lợi ích của v3 thấp vì schema v2 vẫn nhẹ |

## Quyết định (đề xuất)

**Giữ đúng schema v2** trong `ResultCache` (component
`src/loc_nu/result_cache.{h,cpp}`): JSON, key = path + size + mtime, dùng
parser JSON phổ biến (nlohmann_json — vcpkg có sẵn, ADR-0002). Nếu cần thêm
field mới: **chỉ thêm field, không đổi tên field cũ** (backward compatible).

## Hệ quả

- Người dùng nâng cấp vẫn được hưởng "lần quét lần hai tức thì".
- Nếu phát hiện điểm yếu của schema v2 khi port: chốt bằng một trường kiểm
  nghiêm ngặt trong spec, không sửa schema cà tư.

## Xác nhận thực hiện đúng

- Test dùng trực tiếp cache JSON v2 sinh từ bản Python (tệp cố định trong
  `tests/fixture/`) — đọc được và tra cứu ra đúng kết quả.
