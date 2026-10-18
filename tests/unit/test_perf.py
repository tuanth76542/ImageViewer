"""Test đơn vị cho bộ đo tài nguyên (xemanh.perf) — không cần Qt."""
import os
import sys
import time
import types

import pytest

from xemanh import perf

pytestmark = pytest.mark.unit


def _rss():
    try:
        return perf.rss_now_mb()
    except Exception as exc:                      # máy không đo được -> bỏ qua
        pytest.skip("không đo được RAM của tiến trình: %s" % exc)


def test_do_duoc_ram_cua_tien_trinh_hien_tai():
    assert _rss() > 5          # tiến trình python luôn chiếm hơn 5MB


def test_monitor_tra_ve_du_truong():
    mon = perf.ResourceMonitor()
    s = mon.sample(t=1.5)
    assert s.t == 1.5
    assert s.rss_mb > 5
    assert s.threads >= 1 or not perf.has_psutil()
    assert mon.peak_rss_mb >= s.rss_mb


def test_measure_lay_nhieu_mau_theo_thoi_gian():
    mon = perf.ResourceMonitor()
    samples = mon.measure(duration=0.3, interval=0.1)
    assert len(samples) >= 2
    assert samples[-1].t >= 0.3
    assert [s.t for s in samples] == sorted(s.t for s in samples)


def test_summarize_tinh_dung_cac_chi_so():
    samples = [perf.ResourceSample(t=0, rss_mb=100, cpu_pct=10, threads=4),
               perf.ResourceSample(t=1, rss_mb=120, cpu_pct=30, threads=5)]
    m = perf.summarize(samples)
    assert m["n"] == 2
    assert m["duration_s"] == 1
    assert m["rss_min_mb"] == 100 and m["rss_max_mb"] == 120
    assert m["rss_growth_mb"] == 20
    assert m["cpu_avg_pct"] == 20 and m["cpu_max_pct"] == 30
    assert m["threads_max"] == 5


def test_summarize_khi_khong_co_mau():
    assert perf.summarize([]) == {}


def test_summarize_bo_qua_cpu_khi_khong_do_duoc():
    samples = [perf.ResourceSample(t=0, rss_mb=50, cpu_pct=None, threads=2)]
    m = perf.summarize(samples)
    assert m["cpu_avg_pct"] is None
    assert m["rss_max_mb"] == 50


def test_format_report_va_format_row():
    samples = [perf.ResourceSample(t=0, rss_mb=100, cpu_pct=10, threads=4),
               perf.ResourceSample(t=1, rss_mb=120, cpu_pct=30, threads=5)]
    report = perf.format_report(samples, "thử nghiệm")
    assert "thử nghiệm" in report
    assert "120.0 MB" in report
    assert "trung bình 20.0%" in report

    row = perf.format_row(samples[-1])
    assert "RAM=" in row and "120.0 MB" in row


# ------------------------------------------------ đường dự phòng khi thiếu psutil
def test_doc_ram_khong_can_psutil():
    """`_win_rss_mb` là đường dự phòng khi máy không cài psutil."""
    mb = perf._win_rss_mb(os.getpid())
    assert mb > 5
    assert abs(mb - _rss()) < 200          # khớp với số đo qua psutil


def test_doc_ram_bao_loi_khi_pid_sai():
    with pytest.raises(OSError):
        perf._win_rss_mb(0)                # OpenProcess(0) không mở được


def test_monitor_van_do_duoc_khi_thieu_psutil(monkeypatch):
    monkeypatch.setattr(perf, "_psutil", lambda: None)
    mon = perf.ResourceMonitor()

    assert mon._proc is None                       # không có psutil
    assert perf.has_psutil() is False
    rss_mb, cpu_pct, threads, handles = mon.snapshot()
    assert rss_mb > 5
    assert (cpu_pct, threads, handles) == (None, 0, None)
    assert mon.peak_rss_mb == rss_mb


def test_psutil_tra_ve_none_khi_import_loi(monkeypatch):
    # None trong sys.modules làm `import psutil` ném ImportError
    monkeypatch.setitem(sys.modules, "psutil", None)
    assert perf._psutil() is None
    assert perf.has_psutil() is False


def test_doc_ram_bao_loi_khi_api_tra_ve_false(monkeypatch):
    import ctypes

    class PsapiGia:
        @staticmethod
        def GetProcessMemoryInfo(*a):
            return 0                               # thất bại -> phải ném OSError

    monkeypatch.setattr(ctypes.windll, "psapi", PsapiGia())
    with pytest.raises(OSError, match="GetProcessMemoryInfo"):
        perf._win_rss_mb(os.getpid())


def test_snapshot_bo_qua_tien_trinh_da_tat(monkeypatch):
    if not perf.has_psutil():
        pytest.skip("thiếu psutil nên không đi vào nhánh này")
    mon = perf.ResourceMonitor()

    class DaTat:
        pid = 999999

        def oneshot(self):
            raise OSError("tiến trình đã tắt giữa chừng")

    monkeypatch.setattr(mon, "_targets", lambda: [DaTat()])
    rss_mb, cpu_pct, threads, handles = mon.snapshot()

    assert rss_mb == 0.0 and threads == 0
    assert (cpu_pct, handles) == (None, None)


def test_snapshot_bo_qua_cpu_khi_khoang_thoi_gian_khong_duong(monkeypatch):
    if not perf.has_psutil():
        pytest.skip("thiếu psutil nên CPU luôn là None")
    mon = perf.ResourceMonitor()
    mon._prev_wall = time.monotonic() + 10         # mốc ở tương lai -> dt < 0
    mon._prev_cpu = {}

    rss_mb, cpu_pct, _threads, _handles = mon.snapshot()

    assert rss_mb > 0
    assert cpu_pct is None                         # không chia cho dt <= 0


def test_targets_bo_qua_khi_khong_lay_duoc_tien_trinh_con(monkeypatch):
    mon = perf.ResourceMonitor()
    mon.include_children = True

    class Hong:
        pid = 999999

        def children(self, recursive=False):
            raise OSError("không lấy được con")

    hong = Hong()
    monkeypatch.setattr(mon, "_proc", hong)
    assert mon._targets() == [hong]


def test_snapshot_van_chay_khi_khong_dem_duoc_handle(monkeypatch):
    mon = perf.ResourceMonitor()

    class KhongHandle:
        pid = os.getpid()

        def oneshot(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def memory_info(self):
            return types.SimpleNamespace(rss=5 * 1024 * 1024)

        def num_threads(self):
            return 3

        def cpu_times(self):
            return types.SimpleNamespace(user=0.1, system=0.2)

        def num_handles(self):
            raise OSError("hệ thống không cho đếm handle")

    monkeypatch.setattr(mon, "_proc", KhongHandle())
    rss_mb, cpu_pct, threads, handles = mon.snapshot()

    assert rss_mb == 5.0
    assert threads == 3
    assert handles is None                         # bỏ trống cột handle
    assert cpu_pct is None                         # mẫu đầu chưa tính được CPU


def test_measure_lay_mau_va_goi_on_sample():
    mon = perf.ResourceMonitor()
    da_goi = []
    samples = mon.measure(duration=0.05, interval=0.01, on_sample=da_goi.append)

    assert len(samples) == len(da_goi) >= 1
    assert samples[-1].t >= 0.05                   # dừng đúng sau duration


def test_format_report_khi_thieu_psutil():
    s = perf.ResourceSample(t=1.0, rss_mb=10.0, cpu_pct=None, threads=2,
                            handles=None)
    report = perf.format_report([s], "app")
    assert "không đo được (thiếu psutil)" in report
    assert "handle" not in report
    assert perf.format_report([]) == "(không có số liệu)"


def test_main_in_bao_cao_ra_man_hinh(capsys):
    assert perf.main(["0.01"]) == 0
    out = capsys.readouterr().out
    assert "RAM=" in out                           # dòng sống (format_row)
    assert "thời gian đo" in out and "CPU" in out  # báo cáo tổng hợp
