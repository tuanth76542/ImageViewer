# ADR-0004 — Engine suy luận AI: ONNX Runtime C++

- **Ngày**: 2026-10-18
- **Trạng thái**: ĐÃ CHẤP NHẬN (người dùng chốt)
- **Link**: `00_README.md`; đối chiếu baseline `../../../loc_nu.py` (285 dòng)

## Bối cảnh

Bộ lọc ảnh nữ ở baseline (Python `loc_nu.py`) chạy bằng onnxruntime Python API:
YuNet (OpenCV `cv2.FaceDetectorYN`) + 2 vòng phân loại giới tính (FairFace
ResNet-34 rồi ViT phân xử ca khó), 3 tệp ONNX ~430MB trong `models/`, cache
kết quả JSON theo (path + size + mtime), quét song song `ThreadPoolExecutor`.

## Phương án đã cân nhắc

| Phương án | Điểm tốt | Điểm xấu |
|-----------|---------|----------|
| **ONNX Runtime C++ API** | Dùng lại y nguyên 3 model ONNX (~430MB), port logic 1:1 từ API Python, giữ đúng mô hình cache delta | API C++ quản lý bộ nhớ dài dòng hơn Python (Ort::Env, Ort::Session, tensor wrapper) |
| OpenCV DNN `cv::dnn::Net` | YuNet có sẵn trong opencv_zoo | Cần kiểm chứng lại accuracy/khác biệt giữa engine onnxruntime vs DNN (không đảm bảo cùng output) |
| Giữ engine Python (sidecar process) | Port rẻ | Phụ thuộc runtime Python — ngược mục tiêu port; IPC phức tạp |

## Quyết định

**ONNX Runtime C++ API** cho 3 model. OpenCV tiếp tục được dùng cho
`cv::FaceDetectorYN` (phát hiện mặt) và chuẩn bị ảnh đầu vào (`cv::Mat`,
resize, BGR) — giữ đúng 1:1 với baseline Python như hiện tại.

## Port 1:1 cần gác lại đúng

Yếu tố baseline phải **giữ đúng** trong port C++ (gác bằng test đối chiếu):

1. **Pre-processing** — resize, định dạng, chuẩn hóa pixel (bản Python làm qua
   `numpy`) — port nguyên phép tính (`cv::Mat`, `Ort::Value`).
2. **Cascade 2 vòng** — ResNet phân loại nhanh (chạy đầu, ngưỡng quyết), nếu
   kết quả ở biên **không thể quyết** mới gọi ViT để phân xử.
3. **Ngưỡng và hằng số** — MIN_FACE_SIZE, thresh… giữ nguyên giá trị.
4. **Quét song song** — `ThreadPoolExecutor(max_workers=workers)` ở Python →
   `QThreadPool` ở C++ (ADR-0008), số worker = cùng quy tắc.
5. **Cache delta** — key (path + size + mtime), **giữ schema JSON v2 rõ ràng**
   (tách riêng ở ADR-0010 để quản vòng đời cache).

## Hệ quả

- Điểm tốt: không phải train lại model; kiểm chứng được bằng test so sánh giá
  trị Python vs C++ trên bộ ảnh mẫu (tests/fixture/, ADR-0006).
- Rủi ro chính: sai khác float nhỏ giữa runtime Python và C++ → chấp nhận sai
  lệch ≤ 1 ảnh trên 350 (đo được, ghi số trong test report).
