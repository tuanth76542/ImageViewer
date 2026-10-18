"""Cấu hình và fixture dùng chung cho pytest.

* Ép Qt chạy ở chế độ "offscreen" để test giao diện không cần màn hình thật
  (và không bật cửa sổ khi chạy trên CI).
* Fixture tạo ảnh mẫu, mở cửa sổ chính, và hàm "bơm" sự kiện Qt.
"""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import html
import io

import pytest
from PIL import Image

MÀU_MẪU = [(200, 80, 80), (80, 160, 80), (80, 120, 200), (200, 200, 90),
           (150, 90, 200)]


def _make_images(folder, count=3, size=(320, 240)):
    """Tạo `count` ảnh JPEG khác màu trong `folder`; trả về chính thư mục đó."""
    os.makedirs(folder, exist_ok=True)
    for i in range(count):
        Image.new("RGB", size, MÀU_MẪU[i % len(MÀU_MẪU)]).save(
            os.path.join(folder, "anh_%02d.jpg" % i))
    return folder


@pytest.fixture
def make_images():
    """Trả về hàm tạo ảnh mẫu: `make_images(thư_mục, số_ảnh, (rộng, cao))`."""
    return _make_images


# --------------------------------------------------------------- Qt
@pytest.fixture(scope="session")
def qapp():
    """Một QApplication duy nhất cho cả phiên test (Qt chỉ cho phép một)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def pump(qapp):
    """Trả về hàm xử lý sự kiện cho tới khi điều kiện đúng (hoặc hết giờ).

    Cố ý KHÔNG dùng QEventLoop + QTimer.singleShot cho việc chờ: timer đó sống
    lâu hơn vòng lặp sự kiện cục bộ, khi bắn sẽ gọi vào object đã bị hủy
    -> crash Qt (access violation).
    """
    def _pump_until(cond, timeout_ms=15000):
        deadline = time.monotonic() + timeout_ms / 1000.0
        while not cond() and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.01)
        return cond()
    return _pump_until


# --------------------------------------------------------------- dữ liệu mẫu
@pytest.fixture
def folder(tmp_path):
    """Thư mục có 3 ảnh nhỏ."""
    return _make_images(str(tmp_path), 3)


@pytest.fixture
def big_folder(tmp_path):
    """Thư mục 24 ảnh lớn hơn (1600x1200) — dùng cho test tài nguyên."""
    return _make_images(str(tmp_path / "nhieu"), 24, size=(1600, 1200))


@pytest.fixture
def win(qapp, folder):
    """Cửa sổ chính đã mở sẵn thư mục 3 ảnh."""
    import viewer_qt as V

    w = V.MainWindow(start_path=folder)
    w.show()
    qapp.processEvents()
    yield w
    w.close()
    qapp.processEvents()


@pytest.fixture
def empty_win(qapp):
    """Cửa sổ chính chưa mở ảnh nào (đang ở màn hình chào)."""
    import viewer_qt as V

    w = V.MainWindow()
    w.show()
    qapp.processEvents()
    yield w
    w.close()
    qapp.processEvents()


# --------------------------------------------- độ phủ mã nguồn trong báo cáo HTML
def _bang_do_phu():
    """Bảng độ phủ (C0 dòng lệnh + C1 nhánh) dạng text; rỗng nếu không đo."""
    try:
        import coverage
    except ImportError:                  # chưa cài pytest-cov
        return ""
    buf = io.StringIO()
    try:
        cv = coverage.Coverage()         # đọc [tool.coverage.*] trong pyproject.toml
        cv.load()                        # số liệu pytest-cov vừa ghi ra .coverage
        cv.report(file=buf, show_missing=True)
    except Exception:                    # chạy `--no-cov` thì không có số liệu
        return ""
    return buf.getvalue().strip()


def pytest_html_results_summary(prefix, summary, postfix, session):
    """Chèn bảng độ phủ vào phần Summary của báo cáo `reports/test-report.html`.

    pytest-html gọi hook này lúc kết thúc phiên (sau pytest-cov) nên số liệu đã có.
    """
    if session.config.getoption("no_cov", False):
        return          # chạy `--no-cov`: không hiện bảng (tránh số liệu cũ)
    bang = _bang_do_phu()
    if not bang:
        return
    postfix.append(
        "<h2>Độ phủ mã nguồn — C0 (dòng lệnh) và C1 (nhánh)</h2>"
        "<p><b>C0</b> = tỉ lệ dòng lệnh đã chạy · <b>C1</b> = tỉ lệ nhánh "
        "<code>if/else</code>, vòng lặp đã chạy (cột <i>Branch/BrPart</i>). "
        "Xem chi tiết theo từng dòng: <code>reports/cov-html/index.html</code>.</p>"
        "<pre style=\"white-space:pre;overflow:auto;background:#20232a;"
        "color:#e8e8e8;padding:12px;border-radius:8px;font-size:12px;"
        "line-height:1.35\">%s</pre>" % html.escape(bang))
