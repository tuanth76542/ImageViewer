"""Test đơn vị cho logic lọc ảnh nữ (loc_nu).

Không cần model thật, không cần GPU: các "model" được giả lập bằng
monkeypatch nên test nhanh và ổn định (không phụ thuộc 430MB model hay ảnh thật).
"""
import os
import time

import numpy as np
import pytest

import loc_nu

pytestmark = pytest.mark.unit

FACE = np.zeros((8, 8, 3), "uint8")


# ---------------- cache ----------------

def test_cache_key_stable_and_sensitive(tmp_path):
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x" * 10)
    k1 = loc_nu._cache_key(str(f))
    assert k1 is not None
    assert k1 == loc_nu._cache_key(str(f))          # ổn định

    g = tmp_path / "b.jpg"
    g.write_bytes(b"x" * 10)
    assert loc_nu._cache_key(str(g)) != k1          # khác file -> khác key

    time.sleep(1.1)  # mtime phân giải theo giây
    f.write_bytes(b"y" * 20)
    assert loc_nu._cache_key(str(f)) != k1          # đổi nội dung -> đổi key


def test_cache_key_missing_file():
    assert loc_nu._cache_key("khong-ton-tai-xyz.jpg") is None


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(tmp_path / "c.json"))
    assert loc_nu._load_cache() == {}               # chưa có file
    loc_nu._save_cache({"a": True, "b": False})
    assert loc_nu._load_cache() == {"a": True, "b": False}


def test_cache_file_carries_version():
    # đổi logic/model thì tăng CACHE_VERSION -> path đổi -> cache cũ bị bỏ
    assert f"v{loc_nu.CACHE_VERSION}" in os.path.basename(loc_nu.CACHE_PATH)


# ---------------- cascade 2 vòng ----------------

def _fake_cascade(monkeypatch, fast_ret, slow_ret):
    """FemaleFilter với 2 vòng giả lập; đếm số lần gọi vòng 2 (ViT)."""
    f = loc_nu.FemaleFilter()
    slow_calls = []

    def fast(face):
        return fast_ret

    def slow(face):
        slow_calls.append(face)
        return slow_ret

    monkeypatch.setattr(f, "_p_female_fast", fast)
    monkeypatch.setattr(f, "_p_female", slow)
    return f, slow_calls


def test_cascade_fast_confident_female_skips_vit(monkeypatch):
    f, slow = _fake_cascade(monkeypatch, 0.95, 0.0)
    assert f._p_female_cascade(FACE) == (0.95, 1)
    assert slow == []


def test_cascade_fast_confident_male_skips_vit(monkeypatch):
    f, slow = _fake_cascade(monkeypatch, 0.05, 1.0)
    assert f._p_female_cascade(FACE) == (0.05, 1)
    assert slow == []


def test_cascade_boundary_counts_as_confident(monkeypatch):
    f, slow = _fake_cascade(monkeypatch, loc_nu.FAST_FEMALE_MIN, 0.0)
    assert f._p_female_cascade(FACE) == (loc_nu.FAST_FEMALE_MIN, 1)
    f2, slow2 = _fake_cascade(monkeypatch, loc_nu.FAST_MALE_MAX, 0.0)
    assert f2._p_female_cascade(FACE) == (loc_nu.FAST_MALE_MAX, 1)
    assert slow == [] and slow2 == []


def test_cascade_ambiguous_goes_to_vit(monkeypatch):
    mid = (loc_nu.FAST_MALE_MAX + loc_nu.FAST_FEMALE_MIN) / 2
    f, slow = _fake_cascade(monkeypatch, mid, 0.77)
    assert f._p_female_cascade(FACE) == (0.77, 2)
    assert len(slow) == 1


def test_cascade_without_fast_model_uses_vit(monkeypatch):
    f, slow = _fake_cascade(monkeypatch, None, 0.6)
    assert f._p_female_cascade(FACE) == (0.6, 2)
    assert len(slow) == 1


# ---------------- is_female_image (giả lập mặt) ----------------

def _prepared_filter(monkeypatch, faces, probs, img=None):
    f = loc_nu.FemaleFilter()
    if img is None:
        img = np.zeros((300, 300, 3), "uint8")
    monkeypatch.setattr(f, "_ensure", lambda: None)
    monkeypatch.setattr(f, "_load_img", lambda p: img)
    monkeypatch.setattr(f, "_faces", lambda im: faces)
    it = iter(probs)
    monkeypatch.setattr(f, "_p_female_cascade", lambda face: (next(it), 1))
    return f


def test_female_when_any_face_is_female(monkeypatch):
    f = _prepared_filter(monkeypatch, [(10, 10, 60, 60), (150, 150, 80, 80)],
                         [0.1, 0.9])
    ok, info = f.is_female_image("x")
    assert ok is True
    assert info.startswith("female")


def test_male_when_all_faces_male(monkeypatch):
    f = _prepared_filter(monkeypatch, [(10, 10, 60, 60), (150, 150, 80, 80)],
                         [0.2, 0.3])
    ok, info = f.is_female_image("x")
    assert ok is False
    assert info.startswith("male")


def test_no_face(monkeypatch):
    f = _prepared_filter(monkeypatch, [], [])
    assert f.is_female_image("x") == (False, "no-face")


def test_unreadable_image(monkeypatch):
    f = loc_nu.FemaleFilter()
    monkeypatch.setattr(f, "_ensure", lambda: None)
    monkeypatch.setattr(f, "_load_img", lambda p: None)
    assert f.is_female_image("x") == (False, "unreadable")


def test_tiny_face_is_skipped(monkeypatch):
    # box 6x6 + margin vẫn < MIN_FACE_SIZE -> bỏ, KHÔNG gọi phân loại
    f = _prepared_filter(monkeypatch, [(0, 0, 6, 6)], [])
    assert f.is_female_image("x") == (False, "no-face")


# ---------------- filter_female ----------------

def _make_files(tmp_path, n):
    paths = []
    for i in range(n):
        p = tmp_path / f"{i}.jpg"
        p.write_bytes(b"data")
        paths.append(str(p))
    return paths


def _odd_rejects(tmp_path, monkeypatch, calls):
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(tmp_path / "c.json"))

    class FakeFilter:
        def _ensure(self):
            pass

        def is_female_image(self, path):
            calls.append(path)
            return (int(os.path.basename(path)[0]) % 2 == 0, "x")

    monkeypatch.setattr(loc_nu, "FemaleFilter", FakeFilter)


def test_filter_female_keeps_order_and_reports_progress(tmp_path, monkeypatch):
    calls = []
    _odd_rejects(tmp_path, monkeypatch, calls)
    paths = _make_files(tmp_path, 4)
    seen = []
    kept = loc_nu.filter_female(
        paths, on_progress=lambda d, t, p, ok: seen.append((d, t)), workers=2)
    assert kept == [paths[0], paths[2]]      # giữ đúng thứ tự gốc
    assert seen[-1] == (4, 4)                # báo đủ tiến độ
    assert len(calls) == 4


def test_filter_female_second_run_hits_cache(tmp_path, monkeypatch):
    calls = []
    _odd_rejects(tmp_path, monkeypatch, calls)
    paths = _make_files(tmp_path, 3)
    first = loc_nu.filter_female(paths, workers=1)
    assert len(calls) == 3
    second = loc_nu.filter_female(paths, workers=1)
    assert second == first
    assert len(calls) == 3                   # lần 2 không quét lại


def test_filter_female_error_counts_as_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(loc_nu, "CACHE_PATH", str(tmp_path / "c.json"))

    class BoomFilter:
        def _ensure(self):
            pass

        def is_female_image(self, path):
            raise ValueError("ảnh hỏng")

    monkeypatch.setattr(loc_nu, "FemaleFilter", BoomFilter)
    assert loc_nu.filter_female(_make_files(tmp_path, 2), workers=1) == []


# ---------------- đọc ảnh (không cần model, chỉ cần OpenCV) ----------------

def test_load_img_doc_anh_va_hinh_dang(tmp_path):
    from PIL import Image

    p = tmp_path / "anh.png"
    Image.new("RGB", (12, 7), (10, 20, 30)).save(p)

    img = loc_nu.FemaleFilter()._load_img(str(p))

    assert img is not None
    assert img.shape == (7, 12, 3)                     # cao, rộng, kênh màu
    assert tuple(img[0, 0]) == (30, 20, 10)            # OpenCV dùng BGR


def test_load_img_doc_duoc_duong_dan_co_dau_tieng_viet(tmp_path):
    from PIL import Image

    # cv2.imread() không mở được đường dẫn Unicode trên Windows -> phải đọc
    # bằng numpy + imdecode
    p = tmp_path / "ảnh của mẹ 😀.png"
    Image.new("RGB", (5, 4), (200, 100, 50)).save(p)

    img = loc_nu.FemaleFilter()._load_img(str(p))

    assert img is not None
    assert img.shape == (4, 5, 3)


def test_load_img_tra_ve_none_khi_tep_hong(tmp_path):
    p = tmp_path / "hong.png"
    p.write_bytes(b"day khong phai anh")           # nội dung không phải ảnh
    assert loc_nu.FemaleFilter()._load_img(str(p)) is None


def test_load_img_tra_ve_none_khi_thieu_tep(tmp_path):
    assert loc_nu.FemaleFilter()._load_img(
        str(tmp_path / "khong-co.png")) is None
