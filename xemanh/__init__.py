"""Package chính của Phần Mềm Xem Ảnh (PySide6).

Chia theo việc, mỗi tệp một trách nhiệm:

    theme        bảng màu / QSS dùng chung cho giao diện tối
    imageutils   liệt kê ảnh trong thư mục, chuyển PIL -> QImage
    winfx        tiện ích Windows: icon app, app-id cho taskbar, kính mờ Aero
    imageview    khung xem ảnh (zoom, pan, kéo-thả)
    slideshow    cửa sổ trình chiếu toàn màn hình
    helpdialog   bảng trợ giúp phím tắt
    filterthread luồng nền chạy bộ lọc ảnh nữ (loc_nu)
    mainwindow   cửa sổ chính, nối mọi thứ lại
    perf         đo tài nguyên tiêu thụ (RAM, CPU, thread, handle)

Điểm chạy vẫn là ``viewer_qt.py`` ở thư mục gốc.
"""

__version__ = "0.1.0"
