"""Đo tốc độ + RAM của bộ lọc ảnh nữ (`loc_nu`) trên một thư mục ảnh thật.

Cách dùng (chạy từ thư mục gốc dự án)::

    uv run python tools\\bench_loc_nu.py "D:\\Anh"                  # dùng cache thật -> đo delta
    uv run python tools\\bench_loc_nu.py "D:\\Anh" --no-cache       # quét nguội, cache tạm
    uv run python tools\\bench_loc_nu.py "D:\\Anh" --hien-after 5   # mốc ảnh nữ thứ N
    uv run python tools\\bench_loc_nu.py "D:\\Anh" --detail         # kèm 10 ảnh chậm nhất
    uv run python tools\\bench_loc_nu.py "D:\\Anh" --json kq.json   # ghi số liệu ra JSON

Số liệu in ra:
  * số ảnh trong thư mục và số ảnh **phải suy luận** (phần còn lại là cache hit);
  * giây/ảnh: trung bình, trung vị, p95, nhanh nhất / chậm nhất;
  * tổng thời gian quét và **thời gian tới ảnh nữ thứ N** (mốc "hiện dần" của
    giao diện — xem `SHOW_AFTER` trong `xemanh/mainwindow.py`);
  * RAM đỉnh (RSS) của tiến trình trong lúc quét.

``--no-cache`` **không** xoá cache thật của người dùng: nó chỉ trỏ `CACHE_PATH`
sang một thư mục tạm rồi dọn đi khi xong. Muốn đo delta trên chính dữ liệu vừa
quét nguội thì dùng ``--cache`` trỏ cùng một tệp cho hai lần chạy::

    uv run python tools\\bench_loc_nu.py "D:\\Anh" --cache "%TEMP%\\bench.json"   # nguội
    uv run python tools\\bench_loc_nu.py "D:\\Anh" --cache "%TEMP%\\bench.json"   # delta

Số ảnh suy luận được đếm bằng cách bọc `FemaleFilter.is_female_image`, nên đúng
bằng số lần model thực sự phải chạy (cache hit không tính).
"""
import argparse
import json
import os
import shutil
import statistics
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from xemanh.imageutils import list_images_in_folder      # noqa: E402


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
        description="Đo tốc độ + RAM khi lọc ảnh nữ trên một thư mục ảnh.")
    p.add_argument("path", help="thư mục chứa ảnh cần đo")
    p.add_argument("--no-cache", action="store_true",
                   help="quét nguội bằng cache tạm (không đụng cache thật)")
    p.add_argument("--cache", default=None,
                   help="dùng tệp cache chỉ định (để đo nguội rồi delta trên cùng dữ liệu)")
    p.add_argument("--keep-cache", action="store_true",
                   help="giữ lại cache tạm của --no-cache (mặc định xoá)")
    p.add_argument("--limit", type=int, default=0,
                   help="chỉ đo N ảnh đầu (0 = hết thư mục)")
    p.add_argument("--hien-after", type=int, default=5,
                   help="mốc số ảnh nữ để tính thời gian 'hiện dần' (mặc định 5)")
    p.add_argument("--detail", action="store_true",
                   help="in thêm 10 ảnh suy luận chậm nhất")
    p.add_argument("--json", default=None,
                   help="ghi số liệu ra tệp JSON để so sánh giữa các lần chạy")
    return p


class _DoRam(threading.Thread):
    """Luồng nền lấy mẫu RSS, giữ lại mức cao nhất (MB)."""

    def __init__(self, interval=0.2):
        super().__init__(daemon=True)
        self.interval = interval
        self.peak_mb = 0.0
        self._dung = threading.Event()
        self._proc = None
        self._co_psutil = False

    def run(self):
        try:
            import psutil
        except ImportError:
            return
        self._co_psutil = True
        self._proc = psutil.Process()
        while not self._dung.is_set():
            try:
                rss = self._proc.memory_info().rss / (1024.0 * 1024.0)
                self.peak_mb = max(self.peak_mb, rss)
            except Exception:
                pass
            self._dung.wait(self.interval)

    def stop(self):
        self._dung.set()
        self.join(timeout=2.0)


def _chon_cache(args):
    """Trả về (đường dẫn cache, thư mục tạm cần dọn hoặc None)."""
    import loc_nu

    if args.no_cache:
        tam = tempfile.mkdtemp(prefix="bench_loc_nu_")
        return os.path.join(tam, "cache.json"), tam
    if args.cache:
        duong = os.path.abspath(args.cache)
        os.makedirs(os.path.dirname(duong) or ".", exist_ok=True)
        return duong, None
    return loc_nu.CACHE_PATH, None


def _phay(x):
    return f"{x:,.2f}".replace(",", " ")


def _do_do(args):
    import loc_nu

    paths = list_images_in_folder(args.path)
    if args.limit > 0:
        paths = paths[:args.limit]
    if not paths:
        print(f"Không thấy ảnh nào trong: {args.path}")
        return 1

    cache_path, thu_muc_tam = _chon_cache(args)
    loc_nu.CACHE_PATH = cache_path

    # Đếm + bấm giờ từng lần suy luận thật (cache hit không đi qua hàm này).
    goc = loc_nu.FemaleFilter.is_female_image
    thoi_gian = []
    da_suy_luan = []

    def _boc(self, path):
        t0 = time.perf_counter()
        try:
            return goc(self, path)
        finally:
            thoi_gian.append(time.perf_counter() - t0)
            da_suy_luan.append(path)

    loc_nu.FemaleFilter.is_female_image = _boc

    giu_lai = []
    moc_hien = [None]          # giây tới ảnh nữ thứ N
    moc_da_xong = [0]          # lúc đó đã quét xong bao nhiêu ảnh
    t_bat_dau = time.perf_counter()

    def _tien_do(done, total, path, ok):
        if not ok:
            return
        giu_lai.append(path)
        if moc_hien[0] is None and len(giu_lai) >= args.hien_after:
            moc_hien[0] = time.perf_counter() - t_bat_dau
            moc_da_xong[0] = done

    do_ram = _DoRam()
    do_ram.start()
    try:
        loc_nu.download_models()
        kept = loc_nu.filter_female(paths, on_progress=_tien_do)
    finally:
        tong = time.perf_counter() - t_bat_dau
        do_ram.stop()
        loc_nu.FemaleFilter.is_female_image = goc

    if thu_muc_tam and not args.keep_cache:
        shutil.rmtree(thu_muc_tam, ignore_errors=True)

    # ------------------------------------------------------------- báo cáo
    n = len(paths)
    n_suy_luan = len(thoi_gian)
    print()
    print("=" * 68)
    print("BENCH LỌC ẢNH NỮ")
    print("=" * 68)
    print(f"Thư mục            : {args.path}")
    print(f"Số ảnh             : {n}")
    print(f"Cache              : {cache_path}"
          + (f"  (tạm, {'giữ lại' if args.keep_cache else 'đã xoá'})"
             if thu_muc_tam else
             ("  (tệp chỉ định)" if args.cache else "  (cache thật)")))
    print(f"Phải suy luận      : {n_suy_luan} / {n}"
          f"  (cache hit: {n - n_suy_luan})")
    print(f"Tổng thời gian quét: {_phay(tong)} giây")
    if n_suy_luan and tong > 0:
        print(f"Tốc độ tổng        : {_phay(n / tong)} ảnh/giây "
              f"(~{_phay(1000 * tong / n)} ms/ảnh)")
    if moc_hien[0] is not None:
        print(f"Tới {args.hien_after} ảnh nữ đầu : {_phay(moc_hien[0])} giây "
              f"(lúc đó mới quét xong {moc_da_xong[0]}/{n} ảnh)")
    else:
        print(f"Tới {args.hien_after} ảnh nữ đầu : không đủ "
              f"{args.hien_after} ảnh nữ trong thư mục (được {len(giu_lai)})")
    print(f"Kết quả            : giữ lại {len(kept)} / {n} ảnh có người nữ")

    if thoi_gian:
        sx = sorted(thoi_gian)
        p95 = sx[min(len(sx) - 1, int(round(0.95 * (len(sx) - 1))))]
        print("-" * 68)
        print("THỜI GIAN SUY LUẬN MỖI ẢNH (chỉ ảnh phải chạy model)")
        print(f"  trung bình : {_phay(1000 * statistics.mean(thoi_gian))} ms")
        print(f"  trung vị   : {_phay(1000 * statistics.median(thoi_gian))} ms")
        print(f"  p95        : {_phay(1000 * p95)} ms")
        print(f"  nhanh nhất : {_phay(1000 * min(thoi_gian))} ms"
              f"   ({os.path.basename(da_suy_luan[thoi_gian.index(min(thoi_gian))])})")
        print(f"  chậm nhất  : {_phay(1000 * max(thoi_gian))} ms"
              f"   ({os.path.basename(da_suy_luan[thoi_gian.index(max(thoi_gian))])})")

    if do_ram._co_psutil:
        print(f"RAM đỉnh (RSS)     : {_phay(do_ram.peak_mb)} MB")
    else:
        print("RAM đỉnh (RSS)     : không đo được (thiếu psutil — chạy `uv sync`)")

    if args.detail and thoi_gian:
        print("-" * 68)
        print("10 ẢNH SUY LUẬN CHẬM NHẤT")
        for i in sorted(range(len(thoi_gian)), key=lambda k: -thoi_gian[k])[:10]:
            print(f"  {_phay(1000 * thoi_gian[i]):>9} ms  {os.path.basename(da_suy_luan[i])}")

    print("=" * 68)

    if args.json:
        so_lieu = {
            "thu_muc": args.path,
            "so_anh": n,
            "so_anh_suy_luan": n_suy_luan,
            "cache": cache_path,
            "la_cache_that": thu_muc_tam is None and not args.cache,
            "tong_giay": tong,
            "giay_moi_anh_nguoi": (n_suy_luan / tong) if tong > 0 else None,
            "giay_toi_moc_hien": moc_hien[0],
            "moc_hien_after": args.hien_after,
            "ram_dinh_mb": do_ram.peak_mb if do_ram._co_psutil else None,
            "giu_lai": len(kept),
            "ms_trung_binh": 1000 * statistics.mean(thoi_gian) if thoi_gian else None,
            "ms_trung_vi": 1000 * statistics.median(thoi_gian) if thoi_gian else None,
        }
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(so_lieu, fh, ensure_ascii=False, indent=2)
        print(f"đã ghi số liệu vào {args.json}")
    return 0


def main(argv=None):
    _thiet_lap_stdout()
    args = _them_tham_so().parse_args(argv)
    if args.no_cache and args.cache:
        print("Chỉ dùng một trong hai: --no-cache hoặc --cache.")
        return 2
    return _do_do(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nĐã dừng theo yêu cầu.")
        sys.exit(130)
