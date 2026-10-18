"""
viewer_qt.py — điểm chạy Phần Mềm Xem Ảnh (PySide6), giao diện tối, điều khiển nổi.

Mã nguồn chính nằm trong package ``xemanh/`` (xem ``xemanh/__init__.py``).
Tệp này giữ nguyên tên cũ để ``chay.bat``, ``build_exe.bat`` và test không phải
đổi, đồng thời re-export các tên cũ cho tiện ``import viewer_qt as V``.

Tính năng:
  1. Chuyển ảnh: phím ←/→, lăn chuột, nút ◀/▶; kéo-thả thư mục/tệp ảnh vào cửa sổ.
  2. Zoom: pinch touchpad (= Ctrl + lăn chuột, zoom tại con trỏ) + gesture cảm ứng
     + nút ➖/➕ + phím +/-/0/1; kéo chuột để pan khi đã zoom.
  3. Slideshow toàn màn hình cả thư mục (F5), tốc độ theo mốc 3/5/10/20 giây/ảnh.
  4. Lọc chỉ ảnh nữ (F) — dùng chung loc_nu.py.
  5. Trợ giúp phím tắt (H / F1).

Chạy:  python viewer_qt.py [đường-dẫn-ảnh-hoặc-thư-mục]
"""
import sys

from PySide6.QtWidgets import QApplication

# --- re-export: `import viewer_qt as V` vẫn dùng được như trước khi tách package
from xemanh.filterthread import FilterThread                # noqa: F401
from xemanh.helpdialog import HELP_ROWS, HelpDialog         # noqa: F401
from xemanh.imageutils import EXTS                          # noqa: F401
from xemanh.imageutils import list_images_in_folder         # noqa: F401
from xemanh.imageutils import pil_to_qimage                 # noqa: F401
from xemanh.imageview import ImageView                      # noqa: F401
from xemanh.mainwindow import MainWindow                    # noqa: F401
from xemanh.perf import ResourceMonitor                     # noqa: F401
from xemanh.perf import ResourceSample                      # noqa: F401
from xemanh.perf import format_report                       # noqa: F401
from xemanh.perf import summarize                           # noqa: F401
from xemanh.slideshow import SPEED_PRESETS                  # noqa: F401
from xemanh.slideshow import SlideDialog                    # noqa: F401
from xemanh.theme import DARK_QSS                           # noqa: F401
from xemanh.theme import _glass                             # noqa: F401
from xemanh.winfx import AERO_ACRYLIC                       # noqa: F401
from xemanh.winfx import AERO_BLUR                          # noqa: F401
from xemanh.winfx import AERO_TINT                          # noqa: F401
from xemanh.winfx import _set_windows_app_id                # noqa: F401
from xemanh.winfx import aero_available                     # noqa: F401
from xemanh.winfx import app_icon                           # noqa: F401
from xemanh.winfx import disable_window_blur                # noqa: F401
from xemanh.winfx import enable_window_blur                 # noqa: F401

__all__ = [
    "MainWindow", "ImageView", "SlideDialog", "HelpDialog", "FilterThread",
    "DARK_QSS", "_glass",
    "HELP_ROWS", "SPEED_PRESETS", "EXTS",
    "list_images_in_folder", "pil_to_qimage", "main",
    "ResourceMonitor", "ResourceSample", "format_report", "summarize",
    "AERO_ACRYLIC", "AERO_BLUR", "AERO_TINT", "_set_windows_app_id",
    "aero_available", "app_icon", "disable_window_blur",
    "enable_window_blur",
]


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PhanMemXemAnh")
    _set_windows_app_id()
    app.setWindowIcon(app_icon())
    start = sys.argv[1] if len(sys.argv) > 1 else None
    win = MainWindow(start_path=start)
    win.setWindowIcon(app.windowIcon())    # cả thanh tiêu đề lẫn taskbar
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
