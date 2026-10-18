"""Đọc danh sách ảnh và chuyển ảnh PIL sang QImage."""

import os

from PySide6.QtGui import QImage


EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".ico"}


def list_images_in_folder(folder):
    try:
        files = [os.path.join(folder, f) for f in os.listdir(folder)]
    except OSError:
        return []
    imgs = [f for f in files
            if os.path.isfile(f) and os.path.splitext(f)[1].lower() in EXTS]
    imgs.sort(key=lambda p: os.path.basename(p).lower())
    return imgs


def pil_to_qimage(img):
    """PIL RGB -> QImage (an toàn với tên file Unicode vì PIL tự xử lý)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    buf = img.tobytes()
    q = QImage(buf, w, h, w * 3, QImage.Format_RGB888)
    return q.copy()  # copy để giữ buffer
