"""Sinh bảng công việc ``tasks/BOARD.md`` (dùng: ``uv run python tools/board.py``).

Bảng nhóm task theo ``Trạng thái`` (vòng đời ở ``tasks/MAU_TASK.md``) và nêu việc
kế tiếp, để phiên chính nhìn thấy hàng đợi mà không phải grep. ADR-0015 mục 2.

Tệp ``tasks/BOARD.md`` **không được commit**: nó là bản sinh lại được, đã có trong
``.gitignore`` (mục "Bảng công việc" trong tài liệu quy trình 6 vai). Công cụ này
chỉ đọc/ghi tệp, không gọi mạng.
"""
import argparse
import os
import sys

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GOC_DU_AN not in sys.path:                  # để `python tools/board.py` import được
    sys.path.insert(0, GOC_DU_AN)

from tools import agents as cc                  # noqa: E402  (cần sys.path ở trên)
from tools import task as ct                    # noqa: E402

BOARD = os.path.join(GOC_DU_AN, "tasks", "BOARD.md")
NHOM_KHAC = "khác"


def nhom_theo_trang_thai(ds):
    """``[(trạng thái, [task…])]`` theo thứ tự vòng đời; trạng thái lạ gom vào "khác"."""
    nhom = {}
    for x in ds:
        trang_thai = x["trang_thai"]
        if trang_thai not in cc.TRANG_THAI_TASK:
            trang_thai = NHOM_KHAC
        nhom.setdefault(trang_thai, []).append(x)
    return [(tt, nhom[tt]) for tt in list(cc.TRANG_THAI_TASK) + [NHOM_KHAC] if tt in nhom]


def viec_ke_tiep(ds):
    """Task ``chờ làm`` nhỏ nhất (R1 làm tiếp), hoặc None."""
    for x in ds:
        if x["trang_thai"] == "chờ làm":
            return x
    return None


def sinh_board(ds=None):
    """Nội dung ``tasks/BOARD.md`` (hàm thuần, test được bằng dữ liệu giả)."""
    ds = ct.danh_sach_task() if ds is None else list(ds)
    dong = ["<!-- SINH TỰ ĐỘNG từ tools/board.py — KHÔNG commit tệp này "
            "(đã có trong .gitignore); chạy lại lệnh để cập nhật -->", "",
            "# Bảng công việc", ""]

    tiep = viec_ke_tiep(ds)
    if tiep:
        dong += ["**Việc kế tiếp**: `%s` — %s (trạng thái `%s`)."
                 % (tiep["ma"], tiep["tieu_de"], tiep["trang_thai"]), ""]
    else:
        dong += ["**Việc kế tiếp**: không có task nào ở trạng thái `chờ làm`.", ""]

    if not ds:
        dong += ["_Chưa có task nào trong `tasks/`. Tạo mới:_", "",
                 "```bat", "uv run python tools\\task.py new \"<tên-ngắn>\"", "```", ""]
        return "\n".join(dong)

    dong += ["%d task. Nhóm theo trạng thái (vòng đời: %s)."
             % (len(ds), " → ".join(cc.TRANG_THAI_TASK[:6])), ""]
    for trang_thai, nhom in nhom_theo_trang_thai(ds):
        dong += ["## %s — %d task" % (trang_thai, len(nhom)), "",
                 "| Mã | Tệp | Tiêu đề |", "|---|---|---|"]
        for x in nhom:
            dong.append("| `%s` | %s | %s |"
                        % (x["ma"], x["tep"], x["tieu_de"].replace("|", "/")))
        dong.append("")
    dong += ["Cách tạo task mới: `uv run python tools\\task.py new \"<tên-ngắn>\"` "
             "(cấp mã không trùng).", ""]
    return "\n".join(dong)


def ghi_board():
    """Sinh lại ``tasks/BOARD.md``; trả đường dẫn tương đối của tệp."""
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    with open(BOARD, "w", encoding="utf-8", newline="\n") as f:
        f.write(sinh_board())
    return os.path.relpath(BOARD, GOC_DU_AN)


def main(argv=None):
    try:
        # Console Windows mặc định cp1252 -> tiếng Việt sẽ lỗi khi in
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass                              # nơi đã lo mã hoá sẵn (vd. pytest)
    p = argparse.ArgumentParser(
        prog="board.py", description="Sinh bảng công việc tasks/BOARD.md")
    p.parse_args(argv)

    ds = ct.danh_sach_task()
    print("Đã sinh %s (%d task)." % (ghi_board(), len(ds)))
    tiep = viec_ke_tiep(ds)
    if tiep:
        print("Việc kế tiếp: %s — %s" % (tiep["ma"], tiep["tieu_de"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
