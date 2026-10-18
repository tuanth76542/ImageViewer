"""Test đơn vị cho phần tải model và suy luận của `loc_nu` — **giả lập toàn bộ**.

Không tải ~430MB model thật và không cần mạng: `onnxruntime` bị thay bằng module
giả (đặt vào `sys.modules`), `cv2.FaceDetectorYN` bị thay bằng lớp giả trả về box
mặt định sẵn. Nhờ vậy các hàm `_yunet`/`_ensure`/`_p_female*`/`_faces` đo được độ
phủ ngay trong môi trường offline.
"""
import os
import sys
import types

import numpy as np
import pytest

import loc_nu

pytestmark = pytest.mark.unit

# Ảnh BGR nhỏ, đủ để `cv2.cvtColor` + `cv2.resize` chạy thật (cv2 có sẵn).
FACE = np.zeros((16, 16, 3), "uint8")


# ----------------------------------------------------------------- tiện ích giả
class SessionGia:
    """Giả `ort.InferenceSession`: trả về tên input và kết quả `run()` cố định."""

    def __init__(self, ten_input="input", so_output=1, ket_qua=None):
        self.ten_input = ten_input
        self.so_output = so_output
        self.ket_qua = ket_qua
        self.da_chay = []                       # các dict feed đã nhận

    def get_inputs(self):
        return [types.SimpleNamespace(name=self.ten_input)]

    def get_outputs(self):
        return [types.SimpleNamespace(name="out%d" % i) for i in range(self.so_output)]

    def run(self, _outputs, feed):
        self.da_chay.append(feed)
        return self.ket_qua


def _module_ort(tao_session, opts_da_tao=None):
    """Module `onnxruntime` giả: `SessionOptions` + `InferenceSession` tuỳ biến."""

    def _opts():
        opts = types.SimpleNamespace(intra_op_num_threads=-1)
        if opts_da_tao is not None:
            opts_da_tao.append(opts)
        return opts

    return types.SimpleNamespace(SessionOptions=_opts,
                                 InferenceSession=tao_session)


class DetectorGia:
    """Giả `cv2.FaceDetectorYN`: nhớ cỡ input và trả về box mặt định sẵn."""

    def __init__(self, faces=None):
        self.faces = faces
        self.size = None
        self.anh = None

    def setInputSize(self, size):
        self.size = size

    def detect(self, img):
        self.anh = img
        return (0 if self.faces is None else len(self.faces)), self.faces


def _gia_cv2_detector(monkeypatch, det, ghi_tao=None):
    """Thay `cv2.FaceDetectorYN.create` để trả về `det`."""
    import cv2

    class _Gia:
        @staticmethod
        def create(_model, _config, size, score, _nms, _topk):
            if ghi_tao is not None:
                ghi_tao.append((size, score))
            return det

    monkeypatch.setattr(cv2, "FaceDetectorYN", _Gia)


def _duong_dan_models(tmp_path, monkeypatch):
    """Trỏ MODEL_DIR/CACHE_PATH vào thư mục tạm để không đụng máy thật."""
    md = tmp_path / "models"
    monkeypatch.setattr(loc_nu, "MODEL_DIR", str(md))
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(md / "cache.json"))
    return md


# ------------------------------------------------------------ missing / download
def test_missing_models_liet_ke_dung_model_con_thieu(tmp_path, monkeypatch):
    md = _duong_dan_models(tmp_path, monkeypatch)
    assert set(loc_nu.missing_models()) == set(loc_nu.URLS)

    md.mkdir()
    for ten in loc_nu.URLS:
        (md / ten).write_bytes(b"x" * 2000)
    assert loc_nu.missing_models() == []


def test_download_models_tai_file_con_thieu_va_goi_tien_do(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)
    da_tai = []

    def urlretrieve(url, filename, reporthook=None):
        da_tai.append((url, filename))
        with open(filename, "wb") as fh:
            fh.write(b"model gia")
        if reporthook:
            reporthook(1, 128, 512)      # có tổng -> gọi progress
            reporthook(1, 0, 0)          # tổng = 0 -> bỏ qua (không chia 0)

    monkeypatch.setattr(loc_nu.urllib.request, "urlretrieve", urlretrieve)
    tien_do = []
    goc = loc_nu.download_models(
        lambda done, total, ten: tien_do.append((done, total, ten)))

    assert goc == loc_nu.MODEL_DIR
    assert len(da_tai) == len(loc_nu.URLS)
    for ten in loc_nu.URLS:
        assert os.path.getsize(os.path.join(goc, ten)) == len(b"model gia")
        assert not os.path.exists(os.path.join(goc, ten) + ".tmp")
    assert tien_do == [(128, 512, ten) for ten in loc_nu.URLS]


def test_download_models_khong_can_tien_do(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)

    def urlretrieve(_url, filename, reporthook=None):
        with open(filename, "wb") as fh:
            fh.write(b"gia")
        if reporthook:
            reporthook(1, 64, 256)       # không truyền progress -> phải bỏ qua

    monkeypatch.setattr(loc_nu.urllib.request, "urlretrieve", urlretrieve)
    goc = loc_nu.download_models()       # không progress: vẫn chạy bình thường

    for ten in loc_nu.URLS:
        assert os.path.exists(os.path.join(goc, ten))


def test_download_models_bo_qua_khi_da_co_du(tmp_path, monkeypatch):
    md = _duong_dan_models(tmp_path, monkeypatch)
    md.mkdir()
    for ten in loc_nu.URLS:
        (md / ten).write_bytes(b"x" * 2000)

    def khong_duoc_goi(*a, **k):
        raise AssertionError("model đã có (>1000 byte) thì không được tải lại")

    monkeypatch.setattr(loc_nu.urllib.request, "urlretrieve", khong_duoc_goi)
    assert loc_nu.download_models() == str(md)


# ------------------------------------------------------------------ cache
def test_save_cache_bo_qua_khi_ghi_loi(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)

    def hong(*a, **k):
        raise OSError("đĩa đầy")

    monkeypatch.setattr(loc_nu.os, "makedirs", hong)
    loc_nu._save_cache({"a.jpg": True})   # nuốt lỗi, không ném ra ngoài


# ------------------------------------------------------------------ _yunet
def test_yunet_tao_mot_lan_cho_moi_luong(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)
    ghi_tao = []
    det = DetectorGia()
    _gia_cv2_detector(monkeypatch, det, ghi_tao)

    f = loc_nu.FemaleFilter()
    assert f._yunet() is det
    assert f._yunet() is det              # đã nhớ trong thread-local, không tạo lại
    assert len(ghi_tao) == 1
    assert ghi_tao[0] == ((320, 320), loc_nu.YUNET_SCORE_THRESHOLD)


# ------------------------------------------------------------------ _ensure
def test_ensure_nap_du_model_va_dung_mot_core(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)
    da_goi_tai = []
    monkeypatch.setattr(loc_nu, "download_models",
                        lambda *a, **k: da_goi_tai.append(True))
    opts_da_tao = []
    sess_chinh = SessionGia("vit_input")
    sess_nhanh = SessionGia("fast_input", so_output=3)

    def tao_session(path, sess_options=None, providers=None):
        if "res34" in path:
            return sess_nhanh
        return sess_chinh

    monkeypatch.setitem(sys.modules, "onnxruntime",
                        _module_ort(tao_session, opts_da_tao))

    f = loc_nu.FemaleFilter()
    f._ensure()

    assert f.sess is sess_chinh and f.inp_name == "vit_input"
    assert f.fast is sess_nhanh and f.fast_inp == "fast_input"
    assert f.fast_gender_idx == 1          # 3 output -> gender là output thứ 2
    assert f._loaded is True
    assert da_goi_tai == [True]            # _ensure tự tải model còn thiếu
    assert [o.intra_op_num_threads for o in opts_da_tao] == [1]

    # gọi lần 2: đã nạp rồi thì không tải/khởi tạo lại
    f._ensure()
    assert len(opts_da_tao) == 1


def test_ensure_chi_dung_vong_2_khi_model_nhanh_loi(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)
    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: loc_nu.MODEL_DIR)
    sess_chinh = SessionGia("vit_input")

    def tao_session(path, sess_options=None, providers=None):
        if "res34" in path:
            raise RuntimeError("model vòng 1 hỏng")
        return sess_chinh

    monkeypatch.setitem(sys.modules, "onnxruntime", _module_ort(tao_session))

    f = loc_nu.FemaleFilter()
    f._ensure()

    assert f.fast is None                  # lỗi -> chỉ chạy vòng 2
    assert f.sess is sess_chinh
    assert f._loaded is True


def test_ensure_mot_output_thi_gender_la_output_dau(tmp_path, monkeypatch):
    _duong_dan_models(tmp_path, monkeypatch)
    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: loc_nu.MODEL_DIR)
    sess_chinh = SessionGia("vit_input")
    sess_nhanh = SessionGia("fast_input", so_output=1)

    def tao_session(path, sess_options=None, providers=None):
        return sess_nhanh if "res34" in path else sess_chinh

    monkeypatch.setitem(sys.modules, "onnxruntime", _module_ort(tao_session))

    f = loc_nu.FemaleFilter()
    f._ensure()
    assert f.fast_gender_idx == 0          # chỉ 1 output -> lấy output 0


def test_ensure_bao_loi_khi_opencv_khong_co_yunet(monkeypatch):
    import cv2

    monkeypatch.delattr(cv2, "FaceDetectorYN", raising=False)
    with pytest.raises(RuntimeError, match="YuNet"):
        loc_nu.FemaleFilter()._ensure()


# ------------------------------------------------------- suy luận 2 vòng
def test_p_female_fast_tra_ve_none_khi_thieu_model():
    f = loc_nu.FemaleFilter()
    assert f.fast is None
    assert f._p_female_fast(FACE) is None


def test_p_female_fast_softmax_va_dung_ten_input():
    f = loc_nu.FemaleFilter()
    logits = np.array([[0.4, -0.6]], "float32")     # [Male, Female]
    f.fast = SessionGia("fast_input", so_output=1, ket_qua=[np.zeros((1, 1)), logits])
    f.fast_inp = "fast_input"
    f.fast_gender_idx = 1

    p = f._p_female_fast(FACE)

    e = np.exp(logits[0] - logits[0].max())
    assert p == pytest.approx(float(e[1] / e.sum()))
    assert p < 1.0 and p > 0.0


def test_p_female_softmax_va_dung_ten_input():
    f = loc_nu.FemaleFilter()
    logits = np.array([[1.5, -0.5]], "float32")     # index 0 = Female
    f.sess = SessionGia("vit_input", ket_qua=[logits])
    f.inp_name = "vit_input"

    p = f._p_female(FACE)

    e = np.exp(logits[0] - logits[0].max())
    assert p == pytest.approx(float(e[loc_nu.FEMALE_IDX] / e.sum()))
    assert f.sess.da_chay[0]["vit_input"].shape == (1, 3, 224, 224)


# ------------------------------------------------------------------ _faces
def test_faces_tra_ve_rong_khi_khong_thay_mat(monkeypatch):
    f = loc_nu.FemaleFilter()
    monkeypatch.setattr(f, "_yunet", lambda: DetectorGia(None))
    assert f._faces(np.zeros((60, 60, 3), "uint8")) == []


def test_faces_sap_xep_mat_to_nhat_truoc(monkeypatch):
    f = loc_nu.FemaleFilter()
    nho = [10, 10, 10, 10]
    to = [20, 20, 80, 60]                  # diện tích 4800 > 100
    det = DetectorGia(np.array([nho, to], "float32"))
    monkeypatch.setattr(f, "_yunet", lambda: det)

    assert f._faces(np.zeros((100, 100, 3), "uint8")) == [
        (20.0, 20.0, 80.0, 60.0), (10.0, 10.0, 10.0, 10.0)]
    assert det.size == (100, 100)          # ảnh nhỏ: không thu nhỏ


def test_faces_thu_nho_anh_lon_roi_map_ve_toa_do_goc(monkeypatch):
    f = loc_nu.FemaleFilter()
    det = DetectorGia(np.array([[64, 64, 64, 64]], "float32"))
    monkeypatch.setattr(f, "_yunet", lambda: det)

    faces = f._faces(np.zeros((2160, 3840, 3), "uint8"))   # 4K

    assert det.size == (1280, 720)         # thu về cạnh dài DET_MAX_SIDE
    assert faces == [(192.0, 192.0, 192.0, 192.0)]         # box map về ảnh gốc


# ------------------------------------------------------- filter_female & cache
def _fake_giu_chan(tmp_path, monkeypatch, calls):
    """`FemaleFilter` giả: giữ ảnh có chỉ số chẵn."""
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(tmp_path / "cache.json"))

    class FakeFilter:
        def _ensure(self):
            pass

        def is_female_image(self, path):
            calls.append(path)
            return int(os.path.basename(path)[0]) % 2 == 0, "x"

    monkeypatch.setattr(loc_nu, "FemaleFilter", FakeFilter)


def _files(tmp_path, n):
    paths = []
    for i in range(n):
        p = tmp_path / ("%d.jpg" % i)
        p.write_bytes(b"data")
        paths.append(str(p))
    return paths


def test_filter_female_bao_tien_do_cho_anh_lay_tu_cache(tmp_path, monkeypatch):
    calls = []
    _fake_giu_chan(tmp_path, monkeypatch, calls)
    paths = _files(tmp_path, 3)

    loc_nu.filter_female(paths, workers=1)          # lần 1: quét và ghi cache
    assert len(calls) == 3

    seen = []
    loc_nu.filter_female(paths, workers=1,
                         on_progress=lambda d, t, p, ok: seen.append((d, ok)))

    assert len(calls) == 3                          # lần 2 lấy từ cache, không quét
    assert seen == [(1, True), (2, False), (3, True)]


def test_filter_female_them_anh_moi_chi_quet_anh_moi(tmp_path, monkeypatch):
    """Quét delta: thêm ảnh mới thì chỉ ảnh mới phải suy luận, kết quả cũ giữ nguyên."""
    calls = []
    _fake_giu_chan(tmp_path, monkeypatch, calls)
    paths = _files(tmp_path, 3)

    assert loc_nu.filter_female(paths, workers=1) == [paths[0], paths[2]]
    assert len(calls) == 3

    moi = tmp_path / "4.jpg"                        # chỉ số chẵn -> là ảnh nữ
    moi.write_bytes(b"data")

    ket_qua = loc_nu.filter_female(paths + [str(moi)], workers=1)

    assert calls == paths + [str(moi)]              # chỉ ảnh mới phải quét
    assert ket_qua == [paths[0], paths[2], str(moi)]


def test_filter_female_khong_dung_cache_van_chay(tmp_path, monkeypatch):
    calls = []
    _fake_giu_chan(tmp_path, monkeypatch, calls)
    cache = tmp_path / "cache.json"
    paths = _files(tmp_path, 2)

    assert loc_nu.filter_female(paths, workers=1, use_cache=False) == [paths[0]]
    assert len(calls) == 2
    assert not cache.exists()                       # use_cache=False -> không ghi


def test_filter_female_bo_qua_cache_khi_khong_tinh_duoc_khoa(tmp_path, monkeypatch):
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(tmp_path / "cache.json"))
    calls = []

    class FakeFilter:
        def _ensure(self):
            pass

        def is_female_image(self, path):
            calls.append(path)
            return True, "x"

    monkeypatch.setattr(loc_nu, "FemaleFilter", FakeFilter)
    mat = str(tmp_path / "khong-ton-tai.jpg")       # _cache_key -> None

    assert loc_nu.filter_female([mat], workers=1) == [mat]
    assert calls == [mat]                           # vẫn quét dù không lưu được cache
