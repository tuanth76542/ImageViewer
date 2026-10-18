"""Test đơn vị cho tiện ích Windows (xemanh.winfx): icon app, cờ hiệu ứng Aero,
và đoạn dựng cấu trúc ACCENT_POLICY gửi cho DWM.

Không gọi API Windows thật cho phần Aero (test chạy ở chế độ offscreen nên không
có cửa sổ thật): thay `ctypes.windll.user32` / `dwmapi` bằng bản giả để kiểm tra
đúng tham số được gửi đi.
"""
import ctypes
import os
import sys

import pytest

from xemanh import winfx

pytestmark = pytest.mark.unit


class CuaSoGia:
    """Giả lập cửa sổ Qt: phần Aero chỉ cần `winId()`."""

    def __init__(self, wid=1234):
        self._wid = wid

    def winId(self):
        return self._wid


class User32Gia:
    """Giả lập user32 (SetWindowCompositionAttribute)."""

    def __init__(self, co_api=True, tra_ve=1):
        self.goi = []
        if co_api:
            def _goi(hwnd, data):        # hàm thường (để gán được .argtypes)
                self.goi.append((hwnd, data))
                return tra_ve
            self.SetWindowCompositionAttribute = _goi


class DwmGia:
    """Giả lập dwmapi (DwmSetWindowAttribute)."""

    def __init__(self, tra_ve=0):
        self.goi = []
        self.tra_ve = tra_ve

    def DwmSetWindowAttribute(self, hwnd, attr, v, size):
        self.goi.append(attr)
        return self.tra_ve


# ------------------------------------------------------------------ icon app
def test_icon_app_doc_duoc_tu_assets(qapp):
    assert not winfx.app_icon().isNull()


def test_icon_rong_khi_thieu_assets(monkeypatch, tmp_path):
    monkeypatch.setattr(winfx, "_assets_dir", lambda: str(tmp_path))
    assert winfx.app_icon().isNull()


def test_icon_bo_qua_file_ico_hong_roi_thu_tiep(monkeypatch, tmp_path):
    # app.ico có nhưng không phải ảnh -> QIcon rỗng -> phải thử tiếp app.png
    (tmp_path / "app.ico").write_bytes(b"khong phai icon")
    monkeypatch.setattr(winfx, "_assets_dir", lambda: str(tmp_path))
    assert winfx.app_icon().isNull()


def test_assets_dir_lay_tu_thu_muc_giai_nen_khi_dong_goi(monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", os.path.join("C:", "giai-nen"),
                        raising=False)
    assert winfx._assets_dir() == os.path.join("C:", "giai-nen", "assets")


def test_assets_dir_dung_goc_du_an_khi_chay_ma_nguon():
    assert winfx._assets_dir() == os.path.join(winfx.PROJECT_ROOT, "assets")


def test_dat_app_id_cho_taskbar_khong_loi():
    winfx._set_windows_app_id()          # gọi thật: chỉ đặt app-id, không lỗi


class WindllHong:
    """Giả `ctypes.windll`: mọi truy cập thư viện hệ thống đều lỗi."""

    def __getattr__(self, ten):
        raise OSError("không nạp được thư viện %s" % ten)


def test_dat_app_id_bo_qua_khi_khong_goi_duoc_shell32(monkeypatch):
    monkeypatch.setattr(winfx.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", WindllHong())
    winfx._set_windows_app_id()          # nuốt lỗi, không làm app chết


# ------------------------------------------------------------------ Aero
def test_aero_tat_khi_chay_offscreen(qapp):
    assert winfx.aero_available() is False


def test_aero_tat_khi_co_aero_blur_false(monkeypatch, qapp):
    monkeypatch.setattr(winfx, "AERO_BLUR", False)
    assert winfx.aero_available() is False


def test_cac_ham_aero_bo_qua_khi_khong_phai_windows(monkeypatch, qapp):
    monkeypatch.setattr(winfx.sys, "platform", "linux")
    assert winfx.aero_available() is False
    assert winfx._set_dark_caption(CuaSoGia()) is False
    assert winfx.disable_window_blur(CuaSoGia()) is False
    winfx._set_windows_app_id()          # cũng phải bỏ qua, không lỗi


def test_aero_tat_khi_khong_hoi_duoc_nen_tang(monkeypatch):
    """Qt chưa sẵn sàng (platformName ném lỗi) -> coi như không có hiệu ứng."""
    monkeypatch.setattr(winfx.sys, "platform", "win32")
    monkeypatch.setattr(winfx, "AERO_BLUR", True)

    class AppHong:
        @staticmethod
        def platformName():
            raise RuntimeError("Qt chưa khởi tạo xong")

    monkeypatch.setattr(winfx, "QApplication", AppHong)
    assert winfx.aero_available() is False


def test_enable_window_blur_khi_khong_ho_tro(qapp):
    assert winfx.enable_window_blur(CuaSoGia()) is False


def test_enable_window_blur_dong_goi_dung_tham_so(monkeypatch):
    """Nền mờ phải được đóng gói dạng ABGR và dùng đúng state của DWM."""
    da_goi = []
    monkeypatch.setattr(winfx, "aero_available", lambda: True)
    monkeypatch.setattr(winfx, "_set_accent_policy",
                        lambda win, state, gradient=0:
                        (da_goi.append(("accent", state, gradient)), True)[1])
    monkeypatch.setattr(winfx, "_set_dark_caption",
                        lambda win, dark=True:
                        (da_goi.append(("toi", dark)), True)[1])

    assert winfx.enable_window_blur(CuaSoGia()) is True

    r, g, b, a = winfx.AERO_TINT
    _, state, gradient = da_goi[0]
    assert state == winfx._ACCENT_ENABLE_ACRYLICBLURBEHIND      # mặc định acrylic
    assert gradient == (a << 24 | b << 16 | g << 8 | r)         # ABGR
    assert da_goi[1] == ("toi", True)
    assert len(da_goi) == 2


def test_enable_window_blur_kieu_chi_mo_va_mau_tu_chon(monkeypatch):
    state_da_dung = []
    monkeypatch.setattr(winfx, "aero_available", lambda: True)
    monkeypatch.setattr(winfx, "_set_accent_policy",
                        lambda win, state, gradient=0:
                        (state_da_dung.append(state), False)[1])
    monkeypatch.setattr(winfx, "_set_dark_caption", lambda win, dark=True: True)

    # acrylic=False -> chỉ mờ; tint truyền vào được dùng thay AERO_TINT
    assert winfx.enable_window_blur(CuaSoGia(), tint=(1, 2, 3, 4),
                                    acrylic=False) is False
    assert state_da_dung == [winfx._ACCENT_ENABLE_BLURBEHIND]


def test_disable_window_blur_tat_hieu_ung(monkeypatch):
    da_goi = []
    monkeypatch.setattr(winfx, "_set_accent_policy",
                        lambda win, state, gradient=0:
                        (da_goi.append(state), True)[1])
    assert winfx.disable_window_blur(CuaSoGia()) is True
    assert da_goi == [0]                 # ACCENT_DISABLED


# ------------------------------------------- ACCENT_POLICY / dark caption
def test_set_accent_policy_goi_api_va_tra_true(monkeypatch):
    gia = User32Gia()
    monkeypatch.setattr(ctypes.windll, "user32", gia)
    assert winfx._set_accent_policy(CuaSoGia(4242), 4, 0x11223344) is True
    assert len(gia.goi) == 1


def test_set_accent_policy_false_khi_api_tra_ve_0(monkeypatch):
    gia = User32Gia(tra_ve=0)
    monkeypatch.setattr(ctypes.windll, "user32", gia)
    assert winfx._set_accent_policy(CuaSoGia(), 4) is False


def test_set_accent_policy_false_khi_may_thieu_api(monkeypatch):
    monkeypatch.setattr(ctypes.windll, "user32", User32Gia(co_api=False))
    assert winfx._set_accent_policy(CuaSoGia(), 4) is False


def test_dark_caption_dung_attr_20_truoc(monkeypatch):
    gia = DwmGia(tra_ve=0)
    monkeypatch.setattr(ctypes.windll, "dwmapi", gia)
    assert winfx._set_dark_caption(CuaSoGia(7)) is True
    assert gia.goi == [20]               # attr 20 chạy được -> không thử attr 19


def test_dark_caption_lui_ve_attr_19_khi_attr_20_loi(monkeypatch):
    gia = DwmGia(tra_ve=-1)
    monkeypatch.setattr(ctypes.windll, "dwmapi", gia)
    assert winfx._set_dark_caption(CuaSoGia(7), dark=False) is False
    assert gia.goi == [20, 19]


def test_set_accent_policy_false_khi_khong_goi_duoc_api(monkeypatch):
    monkeypatch.setattr(ctypes, "windll", WindllHong())
    assert winfx._set_accent_policy(CuaSoGia(), 4) is False


def test_dark_caption_false_khi_khong_goi_duoc_dwmapi(monkeypatch):
    monkeypatch.setattr(winfx.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", WindllHong())
    assert winfx._set_dark_caption(CuaSoGia()) is False
