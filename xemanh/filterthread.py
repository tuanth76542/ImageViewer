"""Luồng nền chạy bộ lọc ảnh nữ (loc_nu) và phát tín hiệu về UI."""

import bisect

from PySide6.QtCore import QThread, Signal


class FilterThread(QThread):
    progressed = Signal(int, int, str, bool)
    # Danh sách ảnh nữ TÍCH LUỸ (theo đúng thứ tự self.paths) sau mỗi ảnh nữ mới.
    # Có tín hiệu này thì giao diện hiện dần kết quả, khỏi chờ quét hết thư mục.
    found = Signal(list)
    done = Signal(list)
    failed = Signal(str)

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = list(paths)
        self._vi_tri = {p: i for i, p in enumerate(self.paths)}  # path -> thứ tự gốc
        self._giu_lai = []                                       # chỉ số đã sắp tăng dần

    def _tien_do(self, done, total, path, ok):
        """Phát tiến độ, kèm danh sách ảnh nữ tích luỹ khi vừa tìm thêm ảnh nữ.

        Phải sắp lại theo thứ tự ``paths`` gốc: kết quả trong cache được phát
        tiến độ TRƯỚC các ảnh mới quét, nên thứ tự phát không phải thứ tự thư
        mục — nếu không sắp lại thì danh sách hiện dần sẽ lệch so với ``done``.
        """
        if ok:
            i = self._vi_tri.get(path)
            if i is not None and i not in self._giu_lai:
                bisect.insort(self._giu_lai, i)
                self.found.emit([self.paths[j] for j in self._giu_lai])
        self.progressed.emit(done, total, path, ok)

    def run(self):
        try:
            import loc_nu
        except ImportError as ex:
            self.failed.emit(f"Không tải được module lọc: {ex}")
            return
        try:
            loc_nu.download_models()
        except Exception as ex:
            self.failed.emit(f"Không tải được model: {ex}")
            return
        try:
            kept = loc_nu.filter_female(self.paths, on_progress=self._tien_do)
        except Exception as ex:
            self.failed.emit(f"Lỗi khi lọc: {ex}")
            return
        self.done.emit(kept)
