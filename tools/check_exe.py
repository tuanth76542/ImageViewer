"""Kiểm tra nhanh file .exe sau khi build (dùng: uv run python tools/check_exe.py).

Việc kiểm tra được sinh ra từ một lỗi thật: .exe crash 0xC0000005 trong
MSVCP140.dll ngay khi mở, vì PyInstaller gom runtime C++ cu cua JRE (Adoptium)
theo PATH vao bundle. Cong cu nay chay that file .exe va kiem tra:

1. app mo duoc, cua so hien ra, khong crash (RAM, so thread);
2. trong thu muc giai nen khong co DLL cua Windows / runtime C++ cu
   (ucrtbase.dll, api-ms-win-*, msvcp140 14.2x cua JRE);
3. bao loi va tra ma thoat 1 neu co van de (dung duoc trong CI).

Chay nhanh: nó tự tạo vài ảnh mẫu nếu không truyền thư mục ảnh.
"""
import ctypes
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

import psutil
from PIL import Image

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(GOC_DU_AN, "dist", "PhanMemXemAnh.exe")

# Bản runtime C++ cũ (của JRE 19) đã từng làm app crash
BAN_CU = ("14.27", "14.28", "14.29")

user32 = ctypes.windll.user32


def _tieu_de_cua_so():
    """Tiêu đề cửa sổ đang hiện của app (None nếu chưa có)."""
    ket_qua = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _duyet(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value.endswith("Phần Mềm Xem Ảnh") or "Xem Ảnh" in buf.value:
                ket_qua.append(buf.value)
        return True

    user32.EnumWindows(_duyet, None)
    return ket_qua[0] if ket_qua else None


def _phien_ban(path):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Item -LiteralPath '%s').VersionInfo.FileVersion" % path],
        capture_output=True, text=True).stdout.strip()
    return out


def _thu_muc_giai_nen():
    return sorted(glob.glob(os.path.join(tempfile.gettempdir(), "_MEI*")),
                  key=os.path.getmtime)[-1:]


def _tao_anh_mau(thu_muc, so_anh=3):
    os.makedirs(thu_muc, exist_ok=True)
    for i in range(so_anh):
        Image.new("RGB", (640, 480), (40 + i * 60, 90, 160)).save(
            os.path.join(thu_muc, "anh_%02d.png" % (i + 1)))
    return thu_muc


def kiem_tra(thu_muc_anh=None, giay=20, giu_anh=False):
    """Chạy thử .exe; trả về (ok, danh sách lỗi)."""
    loi = []
    if not os.path.exists(EXE):
        return False, ["chưa có %s — chạy build_exe.bat trước" % EXE]

    tam = None
    if not thu_muc_anh:
        tam = tempfile.mkdtemp(prefix="xemanh_check_")
        thu_muc_anh = _tao_anh_mau(tam)

    print("chạy thử:", EXE)
    print("thư mục ảnh:", thu_muc_anh)
    truoc = set(_thu_muc_giai_nen())
    p = subprocess.Popen([EXE, thu_muc_anh], cwd=GOC_DU_AN)
    try:
        tieu_de, rss_cuoi, n_thread = None, 0.0, 0
        het = time.time() + giay
        while time.time() < het:
            time.sleep(1.0)
            if p.poll() is not None:
                ma = p.returncode & 0xFFFFFFFF
                loi.append("app thoát sớm, mã 0x%08X%s" % (
                    ma, " (access violation)" if ma == 0xC0000005 else ""))
                break
            try:
                pr = psutil.Process(p.pid)
                con = [c for c in pr.children(recursive=True) if c.is_running()]
                rss_cuoi = (pr.memory_info().rss
                            + sum(c.memory_info().rss for c in con)) / 1048576
                n_thread = pr.num_threads()
            except psutil.Error:
                pass
            tieu_de = tieu_de or _tieu_de_cua_so()
            if tieu_de:
                break

        if p.poll() is None:
            if not tieu_de:
                loi.append("không thấy cửa sổ app hiện ra sau %ds" % giay)
            else:
                print("cửa sổ:", tieu_de)
                print("RAM: %.1f MB · thread: %d" % (rss_cuoi, n_thread))
                if rss_cuoi > 400:
                    loi.append("RAM %.0f MB — cao bất thường" % rss_cuoi)

        # soi thư mục giải nén của onefile
        moi = [d for d in _thu_muc_giai_nen() if d not in truoc]
        if not moi:
            print("chú ý: không tìm thấy thư mục giải nén _MEI* (app đã tắt?)")
        for d in moi:
            ten = {os.path.basename(x).lower()
                   for x in glob.glob(os.path.join(d, "*.dll"))}
            print("thư mục giải nén:", d, "-", len(ten), "DLL")
            if "ucrtbase.dll" in ten:
                loi.append("có ucrtbase.dll trong bundle (phải dùng bản của Windows)")
            api_set = sorted(n for n in ten if n.startswith("api-ms-win-"))
            if api_set:
                loi.append("có %d DLL api-ms-win-* trong bundle: %s"
                           % (len(api_set), ", ".join(api_set[:3])))
            for ten_dll in ("msvcp140.dll", "vcruntime140.dll"):
                if ten_dll not in ten:
                    continue
                ver = _phien_ban(os.path.join(d, ten_dll))
                print("  %-16s %s" % (ten_dll, ver))
                if ver.startswith(BAN_CU):
                    loi.append("%s bản cũ %s (lấy nhầm từ PATH của phần mềm khác)"
                               % (ten_dll, ver))
            if "msvcp140.dll" not in ten and "vcruntime140.dll" not in ten:
                loi.append("thiếu runtime C++ trong bundle — máy đích phải tự có")
    finally:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=6)
            except subprocess.TimeoutExpired:
                p.kill()
        if tam and not giu_anh:
            shutil.rmtree(tam, ignore_errors=True)
    return (not loi), loi


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    import argparse
    ap = argparse.ArgumentParser(description="Chạy thử file .exe đã đóng gói")
    ap.add_argument("thu_muc_anh", nargs="?", default=None,
                    help="thư mục ảnh để mở (mặc định: tự tạo ảnh mẫu)")
    ap.add_argument("-g", "--giay", type=int, default=20,
                    help="số giây tối đa để chờ cửa sổ hiện ra")
    a = ap.parse_args()

    ok, loi = kiem_tra(a.thu_muc_anh, a.giay)
    print()
    if ok:
        print("KẾT QUẢ: .exe chạy tốt, bundle sạch.")
        return 0
    print("KẾT QUẢ: có vấn đề:")
    for l in loi:
        print("  -", l)
    return 1


if __name__ == "__main__":
    sys.exit(main())
