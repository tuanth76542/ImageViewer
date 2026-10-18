"""Test sự kiện chuột và kéo-thả của khung xem ảnh (xemanh.imageview).

Dựng sự kiện Qt tổng hợp rồi gọi thẳng hàm xử lý để kiểm tra việc "định tuyến"
sang MainWindow: lăn chuột = chuyển ảnh, Ctrl+lăn = zoom tại con trỏ, di chuột =
hiện lại lớp phủ, nháy đôi = toàn màn hình, kéo-thả tệp/thư mục = mở ảnh.

Không dùng QTest/event loop nên vẫn giữ được quy tắc "không QTimer trong test".
"""
import os
import warnings

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import (QDragEnterEvent, QDragMoveEvent, QDropEvent,
                           QMouseEvent, QWheelEvent)
from PySide6.QtWidgets import QGestureEvent, QPinchGesture

pytestmark = pytest.mark.functional


def _lan(view, dy, phim=Qt.NoModifier, dx=0):
    """QWheelEvent tổng hợp ở giữa khung xem."""
    diem = QPointF(view.viewport().rect().center())
    return QWheelEvent(diem, QPointF(view.viewport().mapToGlobal(diem.toPoint())),
                       QPoint(dx, 0), QPoint(0, dy),
                       Qt.NoButton, phim, Qt.NoScrollPhase, False)


def _chuot(loai, nut=Qt.NoButton):
    return QMouseEvent(loai, QPointF(5, 5), QPointF(5, 5),
                       nut, nut, Qt.NoModifier)


def _mime(*duong_dan):
    mime = QMimeData()
    if duong_dan:
        mime.setUrls([QUrl.fromLocalFile(p) for p in duong_dan])
    else:
        mime.setText("chỉ có chữ, không có tệp")
    return mime


def _keo_vao(loai, mime, diem=(10, 10)):
    """Sự kiện kéo-thả (constructor 5 tham số; PySide6 đánh dấu deprecated nên
    tắt cảnh báo tại đây cho gọn kết quả test)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return loai(QPoint(*diem), Qt.CopyAction, mime,
                    Qt.LeftButton, Qt.NoModifier)


def _ghi_lai(monkeypatch, win, *ten):
    """Thay vài hàm của MainWindow bằng bản ghi lại lần gọi."""
    goi = []

    def ghi(ten_ham):
        return lambda *a, **k: goi.append((ten_ham, a))

    for t in ten:
        monkeypatch.setattr(win, t, ghi(t))
    return goi


# ------------------------------------------------------------ lăn chuột
def test_lan_len_xuong_chuyen_anh(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "prev_image", "next_image")

    win.view.wheelEvent(_lan(win.view, 120))       # lăn lên -> ảnh trước
    win.view.wheelEvent(_lan(win.view, -120))      # lăn xuống -> ảnh sau

    assert [t for t, _ in goi] == ["prev_image", "next_image"]


def test_ctrl_lan_chuot_zoom_tai_vi_tri_con_tro(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "wheel_zoom")

    win.view.wheelEvent(_lan(win.view, 120, Qt.ControlModifier))

    assert len(goi) == 1
    ten, (factor, pos) = goi[0]
    assert ten == "wheel_zoom"
    assert 1.17 < factor < 1.19                    # 1.18 ^ 1
    assert pos is not None                         # zoom neo tại con trỏ


def test_ctrl_lan_hai_not_mot_luc_zoom_manh_hon(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "wheel_zoom")

    win.view.wheelEvent(_lan(win.view, 240, Qt.ControlModifier))

    assert goi[0][1][0] > 1.38                     # 1.18 ^ 2


# ------------------------------------------------------------ chuột
def test_di_chuot_hien_lai_lop_phu(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "reveal_overlays")

    win.view.mouseMoveEvent(_chuot(QMouseEvent.Type.MouseMove))

    assert [t for t, _ in goi] == ["reveal_overlays"]


def test_nhay_doi_chuot_bat_tat_toan_man_hinh(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "toggle_fullscreen")

    win.view.mouseDoubleClickEvent(
        _chuot(QMouseEvent.Type.MouseButtonDblClick, Qt.LeftButton))

    assert [t for t, _ in goi] == ["toggle_fullscreen"]


# ------------------------------------------------------------ pinch (touchpad)
class PinchGia(QPinchGesture):
    """QPinchGesture giả: Qt không cho đặt `state()` từ Python nên ghi đè."""

    def __init__(self, he_so=1.5, trang_thai=None):
        super().__init__()
        self._he_so = he_so
        self._trang_thai = Qt.GestureUpdated if trang_thai is None else trang_thai

    def state(self):
        return self._trang_thai

    def scaleFactor(self):
        return self._he_so


def test_pinch_gesture_zoom_theo_he_so(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "pinch_zoom")

    g = PinchGia(1.5)                      # giữ tham chiếu cho tới hết test
    ev = QGestureEvent([g])

    assert win.view.event(ev) is True
    assert goi == [("pinch_zoom", (1.5,))]


def test_pinch_gesture_dang_chay_thi_chua_zoom(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "pinch_zoom")

    g = PinchGia(1.5, Qt.GestureStarted)   # chưa tới lúc GestureUpdated
    ev = QGestureEvent([g])

    win.view.event(ev)
    assert goi == []                       # chỉ zoom khi gesture đã cập nhật


def test_pinch_nhap_dung_module():
    """Chống tái phát lỗi cũ: lớp gesture nằm ở QtWidgets, không phải QtGui.

    `imageview.event()` từng nhập `QPinchGesture` từ QtGui trong try/except nên
    lỗi import bị nuốt -> pinch touchpad không bao giờ chạy.
    """
    from xemanh import imageview

    assert imageview.QPinchGesture is QPinchGesture
    assert imageview.QGestureEvent is QGestureEvent


# ------------------------------------------------------------ kéo-thả
def test_keo_tha_thu_muc_thi_mo_anh(win, qapp, monkeypatch, folder):
    goi = _ghi_lai(monkeypatch, win, "open_dropped")
    mime = _mime(folder)

    vao = _keo_vao(QDragEnterEvent, mime)
    win.view.dragEnterEvent(vao)
    assert vao.isAccepted()

    di = _keo_vao(QDragMoveEvent, mime)
    win.view.dragMoveEvent(di)
    assert di.isAccepted()

    tha = QDropEvent(QPointF(10, 10), Qt.CopyAction, mime,
                     Qt.LeftButton, Qt.NoModifier)
    win.view.dropEvent(tha)

    assert tha.isAccepted()
    assert len(goi) == 1
    ten, (duong_dan,) = goi[0]
    assert ten == "open_dropped"
    # QUrl.toLocalFile() trả về dấu '/' — so sánh sau khi chuẩn hoá
    assert [os.path.normpath(p) for p in duong_dan] == [os.path.normpath(folder)]


def test_keo_tha_khong_co_tep_thi_nhuong_lop_cha(win, qapp, monkeypatch):
    goi = _ghi_lai(monkeypatch, win, "open_dropped")
    mime = _mime()                                 # chỉ có chữ

    vao = _keo_vao(QDragEnterEvent, mime, (9, 9))
    win.view.dragEnterEvent(vao)
    di = _keo_vao(QDragMoveEvent, mime, (9, 9))
    win.view.dragMoveEvent(di)
    tha = QDropEvent(QPointF(9, 9), Qt.CopyAction, mime,
                     Qt.LeftButton, Qt.NoModifier)
    win.view.dropEvent(tha)

    assert goi == []                               # không mở gì cả
