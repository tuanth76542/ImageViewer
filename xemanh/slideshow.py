"""Cửa sổ trình chiếu toàn màn hình kèm thanh điều khiển nổi."""

from PIL import Image
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QDialog, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout)

from xemanh.imageutils import pil_to_qimage
from xemanh.theme import DARK_QSS, _glass


# Mốc tốc độ trình chiếu cố định (giây mỗi ảnh)
SPEED_PRESETS = (3, 5, 10, 20)


class SlideDialog(QDialog):
    """Trình chiếu toàn màn hình: nền đen + thanh điều khiển nổi (tự ẩn).

    Là cửa sổ riêng, KHÔNG viền, mở bằng showFullScreen() để phủ trọn màn hình.
    Cửa sổ chính được ẩn trong lúc trình chiếu (xem MainWindow.toggle_slideshow).
    """

    closed = Signal()

    def __init__(self, window):
        super().__init__(window)
        self.win = window
        self.setWindowTitle("Trình chiếu")
        self.setStyleSheet(DARK_QSS)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setMouseTracking(True)

        # ảnh: cho sự kiện chuột "xuyên qua" để bấm vào ảnh = tạm dừng
        self.label = QLabel(alignment=Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setStyleSheet("background: #000;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label, 1)

        # thanh điều khiển nổi
        self.controls = _glass("slideBar")
        self.controls.setParent(self)
        cb = QHBoxLayout(self.controls)
        cb.setContentsMargins(10, 7, 10, 7)
        cb.setSpacing(3)
        cb.addWidget(self._sbtn("◀", "Ảnh trước (←)", lambda: self.step(-1)))
        self.btn_play = self._sbtn("❚❚", "Tạm dừng / tiếp tục (Space)", self.toggle_play)
        cb.addWidget(self.btn_play)
        cb.addWidget(self._sbtn("▶", "Ảnh tiếp (→)", lambda: self.step(1)))
        self.count_lbl = QLabel("", objectName="slideCount")
        cb.addWidget(self.count_lbl)
        cb.addSpacing(10)
        cb.addWidget(QLabel("Tốc độ"))
        # các mốc cố định, bấm để chọn (giây mỗi ảnh)
        self.speed_group = QButtonGroup(self)
        self.speed_group.setExclusive(True)
        self.speed_btns = []
        cur_sec = int(round(window.slideshow_delay / 1000.0))
        for sec in SPEED_PRESETS:
            b = self._sbtn("%ds" % sec, "%d giây mỗi ảnh" % sec,
                           lambda s=sec: self.speed_changed(s))
            b.setCheckable(True)
            b.setChecked(sec == cur_sec)
            self.speed_group.addButton(b)
            self.speed_btns.append(b)
            cb.addWidget(b)
        cb.addSpacing(10)
        cb.addWidget(self._sbtn("✕", "Đóng (Esc)", self.close))
        self.controls.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_next)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_controls)

        self.playing = True
        self.idx = window.index if window.index >= 0 else 0
        self.show_slide()
        self.arm()

    def _sbtn(self, text, tip, slot):
        b = QPushButton(text)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setFocusPolicy(Qt.NoFocus)
        b.clicked.connect(lambda _c=False: slot())
        return b

    # ---------- hiện/ẩn thanh điều khiển ----------
    def start(self):
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.reveal_controls()

    def _position_controls(self):
        self.controls.adjustSize()
        w, h = self.width(), self.height()
        self.controls.move(max(16, (w - self.controls.width()) // 2),
                           max(16, h - self.controls.height() - 30))

    def reveal_controls(self):
        self.controls.show()
        self.controls.raise_()
        self.setCursor(Qt.ArrowCursor)
        self.hide_timer.start(2500)

    def _hide_controls(self):
        self.controls.hide()
        self.setCursor(Qt.BlankCursor)

    def mouseMoveEvent(self, ev):
        self.reveal_controls()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.toggle_play()
            self.reveal_controls()
        super().mouseReleaseEvent(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._position_controls()

    # ---------- ảnh ----------
    def current_paths(self):
        return self.win.image_list

    def show_slide(self):
        paths = self.current_paths()
        if not paths:
            return
        self.idx %= len(paths)
        path = paths[self.idx]
        try:
            with Image.open(path) as img:
                q = pil_to_qimage(img.convert("RGB"))
        except Exception:
            return
        scr = QApplication.primaryScreen().size()
        pm = QPixmap.fromImage(q).scaled(
            scr.width(), scr.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(pm)
        self.count_lbl.setText(f"{self.idx + 1} / {len(paths)}")
        self.win.index = self.idx
        self.win.show_current(update_slide=False)

    def arm(self):
        self.timer.stop()
        if self.playing:
            self.timer.start(self.win.slideshow_delay)

    def auto_next(self):
        self.step(1)

    def step(self, d):
        paths = self.current_paths()
        if not paths:
            return
        self.idx = (self.idx + d) % len(paths)
        self.show_slide()
        self._position_controls()
        self.arm()

    def toggle_play(self):
        self.playing = not self.playing
        self.btn_play.setText("❚❚" if self.playing else "▶")
        self.arm()

    def speed_changed(self, sec):
        """Đặt tốc độ theo mốc cố định (giây mỗi ảnh)."""
        sec = int(sec)
        self.win.slideshow_delay = sec * 1000
        for b, preset in zip(self.speed_btns, SPEED_PRESETS):
            b.setChecked(preset == sec)
        self.arm()

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key_Escape:
            self.close()
        elif k == Qt.Key_Right:
            self.step(1)
        elif k == Qt.Key_Left:
            self.step(-1)
        elif k == Qt.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(ev)

    def closeEvent(self, ev):
        self.timer.stop()
        self.hide_timer.stop()
        self.closed.emit()
        super().closeEvent(ev)
