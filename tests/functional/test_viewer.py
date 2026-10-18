"""Test chức năng giao diện: mở thư mục, điều hướng, zoom, lớp phủ, trợ giúp.

Chạy ở chế độ offscreen (xem tests/conftest.py) nên không cần màn hình thật.
"""
import os

import pytest

import viewer_qt as V

pytestmark = pytest.mark.functional


# ---------------- mở thư mục ----------------

def test_mo_thu_muc_nap_dung_danh_sach(win):
    assert len(win.all_images) == 3
    assert len(win.image_list) == 3
    assert win.index == 0
    assert not win.welcome.isVisible()          # màn hình chào đã ẩn


def test_man_hinh_chao_hien_khi_chua_co_anh(empty_win):
    assert empty_win.image_list == []
    assert empty_win.welcome.isVisible()
    assert not empty_win.info_pill.isVisible()   # không có ảnh -> không có thẻ


def test_mo_thu_muc_tu_man_hinh_chao_hien_lai_the_thong_tin(empty_win, folder,
                                                            qapp):
    empty_win.open_folder(folder)
    qapp.processEvents()
    assert not empty_win.welcome.isVisible()
    assert empty_win.info_pill.isVisible()
    assert empty_win.topbar.isVisible()


def test_mo_truc_tiep_mot_tep_anh(win, folder):
    # mở 1 tệp -> mở cả thư mục và chọn đúng tệp đó
    win.open_folder(folder, select="anh_01.jpg")
    assert win.index == 1
    assert os.path.basename(win.image_list[win.index]) == "anh_01.jpg"


def test_keo_tha_thu_muc_mo_noi_dung(empty_win, folder, qapp):
    empty_win.open_dropped([folder])
    qapp.processEvents()
    assert len(empty_win.image_list) == 3
    assert not empty_win.welcome.isVisible()


def test_keo_tha_tep_anh_chon_dung_anh(empty_win, folder, qapp):
    target = os.path.join(folder, "anh_02.jpg")
    empty_win.open_dropped([target])
    qapp.processEvents()
    assert os.path.basename(empty_win.image_list[empty_win.index]) == "anh_02.jpg"


# ---------------- thẻ thông tin & điều hướng ----------------

def test_the_thong_tin_phan_anh_anh_hien_tai(win):
    assert win.info_name.text() == "anh_00.jpg"
    assert win.info_meta.text().startswith("1 / 3")
    assert "320×240" in win.info_meta.text()


def test_dieu_huong_vong_tro_lai_va_cap_nhat_the(win):
    win.next_image()
    assert win.index == 1
    assert win.info_name.text() == "anh_01.jpg"
    win.next_image()
    win.next_image()
    assert win.index == 0                       # vòng xuôi
    win.prev_image()
    assert win.index == 2                       # vòng ngược
    assert win.info_name.text() == "anh_02.jpg"


def test_danh_sach_mot_anh_khong_bi_loi(empty_win, tmp_path, make_images):
    make_images(str(tmp_path / "le"), 1)
    empty_win.open_folder(str(tmp_path / "le"))
    empty_win.next_image()
    empty_win.prev_image()
    assert empty_win.index == 0


# ---------------- zoom & xoay ----------------

def test_zoom_va_xoay(win):
    z0 = win.zoom
    win.zoom_in()
    assert win.zoom > z0
    win.zoom_out()
    win.zoom_out()
    assert win.zoom < z0
    win.zoom_fit()
    assert win.fit_mode is True
    win.zoom_100()
    assert win.zoom == 1.0 and win.fit_mode is False
    assert win.zoom_pct.text() == "100%"
    for _ in range(4):
        win.rotate_image()
    assert win.rotation == 0                     # xoay 4 lần quay về ban đầu


def test_zoom_bang_lan_chuot_va_pinch(win):
    win.zoom_100()
    win.zoom = 1.0
    win.wheel_zoom(1.5)                          # Ctrl + lăn chuột
    assert win.zoom == pytest.approx(1.5)
    assert win.zoom_pct.text() == "150%"
    win.pinch_zoom(2.0)                          # pinch touchpad
    assert win.zoom == pytest.approx(3.0)
    win.wheel_zoom(1000.0)                       # có trần
    assert win.zoom == 20.0


def test_xoay_cap_nhat_lai_kich_thuoc_the(win):
    win.rotate_image()
    assert win.rotation == 90
    assert "240×320" in win.info_meta.text()      # đã đổi chiều


# ---------------- lớp phủ, thông báo, trợ giúp ----------------

def test_lop_phu_an_hien(win):
    win.reveal_overlays()
    assert win.topbar.isVisible()
    assert win.info_pill.isVisible()
    win._hide_overlays()
    assert not win.topbar.isVisible()
    assert not win.info_pill.isVisible()


def test_thong_bao_noi_hien_va_tu_an(win):
    win.status_msg("Xin chào")
    assert win.toast_lbl.text() == "Xin chào"
    assert win.toast.isVisible()
    win.status_msg("")                           # chuỗi rỗng -> không làm gì
    assert win.toast_lbl.text() == "Xin chào"


def test_bang_tro_giup_mo_va_dong(win):
    win.show_help()
    assert win.help_dlg is not None
    assert win.help_dlg.isVisible()
    win.show_help()                              # gọi lần 2 không tạo thêm
    assert win.help_dlg is not None
    win.help_dlg.close()
    win.help_dlg = None


def test_bang_tro_giup_dat_giua_cua_so_cha(win, qapp):
    win.show_help()
    qapp.processEvents()
    dlg = win.help_dlg
    assert dlg.parent() is win
    # showEvent đặt hộp thoại quanh tâm cửa sổ cha (có thể lệch chút do viền)
    tam_cha = win.geometry().center()
    assert abs(dlg.geometry().center().x() - tam_cha.x()) < 200
    dlg.close()
    win.help_dlg = None


def test_bang_tro_giup_khong_co_cua_so_cha_van_mo_duoc(qapp):
    from xemanh.helpdialog import HelpDialog

    dlg = HelpDialog()                           # parent = None -> showEvent bỏ qua
    dlg.show()
    qapp.processEvents()
    try:
        assert dlg.parent() is None
        assert dlg.isVisible()
    finally:
        dlg.close()


def test_phim_tat_trong_bang_tro_giup(win, qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    win.show_help()
    dlg = win.help_dlg

    def bam(key):
        dlg.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, key, Qt.NoModifier))

    bam(Qt.Key_Z)                                # phím lạ -> nhường lớp cha
    assert dlg.isVisible()
    bam(Qt.Key_F1)                               # F1 đóng bảng trợ giúp
    assert not dlg.isVisible()
    win.help_dlg = None


def test_toan_man_hinh_bat_va_tat(win):
    assert win._f11_full is False
    win.toggle_fullscreen()
    assert win._f11_full is True
    win.toggle_fullscreen()
    assert win._f11_full is False


# ---------------- phím tắt ----------------

def test_phim_tat_dieu_huong_va_dong_bo_giao_dien(win, qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    def press(key):
        win.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, key, Qt.NoModifier))

    press(Qt.Key_Right)
    assert win.index == 1
    press(Qt.Key_Left)
    assert win.index == 0
    press(Qt.Key_1)
    assert win.zoom == 1.0
    press(Qt.Key_R)
    assert win.rotation == 90
    press(Qt.Key_0)
    assert win.fit_mode is True


# ---------------- hiệu ứng / icon (chỉ Windows mới có tác dụng) ----------------

def test_hieu_ung_aero_tu_tat_tren_nen_tang_khac(win):
    assert V.aero_available() is False           # offscreen -> không có hiệu ứng
    assert win._aero_on is False
    win.toggle_aero()                             # không được ném lỗi
    assert win._aero_on is False


def test_icon_app_tai_duoc(qapp):
    icon = V.app_icon()
    assert not icon.isNull()
    sizes = [(s.width(), s.height()) for s in icon.availableSizes()]
    assert (16, 16) in sizes                      # cần cỡ nhỏ cho thanh tiêu đề


def test_khung_xem_van_chay_khi_nen_tang_khong_ho_tro_pinch(monkeypatch, qapp):
    """`grabGesture` lỗi (nền tảng không hỗ trợ) không được làm app chết."""
    from PySide6.QtWidgets import QWidget

    from xemanh.mainwindow import MainWindow

    def hong(*a, **k):
        raise RuntimeError("nền tảng không hỗ trợ gesture")

    monkeypatch.setattr(QWidget, "grabGesture", hong)

    w = MainWindow()
    try:
        assert w.view is not None
        assert w.view.scene is not None
    finally:
        w.close()
        qapp.processEvents()
