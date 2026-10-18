"""Test đơn vị cho luồng nền lọc ảnh nữ (xemanh.filterthread).

Cố ý gọi thẳng ``run()`` trên luồng chính thay vì ``start()``: tín hiệu phát ra
tức thì (cùng luồng -> kết nối kiểu direct) nên test nhanh, xác định, không phải
bơm sự kiện. Luồng do Qt tạo là luồng native nên coverage không theo dõi được,
gọi thẳng như vậy mới đo được độ phủ của tệp này.

Bản chạy thật qua ``start()`` (kiểm tra luồng + tín hiệu qua hàng đợi) nằm ở
``tests/functional/test_filter_flow.py``.
"""
import sys

import pytest

from xemanh.filterthread import FilterThread

pytestmark = pytest.mark.unit


def _duong_dan(tmp_path, n=3):
    return [str(tmp_path / ("anh_%02d.jpg" % i)) for i in range(n)]


def _chay(monkeypatch, paths, *, download=None, loc=None):
    """Chạy `run()` một lần, trả về (đã_giữ, thông_báo_lỗi, tiến_độ)."""
    import loc_nu

    if download is None:
        monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)
    else:
        monkeypatch.setattr(loc_nu, "download_models", download)
    if loc is not None:
        monkeypatch.setattr(loc_nu, "filter_female", loc)

    t = FilterThread(paths)
    ket_qua, loi, tien_do = [], [], []
    t.done.connect(ket_qua.extend)
    t.failed.connect(loi.append)
    t.progressed.connect(lambda d, tong, p, ok: tien_do.append((d, tong, p, ok)))
    t.run()
    return ket_qua, loi, tien_do


def test_run_phat_tien_do_va_danh_sach_giu_lai(monkeypatch, qapp, tmp_path):
    def loc_gia(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            on_progress(i + 1, len(paths), p, i % 2 == 0)
        return [p for i, p in enumerate(paths) if i % 2 == 0]

    paths = _duong_dan(tmp_path)
    ket_qua, loi, tien_do = _chay(monkeypatch, paths, loc=loc_gia)

    assert loi == []
    assert ket_qua == [paths[0], paths[2]]          # chỉ số chẵn
    assert [x[0] for x in tien_do] == [1, 2, 3]     # tiến độ 1..n
    assert [x[1] for x in tien_do] == [3, 3, 3]
    assert [x[3] for x in tien_do] == [True, False, True]


def test_run_bao_loi_khi_tai_model_that_bai(monkeypatch, qapp, tmp_path):
    def hong(*a, **k):
        raise RuntimeError("mất mạng")

    ket_qua, loi, _ = _chay(monkeypatch, _duong_dan(tmp_path, 1), download=hong)

    assert ket_qua == []
    assert len(loi) == 1
    assert "Không tải được model" in loi[0] and "mất mạng" in loi[0]


def test_run_bao_loi_khi_loc_hong(monkeypatch, qapp, tmp_path):
    def hong(*a, **k):
        raise ValueError("model hỏng")

    ket_qua, loi, _ = _chay(monkeypatch, _duong_dan(tmp_path, 1), loc=hong)

    assert ket_qua == []
    assert len(loi) == 1
    assert "Lỗi khi lọc" in loi[0] and "model hỏng" in loi[0]


def test_run_bao_loi_khi_khong_import_duoc_loc_nu(monkeypatch, qapp, tmp_path):
    # None trong sys.modules làm `import loc_nu` ném ImportError
    monkeypatch.setitem(sys.modules, "loc_nu", None)

    t = FilterThread(_duong_dan(tmp_path, 1))
    loi = []
    t.failed.connect(loi.append)
    t.run()

    assert len(loi) == 1
    assert "Không tải được module lọc" in loi[0]


# ------------------------------------------- tín hiệu `found` (hiện dần kết quả)

def _chay_co_found(monkeypatch, paths, loc):
    """Như `_chay` nhưng trả thêm danh sách các lần phát tín hiệu `found`."""
    import loc_nu

    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)
    monkeypatch.setattr(loc_nu, "filter_female", loc)

    t = FilterThread(paths)
    found, ket_qua = [], []
    t.found.connect(found.append)
    t.done.connect(ket_qua.extend)
    t.run()
    return found, ket_qua


def test_found_phat_danh_sach_tich_luy_theo_thu_tu_anh(monkeypatch, qapp, tmp_path):
    def loc_gia(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            on_progress(i + 1, len(paths), p, i % 2 == 0)
        return [p for i, p in enumerate(paths) if i % 2 == 0]

    paths = _duong_dan(tmp_path, 6)
    found, ket_qua = _chay_co_found(monkeypatch, paths, loc_gia)

    # mỗi ảnh nữ mới -> một lần phát, danh sách tích luỹ dần
    assert found == [[paths[0]], [paths[0], paths[2]], [paths[0], paths[2], paths[4]]]
    assert ket_qua == found[-1]          # kết quả cuối khớp lần phát cuối


def test_found_sap_lai_theo_thu_tu_goc_khi_tien_do_phat_dao(monkeypatch, qapp, tmp_path):
    """Cache phát tiến độ trước ảnh mới quét -> `found` vẫn phải theo thứ tự gốc."""
    def loc_gia(paths, on_progress=None, **k):
        # phát ngược thứ tự (như ảnh lấy từ cache xong trước)
        on_progress(1, len(paths), paths[2], True)
        on_progress(2, len(paths), paths[1], False)
        on_progress(3, len(paths), paths[0], True)
        return [paths[0], paths[2]]

    paths = _duong_dan(tmp_path, 3)
    found, ket_qua = _chay_co_found(monkeypatch, paths, loc_gia)

    assert found == [[paths[2]], [paths[0], paths[2]]]
    assert ket_qua == [paths[0], paths[2]]      # khớp danh sách hiện dần cuối cùng


def test_found_bo_qua_duong_dan_la_va_anh_nu_lap_lai(monkeypatch, qapp, tmp_path):
    def loc_gia(paths, on_progress=None, **k):
        on_progress(1, 3, str(tmp_path / "khong-thuoc-danh-sach.jpg"), True)
        on_progress(2, 3, paths[0], True)
        on_progress(3, 3, paths[0], True)        # cùng ảnh nữ, phát lần hai
        return [paths[0]]

    paths = _duong_dan(tmp_path, 1)
    found, ket_qua = _chay_co_found(monkeypatch, paths, loc_gia)

    assert found == [[paths[0]]]                 # không phát thừa
    assert ket_qua == [paths[0]]


def test_khong_phat_found_khi_khong_co_anh_nu(monkeypatch, qapp, tmp_path):
    def loc_gia(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            on_progress(i + 1, len(paths), p, False)
        return []

    paths = _duong_dan(tmp_path, 3)
    found, ket_qua = _chay_co_found(monkeypatch, paths, loc_gia)

    assert found == []
    assert ket_qua == []

