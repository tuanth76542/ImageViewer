"""Đo tài nguyên app tiêu thụ: RAM, CPU, số thread, số handle.

Cách dùng (chạy từ thư mục gốc dự án)::

    uv run python tools/measure_resources.py                        # mở app trống
    uv run python tools/measure_resources.py "D:\\Anh"             # mở sẵn thư mục ảnh
    uv run python tools/measure_resources.py "D:\\Anh" -s 30        # đo trong 30 giây
    uv run python tools/measure_resources.py --pid 1234             # đo tiến trình đang chạy
    uv run python tools/measure_resources.py "D:\\Anh" --csv ket-qua.csv

Trong lúc đo, bạn cứ thao tác bình thường (chuyển ảnh, zoom, trình chiếu...)
để xem RAM/CPU thay đổi thế nào; số liệu in ra từng mẫu và tổng kết ở cuối.

Số liệu mặc định được cộng gộp cả tiến trình con, vì trên Windows app được mở
qua ``.venv\\Scripts\\python.exe`` (chỉ là "vỏ" khởi chạy) còn tiến trình thật
nằm ở con của nó.
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from xemanh import perf          # noqa: E402


def _thiet_lap_stdout():
    """Console Windows thật đã tự lo UTF-8; khi bị pipe thì in kiểu an toàn."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _them_tham_so():
    p = argparse.ArgumentParser(
        description="Đo RAM/CPU của app xem ảnh (tự mở app rồi lấy số liệu).")
    p.add_argument("path", nargs="?", default=None,
                   help="thư mục hoặc tệp ảnh để app mở sẵn")
    p.add_argument("-s", "--seconds", type=float, default=20.0,
                   help="thời gian đo, giây (0 = tới khi bạn đóng app)")
    p.add_argument("-i", "--interval", type=float, default=0.5,
                   help="khoảng cách giữa hai lần lấy mẫu, giây")
    p.add_argument("--pid", type=int, default=None,
                   help="đo tiến trình đang chạy thay vì mở app mới")
    p.add_argument("--no-children", action="store_true",
                   help="chỉ đo tiến trình chính, không cộng tiến trình con "
                        "(mặc định có cộng, vì app được mở qua python.exe launcher)")
    p.add_argument("--csv", default=None,
                   help="ghi từng mẫu ra tệp CSV để vẽ biểu đồ")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="chỉ in tổng kết, không in từng mẫu")
    return p


def _ghi_csv(path, samples):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_giay", "ram_mb", "cpu_pct", "thread", "handle"])
        for s in samples:
            w.writerow([round(s.t, 2), round(s.rss_mb, 1),
                        "" if s.cpu_pct is None else round(s.cpu_pct, 1),
                        s.threads, "" if s.handles is None else s.handles])
    print("đã ghi %d mẫu vào %s" % (len(samples), path))


def _vong_do(mon, duration, interval, quiet, con_song=None):
    """Lấy mẫu theo thời gian; dừng sớm nếu `con_song()` trả False.

    Trả về (danh sách mẫu, lý do dừng).
    """
    samples = []
    start = time.monotonic()
    while True:
        if con_song is not None and not con_song():
            return samples, "app đã thoát"
        t = time.monotonic() - start
        try:
            s = mon.sample(t)
        except Exception:
            return samples, "không đọc được số liệu tiến trình"
        samples.append(s)
        if not quiet:
            print("  " + perf.format_row(s), flush=True)
        if duration is not None and t >= duration:
            return samples, "hết thời gian đo"
        time.sleep(interval)


def _do_pid(args):
    nhan = "cả tiến trình con" if not args.no_children else "riêng tiến trình"
    print("Đang đo tiến trình PID %d (%s) trong %.0f giây..."
          % (args.pid, nhan, args.seconds))
    mon = perf.ResourceMonitor(args.pid,
                               include_children=not args.no_children)
    samples, ly_do = _vong_do(mon, args.seconds, args.interval, args.quiet)
    if samples:
        print(perf.format_report(samples, "tiến trình %d (%s)" % (args.pid, nhan)))
    else:
        print("Không lấy được số liệu (%s)." % ly_do)
    if samples and args.csv:
        _ghi_csv(args.csv, samples)
    return 0


def _mo_app_va_do(args):
    cmd = [sys.executable, os.path.join(ROOT, "viewer_qt.py")]
    if args.path:
        cmd.append(args.path)
    log = tempfile.NamedTemporaryFile(
        mode="w+", suffix=".log", delete=False, encoding="utf-8")
    print("Mở app: %s" % " ".join(cmd))
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    try:
        mon = perf.ResourceMonitor(proc.pid,
                                   include_children=not args.no_children)
        # chờ app nạp xong (import Qt...) — số liệu chỉ tính từ lúc RAM đứng yên
        truoc = 0.0
        for _ in range(24):
            if proc.poll() is not None:
                break
            try:
                rss = mon.snapshot()[0]
            except Exception:
                break
            if rss > 20 and abs(rss - truoc) < 1.5:
                break
            truoc = rss
            time.sleep(0.25)
        time.sleep(0.3)                         # lấy mốc CPU rõ ràng
        mon.snapshot()
        duration = None if args.seconds <= 0 else args.seconds
        if duration is None:
            print("Đo cho tới khi bạn đóng app (Ctrl+C để dừng sớm).")
        else:
            print("Đo trong %.0f giây (cứ thao tác bình thường)." % duration)

        samples, ly_do = _vong_do(
            mon, duration, args.interval, args.quiet,
            con_song=lambda: proc.poll() is None)
        if samples:
            nhan = "cả tiến trình con" if not args.no_children else "riêng tiến trình"
            print(perf.format_report(
                samples, "app xem ảnh (PID %d, %s)" % (proc.pid, nhan)))
            if args.csv:
                _ghi_csv(args.csv, samples)
        else:
            print("Không lấy được số liệu (%s)." % ly_do)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        log.flush()
        log.close()
        out = open(log.name, encoding="utf-8", errors="replace").read().strip()
        if out:                      # app in lỗi ra thì hiện cho thấy
            print("\n--- app in ra ---\n%s" % out[-2000:])
        try:
            os.unlink(log.name)
        except OSError:
            pass
    return 0


def main(argv=None):
    _thiet_lap_stdout()
    args = _them_tham_so().parse_args(argv)
    if not perf.has_psutil():
        print("Lưu ý: chưa có psutil nên không đo được CPU "
              "(cài bằng `uv sync`, hoặc chạy `uv run --with psutil ...`).")
    if args.pid:
        return _do_pid(args)
    return _mo_app_va_do(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nĐã dừng theo yêu cầu.")
        sys.exit(130)
