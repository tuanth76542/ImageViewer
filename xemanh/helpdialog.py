"""Bảng trợ giúp phím tắt."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout

from xemanh.theme import _glass


HELP_ROWS = [
    ("← / →", "Ảnh trước / ảnh tiếp"),
    ("Chuột lăn", "Chuyển ảnh"),
    ("Ctrl + lăn  ·  pinch touchpad", "Zoom tại vị trí con trỏ"),
    ("+ / −", "Phóng to / thu nhỏ"),
    ("0 / 1", "Vừa màn hình / kích thước thật"),
    ("Kéo chuột", "Di chuyển ảnh khi đã zoom"),
    ("R", "Xoay 90°"),
    ("F5", "Trình chiếu toàn màn hình"),
    ("F", "Bật/tắt lọc chỉ ảnh nữ"),
    ("F11  ·  nháy đúp", "Toàn màn hình"),
    ("H / F1", "Mở bảng trợ giúp này"),
    ("Ctrl + O", "Mở thư mục"),
    ("Ctrl + A", "Bật/tắt nền kính mờ (Aero) cho thanh tiêu đề"),
    ("Kéo-thả tệp", "Thả thư mục hoặc ảnh vào cửa sổ"),
    ("Esc", "Đóng trợ giúp / thoát toàn màn hình"),
]


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)

        card = _glass("helpCard")
        grid = QGridLayout(card)
        grid.setContentsMargins(26, 22, 26, 20)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(9)

        title = QLabel("Phím tắt & mẹo", objectName="helpTitle")
        grid.addWidget(title, 0, 0, 1, 2)
        for i, (key, desc) in enumerate(HELP_ROWS, start=1):
            k = QLabel(key, objectName="helpKey")
            k.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(k, i, 0)
            grid.addWidget(QLabel(desc, objectName="helpDesc"), i, 1)

        btn = QPushButton("Đóng (Esc)")
        btn.clicked.connect(lambda _c=False: self.close())
        grid.addWidget(btn, len(HELP_ROWS) + 1, 0, 1, 2, Qt.AlignRight)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

    def showEvent(self, ev):
        super().showEvent(ev)
        parent = self.parent()
        if parent is not None:
            self.move(parent.geometry().center() - self.rect().center())

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key_Escape, Qt.Key_H, Qt.Key_F1):
            self.close()
        else:
            super().keyPressEvent(ev)
