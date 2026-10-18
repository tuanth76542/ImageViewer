"""Test chức năng phủ các nhánh khó của `xemanh.mainwindow`.

Tập trung vào những chỗ bộ test chính chưa chạm: các phím tắt còn lại, khởi tạo
bằng đường dẫn tệp ảnh, chọn thư mục / mở thư mục rỗng, các hàm zoom-xoay khi
chưa có ảnh, hiệu ứng Aero, nhánh lỗi/hủy của luồng lọc nữ và `closeEvent`.

Mọi hộp thoại của Qt (`QMessageBox`, `QProgressDialog`, `QFileDialog`) đều được
thay bằng đồ giả: ở chế độ offscreen, hộp thoại thật sẽ **treo test**.
"""
import os
import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QShowEvent

import viewer_qt as V

from xemanh import mainwindow as MW

pytestmark = pytest.mark.functional


# ------------------------------------------------------------------ tiện ích
def _bam(win, key, mod=Qt.NoModifier):
    win.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, key, mod))


def _ghi_lai(monkeypatch, doi_tuong, *ten):
    """Thay vài hàm của `doi_tuong` bằng bản chỉ ghi lại lời gọi."""
    goi = []

    def ghi(ten_ham):
        return lambda *a, **k: goi.append((ten_ham, a))

    for t in ten:
        monkeypatch.setattr(doi_tuong, t, ghi(t))
    return goi


class TinHieuHong:
    """Giả tín hiệu: `disconnect()` luôn ném lỗi (như tín hiệu chưa nối gì)."""

    def disconnect(self, *a):
        raise RuntimeError("tín hiệu chưa được nối")


class ProgressGia:
    """Giả `QProgressDialog`: đủ hàm để mainwindow gọi, không hiện cửa sổ thật."""

    def __init__(self, *a, **k):
        self.canceled = TinHieuHong()

    def setWindowTitle(self, *a):
        pass

    def setMinimumWidth(self, *a):
        pass

    def setValue(self, v):
        pass

    def setMaximum(self, *a):
        pass

    def setLabelText(self, *a):
        pass

    def show(self):
        pass

    def close(self):
        pass


# ------------------------------------------------- khởi tạo & mở thư mục
def test_khoi_tao_bang_duong_dan_tep_anh_mo_ca_thu_muc(qapp, folder):
    w = V.MainWindow(start_path=os.path.join(folder, "anh_01.jpg"))
    qapp.processEvents()
    try:
        assert len(w.image_list) == 3
        assert os.path.basename(w.image_list[w.index]) == "anh_01.jpg"
    finally:
        w.close()
        qapp.processEvents()


def test_khoi_tao_bang_duong_dan_khong_ton_tai_thi_o_man_hinh_chao(qapp, tmp_path):
    # không phải thư mục cũng không phải tệp -> bỏ qua, không ném lỗi
    w = V.MainWindow(start_path=str(tmp_path / "khong-ton-tai.jpg"))
    qapp.processEvents()
    try:
        assert w.image_list == []
        assert w.index == -1
    finally:
        w.close()
        qapp.processEvents()


def test_choose_folder_mo_thu_muc_nguoi_dung_chon(win, monkeypatch, folder, qapp):
    monkeypatch.setattr(MW.QFileDialog, "getExistingDirectory",
                        lambda *a, **k: folder)
    win.choose_folder()
    qapp.processEvents()
    assert win.folder == folder
    assert len(win.image_list) == 3


def test_choose_folder_huy_thi_khong_lam_gi(win, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "open_folder")
    monkeypatch.setattr(MW.QFileDialog, "getExistingDirectory", lambda *a, **k: "")
    win.choose_folder()
    assert goi == []


def test_open_folder_rong_thi_bao_khong_co_anh(empty_win, monkeypatch, tmp_path):
    da_bao = []
    monkeypatch.setattr(MW.QMessageBox, "information",
                        lambda *a, **k: da_bao.append(a[2]))

    empty_win.open_folder(str(tmp_path))       # tmp_path không có ảnh nào

    assert da_bao and "không chứa file ảnh nào" in da_bao[0]
    assert empty_win.image_list == []


def test_mo_thu_muc_chon_ten_khong_khop_thi_lay_anh_dau(win, folder):
    win.open_folder(folder, select="khong-co-ai.jpg")
    assert win.index == 0


def test_open_dropped_bo_qua_khi_khong_co_anh(empty_win, monkeypatch, tmp_path):
    goi = _ghi_lai(monkeypatch, empty_win, "open_folder")
    tep = tmp_path / "ghi_chu.txt"
    tep.write_text("khong phai anh")

    empty_win.open_dropped([str(tep), str(tmp_path / "khong-ton-tai.jpg")])

    assert goi == []
    assert empty_win.image_list == []


# ------------------------------------------------- hiển thị khi chưa có ảnh
def test_show_current_khi_danh_sach_rong_thi_hien_man_hinh_chao(win, qapp):
    win.image_list = []
    win.index = -1
    win.show_current()
    assert win.welcome.isVisible()
    assert not win.info_pill.isVisible()


def test_show_current_bao_loi_khi_doc_anh_hong(win, tmp_path):
    hong = tmp_path / "hong.jpg"
    hong.write_bytes(b"day khong phai anh")
    win.image_list = [str(hong)]
    win.index = 0

    win.show_current()

    assert win.toast_lbl.text().startswith("Không đọc được")


def test_compute_fit_va_apply_view_khi_chua_co_anh(empty_win):
    assert empty_win.pil_image is None
    empty_win._compute_fit()                   # phải bỏ qua, không lỗi
    empty_win._apply_view()
    assert empty_win.zoom == 1.0


def test_hien_lai_lop_phu_khi_chua_co_anh(empty_win):
    empty_win.reveal_overlays()
    assert empty_win.topbar.isVisible()
    assert not empty_win.info_pill.isVisible()  # chưa có ảnh -> không có thẻ


# ------------------------------------------------- zoom / xoay khi có và chưa có ảnh
def test_phim_di_chuyen_gom_len_xuong_va_space(win, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "prev_image", "next_image")
    for key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Space):
        _bam(win, key)
    assert [t for t, _ in goi] == ["prev_image", "next_image", "next_image"]


def test_phim_zoom_va_xoay_dinh_tuyen_dung_ham(win, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "zoom_in", "zoom_out", "zoom_fit",
                   "zoom_100", "rotate_image")
    for key in (Qt.Key_Plus, Qt.Key_Equal, Qt.Key_Minus, Qt.Key_0, Qt.Key_1,
                Qt.Key_R):
        _bam(win, key)
    assert [t for t, _ in goi] == ["zoom_in", "zoom_in", "zoom_out", "zoom_fit",
                                   "zoom_100", "rotate_image"]


def test_phim_chuc_nang_f5_f11_loc_nu_tro_giup(win, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "toggle_slideshow", "toggle_fullscreen",
                   "toggle_female_filter", "show_help")
    for key in (Qt.Key_F5, Qt.Key_F11, Qt.Key_F, Qt.Key_H, Qt.Key_F1):
        _bam(win, key)
    assert [t for t, _ in goi] == ["toggle_slideshow", "toggle_fullscreen",
                                   "toggle_female_filter", "show_help", "show_help"]


def test_phim_ctrl_o_va_ctrl_a(win, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "choose_folder", "toggle_aero")
    _bam(win, Qt.Key_O, Qt.ControlModifier)
    _bam(win, Qt.Key_A, Qt.ControlModifier)
    assert [t for t, _ in goi] == ["choose_folder", "toggle_aero"]


def test_phim_la_thi_nhuong_lop_cha(win):
    truoc = win.index
    _bam(win, Qt.Key_Z)                        # phím không gắn tác vụ nào
    assert win.index == truoc


def test_esc_chi_thoat_toan_man_hinh_khi_dang_bat(win):
    assert win._f11_full is False
    _bam(win, Qt.Key_Escape)                   # chưa toàn màn hình -> nhường lớp cha
    assert win._f11_full is False

    win.toggle_fullscreen()
    assert win._f11_full is True
    _bam(win, Qt.Key_Escape)                   # đang toàn màn hình -> thoát
    assert win._f11_full is False


def test_step_va_zoom_xoay_bo_qua_khi_chua_co_anh(empty_win):
    empty_win.next_image()
    empty_win.prev_image()
    empty_win.wheel_zoom(1.5)
    empty_win.zoom_in()
    empty_win.zoom_out()
    empty_win.zoom_fit()
    empty_win.zoom_100()
    empty_win.rotate_image()

    assert empty_win.index == -1               # không dịch chuyển khi rỗng
    assert empty_win.zoom == 1.0
    assert empty_win.rotation == 0


def test_pinch_zoom_bo_qua_he_so_bang_mot_hoac_rong(win):
    win.zoom_100()
    truoc = win.zoom
    win.pinch_zoom(1.0)                        # hệ số 1 -> không đổi
    win.pinch_zoom(0)                          # hệ số rỗng -> không đổi
    assert win.zoom == truoc


# ------------------------------------------------- hiệu ứng Aero
def test_show_event_bat_lai_hieu_ung_khi_aero_dang_bat(empty_win, monkeypatch):
    goi = []
    monkeypatch.setattr(MW, "enable_window_blur", lambda w: goi.append(w))
    empty_win._aero_on = True

    empty_win.showEvent(QShowEvent())

    assert goi == [empty_win]
    empty_win._aero_on = False


def test_toggle_aero_bat_roi_tat(empty_win, monkeypatch):
    goi = []
    monkeypatch.setattr(MW, "aero_available", lambda: True)
    monkeypatch.setattr(MW, "enable_window_blur",
                        lambda w: goi.append(("bat", w)))
    monkeypatch.setattr(MW, "disable_window_blur",
                        lambda w: goi.append(("tat", w)))
    empty_win._aero_on = False

    empty_win.toggle_aero()
    assert empty_win._aero_on is True
    assert goi == [("bat", empty_win)]
    assert "bật nền kính mờ" in empty_win.toast_lbl.text()

    empty_win.toggle_aero()
    assert empty_win._aero_on is False
    assert goi[-1] == ("tat", empty_win)
    assert "Đã tắt" in empty_win.toast_lbl.text()


# ------------------------------------------------- slideshow
def test_dong_trinh_chieu_tra_ve_toan_man_hinh(win, qapp, pump):
    win.toggle_fullscreen()
    assert win._f11_full is True                  # mở trình chiếu lúc đang F11

    win.toggle_slideshow()
    qapp.processEvents()
    assert win.slide_dlg is not None

    win.toggle_slideshow()                        # F5 lần nữa để đóng
    assert pump(lambda: win.slide_dlg is None)
    assert win._f11_full is True                  # quay lại đúng toàn màn hình

    win.toggle_fullscreen()


# ------------------------------------------------- lọc nữ: các nhánh
def test_khong_bat_loc_khi_luong_dang_chay(win, monkeypatch):
    goi = []

    class LuongGia:
        def isRunning(self):
            return True

        def wait(self, ms):
            goi.append(ms)
            return True

    win.filter_thread = LuongGia()
    win.toggle_female_filter()
    assert win.filter_female is False             # đang chạy -> bấm không có tác dụng
    win.filter_thread = None


def test_bat_loc_nu_bao_thieu_opencv(win, monkeypatch):
    da_bao = []
    monkeypatch.setattr(MW.QMessageBox, "critical",
                        lambda *a, **k: da_bao.append(a[2]))
    monkeypatch.setitem(sys.modules, "cv2", None)   # `import cv2` ném ImportError

    win.toggle_female_filter()

    assert win.filter_thread is None
    assert da_bao and "OpenCV" in da_bao[0]


def test_bat_loc_nu_khi_nguoi_dung_khong_tai_model(win, monkeypatch):
    import loc_nu

    monkeypatch.setattr(loc_nu, "missing_models", lambda: ["fairface_res34.onnx"])
    monkeypatch.setattr(MW.QMessageBox, "question",
                        lambda *a, **k: MW.QMessageBox.No)

    win.toggle_female_filter()

    assert win.filter_thread is None               # hủy tải -> không chạy lọc
    assert win.progress is None


def test_bat_loc_nu_khong_giu_anh_nao(win, qapp, pump, monkeypatch):
    """Chạy trọn luồng lọc với hộp thoại tiến độ giả: không ảnh nào được giữ."""
    import loc_nu

    da_bao = []
    monkeypatch.setattr(MW, "QProgressDialog", ProgressGia)
    monkeypatch.setattr(MW.QMessageBox, "information",
                        lambda *a, **k: da_bao.append(a[2]))
    monkeypatch.setattr(loc_nu, "missing_models", lambda: ["fairface_res34.onnx"])
    monkeypatch.setattr(MW.QMessageBox, "question",
                        lambda *a, **k: MW.QMessageBox.Yes)   # đồng ý tải model
    monkeypatch.setattr(loc_nu, "download_models", lambda *a, **k: None)

    def loc_khong_giu(paths, on_progress=None, **k):
        for i, p in enumerate(paths):
            if on_progress:
                on_progress(i + 1, len(paths), p, False)
        return []

    monkeypatch.setattr(loc_nu, "filter_female", loc_khong_giu)

    win.toggle_female_filter()
    assert win.progress is not None                # hộp thoại giả đã được tạo

    assert pump(lambda: bool(da_bao), timeout_ms=30000)
    assert "không tìm thấy ảnh nữ nào" in da_bao[0]
    assert win.filter_female is False              # không bật lọc
    assert win.progress is None                    # đã đóng hộp thoại


def test_filter_tick_va_close_progress_bo_qua_khi_khong_con_hop_thoai(win):
    win.progress = None
    win._filter_tick(1, 3, "a.jpg", True)          # không lỗi
    win._close_progress()                          # không lỗi
    assert win.progress is None


def test_close_progress_bo_qua_loi_khi_dong_hop_thoai(win):
    class ProgressHong:
        def close(self):
            raise RuntimeError("hộp thoại đã bị hủy")

    win.progress = ProgressHong()
    win._close_progress()
    assert win.progress is None


def test_filter_failed_dong_hop_thoai_va_bao_loi(win, monkeypatch):
    da_bao = []
    monkeypatch.setattr(MW.QMessageBox, "critical",
                        lambda *a, **k: da_bao.append(a[2]))
    win.progress = ProgressGia()

    win._filter_failed("bộ lọc hỏng")

    assert da_bao == ["bộ lọc hỏng"]
    assert win.progress is None


# ------------------------------------------------- hiện dần kết quả lọc nữ
def test_anh_dang_xem_xu_ly_chi_so_ngoai_danh_sach(empty_win):
    assert empty_win._anh_dang_xem() is None          # chưa có ảnh nào
    empty_win.image_list = ["a.jpg"]
    empty_win.index = -1
    assert empty_win._anh_dang_xem() is None          # chỉ số âm
    empty_win.index = 5
    assert empty_win._anh_dang_xem() is None          # vượt quá danh sách
    empty_win.index = 0
    assert empty_win._anh_dang_xem() == "a.jpg"


def test_refresh_filter_meta_bo_qua_khi_khong_co_anh(empty_win):
    empty_win._refresh_filter_meta()                  # không lỗi, không đổi gì
    assert empty_win.windowTitle() == "Phần Mềm Xem Ảnh"


def test_filter_found_cho_quet_xong_khi_chua_du_anh_nu(win):
    truoc = list(win.image_list)
    win._filter_found(truoc[:2])                      # < SHOW_AFTER -> chưa hiện gì
    assert win.image_list == truoc
    assert win.filter_female is False


def test_filter_found_hien_anh_nu_dau_khi_anh_dang_xem_khong_phai_nu(
        win, qapp, make_images, tmp_path):
    win.open_folder(make_images(str(tmp_path / "nhieu"), 12))
    win.index = 1                                     # đang xem ảnh ở vị trí lẻ (nam)
    win.show_current()
    kept = [p for i, p in enumerate(win.all_images) if i % 2 == 0]

    win._filter_found(kept)

    assert win.filter_female is True
    assert win.image_list == kept
    assert win.index == 0                             # nhảy về ảnh nữ đầu tiên
    assert win.filter_btn.text() == "👩 ✕"


def test_filter_failed_giu_lai_anh_nu_da_hien_dan(win, monkeypatch):
    da_bao = []
    monkeypatch.setattr(MW.QMessageBox, "critical",
                        lambda *a, **k: da_bao.append(a[2]))
    win.progress = ProgressGia()
    win.filter_female = True
    win.image_list = ["a.jpg", "b.jpg"]

    win._filter_failed("bộ lọc hỏng")

    assert da_bao == ["bộ lọc hỏng"]
    assert "Lọc dừng giữa chừng" in win.toast_lbl.text()
    assert "2" in win.toast_lbl.text()


def test_filter_done_giu_nguyen_anh_dang_xem(win, qapp):
    """Quét xong: ảnh đang xem còn trong danh sách thì không bị nhảy về đầu."""
    dang_xem = win.all_images[1]
    win.index = 1
    win.show_current()

    win._filter_done([win.all_images[0], dang_xem])

    assert win.image_list[win.index] == dang_xem



# ------------------------------------------------- đóng cửa sổ
def test_close_event_cho_luong_loc_dung_han(empty_win):
    goi = []

    class LuongGia:
        def isRunning(self):
            return True

        def wait(self, ms):
            goi.append(ms)
            return True

    empty_win.filter_thread = LuongGia()
    empty_win.close()

    assert goi == [3000]                           # chờ luồng tối đa 3 giây
    empty_win.filter_thread = None


def test_close_event_bo_qua_loi_khi_hoi_luong_loc(empty_win):
    class LuongHong:
        def isRunning(self):
            raise RuntimeError("luồng đã bị hủy")

    empty_win.filter_thread = LuongHong()
    empty_win.close()                              # nuốt lỗi, vẫn đóng bình thường
    empty_win.filter_thread = None
