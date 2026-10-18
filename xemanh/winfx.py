"""Tiện ích riêng của Windows: icon app, app-id cho taskbar và
hiệu ứng kính mờ kiểu Aero. Nơi khác gọi vào đây, không cần
quan tâm chi tiết ctypes."""

import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

# thư mục gốc dự án (xemanh/ nằm trong đó) — dùng để tìm assets/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _assets_dir():
    """Thư mục assets (chạy được cả khi đóng gói bằng PyInstaller)."""
    base = getattr(sys, "_MEIPASS", PROJECT_ROOT)
    return os.path.join(base, "assets")


def app_icon():
    """Icon của app (assets/app.ico); trả QIcon rỗng nếu thiếu tệp."""
    for name in ("app.ico", "app.png"):
        path = os.path.join(_assets_dir(), name)
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
    return QIcon()


def _set_windows_app_id():
    """Để Windows dùng icon của app trên taskbar (thay vì icon python.exe)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PhanMemXemAnh.PhotoViewer")
    except Exception:
        pass


# ---------- Hiệu ứng kính mờ kiểu Aero cho thanh tiêu đề (chỉ Windows) ----------
AERO_BLUR = True                # đổi thành False nếu muốn tắt hiệu ứng


AERO_ACRYLIC = True             # True: acrylic (có phủ màu) — False: chỉ mờ (blur)


AERO_TINT = (16, 16, 20, 0x50)  # (R, G, B, A) — nền mờ tối cho hợp giao diện; A nhỏ = trong hơn


_ACCENT_ENABLE_BLURBEHIND = 3


_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4


_WCA_ACCENT_POLICY = 19


def aero_available():
    """Hiệu ứng chỉ có trên Windows và khi Qt đang dùng nền tảng 'windows'."""
    if not AERO_BLUR or sys.platform != "win32":
        return False
    try:
        return QApplication.platformName() == "windows"
    except Exception:
        return False


def _set_accent_policy(win, state, gradient=0):
    """Gọi SetWindowCompositionAttribute với một ACCENT_POLICY. Lỗi -> False."""
    try:
        import ctypes
        from ctypes import wintypes

        class _ACCENT_POLICY(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_uint),
                        ("AccentFlags", ctypes.c_uint),
                        ("GradientColor", ctypes.c_uint),
                        ("AnimationId", ctypes.c_uint)]

        class _WCADATA(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_uint),
                        ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t)]

        set_wca = getattr(ctypes.windll.user32,
                          "SetWindowCompositionAttribute", None)
        if set_wca is None:
            return False
        set_wca.argtypes = [wintypes.HWND, ctypes.POINTER(_WCADATA)]
        set_wca.restype = wintypes.BOOL

        accent = _ACCENT_POLICY(state, 2, int(gradient) & 0xFFFFFFFF, 0)
        data = _WCADATA(_WCA_ACCENT_POLICY,
                        ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
                        ctypes.sizeof(accent))
        return bool(set_wca(wintypes.HWND(int(win.winId())), ctypes.byref(data)))
    except Exception:
        return False


def _set_dark_caption(win, dark=True):
    """Thanh tiêu đề dùng chữ sáng (Windows 10 1809+ dùng attr 20)."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        dwm = ctypes.windll.dwmapi
        hwnd = wintypes.HWND(int(win.winId()))
        v = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):
            if dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v),
                                         ctypes.sizeof(v)) == 0:
                return True
    except Exception:
        pass
    return False


def enable_window_blur(win, tint=None, acrylic=None):
    """Làm mờ/trong suốt thanh tiêu đề + nền cửa sổ (kiểu Aero của Windows 7).

    Dùng DWM: SetWindowCompositionAttribute (Win10 1809+) và bật chữ sáng cho
    thanh tiêu đề. Mọi lỗi đều bị nuốt để app vẫn chạy bình thường.

    Trả về True nếu đã áp dụng được.
    """
    if not aero_available():
        return False
    r, g, b, a = tint or AERO_TINT
    if acrylic is None:
        acrylic = AERO_ACRYLIC
    # GradientColor của DWM là dạng ABGR
    gradient = ((int(a) & 0xFF) << 24 | (int(b) & 0xFF) << 16
                | (int(g) & 0xFF) << 8 | (int(r) & 0xFF))
    state = (_ACCENT_ENABLE_ACRYLICBLURBEHIND if acrylic
             else _ACCENT_ENABLE_BLURBEHIND)
    ok = _set_accent_policy(win, state, gradient)
    _set_dark_caption(win, True)
    return ok


def disable_window_blur(win):
    """Tắt phần mờ/trong suốt (thanh tiêu đề vẫn tối cho hợp giao diện)."""
    if sys.platform != "win32":
        return False
    # ACCENT_DISABLED = 0
    return _set_accent_policy(win, 0, 0)
