"""Test chức năng lọc ảnh nữ: FilterThread, luồng tín hiệu và nút lọc.

Model được giả lập (giữ ảnh có chỉ số chẵn) nên test nhanh, không cần 430MB
model và không cần GPU.
"""
import os
import threading

import pytest
from PIL import Image

import viewer_qt as V

pytestmark = pytest.mark.functional


def _gia_lap_model(monkeypatch):
    """Thay loc_nu bằng bản giả: 'giữ' các ảnh có chỉ số chẵn."""
    import loc_nu

    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)
    monkeypatch.setattr(loc_nu, "missing_models", lambda *a, **k: False)

    def fake_filter(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            if on_progress:
                on_progress(i + 1, len(paths), p, i % 2 == 0)
        return [p for i, p in enumerate(paths) if i % 2 == 0]

    monkeypatch.setattr(loc_nu, "filter_female", fake_filter)
    return loc_nu


def _duong_dan(folder, n=3):
    return [os.path.join(folder, "anh_%02d.jpg" % i) for i in range(n)]


# ---------------- luồng nền ----------------

def test_filter_thread_phat_tin_hieu_ket_thuc(folder, monkeypatch, pump):
    _gia_lap_model(monkeypatch)
    res = {}
    t = V.FilterThread(_duong_dan(folder))
    t.done.connect(lambda kept: res.update(kept=kept))
    t.failed.connect(lambda msg: res.update(failed=msg))
    t.start()
    assert pump(lambda: "kept" in res or "failed" in res, timeout_ms=30000)
    t.wait()
    assert "failed" not in res
    assert len(res["kept"]) == 2                 # chỉ số chẵn: 0 và 2


def test_filter_thread_bao_loi_khi_loc_hong(folder, monkeypatch, pump):
    import loc_nu

    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)

    def boom(*a, **k):
        raise RuntimeError("model hỏng")

    monkeypatch.setattr(loc_nu, "filter_female", boom)
    res = {}
    t = V.FilterThread(_duong_dan(folder, 1))
    t.failed.connect(lambda msg: res.update(failed=msg))
    t.start()
    assert pump(lambda: "failed" in res, timeout_ms=30000)
    t.wait()
    assert "model hỏng" in res["failed"]


def test_filter_thread_bao_loi_khi_tai_model_that_bai(folder, monkeypatch, pump):
    import loc_nu

    def boom(*a, **k):
        raise RuntimeError("mất mạng")

    monkeypatch.setattr(loc_nu, "download_models", boom)
    res = {}
    t = V.FilterThread(_duong_dan(folder, 1))
    t.failed.connect(lambda msg: res.update(failed=msg))
    t.start()
    assert pump(lambda: "failed" in res, timeout_ms=30000)
    t.wait()
    assert "mất mạng" in res["failed"]


# ---------------- luồng giao diện ----------------

def test_bat_loc_chi_hien_anh_duoc_giu(win, qapp, monkeypatch, pump):
    _gia_lap_model(monkeypatch)
    assert win.filter_female is False
    win.toggle_female_filter()
    assert win.filter_thread is not None
    assert pump(lambda: win.filter_female, timeout_ms=30000)
    win.filter_thread.wait(5000)
    assert len(win.all_images) == 3              # danh sách gốc vẫn còn
    assert len(win.image_list) == 2              # chỉ còn ảnh được giữ
    assert win.index == 0
    assert win.filter_btn.text() == "👩 ✕"
    assert win.filter_btn.property("active") == "true"


def test_tat_loc_hien_lai_toan_bo_anh(win, qapp, monkeypatch, pump):
    _gia_lap_model(monkeypatch)
    win.toggle_female_filter()
    assert pump(lambda: win.filter_female, timeout_ms=30000)
    win.filter_thread.wait(5000)
    assert len(win.image_list) == 2
    win.toggle_female_filter()                   # tắt lọc
    assert win.filter_female is False
    assert win.image_list == win.all_images
    assert win.index == 0
    assert win.filter_btn.text() == "👩"
    assert win.filter_btn.property("active") == "false"


def test_loc_khi_chua_mo_anh_thi_chi_bao_thong_bao(empty_win):
    empty_win.toggle_female_filter()
    assert empty_win.filter_thread is None
    assert empty_win.toast.isVisible()


# ---------------- hiện dần kết quả + quét delta ----------------

def _dat_quy_tac_nu(paths, giu):
    """Đặt quy tắc giả: ảnh ở vị trí chẵn là nữ."""
    for i, p in enumerate(paths):
        giu[p] = (i % 2 == 0)


def _gia_lap_loc_tung_buoc(monkeypatch, giu, cho_phep, so_nu_roi_moi_dung=5):
    """Giả `loc_nu.filter_female`: báo tiến độ tới khi đủ N ảnh nữ thì ĐỨNG CHỜ.

    Cần vậy vì bộ lọc thật (dù đã giả lập model) chạy xong trong vài ms, không
    kịp quan sát trạng thái "luồng vẫn đang quét mà danh sách đã có ảnh".
    """
    import loc_nu

    def fake_filter(paths, on_progress=None, **k):
        giu_lai, da_bao = [], 0
        for i, p in enumerate(paths):
            ok = giu[p]
            if ok:
                giu_lai.append(p)
            da_bao = i + 1
            if on_progress:
                on_progress(da_bao, len(paths), p, ok)
            if len(giu_lai) >= so_nu_roi_moi_dung:
                break
        cho_phep.wait(timeout=30)               # vẫn đang quét
        for i, p in enumerate(paths[da_bao:], start=da_bao):
            ok = giu[p]
            if ok:
                giu_lai.append(p)
            if on_progress:
                on_progress(i + 1, len(paths), p, ok)
        return giu_lai

    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)
    monkeypatch.setattr(loc_nu, "missing_models", lambda *a, **k: False)
    monkeypatch.setattr(loc_nu, "filter_female", fake_filter)


def _gia_lap_loc_co_cache(monkeypatch, giu):
    """Giả `loc_nu.filter_female` có cache (giữ nguyên hợp đồng với giao diện).

    Cố ý KHÔNG dùng `loc_nu.filter_female` thật ở đây: nó mở ThreadPoolExecutor
    bên trong luồng Qt nên vừa chậm vừa dễ va chạm với việc bơm sự kiện liên tục
    của test. Phần cache thật (khoá theo đường dẫn + size + mtime, chỉ quét ảnh
    mới) được kiểm ở `tests/unit/test_loc_nu_models.py`.
    """
    import loc_nu

    cache, da_suy_luan = {}, []

    def fake_filter(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            if p not in cache:
                da_suy_luan.append(p)
                cache[p] = giu.get(p, False)
            if on_progress:
                on_progress(i + 1, len(paths), p, cache[p])
        return [p for p in paths if cache[p]]

    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)
    monkeypatch.setattr(loc_nu, "missing_models", lambda *a, **k: False)
    monkeypatch.setattr(loc_nu, "filter_female", fake_filter)
    return da_suy_luan


def _anh_nu(all_images, giu):
    return [p for p in all_images if giu.get(p, False)]


def _xả_su_kien(qapp, lan=3):
    """Xả hết sự kiện Qt còn nằm trong hàng đợi.

    Bắt buộc trước khi test kết thúc: tín hiệu của luồng lọc được phát theo hàng
    đợi, nếu còn sót lại thì lúc được xử lý nó sẽ gọi vào cửa sổ đã bị đóng
    (object Qt đã hủy) -> crash cả tiến trình pytest (bài học trong conftest.py).
    """
    for _ in range(lan):
        qapp.processEvents()


def _cho_quet_xong(win, pump, qapp):
    """Chờ tới khi hộp tiến độ đóng (`_filter_done` đã chạy) rồi xả hết sự kiện."""
    xong = pump(lambda: win.progress is None and not win.filter_thread.isRunning(),
                timeout_ms=30000)
    _xả_su_kien(qapp)
    win.filter_thread.wait(5000)
    return xong


def test_hien_dan_du_5_anh_nu_khi_luong_chua_quet_xong(win, qapp, pump, monkeypatch,
                                                       make_images, tmp_path):
    win.open_folder(make_images(str(tmp_path / "nhieu"), 12))
    giu, cho_phep = {}, threading.Event()
    _dat_quy_tac_nu(win.all_images, giu)
    _gia_lap_loc_tung_buoc(monkeypatch, giu, cho_phep)

    win.toggle_female_filter()
    assert pump(lambda: win.filter_female, timeout_ms=30000)

    # Đã hiện 5 ảnh nữ ĐẦU TIÊN trong khi luồng nền vẫn đang quét
    assert win.filter_thread.isRunning()
    assert win.progress is not None                      # hộp tiến độ vẫn mở
    assert win.image_list == _anh_nu(win.all_images, giu)[:5]
    assert win.index == 0
    assert win.filter_btn.text() == "👩 ✕"
    assert "đang quét tiếp" in win.toast_lbl.text()

    cho_phep.set()
    assert _cho_quet_xong(win, pump, qapp)

    # Quét xong: danh sách y hệt hành vi cũ (cùng tập, cùng thứ tự thư mục)
    assert win.image_list == _anh_nu(win.all_images, giu)
    assert win.progress is None


def test_dong_hop_tien_do_khong_dung_quet(win, qapp, pump, monkeypatch,
                                          make_images, tmp_path):
    win.open_folder(make_images(str(tmp_path / "nhieu"), 12))
    giu, cho_phep = {}, threading.Event()
    _dat_quy_tac_nu(win.all_images, giu)
    _gia_lap_loc_tung_buoc(monkeypatch, giu, cho_phep)

    win.toggle_female_filter()
    assert pump(lambda: win.progress is not None, timeout_ms=30000)
    win._close_progress()                        # người dùng bấm "Đóng"
    assert win.progress is None

    cho_phep.set()
    assert pump(lambda: win.filter_female and not win.filter_thread.isRunning(),
                timeout_ms=30000)
    _xả_su_kien(qapp)                            # quét vẫn chạy tiếp, báo kết quả
    win.filter_thread.wait(5000)

    assert win.image_list == _anh_nu(win.all_images, giu)


def test_giu_nguyen_anh_dang_xem_khi_danh_sach_dai_them(win, qapp, pump, monkeypatch,
                                                        make_images, tmp_path):
    win.open_folder(make_images(str(tmp_path / "nhieu"), 12))
    giu, cho_phep = {}, threading.Event()
    _dat_quy_tac_nu(win.all_images, giu)
    _gia_lap_loc_tung_buoc(monkeypatch, giu, cho_phep)

    dang_xem = win.all_images[4]                 # ảnh nữ ở giữa thư mục
    win.index = 4
    win.show_current()

    win.toggle_female_filter()
    assert pump(lambda: win.filter_female, timeout_ms=30000)

    cho_phep.set()                               # danh sách dài thêm từ đây
    assert _cho_quet_xong(win, pump, qapp)

    assert win.image_list[win.index] == dang_xem  # vẫn đang xem đúng ảnh đó


def test_bam_lan_hai_khong_suy_luan_lai_va_chi_quet_anh_moi(win, qapp, pump, monkeypatch,
                                                            make_images, tmp_path):
    win.open_folder(make_images(str(tmp_path / "anh"), 12))
    giu = {}
    _dat_quy_tac_nu(win.all_images, giu)
    da_suy_luan = _gia_lap_loc_co_cache(monkeypatch, giu)

    win.toggle_female_filter()
    assert _cho_quet_xong(win, pump, qapp)
    assert len(da_suy_luan) == 12                # lần đầu: suy luận cả thư mục
    assert win.image_list == _anh_nu(win.all_images, giu)

    # Bấm F lần hai trên cùng thư mục: 0 lần suy luận, danh sách có ngay
    win.toggle_female_filter()                   # tắt lọc
    assert win.filter_female is False
    win.toggle_female_filter()                   # bật lại
    assert _cho_quet_xong(win, pump, qapp)
    assert len(da_suy_luan) == 12                # không suy luận lại ảnh cũ
    assert win.image_list == _anh_nu(win.all_images, giu)

    # Thêm ảnh mới: chỉ suy luận ảnh mới, kết quả cũ giữ nguyên
    moi = os.path.join(win.folder, "anh_12.jpg")
    Image.new("RGB", (320, 240), (10, 10, 10)).save(moi)
    win.open_folder(win.folder)
    giu[moi] = True
    assert len(win.all_images) == 13

    win.toggle_female_filter()
    assert _cho_quet_xong(win, pump, qapp)
    assert da_suy_luan[12:] == [moi]             # chỉ ảnh mới phải suy luận
    assert win.image_list == _anh_nu(win.all_images, giu)


