"""Cấp mã ``TASK-NNN`` không trùng + liệt kê task (dùng: ``uv run python tools/task.py <lệnh>``).

Vì sao có công cụ này: khi nhiều phiên/người cùng lập kế hoạch thì gõ tay dễ chọn
trùng số (TASK-002 từng có 2 tệp cùng số ở hai thời điểm). Quyết định: ADR-0015.

Lệnh::

    new <tên-ngắn>   cấp số nhỏ nhất còn trống rồi tạo tệp từ tasks/MAU_TASK.md
    list             liệt kê task + trạng thái đọc từ tệp

Số đang dùng được quét từ **tệp trên đĩa** và từ **các nhánh local/remote** của
repo (``git for-each-ref`` + ``git ls-tree`` — chỉ đọc, **không gọi mạng**).

Mẫu tệp là ``tasks/MAU_TASK.md``: nguồn duy nhất, dùng chung với agent
``task-planning`` (``uv run python tools\\agents.py check`` sẽ bắt nếu hai bên lệch).
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import unicodedata

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THU_MUC_TASK = os.path.join(GOC_DU_AN, "tasks")
MAU_TASK = os.path.join(THU_MUC_TASK, "MAU_TASK.md")

TEP_TASK = re.compile(r"^TASK-(\d{3})-.*\.md$")   # tên tệp task trên đĩa / trên cây git
TRANG_THAI = re.compile(r"^\s*-?\s*\*\*Trạng thái\*\*:\s*(.+)$", re.M)
TIEU_DE = re.compile(r"^#\s+(.+)$", re.M)

# Chỗ trống trong tasks/MAU_TASK.md, được thay khi sinh tệp task
MA_TAM = "TASK-NNN"
TEN_TAM = "<Tên việc>"
NGAY_TAM = "<YYYY-MM-DD>"

SO_TOI_DA = 999
TEN_TEP_TOI_DA = 60


# ------------------------------------------------------------------ đọc / ghi
def _doc(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")


def _ghi(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _slug(ten):
    """``"Hiển dần kết quả lọc nữ"`` -> ``"hien-dan-ket-qua-loc-nu"`` (tên tệp không dấu)."""
    sach = unicodedata.normalize("NFD", ten.strip().lower()).replace("đ", "d")
    sach = "".join(c for c in sach if not unicodedata.combining(c))
    sach = re.sub(r"[^a-z0-9]+", "-", sach).strip("-")
    return sach[:TEN_TEP_TOI_DA].strip("-")


# ------------------------------------------------------------- số đang dùng
def so_tren_dia(thu_muc=None):
    """Các số ``TASK-NNN`` có tệp trên đĩa (kể cả tệp chưa commit)."""
    thu_muc = THU_MUC_TASK if thu_muc is None else thu_muc
    if not os.path.isdir(thu_muc):
        return set()
    return {int(m.group(1)) for m in (TEP_TASK.match(f) for f in os.listdir(thu_muc)) if m}


def _git(dong_lenh, timeout=15):
    """Chạy một lệnh git chỉ-đọc; trả stdout, hoặc None nếu git lỗi/không có git."""
    try:
        kq = subprocess.run(["git"] + dong_lenh, cwd=GOC_DU_AN, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return kq.stdout if kq.returncode == 0 else None


def so_tren_git():
    """Các số ``TASK-NNN`` đang có trên **các nhánh local/remote** (không gọi mạng)."""
    refs = _git(["for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"])
    if not refs:
        return set()
    so = set()
    for ref in refs.split():
        cay = _git(["ls-tree", "--name-only", ref, "tasks/"])
        if not cay:
            continue
        for dong in cay.splitlines():
            m = TEP_TASK.match(os.path.basename(dong.strip()))
            if m:
                so.add(int(m.group(1)))
    return so


def so_da_dung():
    """Hợp của tệp trên đĩa và các nhánh đang mở."""
    return so_tren_dia() | so_tren_git()


def _ma_ke_tiep(da_dung=None):
    """Số nhỏ nhất còn trống (>= 1)."""
    da_dung = so_da_dung() if da_dung is None else set(da_dung)
    so = 1
    while so in da_dung and so < SO_TOI_DA:
        so += 1
    return so


# ------------------------------------------------------------------ danh sách
def danh_sach_task():
    """Danh sách task trên đĩa, sắp theo mã.

    Mỗi mục: ``{"ma", "tep", "trang_thai", "tieu_de"}`` — ``tep`` là đường dẫn
    tương đối so với gốc dự án (dùng để in).
    """
    ds = []
    if not os.path.isdir(THU_MUC_TASK):
        return ds
    for ten_tep in sorted(os.listdir(THU_MUC_TASK)):
        if not TEP_TASK.match(ten_tep):
            continue
        text = _doc(os.path.join(THU_MUC_TASK, ten_tep))
        m_tt = TRANG_THAI.search(text)
        m_td = TIEU_DE.search(text)
        ma = "TASK-" + TEP_TASK.match(ten_tep).group(1)
        tieu_de = m_td.group(1).strip() if m_td else ma
        if tieu_de.startswith(ma):        # tiêu đề đã có mã thì đừng lặp lại khi in
            tieu_de = tieu_de[len(ma):].lstrip(" —-").strip()
        ds.append({"ma": ma, "tep": "tasks/" + ten_tep,
                   "trang_thai": m_tt.group(1).strip() if m_tt else "(không rõ)",
                   "tieu_de": tieu_de})
    ds.sort(key=lambda x: x["ma"])
    return ds


# -------------------------------------------------------------------- lệnh
def _lenh_new(ten):
    slug = _slug(ten)
    if not slug:
        print("Tên '%s' không dùng được: cần ít nhất một chữ hoặc số." % ten)
        return 1
    if not os.path.exists(MAU_TASK):
        print("Thiếu mẫu %s — không tạo được tệp task."
              % os.path.relpath(MAU_TASK, GOC_DU_AN))
        return 1

    so = _ma_ke_tiep()
    ma = "TASK-%03d" % so
    ten_tep = "%s-%s.md" % (ma, slug)
    path = os.path.join(THU_MUC_TASK, ten_tep)
    if os.path.exists(path):
        print("Đã có %s — chạy lại lệnh để lấy số khác." % ten_tep)
        return 1

    noi_dung = (_doc(MAU_TASK).replace(MA_TAM, ma)
                .replace(TEN_TAM, ten.strip())
                .replace(NGAY_TAM, datetime.date.today().isoformat()))
    _ghi(path, noi_dung)
    print("Đã tạo tasks/%s" % ten_tep)
    print("Mã task: %s" % ma)
    print("Việc tiếp theo: điền các mục <...>, rồi trình người dùng duyệt (G1).")
    return 0


def _lenh_list():
    ds = danh_sach_task()
    if not ds:
        print("Chưa có task nào trong tasks/. Tạo mới: "
              "uv run python tools\\task.py new \"<tên-ngắn>\"")
        return 0
    w_ma = max(len("MÃ"), max(len(x["ma"]) for x in ds))
    w_tt = max(len("TRẠNG THÁI"), max(len(x["trang_thai"]) for x in ds))
    print("%-*s  %-*s  %s" % (w_ma, "MÃ", w_tt, "TRẠNG THÁI", "TỆP — TIÊU ĐỀ"))
    for x in ds:
        print("%-*s  %-*s  %s — %s"
              % (w_ma, x["ma"], w_tt, x["trang_thai"], x["tep"], x["tieu_de"]))
    print("\n%d task." % len(ds))
    return 0


def main(argv=None):
    try:
        # Console Windows mặc định cp1252 -> tiếng Việt sẽ lỗi khi in
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass                              # nơi đã lo mã hoá sẵn (vd. pytest)
    p = argparse.ArgumentParser(
        prog="task.py", description="Cấp mã TASK-NNN không trùng + liệt kê task")
    sub = p.add_subparsers(dest="lenh", required=True)
    s = sub.add_parser("new", help="tạo task mới với mã nhỏ nhất còn trống")
    s.add_argument("ten", help="tên việc ngắn (tiếng Việt có dấu cũng được)")
    sub.add_parser("list", help="liệt kê task + trạng thái")
    args = p.parse_args(argv)

    if args.lenh == "new":
        return _lenh_new(args.ten)
    if args.lenh == "list":
        return _lenh_list()
    return 1


if __name__ == "__main__":
    sys.exit(main())
