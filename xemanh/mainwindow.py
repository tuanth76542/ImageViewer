"""Cửa sổ chính: thanh công cụ nổi, điều hướng, zoom, lọc, slideshow."""

import importlib.util
import os

from PIL import Image
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QFileDialog, QFrame, QGraphicsView, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QProgressDialog, QPushButton,
                               QVBoxLayout, QWidget)

from xemanh.filterthread import FilterThread
from xemanh.helpdialog import HelpDialog
from xemanh.imageutils import EXTS, list_images_in_folder, pil_to_qimage
from xemanh.imageview import ImageView
from xemanh.slideshow import SlideDialog
from xemanh.theme import DARK_QSS, _glass
from xemanh.winfx import aero_available, disable_window_blur, enable_window_blur

# Hiện dần: vừa tìm đủ ngần này ảnh nữ là cập nhật danh sách + hiển thị ngay,
# không chờ quét hết thư mục (quét vẫn chạy tiếp ở luồng nền).
SHOW_AFTER = 5


class MainWindow(QMainWindow):
    def __init__(self, start_path=None):
        super().__init__()
        self.setWindowTitle("Phần Mềm Xem Ảnh")
        self.resize(1200, 820)
        self.setMinimumSize(560, 400)
        self.setStyleSheet(DARK_QSS)
        self.setAcceptDrops(True)

        self.image_list = []
        self.all_images = []
        self.index = -1
        self.folder = None
        self.filter_female = False
        self.filter_thread = None
        self.progress = None
        self.help_dlg = None
        self.slide_dlg = None
        self._was_fullscreen = False

        self.pil_image = None   # ảnh PIL hiện tại (đã xoay)
        self.zoom = 1.0
        self.fit_mode = True
        self.rotation = 0
        self.slideshow_delay = 3000
        self._f11_full = False
        self._aero_on = aero_available()

        self._build_ui()
        self._shortcuts()
        self.position_overlays()

        if start_path:
            if os.path.isdir(start_path):
                self.open_folder(start_path)
            elif os.path.isfile(start_path):
                self.open_folder(os.path.dirname(start_path) or ".",
                                 select=os.path.basename(start_path))

    # ================= UI =================
    def _obtn(self, layout, text, tip, slot):
        b = QPushButton(text)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setFocusPolicy(Qt.NoFocus)
        b.clicked.connect(slot)
        layout.addWidget(b)
        return b

    def _sep(self):
        s = QFrame(objectName="sep")
        s.setFrameShape(QFrame.VLine)
        s.setFixedWidth(1)
        s.setFixedHeight(20)
        return s

    def _build_ui(self):
        self.view = ImageView(self)
        self.setCentralWidget(self.view)

        # --- thanh điều khiển nổi phía trên ---
        self.topbar = _glass("overlayBar")
        self.topbar.setParent(self.view)
        hb = QHBoxLayout(self.topbar)
        hb.setContentsMargins(9, 6, 9, 6)
        hb.setSpacing(2)

        self._obtn(hb, "📂", "Mở thư mục (Ctrl+O)", self.choose_folder)
        hb.addWidget(self._sep())
        self._obtn(hb, "◀", "Ảnh trước (←)", self.prev_image)
        self._obtn(hb, "▶", "Ảnh tiếp (→)", self.next_image)
        hb.addWidget(self._sep())
        self._obtn(hb, "➖", "Thu nhỏ (−)", self.zoom_out)
        self.zoom_pct = QLabel("100%", objectName="zoomPct")
        hb.addWidget(self.zoom_pct)
        self._obtn(hb, "➕", "Phóng to (+)", self.zoom_in)
        self._obtn(hb, "⤢", "Vừa màn hình (0)", self.zoom_fit)
        self._obtn(hb, "1:1", "Kích thước thật (1)", self.zoom_100)
        hb.addWidget(self._sep())
        self._obtn(hb, "⟳", "Xoay 90° (R)", self.rotate_image)
        self._obtn(hb, "🎬", "Trình chiếu toàn màn hình (F5)", self.toggle_slideshow)
        self.filter_btn = self._obtn(hb, "👩", "Chỉ hiện ảnh có người nữ (F)",
                                     self.toggle_female_filter)
        hb.addWidget(self._sep())
        self._obtn(hb, "❔", "Trợ giúp phím tắt (H)", self.show_help)

        # --- thẻ thông tin ảnh (dưới trái) ---
        self.info_pill = _glass("infoPill")
        self.info_pill.setParent(self.view)
        self.info_pill.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        vb = QVBoxLayout(self.info_pill)
        vb.setContentsMargins(14, 8, 16, 9)
        vb.setSpacing(1)
        self.info_name = QLabel("", objectName="infoName")
        self.info_meta = QLabel("", objectName="infoMeta")
        vb.addWidget(self.info_name)
        vb.addWidget(self.info_meta)

        # --- toast thông báo ---
        self.toast = _glass("toast")
        self.toast.setParent(self.view)
        self.toast.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        tl = QHBoxLayout(self.toast)
        tl.setContentsMargins(14, 8, 14, 8)
        self.toast_lbl = QLabel("")
        tl.addWidget(self.toast_lbl)
        self.toast.hide()
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast.hide)

        # --- màn hình chào khi chưa có ảnh ---
        self.welcome = QWidget()
        self.welcome.setParent(self.view)
        wv = QVBoxLayout(self.welcome)
        wv.setContentsMargins(40, 34, 40, 34)
        wv.setSpacing(8)
        icon = QLabel("🖼", objectName="welcomeIcon")
        icon.setAlignment(Qt.AlignCenter)
        title = QLabel("Chưa có ảnh nào", objectName="welcomeTitle")
        title.setAlignment(Qt.AlignCenter)
        sub = QLabel("Kéo-thả một thư mục hoặc tệp ảnh vào cửa sổ,\n"
                     "hoặc bấm nút bên dưới để chọn.", objectName="welcomeSub")
        sub.setAlignment(Qt.AlignCenter)
        btn = QPushButton("📂  Mở thư mục", objectName="welcomeBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.choose_folder)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn)
        row.addStretch(1)
        wv.addWidget(icon)
        wv.addWidget(title)
        wv.addWidget(sub)
        wv.addSpacing(6)
        wv.addLayout(row)

        # --- bộ đếm ẩn để tự ẩn thanh khi toàn màn hình ---
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_overlays)

        self.welcome.show()
        self.info_pill.hide()        # chưa có ảnh thì không có gì để báo

    def _shortcuts(self):
        for seq, slot in [(QKeySequence.MoveToPreviousChar, self.prev_image),
                          (QKeySequence.MoveToNextChar, self.next_image)]:
            QShortcut(seq, self).activated.connect(slot)

    def keyPressEvent(self, ev):
        k = ev.key()
        m = ev.modifiers()
        if k in (Qt.Key_Left, Qt.Key_Up):
            self.prev_image()
        elif k in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Space):
            self.next_image()
        elif k in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_in()
        elif k == Qt.Key_Minus:
            self.zoom_out()
        elif k == Qt.Key_0:
            self.zoom_fit()
        elif k == Qt.Key_1:
            self.zoom_100()
        elif k == Qt.Key_R:
            self.rotate_image()
        elif k == Qt.Key_F5:
            self.toggle_slideshow()
        elif k == Qt.Key_F11:
            self.toggle_fullscreen()
        elif k == Qt.Key_Escape and self._f11_full:
            self.toggle_fullscreen()
        elif k == Qt.Key_F:
            self.toggle_female_filter()
        elif k in (Qt.Key_H, Qt.Key_F1):
            self.show_help()
        elif k == Qt.Key_O and (m & Qt.ControlModifier):
            self.choose_folder()
        elif k == Qt.Key_A and (m & Qt.ControlModifier):
            self.toggle_aero()
        else:
            super().keyPressEvent(ev)

    # ================= lớp phủ =================
    def position_overlays(self):
        v = self.view
        W, H = v.width(), v.height()
        for w in (self.topbar, self.welcome, self.toast, self.info_pill):
            w.adjustSize()
        self.topbar.move(max(8, (W - self.topbar.width()) // 2), 12)
        self.info_pill.move(14, max(8, H - self.info_pill.height() - 14))
        self.toast.move(max(8, (W - self.toast.width()) // 2),
                        max(8, H - self.toast.height() - 14))
        self.welcome.move(max(8, (W - self.welcome.width()) // 2),
                          max(8, (H - self.welcome.height()) // 2))
        for w in (self.topbar, self.info_pill, self.toast, self.welcome):
            w.raise_()

    def reveal_overlays(self):
        self.topbar.show()
        if self.image_list:          # chưa có ảnh thì thẻ thông tin trống, khỏi hiện
            self.info_pill.show()
        self.topbar.raise_()
        self.info_pill.raise_()
        if self._f11_full:
            self.hide_timer.start(2500)
        else:
            self.hide_timer.stop()

    def _hide_overlays(self):
        self.topbar.hide()
        self.info_pill.hide()

    def status_msg(self, text):
        """Thông báo nổi (tự ẩn sau 3 giây)."""
        if not text:
            return
        self.toast_lbl.setText(text)
        self.position_overlays()
        self.toast.show()
        self.toast.raise_()
        self.toast_timer.start(3200)

    def show_help(self):
        if self.help_dlg is None:
            self.help_dlg = HelpDialog(self)
        self.help_dlg.show()
        self.help_dlg.raise_()
        self.help_dlg.activateWindow()

    # ================= mở ảnh =================
    def choose_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
        if d:
            self.open_folder(d)

    def open_dropped(self, paths):
        for p in paths:
            if os.path.isdir(p):
                self.open_folder(p)
                return
        for p in paths:
            if os.path.isfile(p) and os.path.splitext(p)[1].lower() in EXTS:
                self.open_folder(os.path.dirname(p) or ".",
                                 select=os.path.basename(p))
                return

    def open_folder(self, folder, select=None):
        imgs = list_images_in_folder(folder)
        if not imgs:
            QMessageBox.information(self, "Không có ảnh",
                                    f"Thư mục:\n{folder}\nkhông chứa file ảnh nào.")
            return
        self.folder = folder
        self.all_images = list(imgs)
        self.image_list = imgs
        self.filter_female = False
        self._refresh_filter_btn()
        self.index = 0
        if select:
            for i, p in enumerate(imgs):
                if os.path.basename(p) == select:
                    self.index = i
                    break
        self.rotation = 0
        self.fit_mode = True
        self.show_current()

    # ================= hiển thị =================
    def show_current(self, update_slide=True):
        if not self.image_list or self.index < 0:
            self.welcome.show()
            self.info_pill.hide()        # màn hình chào: không có thẻ thông tin
            self.position_overlays()
            return
        self.index %= len(self.image_list)
        path = self.image_list[self.index]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                if self.rotation:
                    img = img.rotate(-self.rotation, expand=True)
                self.pil_image = img.copy()
        except Exception:
            self.status_msg(f"Không đọc được: {os.path.basename(path)}")
            return
        if not self.welcome.isHidden():  # đang ở màn hình chào -> chuyển sang xem ảnh
            self.welcome.hide()
            self.reveal_overlays()       # hiện lại thanh công cụ + thẻ thông tin
        if self.fit_mode:
            self._compute_fit()
        self._apply_view()
        base = os.path.basename(path)
        w, h = self.pil_image.size
        self.info_name.setText(base)
        meta = f"{self.index + 1} / {len(self.image_list)}   ·   {w}×{h}"
        if self.filter_female:
            meta += f"   ·   👩 {len(self.image_list)}/{len(self.all_images)}"
        self.info_meta.setText(meta)
        tag = " [Lọc nữ]" if self.filter_female else ""
        self.setWindowTitle(
            f"{base} — {self.index + 1}/{len(self.image_list)} · Phần Mềm Xem Ảnh{tag}")
        self.position_overlays()

    def _compute_fit(self):
        if self.pil_image is None:
            return
        vw = self.view.viewport().width() or 1000
        vh = self.view.viewport().height() or 650
        iw, ih = self.pil_image.size
        self.zoom = max(0.02, min(10.0, min(vw / iw, vh / ih)))

    def _apply_view(self):
        if self.pil_image is None:
            return
        pm = QPixmap.fromImage(pil_to_qimage(self.pil_image))
        self.view.item.setPixmap(pm)
        self.view.scene.setSceneRect(pm.rect())
        self.view.resetTransform()
        self.view.scale(self.zoom, self.zoom)
        self.view.centerOn(self.view.scene.sceneRect().center())
        self.zoom_pct.setText(f"{int(round(self.zoom * 100))}%")

    def view_resized(self):
        if self.fit_mode and self.pil_image is not None:
            self._compute_fit()
            self._apply_view()

    # ================= điều hướng =================
    def _step(self, d):
        if not self.image_list:
            return
        self.index = (self.index + d) % len(self.image_list)
        self.rotation = 0
        self.fit_mode = True
        self.show_current()

    def next_image(self):
        self._step(1)

    def prev_image(self):
        self._step(-1)

    # ================= zoom =================
    def wheel_zoom(self, factor, pos=None):
        if self.pil_image is None:
            return
        self.zoom = max(0.05, min(20.0, self.zoom * factor))
        self.fit_mode = False
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.resetTransform()
        self.view.scale(self.zoom, self.zoom)
        self.view.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.zoom_pct.setText(f"{int(round(self.zoom * 100))}%")

    def pinch_zoom(self, factor):
        if factor and factor != 1.0:
            self.wheel_zoom(factor)

    def zoom_in(self):
        if self.pil_image is None:
            return
        self.zoom = min(20.0, self.zoom * 1.25)
        self.fit_mode = False
        self._apply_view()

    def zoom_out(self):
        if self.pil_image is None:
            return
        self.zoom = max(0.05, self.zoom / 1.25)
        self.fit_mode = False
        self._apply_view()

    def zoom_fit(self):
        if self.pil_image is None:
            return
        self.fit_mode = True
        self._compute_fit()
        self._apply_view()

    def zoom_100(self):
        if self.pil_image is None:
            return
        self.zoom = 1.0
        self.fit_mode = False
        self._apply_view()

    def rotate_image(self):
        if self.pil_image is None:
            return
        self.rotation = (self.rotation + 90) % 360
        self.show_current()

    # ================= hiệu ứng kính mờ (Aero) =================
    def showEvent(self, ev):
        super().showEvent(ev)
        # giữ hiệu ứng mỗi khi cửa sổ hiện lại (thoát toàn màn hình, mở lại...)
        if self._aero_on:
            enable_window_blur(self)

    def toggle_aero(self):
        """Bật/tắt nền kính mờ kiểu Aero cho thanh tiêu đề (Ctrl+A)."""
        if not aero_available():
            self.status_msg("Hiệu ứng kính mờ chỉ có trên Windows.")
            return
        self._aero_on = not self._aero_on
        if self._aero_on:
            enable_window_blur(self)
            self.status_msg("Đã bật nền kính mờ (Aero) cho thanh tiêu đề.")
        else:
            disable_window_blur(self)
            self.status_msg("Đã tắt nền kính mờ.")

    # ================= toàn màn hình =================
    def toggle_fullscreen(self):
        if self._f11_full:
            self.showNormal()
            self._f11_full = False
            self.hide_timer.stop()
            self.reveal_overlays()
        else:
            self.showFullScreen()
            self._f11_full = True
            self.reveal_overlays()

    # ================= slideshow =================
    def toggle_slideshow(self):
        if self.slide_dlg is not None:
            self.slide_dlg.close()
            return
        if not self.image_list:
            self.status_msg("Hãy mở thư mục chứa ảnh trước.")
            return
        self._was_fullscreen = self._f11_full
        self.slide_dlg = SlideDialog(self)
        self.slide_dlg.closed.connect(self._on_slideshow_closed)
        self.hide()                       # ẩn cửa sổ chính, không để lộ GUI
        self.slide_dlg.start()

    def _on_slideshow_closed(self):
        self.slide_dlg = None
        if self._was_fullscreen:
            self.showFullScreen()
        else:
            self.show()
        self.position_overlays()
        self.reveal_overlays()
        self.raise_()
        self.activateWindow()

    # ================= lọc nữ =================
    def _refresh_filter_btn(self):
        self.filter_btn.setText("👩" if not self.filter_female else "👩 ✕")
        self.filter_btn.setToolTip(
            "Đang lọc ảnh nữ — bấm để tắt (F)" if self.filter_female
            else "Chỉ hiện ảnh có người nữ (F)")
        self.filter_btn.setProperty("active", "true" if self.filter_female else "false")
        self.filter_btn.style().unpolish(self.filter_btn)
        self.filter_btn.style().polish(self.filter_btn)

    def toggle_female_filter(self):
        if self.filter_thread is not None and self.filter_thread.isRunning():
            return
        if not self.all_images and not self.image_list:
            self.status_msg("Hãy mở thư mục chứa ảnh trước.")
            return
        if self.filter_female:
            self.filter_female = False
            self.image_list = list(self.all_images)
            self.index = 0 if self.image_list else -1
            self.rotation = 0
            self.fit_mode = True
            self._refresh_filter_btn()
            self.show_current()
            self.status_msg(f"Đã tắt lọc — hiện toàn bộ {len(self.image_list)} ảnh")
            return
        if importlib.util.find_spec("cv2") is None:
            QMessageBox.critical(
                self, "Thiếu thư viện",
                "Tính năng lọc nữ cần OpenCV + onnxruntime.\n\n"
                "Hãy chạy:  uv sync")
            return
        import loc_nu
        if loc_nu.missing_models():
            ok = QMessageBox.question(
                self, "Tải model nhận diện",
                "Lần đầu dùng cần tải model nhận diện (~430MB, 1 lần duy nhất,"
                " cần Internet).\n\nTải ngay?")
            if ok != QMessageBox.Yes:
                return
        total = len(self.all_images)
        self.progress = QProgressDialog(
            "Đang nhận diện khuôn mặt nữ trong từng ảnh...", "Đóng",
            0, max(1, total), self)
        self.progress.setWindowTitle("Đang lọc ảnh nữ...")
        self.progress.setMinimumWidth(420)
        self.progress.setValue(0)
        try:
            self.progress.canceled.disconnect()
        except Exception:
            pass
        self.progress.show()

        self.filter_thread = FilterThread(list(self.all_images), self)
        self.filter_thread.progressed.connect(self._filter_tick)
        self.filter_thread.found.connect(self._filter_found)
        self.filter_thread.done.connect(self._filter_done)
        self.filter_thread.failed.connect(self._filter_failed)
        self.filter_thread.start()

    def _filter_tick(self, n, total, path, ok):
        if self.progress is not None:
            self.progress.setMaximum(max(1, total))
            self.progress.setValue(n)
            mark = "✓ " if ok else ""
            self.progress.setLabelText(f"{n} / {total} — {mark}{os.path.basename(path)}")

    def _close_progress(self):
        if self.progress is not None:
            try:
                self.progress.close()
            except Exception:
                pass
            self.progress = None

    def _anh_dang_xem(self):
        """Đường dẫn ảnh đang hiển thị (None nếu chưa có ảnh nào)."""
        if not self.image_list:
            return None
        if 0 <= self.index < len(self.image_list):
            return self.image_list[self.index]
        return None

    def _refresh_filter_meta(self):
        """Chỉ cập nhật chữ (số ảnh / thanh tiêu đề), KHÔNG đọc lại ảnh.

        Dùng khi danh sách ảnh nữ dài thêm mà ảnh đang xem không đổi: gọi
        ``show_current()`` mỗi lần sẽ giải mã lại ảnh từ đĩa hàng trăm lần trong
        lúc quét, làm chậm cả việc quét lẫn giao diện.
        """
        path = self._anh_dang_xem()
        if path is None:
            return
        n, tong = len(self.image_list), len(self.all_images)
        w, h = self.pil_image.size if self.pil_image is not None else (0, 0)
        base = os.path.basename(path)
        self.info_name.setText(base)
        self.info_meta.setText(
            f"{self.index + 1} / {n}   ·   {w}×{h}   ·   👩 {n}/{tong}")
        self.setWindowTitle(
            f"{base} — {self.index + 1}/{n} · Phần Mềm Xem Ảnh [Lọc nữ]")

    def _filter_found(self, kept):
        """Hiện dần: đủ SHOW_AFTER ảnh nữ là cập nhật danh sách + hiển thị ngay.

        Danh sách chỉ gồm ảnh nữ đã tìm được (không kèm ảnh chưa quét). Ảnh đang
        xem được giữ nguyên theo đường dẫn nếu nó còn trong danh sách. Luồng quét
        vẫn chạy tiếp — hàm này không chạm gì tới ``filter_thread``/hộp tiến độ.
        """
        if len(kept) < SHOW_AFTER:
            return                      # quá ít ảnh nữ: để _filter_done xử như trước
        lan_dau = not self.filter_female
        dang_xem = self._anh_dang_xem()
        self.filter_female = True
        self.image_list = list(kept)
        if dang_xem in self.image_list:
            self.index = self.image_list.index(dang_xem)      # giữ nguyên ảnh đang xem
        else:
            self.index = 0                                    # lần đầu: hiện ảnh nữ đầu tiên
        if lan_dau:
            self.rotation = 0
            self.fit_mode = True
            self._refresh_filter_btn()
            self.show_current()                               # phải vẽ -> đọc ảnh 1 lần
        else:
            self._refresh_filter_meta()
        self.status_msg(f"Đã tìm thấy {len(kept)} ảnh nữ, đang quét tiếp...")

    def _filter_failed(self, msg):
        self._close_progress()
        if self.filter_female:      # đã hiện dần được vài ảnh -> giữ lại, đừng nói "đang quét tiếp"
            self.status_msg(
                f"Lọc dừng giữa chừng — đang giữ {len(self.image_list)} ảnh nữ tìm được")
        QMessageBox.critical(self, "Lọc ảnh nữ", msg)

    def _filter_done(self, kept):
        self._close_progress()
        if not kept:
            QMessageBox.information(
                self, "Lọc ảnh nữ",
                f"Đã quét {len(self.all_images)} ảnh, không tìm thấy ảnh nữ nào.")
            return
        dang_xem = self._anh_dang_xem()
        self.filter_female = True
        self.image_list = kept
        self.index = self.image_list.index(dang_xem) if dang_xem in kept else 0
        self.rotation = 0
        self.fit_mode = True
        self._refresh_filter_btn()
        self.show_current()
        self.status_msg(f"Giữ lại {len(kept)} / {len(self.all_images)} ảnh có người nữ")

    def closeEvent(self, ev):
        try:
            if self.filter_thread is not None and self.filter_thread.isRunning():
                self.filter_thread.wait(3000)
        except Exception:
            pass
        super().closeEvent(ev)
