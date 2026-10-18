"""Test chức năng trình chiếu (SlideDialog) và việc ẩn/hiện cửa sổ chính."""
import pytest

import viewer_qt as V

pytestmark = pytest.mark.functional


def _open(win, qapp):
    """Bật trình chiếu (F5) và trả về hộp thoại vừa mở."""
    win.toggle_slideshow()
    qapp.processEvents()
    return win.slide_dlg


def test_mo_toan_man_hinh_va_an_cua_so_chinh(win, qapp):
    dlg = _open(win, qapp)
    assert dlg is not None
    assert dlg.isFullScreen()
    assert not win.isVisible()                   # không lộ GUI cũ
    assert not dlg.label.pixmap().isNull()       # đã hiện ảnh đầu tiên
    assert dlg.count_lbl.text() == "1 / 3"
    win.toggle_slideshow()                        # F5 lần nữa để đóng


def test_dong_thi_hien_lai_cua_so_chinh(win, qapp, pump):
    _open(win, qapp)
    win.toggle_slideshow()
    assert pump(lambda: win.slide_dlg is None and win.isVisible())


def test_step_va_quay_vong(win, qapp):
    dlg = _open(win, qapp)
    dlg.step(1)
    assert dlg.idx == 1
    assert win.index == 1                        # cửa sổ chính đi theo
    dlg.step(1)
    dlg.step(1)
    assert dlg.idx == 0                          # vòng xuôi
    dlg.step(-1)
    assert dlg.idx == 2                          # vòng ngược
    assert dlg.count_lbl.text() == "3 / 3"
    win.toggle_slideshow()


def test_tam_dung_va_tiep_tuc(win, qapp):
    dlg = _open(win, qapp)
    assert dlg.playing is True
    assert dlg.timer.isActive()
    dlg.toggle_play()
    assert dlg.playing is False
    assert not dlg.timer.isActive()              # tạm dừng -> hết đếm giờ
    assert dlg.btn_play.text() == "▶"
    dlg.toggle_play()
    assert dlg.playing is True
    assert dlg.timer.isActive()
    assert dlg.btn_play.text() == "❚❚"
    win.toggle_slideshow()


def test_toc_do_la_cac_moc_co_dinh(win, qapp):
    assert V.SPEED_PRESETS == (3, 5, 10, 20)
    dlg = _open(win, qapp)
    assert [b.text() for b in dlg.speed_btns] == ["3s", "5s", "10s", "20s"]
    dlg.speed_btns[1].click()
    assert win.slideshow_delay == 5000
    assert dlg.speed_btns[1].isChecked()
    dlg.speed_btns[3].click()
    assert win.slideshow_delay == 20000
    assert dlg.speed_btns[3].isChecked()
    assert not dlg.speed_btns[1].isChecked()     # chỉ một mốc được chọn
    win.toggle_slideshow()


def test_tu_dong_chuyen_anh_theo_thoi_gian(win, qapp, pump):
    win.slideshow_delay = 150                    # rút ngắn cho test
    dlg = _open(win, qapp)
    assert dlg.idx == 0
    assert pump(lambda: dlg.idx != 0, timeout_ms=5000)
    win.toggle_slideshow()


def test_thanh_dieu_khien_tu_an_khi_roi_chuot(win, qapp, pump):
    dlg = _open(win, qapp)
    dlg.reveal_controls()
    assert dlg.controls.isVisible()
    dlg.hide_timer.start(100)                    # rút ngắn cho test
    assert pump(lambda: not dlg.controls.isVisible(), timeout_ms=5000)
    dlg.reveal_controls()
    assert dlg.controls.isVisible()
    win.toggle_slideshow()


def test_phim_tat_trong_trinh_chieu(win, qapp, pump):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    dlg = _open(win, qapp)

    def press(key):
        dlg.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, key, Qt.NoModifier))

    press(Qt.Key_Right)
    assert dlg.idx == 1
    press(Qt.Key_Left)
    assert dlg.idx == 0
    press(Qt.Key_Space)
    assert dlg.playing is False
    press(Qt.Key_Space)
    assert dlg.playing is True
    press(Qt.Key_Escape)
    assert pump(lambda: win.slide_dlg is None and win.isVisible())


def test_khong_mo_trinh_chieu_khi_chua_co_anh(empty_win):
    empty_win.toggle_slideshow()
    assert empty_win.slide_dlg is None
    assert empty_win.toast.isVisible()


# ------------------------------ các nhánh sự kiện/ảnh còn thiếu

def test_di_chuot_hien_lai_thanh_dieu_khien(win, qapp):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    dlg = _open(win, qapp)
    dlg._hide_controls()
    assert not dlg.controls.isVisible()

    dlg.mouseMoveEvent(QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(5, 5),
                                   QPointF(5, 5), Qt.NoButton, Qt.NoButton,
                                   Qt.NoModifier))

    assert dlg.controls.isVisible()
    win.toggle_slideshow()


def test_nha_chuot_trai_tam_dung_va_hien_lai_thanh(win, qapp):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    def nha(nut):
        return QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(5, 5),
                           QPointF(5, 5), nut, Qt.NoButton, Qt.NoModifier)

    dlg = _open(win, qapp)
    assert dlg.playing is True
    dlg._hide_controls()

    dlg.mouseReleaseEvent(nha(Qt.RightButton))   # chuột phải -> không tạm dừng
    assert dlg.playing is True
    assert not dlg.controls.isVisible()

    dlg.mouseReleaseEvent(nha(Qt.LeftButton))    # chuột trái -> tạm dừng + hiện thanh
    assert dlg.playing is False
    assert dlg.controls.isVisible()
    win.toggle_slideshow()


def test_trinh_chieu_khi_danh_sach_rong_thi_bo_qua(empty_win, qapp):
    dlg = V.SlideDialog(empty_win)
    try:
        dlg.idx = 0
        dlg.show_slide()                         # rỗng -> không làm gì
        assert dlg.count_lbl.text() == ""
        dlg.step(1)                              # rỗng -> không dịch chuyển
        assert dlg.idx == 0
    finally:
        dlg.close()


def test_trinh_chieu_bo_qua_anh_doc_loi(empty_win, tmp_path, qapp):
    hong = tmp_path / "hong.jpg"
    hong.write_bytes(b"day khong phai anh")
    empty_win.image_list = [str(hong)]
    empty_win.index = 0

    dlg = V.SlideDialog(empty_win)
    try:
        assert dlg.label.pixmap().isNull()       # đọc lỗi -> giữ nguyên nền đen
        assert dlg.count_lbl.text() == ""        # không cập nhật số thứ tự
    finally:
        dlg.close()
        empty_win.image_list = []
        empty_win.index = -1


def test_phim_la_trong_trinh_chieu_nhuong_lop_cha(win, qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    dlg = _open(win, qapp)
    dlg.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Z, Qt.NoModifier))
    assert dlg.idx == 0
    win.toggle_slideshow()
