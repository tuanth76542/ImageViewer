"""
loc_nu.py - Lọc ảnh "chủ thể là con người, là nữ".

Cách hoạt động (chạy hoàn toàn offline sau lần tải model đầu tiên):
  B1. Phát hiện khuôn mặt bằng YuNet (nhẹ ~230KB, bắt được mặt nhỏ,
      mặt nghiêng tốt hơn SSD cũ). Ảnh lớn được thu nhỏ (cạnh dài tối
      đa 1280px) chỉ để tìm mặt cho nhanh, rồi map box về tọa độ gốc.
  B2. Với mỗi mặt (mở rộng 25% lấy thêm context, mặt to nhất check trước),
      đoán giới tính 2 vòng: vòng 1 dùng FairFace ResNet-34 (nhanh ~0.07s);
      ca nào lưỡng lự mới đưa sang vòng 2 là FairFace ViT (chậm mà kỹ).
  -> Giữ ảnh nếu có ÍT NHẤT 1 khuôn mặt được đoán là Female.

Tốc độ: quét song song nhiều ảnh cùng lúc + cache kết quả theo từng file
(lần lọc sau với folder cũ chạy gần như tức thì).

Model tự tải 1 lần duy nhất vào thư mục ./models (bản .exe: thư mục
%LOCALAPPDATA%\\PhanMemXemAnh\\models, hoặc ./models cạnh file .exe nếu có sẵn):
  - yunet_2023mar.onnx (~230KB, face detector)
  - fairface_res34.onnx (~85MB, giới tính vòng 1 - nhanh)
  - fairface_gender_fp32.onnx (~343MB, giới tính vòng 2 - kỹ)
"""
import concurrent.futures
import json
import os
import sys
import threading
import urllib.request


# --------------------------------------------------------------- đường dẫn
def _data_dir():
    """Thư mục chứa ``models/`` và cache kết quả lọc.

    * Chạy từ mã nguồn: cạnh ``loc_nu.py`` (như trước giờ).
    * Chạy từ .exe (PyInstaller onefile): thư mục giải nén của onefile bị Windows
      xoá sau khi thoát, nên phải dùng thư mục cố định — không thì mỗi lần mở app
      lại phải tải lại ~430MB model và mất cache. Ai copy kèm thư mục ``models/``
      cạnh file .exe thì dùng luôn thư mục đó.
    """
    if not getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(__file__))
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    if os.path.isdir(os.path.join(exe_dir, "models")):
        return exe_dir
    goc = (os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
           or os.path.expanduser("~"))
    return os.path.join(goc, "PhanMemXemAnh")


def _model_dir():
    return os.path.join(_data_dir(), "models")


MODEL_DIR = _model_dir()
CACHE_VERSION = 2  # tăng khi đổi logic/model để cache cũ không dùng lại
CACHE_PATH = os.path.join(MODEL_DIR, f"loc_nu_cache_v{CACHE_VERSION}.json")

URLS = {
    "yunet_2023mar.onnx":
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "fairface_res34.onnx":
        "https://github.com/yakhyo/fairface-onnx/releases/download/weights/fairface.onnx",
    "fairface_gender_fp32.onnx":
        "https://huggingface.co/onnx-community/fairface_gender_image_detection-ONNX/resolve/main/onnx/model.onnx",
}

# id2label FairFace ViT: 0 = Female, 1 = Male
FEMALE_IDX = 0
# Vòng 1 (ResNet-34) chắc chắn thì tin ngay, lưỡng lự thì đưa sang vòng 2 (ViT)
FAST_FEMALE_MIN = 0.8   # p >= mức này -> nữ, khỏi chạy vòng 2
FAST_MALE_MAX = 0.2     # p <= mức này -> nam, khỏi chạy vòng 2
YUNET_SCORE_THRESHOLD = 0.4  # ngưỡng tin cậy phát hiện mặt
FEMALE_THRESHOLD = 0.5       # P(Female) tối thiểu để coi là nữ (= ngưỡng của model)
FACE_MARGIN = 0.25           # mở rộng box mặt mỗi phía để lấy context
MIN_FACE_SIZE = 15           # crop nhỏ hơn thì bỏ (quá mờ, đoán bừa)
DET_MAX_SIDE = 1280          # thu nhỏ ảnh về cạnh dài tối đa này khi tìm mặt
WORKERS = min(8, os.cpu_count() or 4)  # số luồng quét song song


def missing_models():
    return [n for n in URLS if not os.path.exists(os.path.join(MODEL_DIR, n))]


def download_models(progress=None):
    """Tải model còn thiếu. progress(downloaded_bytes, total_bytes, filename)."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in URLS.items():
        dst = os.path.join(MODEL_DIR, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            continue
        tmp = dst + ".tmp"

        def _hook(block, size, total, _n=name):
            if progress and total > 0:
                progress(block * size, total, _n)

        urllib.request.urlretrieve(url, tmp, reporthook=_hook)
        os.replace(tmp, dst)
    return MODEL_DIR


def _cache_key(path):
    try:
        st = os.stat(path)
        return f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}"
    except OSError:
        return None


def _load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        tmp = CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cache, fh)
        os.replace(tmp, CACHE_PATH)
    except OSError:
        pass


class FemaleFilter:
    """Lazy-load YuNet + FairFace ONNX, tái sử dụng cho cả folder.

    An toàn khi gọi từ nhiều luồng: mỗi luồng dùng 1 YuNet riêng,
    onnxruntime run() vốn đã thread-safe nên suy luận song song được.
    """

    def __init__(self):
        self._loaded = False
        self._local = threading.local()  # mỗi luồng 1 YuNet riêng (song song thật)
        self.fast = None
        self.sess = None

    def _yunet(self):
        det = getattr(self._local, "det", None)
        if det is None:
            import cv2
            det = cv2.FaceDetectorYN.create(
                os.path.join(MODEL_DIR, "yunet_2023mar.onnx"), "",
                (320, 320), YUNET_SCORE_THRESHOLD, 0.3, 50)
            self._local.det = det
        return det

    def _ensure(self):
        if self._loaded:
            return
        import cv2
        if not hasattr(cv2, "FaceDetectorYN"):
            raise RuntimeError(
                f"OpenCV {cv2.__version__} không có YuNet. "
                "Hãy chạy: pip install \"opencv-python>=4.8,<5\"")
        import onnxruntime as ort
        download_models()
        opts = ort.SessionOptions()
        # mỗi ảnh chỉ dùng 1 core để suy luận — core còn lại dành cho các
        # luồng quét ảnh khác chạy song song (tổng nhanh hơn nhiều)
        opts.intra_op_num_threads = 1
        vit_path = os.path.join(MODEL_DIR, "fairface_gender_fp32.onnx")
        self.sess = ort.InferenceSession(
            vit_path, sess_options=opts, providers=["CPUExecutionProvider"])
        self.inp_name = self.sess.get_inputs()[0].name
        # vòng 1 (nhanh): có thì dùng, lỗi thì chỉ chạy vòng 2
        try:
            self.fast = ort.InferenceSession(
                os.path.join(MODEL_DIR, "fairface_res34.onnx"),
                sess_options=opts, providers=["CPUExecutionProvider"])
            outs = self.fast.get_outputs()
            self.fast_inp = self.fast.get_inputs()[0].name
            # đầu ra gender là output thứ 2 (race, gender, age)
            self.fast_gender_idx = 1 if len(outs) > 1 else 0
        except Exception:
            self.fast = None
        self._loaded = True

    def _p_female_fast(self, face_bgr):
        """Vòng 1: ResNet-34 (~0.07s). Trả None nếu không có model."""
        import cv2
        import numpy as np
        if self.fast is None:
            return None
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
        x = rgb.astype("float32") / 255.0
        x = (x - np.array([0.485, 0.456, 0.406], "float32")) / np.array(
            [0.229, 0.224, 0.225], "float32")
        x = np.transpose(x, (2, 0, 1))[None]
        g = self.fast.run(None, {self.fast_inp: x})[self.fast_gender_idx][0]
        e = np.exp(g - g.max())
        # GENDER_LABELS của FairFace ResNet: ["Male", "Female"] -> nữ là index 1
        return float(e[1] / e.sum())

    def _p_female(self, face_bgr):
        """Vòng 2 (ViT): kỹ nhưng chậm. Chỉ gọi cho ca khó."""
        import cv2
        import numpy as np
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
        x = rgb.astype("float32") / 255.0
        x = (x - 0.5) / 0.5
        x = np.transpose(x, (2, 0, 1))[None]
        logits = self.sess.run(None, {self.inp_name: x})[0][0]
        e = np.exp(logits - logits.max())
        return float(e[FEMALE_IDX] / e.sum())

    def _p_female_cascade(self, face_bgr):
        """Vòng 1 nhanh trước, lưỡng lự mới chạy vòng 2. Trả (p, vòng)."""
        p1 = self._p_female_fast(face_bgr)
        if p1 is None:
            return self._p_female(face_bgr), 2
        if p1 >= FAST_FEMALE_MIN or p1 <= FAST_MALE_MAX:
            return p1, 1
        return self._p_female(face_bgr), 2

    def _load_img(self, path):
        import cv2
        import numpy as np
        # cv2.imread KHÔNG đọc được đường dẫn có dấu/emoji trên Windows
        # -> đọc bytes bằng numpy rồi giải mã (hỗ trợ Unicode)
        try:
            data = np.fromfile(path, dtype=np.uint8)
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def _faces(self, img):
        import cv2
        h, w = img.shape[:2]
        scale = 1.0
        det_img = img
        if max(h, w) > DET_MAX_SIDE:
            scale = DET_MAX_SIDE / max(h, w)
            det_img = cv2.resize(img, (int(w * scale), int(h * scale)),
                                 interpolation=cv2.INTER_LINEAR)
        dh, dw = det_img.shape[:2]
        det = self._yunet()  # onnxruntime run() thread-safe; YuNet mỗi luồng 1 cái
        det.setInputSize((dw, dh))
        _n, faces = det.detect(det_img)
        if faces is None:
            return []
        # map box về tọa độ ảnh gốc, mặt to nhất trước (hay là chủ thể)
        out = []
        for fc in faces:
            x, y, bw, bh = (float(v) / scale for v in fc[:4])
            out.append((bw * bh, (x, y, bw, bh)))
        out.sort(key=lambda t: t[0], reverse=True)
        return [b for _, b in out]

    def is_female_image(self, path):
        """Trả về (is_female: bool, info: str). Không mặt -> (False, 'no-face')."""
        self._ensure()
        img = self._load_img(path)
        if img is None:
            return False, "unreadable"
        h, w = img.shape[:2]
        best = 0.0
        for (x, y, bw, bh) in self._faces(img):
            mx, my = int(bw * FACE_MARGIN), int(bh * FACE_MARGIN)
            x1, y1 = max(0, int(x - mx)), max(0, int(y - my))
            x2, y2 = min(w, int(x + bw + mx)), min(h, int(y + bh + my))
            if x2 - x1 < MIN_FACE_SIZE or y2 - y1 < MIN_FACE_SIZE:
                continue
            face = img[y1:y2, x1:x2]
            if face.size == 0:
                continue
            p, _vong = self._p_female_cascade(face)
            best = max(best, p)
            if p >= FEMALE_THRESHOLD:
                return True, f"female:{p:.2f}"
        if best > 0:
            return False, f"male:{1 - best:.2f}"
        return False, "no-face"


def filter_female(paths, on_progress=None, workers=WORKERS, use_cache=True):
    """Lọc song song 1 list path, giữ nguyên thứ tự.

    on_progress(done, total, path, kept). Kết quả được cache theo
    (đường dẫn + size + mtime) nên lần sau chạy tức thì.
    """
    paths = list(paths)
    filt = FemaleFilter()
    cache = _load_cache() if use_cache else {}
    results = {}
    todo = []
    for p in paths:
        if use_cache:
            key = _cache_key(p)
            if key is not None and key in cache:
                results[p] = bool(cache[key])
                if on_progress:
                    on_progress(len(results), len(paths), p, results[p])
                continue
        todo.append(p)

    if todo:
        filt._ensure()
        lock = threading.Lock()

        def one(p):
            try:
                ok, _info = filt.is_female_image(p)
            except Exception:
                ok = False
            return p, ok

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for p, ok in ex.map(one, todo):
                results[p] = ok
                if use_cache:
                    key = _cache_key(p)
                    if key is not None:
                        with lock:
                            cache[key] = ok
                if on_progress:
                    on_progress(len(results), len(paths), p, ok)
        if use_cache:
            _save_cache(cache)

    return [p for p in paths if results.get(p, False)]
