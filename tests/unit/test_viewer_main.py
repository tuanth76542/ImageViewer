"""Test đơn vị cho `viewer_qt.main()` — điểm chạy app, bằng đồ giả Qt.

`main()` thật sẽ tạo `QApplication`, mở cửa sổ rồi chạy `app.exec()` (vòng lặp sự
kiện) nên không thể chạy trong test. Thay `QApplication`, `MainWindow` và `sys.exit`
bằng đồ giả để kiểm tra đúng trình tự khởi tạo và mã thoát.
"""
import pytest

import viewer_qt as V

pytestmark = pytest.mark.unit


class AppGia:
    """Giả `QApplication`: ghi lại lời gọi, `exec()` không chạy vòng lặp thật."""

    def __init__(self, argv):
        self.argv = list(argv)
        self.ten_app = None
        self.icon_app = None

    def setApplicationName(self, ten):
        self.ten_app = ten

    def setWindowIcon(self, icon):
        self.icon_app = icon

    def windowIcon(self):
        return "icon-cua-so"

    def exec(self):
        return 7                      # mã thoát để kiểm tra sys.exit nhận đúng


class WindowGia:
    """Giả `MainWindow`: chỉ ghi lại tham số và các lời gọi."""

    def __init__(self, start_path=None):
        self.start_path = start_path
        self.icon = None
        self.da_hien = False

    def setWindowIcon(self, icon):
        self.icon = icon

    def show(self):
        self.da_hien = True


def _dung_do_gia(monkeypatch, argv):
    """Thay Qt/MainWindow bằng đồ giả; trả về (app, hộp đựng cửa sổ, lời gọi)."""
    goi = []
    app_box, win_box = [], []

    def tao_app(a):
        app = AppGia(a)
        app_box.append(app)
        return app

    def tao_window(start_path=None):
        w = WindowGia(start_path)
        win_box.append(w)
        return w

    monkeypatch.setattr(V, "QApplication", tao_app)
    monkeypatch.setattr(V, "MainWindow", tao_window)
    monkeypatch.setattr(V, "_set_windows_app_id", lambda: goi.append("app_id"))
    monkeypatch.setattr(V, "app_icon", lambda: "icon-tu-assets")
    monkeypatch.setattr(V.sys, "argv", list(argv))
    return app_box, win_box, goi


def test_main_khoi_tao_app_cua_so_roi_thoat_theo_ma_cua_exec(monkeypatch):
    app_box, win_box, goi = _dung_do_gia(monkeypatch, ["viewer_qt.py"])

    with pytest.raises(SystemExit) as loi:
        V.main()

    assert loi.value.code == 7                   # sys.exit nhận mã thoát của exec
    (app,) = app_box
    (win,) = win_box
    assert app.ten_app == "PhanMemXemAnh"
    assert app.icon_app == "icon-tu-assets"
    assert goi == ["app_id"]                     # có đặt app-id cho taskbar
    assert win.start_path is None                # không có tham số -> màn hình chào
    assert win.da_hien is True
    assert win.icon == "icon-cua-so"             # icon taskbar lấy từ app


def test_main_truyen_tham_so_dong_lenh_lam_duong_dan_mo(monkeypatch, tmp_path):
    app_box, win_box, goi = _dung_do_gia(monkeypatch, ["viewer_qt.py", str(tmp_path)])

    with pytest.raises(SystemExit):
        V.main()

    (win,) = win_box
    assert win.start_path == str(tmp_path)
    assert goi == ["app_id"]
