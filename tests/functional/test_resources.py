"""Test đo tài nguyên: RAM không phình, CPU lúc rảnh thấp.

Ngưỡng đặt rộng (gấp ~4-8 lần số đo thực tế) để không báo lỗi giả, nhưng vẫn
đủ chặt để bắt các lỗi thật: nạp sẵn cả thư mục ảnh vào RAM, rò rỉ RAM khi
chuyển ảnh/zoom, hoặc vòng lặp sự kiện quay nóng CPU.

Số đo trên máy dev (offscreen, chỉ PySide6 + Pillow): nền ~55MB, mở 24 ảnh
1600x1200 ~72MB, 60 lần chuyển ảnh tăng ~0.2MB, CPU lúc rảnh 0.0%.
Khi dùng bộ lọc nữ, app nạp thêm OpenCV + onnxruntime (~200MB) nên đừng đo ở
trạng thái đó.
"""
import time

import pytest

import viewer_qt as V

from xemanh import perf

pytestmark = pytest.mark.resources

RAM_TOI_DA_KHI_MO_CUA_SO = 300          # MB
RAM_TANG_TOI_DA_KHI_MO_THU_MUC = 120    # MB — mở 24 ảnh lớn
RAM_TANG_TOI_DA_KHI_CHUYEN_ANH = 30     # MB — 60 lần chuyển ảnh
RAM_TANG_TOI_DA_KHI_ZOOM_XOAY = 30      # MB — 30 vòng zoom + xoay
RAM_TANG_TOI_DA_KHI_TRINH_CHIEU = 80    # MB — 20 bước trình chiếu
CPU_TOI_DA_LUC_RA_NHANH = 60.0          # % của một nhân, đo trong 2 giây


def _rss_mb():
    try:
        return perf.rss_now_mb()
    except Exception as exc:            # máy không đo được -> bỏ qua, không fail
        pytest.skip("không đo được RAM của tiến trình: %s" % exc)


def test_ram_sau_khi_mo_cua_so_nam_trong_nguong(win):
    rss = _rss_mb()
    assert rss < RAM_TOI_DA_KHI_MO_CUA_SO, "RAM %.0f MB khi mới mở cửa sổ" % rss


def test_mo_thu_muc_anh_lon_khong_nap_san_toan_bo(empty_win, big_folder, qapp):
    truoc = _rss_mb()
    empty_win.open_folder(big_folder)
    qapp.processEvents()
    tang = _rss_mb() - truoc
    assert len(empty_win.image_list) == 24
    assert tang < RAM_TANG_TOI_DA_KHI_MO_THU_MUC, (
        "mở 24 ảnh 1600x1200 làm RAM tăng %.0f MB — nghi nạp sẵn toàn bộ ảnh"
        % tang)


def test_chuyen_anh_nhieu_lan_khong_ro_ri_ram(win, qapp):
    truoc = _rss_mb()
    for _ in range(60):
        win.next_image()
        qapp.processEvents()
    tang = _rss_mb() - truoc
    assert tang < RAM_TANG_TOI_DA_KHI_CHUYEN_ANH, (
        "RAM tăng %.0f MB sau 60 lần chuyển ảnh" % tang)


def test_zoom_va_xoay_nhieu_lan_khong_ro_ri_ram(win, qapp):
    truoc = _rss_mb()
    for _ in range(30):
        win.zoom_in()
        win.zoom_out()
        win.rotate_image()
        qapp.processEvents()
    tang = _rss_mb() - truoc
    assert tang < RAM_TANG_TOI_DA_KHI_ZOOM_XOAY, (
        "RAM tăng %.0f MB sau 30 vòng zoom + xoay" % tang)


def test_trinh_chieu_nhieu_buoc_khong_ro_ri_ram(win, qapp):
    truoc = _rss_mb()
    dlg = V.SlideDialog(win)
    try:
        for _ in range(20):
            dlg.step(1)
            qapp.processEvents()
    finally:
        dlg.close()
    tang = _rss_mb() - truoc
    assert tang < RAM_TANG_TOI_DA_KHI_TRINH_CHIEU, (
        "RAM tăng %.0f MB sau 20 bước trình chiếu" % tang)


def test_cpu_luc_ranh_thap(win, qapp):
    if not perf.has_psutil():
        pytest.skip("thiếu psutil nên không đo được CPU")
    mon = perf.ResourceMonitor()
    mon.sample()                        # mẫu đầu chỉ để lấy mốc thời gian CPU
    time.sleep(2.0)
    qapp.processEvents()
    s = mon.sample()
    assert s.cpu_pct is not None
    assert s.cpu_pct < CPU_TOI_DA_LUC_RA_NHANH, (
        "CPU lúc rảnh %.1f%% — có vòng lặp/timer quay nóng" % s.cpu_pct)


def test_do_duoc_ca_tien_trinh_con():
    """App thật chạy sau một 'vỏ' python.exe, nên phải cộng được cả con."""
    if not perf.has_psutil():
        pytest.skip("thiếu psutil nên không đo được tiến trình con")
    import subprocess
    import sys

    code = ("import time\n"
            "x = bytearray(150 * 1024 * 1024)\n"   # giữ 150MB
            "time.sleep(20)\n")
    child = subprocess.Popen([sys.executable, "-c", code])
    try:
        time.sleep(3.0)
        rieng = perf.ResourceMonitor().sample().rss_mb
        ca_con = perf.ResourceMonitor(include_children=True).sample().rss_mb
        assert ca_con > rieng + 100, (
            "không cộng được RAM tiến trình con: riêng %.0f MB, cả con %.0f MB"
            % (rieng, ca_con))
    finally:
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
