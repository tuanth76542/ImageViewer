"""Đo tài nguyên tiêu thụ của tiến trình: RAM, CPU, số thread, số handle.

Dùng cho hai việc:

* ``tools/measure_resources.py`` — chạy app rồi in báo cáo tài nguyên.
* ``tests/functional/test_resources.py`` — test tự động có ngưỡng RAM/CPU.

``psutil`` là nguồn số liệu chính; nếu máy chưa có psutil thì vẫn đo được RAM
trên Windows bằng ctypes (CPU sẽ bỏ trống chứ không báo sai).
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass

__all__ = ["ResourceSample", "ResourceMonitor", "summarize", "format_report",
           "format_row", "has_psutil"]


def _psutil():
    try:
        import psutil
        return psutil
    except Exception:
        return None


def has_psutil():
    """True nếu đo được cả CPU (có psutil)."""
    return _psutil() is not None


# ---------------------------------------------------------------- mẫu số liệu
@dataclass
class ResourceSample:
    """Một lần đo tài nguyên."""

    t: float = 0.0                  # giây kể từ lúc bắt đầu đo
    rss_mb: float = 0.0             # RAM thực tế (working set), MB
    cpu_pct: float = None           # % CPU (100% = 1 nhân); None nếu chưa đo được
    threads: int = 0
    handles: int = None             # Windows: số handle đang mở


def _win_rss_mb(pid):
    """RAM (working set) trên Windows, không cần psutil."""
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        raise OSError("không mở được tiến trình %s" % pid)
    try:
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        if not ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb):
            raise OSError("GetProcessMemoryInfo lỗi")
        return counters.WorkingSetSize / (1024.0 * 1024.0)
    finally:
        kernel32.CloseHandle(handle)


class ResourceMonitor:
    """Lấy mẫu tài nguyên của một tiến trình (mặc định: tiến trình hiện tại).

    ``include_children=True`` sẽ cộng gộp cả các tiến trình con — cần thiết khi
    tiến trình được đo chỉ là "vỏ" khởi chạy (ví dụ ``.venv\\Scripts\\python.exe``
    là bản launcher, tiến trình thật là con của nó).

    >>> mon = ResourceMonitor()
    >>> mon.sample().rss_mb > 0
    True
    """

    def __init__(self, pid=None, include_children=False):
        self.pid = int(pid or os.getpid())
        self.include_children = bool(include_children)
        self._ps = _psutil()
        self._proc = None
        if self._ps is not None:
            self._proc = self._ps.Process(self.pid)
        self._prev_cpu = {}
        self._prev_wall = None
        self.peak_rss_mb = 0.0

    def _targets(self):
        """Tiến trình cần đo (kèm con cháu nếu được yêu cầu)."""
        procs = [self._proc]
        if self.include_children:
            try:
                procs += self._proc.children(recursive=True)
            except Exception:
                pass
        return procs

    # -- một lần đo ------------------------------------------------------
    def snapshot(self):
        """(rss_mb, cpu_pct, threads, handles) tại thời điểm gọi."""
        if self._proc is None:                      # không có psutil
            rss_mb = _win_rss_mb(self.pid)
            self.peak_rss_mb = max(self.peak_rss_mb, rss_mb)
            return rss_mb, None, 0, None

        now = time.monotonic()
        rss = 0.0
        threads = 0
        handles = 0
        co_handle = False
        cur_cpu = {}
        for p in self._targets():
            try:
                with p.oneshot():
                    rss += p.memory_info().rss
                    threads += p.num_threads()
                    times = p.cpu_times()
                    cur_cpu[p.pid] = (float(getattr(times, "user", 0.0))
                                      + float(getattr(times, "system", 0.0)))
                    try:
                        handles += p.num_handles()
                        co_handle = True
                    except Exception:
                        pass
            except Exception:                       # tiến trình đã tắt giữa chừng
                continue
        rss_mb = rss / (1024.0 * 1024.0)
        cpu_pct = None
        if self._prev_wall is not None:
            dt = now - self._prev_wall
            if dt > 0:
                delta = sum(max(0.0, c - self._prev_cpu[pid])
                            for pid, c in cur_cpu.items()
                            if pid in self._prev_cpu)
                cpu_pct = 100.0 * delta / dt
        self._prev_cpu, self._prev_wall = cur_cpu, now
        self.peak_rss_mb = max(self.peak_rss_mb, rss_mb)
        return rss_mb, cpu_pct, threads, handles if co_handle else None

    def sample(self, t=0.0):
        rss_mb, cpu_pct, threads, handles = self.snapshot()
        return ResourceSample(t=t, rss_mb=rss_mb, cpu_pct=cpu_pct,
                              threads=threads, handles=handles)

    # -- nhiều lần đo ----------------------------------------------------
    def measure(self, duration=5.0, interval=0.5, on_sample=None):
        """Lấy mẫu trong `duration` giây; trả về danh sách ResourceSample."""
        out = []
        start = time.monotonic()
        while True:
            t = time.monotonic() - start
            s = self.sample(t)
            out.append(s)
            if on_sample is not None:
                on_sample(s)
            if t >= duration:
                break
            time.sleep(min(interval, max(0.0, duration - t)))
        return out


# ------------------------------------------------------------------- báo cáo
def rss_now_mb(pid=None):
    """RAM hiện tại (MB) — tiện cho test."""
    return ResourceMonitor(pid).snapshot()[0]


def summarize(samples):
    """Gộp danh sách mẫu thành các con số tổng hợp."""
    if not samples:
        return {}
    rss = [s.rss_mb for s in samples]
    cpu = [s.cpu_pct for s in samples if s.cpu_pct is not None]
    handles = [s.handles for s in samples if s.handles is not None]
    return {
        "n": len(samples),
        "duration_s": samples[-1].t - samples[0].t,
        "rss_min_mb": min(rss),
        "rss_max_mb": max(rss),
        "rss_avg_mb": sum(rss) / len(rss),
        "rss_growth_mb": rss[-1] - rss[0],
        "cpu_avg_pct": (sum(cpu) / len(cpu)) if cpu else None,
        "cpu_max_pct": max(cpu) if cpu else None,
        "threads_max": max(s.threads for s in samples),
        "handles_max": max(handles) if handles else None,
    }


def format_row(s):
    """Một dòng sống cho chế độ theo dõi trực tiếp."""
    cpu = "  --  " if s.cpu_pct is None else "%5.1f%%" % s.cpu_pct
    extra = "" if s.handles is None else "  handle=%-5d" % s.handles
    return "t=%6.1fs  RAM=%7.1f MB  CPU=%s  thread=%-3d%s" % (
        s.t, s.rss_mb, cpu, s.threads, extra)


def format_report(samples, label="app"):
    """Báo cáo nhiều dòng để in ra màn hình."""
    m = summarize(samples)
    if not m:
        return "(không có số liệu)"
    cpu_txt = "không đo được (thiếu psutil)"
    if m["cpu_avg_pct"] is not None:
        cpu_txt = "trung bình %.1f%% · cao nhất %.1f%%" % (
            m["cpu_avg_pct"], m["cpu_max_pct"])
    handle_txt = "" if m["handles_max"] is None else \
        " · handle tối đa %d" % m["handles_max"]
    return "\n".join([
        "== %s ==" % label,
        "  thời gian đo : %.1f giây (%d mẫu)" % (m["duration_s"], m["n"]),
        "  RAM          : thấp nhất %.1f MB · trung bình %.1f MB · cao nhất %.1f MB"
        % (m["rss_min_mb"], m["rss_avg_mb"], m["rss_max_mb"]),
        "  RAM tăng thêm: %+.1f MB" % m["rss_growth_mb"],
        "  CPU          : %s" % cpu_txt,
        "  thread tối đa: %d%s" % (m["threads_max"], handle_txt),
    ])


def main(argv=None):
    """Chạy nhanh: `python -m xemanh.perf [giây]` đo chính tiến trình này."""
    argv = list(sys.argv[1:] if argv is None else argv)
    duration = float(argv[0]) if argv else 5.0
    mon = ResourceMonitor()
    samples = mon.measure(duration=duration, interval=0.5,
                          on_sample=lambda s: print(format_row(s), flush=True))
    print(format_report(samples, "tiến trình %d" % mon.pid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
