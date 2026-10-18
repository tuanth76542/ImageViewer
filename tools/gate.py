"""Chạy trọn cổng chất lượng local bằng MỘT lệnh: ``uv run python tools/gate.py``.

Bộ cổng (ADR-0013 mục 1) chạy tuần tự, dừng ngay ở bước đầu tiên đỏ:

1. ``uv run pytest``                                — xanh toàn bộ + độ phủ >= 80;
2. ``uv run --with pyflakes python -m pyflakes …``  — soi các tệp ``.py`` đã sửa/thêm;
3. ``uv run python -m compileall -q …``             — cùng danh sách tệp đó.

Cờ ``--exe`` thêm 2 bước nặng (mặc định **TẮT** để giữ cổng <= 60 s — NF-P5):

4. ``build_exe.bat``  — đóng gói lại;
5. ``uv run python tools\\check_exe.py`` — kiểm tra bundle .exe.

Mã thoát: ``0`` khi mọi bước xanh, khác ``0`` khi có bước đỏ (giữ nguyên mã lỗi
của bước đỏ để dùng được trong script/CI tham chiếu).
"""
import argparse
import os
import subprocess
import sys

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(dong_lenh, timeout=20):
    """Chạy một lệnh git chỉ-đọc; trả stdout, hoặc None nếu git lỗi/không có git."""
    try:
        kq = subprocess.run(["git"] + dong_lenh, cwd=GOC_DU_AN, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return kq.stdout if kq.returncode == 0 else None


def tep_py_da_doi():
    """Các tệp ``.py`` đã sửa/thêm so với ``main`` (kể cả tệp chưa được `git add`).

    Dùng cho bước pyflakes/compileall: chỉ soi phần vừa đụng, giữ cổng chạy nhanh.
    Không có git (hoặc không có nhánh ``main``) thì trả danh sách rỗng — cổng vẫn
    chạy pytest.
    """
    ten = set()
    goc = "main" if _git(["rev-parse", "--verify", "main"]) is not None else "HEAD"
    ra = _git(["diff", "--name-only", "--diff-filter=d", goc])
    if ra:
        ten.update(ra.splitlines())
    ra = _git(["ls-files", "--others", "--exclude-standard"])
    if ra:
        ten.update(ra.splitlines())
    return sorted(t.strip() for t in ten
                  if t.strip().endswith(".py")
                  and os.path.exists(os.path.join(GOC_DU_AN, t.strip())))


def _pyflakes(tep):
    return ["uv", "run", "--with", "pyflakes", "python", "-m", "pyflakes"] + list(tep)


def _compileall(tep):
    return ["uv", "run", "python", "-m", "compileall", "-q"] + list(tep)


def cac_buoc(tep=None, exe=False):
    """Danh sách ``[(tên bước, lệnh)]`` của cổng local."""
    if tep is None:
        tep = tep_py_da_doi()
    buoc = [("pytest", ["uv", "run", "pytest"])]
    if tep:
        buoc.append(("pyflakes", _pyflakes(tep)))
        buoc.append(("compileall", _compileall(tep)))
    if exe:
        buoc.append(("build .exe", ["cmd", "/c", "build_exe.bat"]))
        buoc.append(("check .exe", ["uv", "run", "python",
                                    os.path.join("tools", "check_exe.py")]))
    return buoc


def _chay_that(lenh):
    """Chạy thật một lệnh, trả mã thoát (1 nếu không chạy được)."""
    try:
        return subprocess.run(lenh, cwd=GOC_DU_AN).returncode
    except OSError as ex:
        print("  không chạy được: %s" % ex)
        return 1


def chay(buoc, runner=None):
    """Chạy lần lượt các bước, dừng ở bước đỏ. Trả mã thoát (0 = cổng xanh).

    ``runner`` là hàm nhận một lệnh và trả mã thoát — test truyền runner giả để
    kiểm 2 nhánh xanh/đỏ mà không thật sự chạy pytest.
    """
    runner = runner or _chay_that
    for so, (ten, lenh) in enumerate(buoc, 1):
        print("[%d/%d] %s: %s" % (so, len(buoc), ten, " ".join(lenh)))
        ma = runner(lenh)
        if ma != 0:
            print("  ĐỎ — dừng ở bước '%s' (mã thoát %s)." % (ten, ma))
            return ma if isinstance(ma, int) and ma > 0 else 1
        print("  xanh")
    print("Cổng local: XANH.")
    return 0


def main(argv=None, runner=None):
    try:
        # Console Windows mặc định cp1252 -> tiếng Việt sẽ lỗi khi in
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass                              # nơi đã lo mã hoá sẵn (vd. pytest)
    p = argparse.ArgumentParser(
        prog="gate.py", description="Chạy trọn cổng chất lượng local (một lệnh)")
    p.add_argument("--exe", action="store_true",
                   help="thêm build .exe + tools\\check_exe.py (mặc định tắt cho nhanh)")
    args = p.parse_args(argv)

    tep = tep_py_da_doi()
    if tep:
        print("Tệp .py đã sửa/thêm (%d): %s" % (len(tep), ", ".join(tep)))
    else:
        print("Không thấy tệp .py nào đã sửa/thêm — bỏ qua pyflakes/compileall.")
    return chay(cac_buoc(tep, exe=args.exe), runner=runner)


if __name__ == "__main__":
    sys.exit(main())
