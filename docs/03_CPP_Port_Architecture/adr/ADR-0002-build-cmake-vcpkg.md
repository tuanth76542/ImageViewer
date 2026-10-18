# ADR-0002 — Hệ build & phụ thuộc: CMake + vcpkg

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHẤP NHẬN (người dùng chốt)
- **Link**: `00_README.md`, đối chiếu baseline `../../../pyproject.toml`, `../../../PhanMemXemAnh.spec`

## Bối cảnh

Baseline Python quản lý thư viện runtime bằng `pyproject.toml` + `uv.lock`
(uv), đóng gói phát hành bằng PyInstaller + `PhanMemXemAnh.spec` (spec phải lọc
DLL runtime bị xung đột từ PATH). Chuyển sang C++ cần công cụ build có kiểm và
kho phụ thuộc tái lập được.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **CMake ≥ 3.28 + vcpkg (manifest mode)** | Chuẩn thực tế cho C++ + Qt trên Windows, cmake/tgt/vcpkg-presets file hoá, CI nhanh, vcpkg có `onnxruntime`, `opencv4`, `qtbase` (Qt6), `gtest` | vcpkg binary-cache cần thiết lập (dù vcpkg có build cache builtin) |
| CMake + Conan | Kiểm soát version chặt theo recipe | Config nặng hơn; không dùng được nhiều CMake hint builtin của vcpkg |
| CMake + tải lib thủ công | Không cần công cụ thêm | Phụ thuộc drift, rebuild sạch khó, dễ lặp lại kiểu DLL runtime cũ gây lỗi như PyInstaller từng gặp |

## Quyết định

**CMake ≥ 3.28 + vcpkg manifest mode**. File quan trọng:

```
CMakePresets.json       — preset debug/release + toolchain vcpkg
vcpkg.json              — manifest: qtbase, onnxruntime, opencv4, gtest
CMakeLists.txt          — target: xemanh_core, xemanh_ai, xemanh_gui,
                          xemanh_platform, xemanh (executable app)
```

Mọi lib phụ thuộc được pin version trong `vcpkg.json` + baseline trong
`vcpkg-configuration.json` (vai trò tương đương `uv.lock`).

## Hệ quả

- Tooling phát triển/tests đo kiểm (Python: `tools/measure_resources.py`,
  `tools/check_exe.py`, `tools/agents.py`, `pytest`) **giữ nguyên bằng Python** —
  tooling không cần port sang C++ (chỉ thay đường dẫn app .exe rồi kiểm lại).
  File `pyproject.toml` + `uv` tiếp tục quản lý vùng tooling trong repo mới
  (giảm khối lượng port, giữ chuẩn bàn phím của dự án — xem ADR-0006).
- So với baseline PyInstaller + spec lọc DLL: bản C++ chỉ ghép runtime DLL của
  Qt/OpenCV/onnxruntime vào thư mục output (kỹ thuật chuẩn `CMAKE_INSTALL_RPATH`
  + `WINDEPLOYQT`); DLL runtime không còn bị ảnh hưởng PATH như PyInstaller
  trước (vấn đề thật của baseline từng gặp từ JRE trên máy dev — được ghi cụ thể
  trong `README.md` mục "Đóng gói .exe").

## Xác nhận thực hiện đúng

- Build từ máy sạch chỉ cần: install MSVC BuildTools 2022 + `git clone` +
  `cmake --preset release` (vcpkg tự dựng/restore cache) — được kiểm chứng CI
  (xem `10_process_architecture_6_roles.md`).
- `vcpkg.json` pin đủ version, không có lib khai thiếu (không dùng "unspecific").
