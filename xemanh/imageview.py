"""Khung xem ảnh: zoom bằng pinch/lăn chuột, kéo thả tệp."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QGestureEvent, QGraphicsPixmapItem,
                               QGraphicsScene, QGraphicsView, QPinchGesture)


class ImageView(QGraphicsView):
    """Vùng xem ảnh: pan/kéo, zoom, và là nơi neo các lớp phủ (overlay)."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.win = window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.item = QGraphicsPixmapItem()
        self.scene.addItem(self.item)
        try:
            self.viewport().grabGesture(Qt.PinchGesture)
        except Exception:
            pass
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

    # -- zoom bằng pinch / Ctrl+lăn / lăn để chuyển ảnh --
    def event(self, ev):
        # Nhập ở đầu tệp (không phải trong try/except): trước đây `QPinchGesture`
        # bị nhập nhầm từ QtGui, lỗi import bị nuốt nên pinch touchpad không
        # bao giờ chạy. Qt để lớp gesture trong QtWidgets.
        if isinstance(ev, QGestureEvent):
            g = ev.gesture(Qt.PinchGesture)
            if isinstance(g, QPinchGesture) and g.state() == Qt.GestureUpdated:
                self.win.pinch_zoom(g.scaleFactor())
                ev.accept()
                return True
        return super().event(ev)

    def wheelEvent(self, ev):
        if ev.modifiers() & Qt.ControlModifier:
            steps = ev.angleDelta().y() / 120.0
            self.win.wheel_zoom(1.18 ** steps, ev.position().toPoint())
        elif ev.angleDelta().y() > 0:
            self.win.prev_image()
        else:
            self.win.next_image()
        ev.accept()

    def mouseMoveEvent(self, ev):
        self.win.reveal_overlays()
        super().mouseMoveEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        self.win.toggle_fullscreen()
        super().mouseDoubleClickEvent(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.win.position_overlays()
        self.win.view_resized()

    # -- kéo-thả thư mục / tệp ảnh vào cửa sổ --
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
        else:
            super().dragEnterEvent(ev)

    def dragMoveEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
        else:
            super().dragMoveEvent(ev)

    def dropEvent(self, ev):
        if ev.mimeData().hasUrls():
            urls = [u.toLocalFile() for u in ev.mimeData().urls()]
            self.win.open_dropped(urls)
            ev.acceptProposedAction()
        else:
            super().dropEvent(ev)
