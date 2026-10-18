# -*- mode: python ; coding: utf-8 -*-
"""Cấu hình đóng gói .exe bằng PyInstaller — dùng qua ``build_exe.bat``.

Vì sao cần tệp spec này thay vì gọi pyinstaller bằng dòng lệnh:

    PyInstaller tìm DLL phụ thuộc **theo biến PATH**. Trên máy có cài Java
    (Adoptium JRE), thư mục ``bin`` của JRE nằm trên PATH và chứa một bản
    runtime C++ riêng: ``msvcp140.dll`` 14.27 (cũ), ``vcruntime140.dll``,
    cả ``ucrtbase.dll`` và hàng loạt ``api-ms-win-*``. PyInstaller gom đúng
    bản cũ đó vào app, nên .exe crash ``0xC0000005`` trong ``MSVCP140.dll``
    ngay khi khởi động (lần đầu phát hiện 18/10/2026).

Spec này vì vậy:

* bỏ ``msvcp140*/vcruntime140*/concrt140*`` lấy từ ngoài dự án (PATH), rồi thêm lại
  bản mới nhất đi kèm PySide6 nếu thiếu — nhưng vẫn giữ bản runtime riêng của
  numpy (``msvcp140-<hash>.dll``) vì numpy gọi nó theo đúng tên đó;
* không bao giờ đóng gói ``ucrtbase.dll`` và ``api-ms-win-*`` — đó là thành phần
  của Windows, phải dùng bản của hệ điều hành.

Nhờ vậy .exe build ra đúng dù PATH của máy có gì.

(Ghi chú: pyflakes sẽ báo ``undefined name 'Analysis'/'PYZ'/'EXE'/'SPECPATH'`` trong
tệp này — đó là các tên do PyInstaller bơm vào lúc chạy spec, không phải lỗi.)
"""
import os

import PySide6
import shiboken6

PY_DIR = os.path.dirname(os.path.abspath(PySide6.__file__))
SHIBO_DIR = os.path.dirname(os.path.abspath(shiboken6.__file__))
# DLL nằm trong dự án/venv là của chính ta (numpy có bản runtime riêng có hash);
# DLL lấy được từ PATH mới là loại hay bị "nhiễm" từ phần mềm khác.
GOC_DU_AN = os.path.abspath(SPECPATH).lower()

# Runtime C++ chỉ lấy từ PySide6/shiboken6 (bản mới nhất có trên máy)
RUNTIME_NAMES = (
    "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
    "msvcp140_codecvt_ids.dll", "vcruntime140.dll", "vcruntime140_1.dll",
    "concrt140.dll",
)
RUNTIME_PREFIXES = ("msvcp140", "vcruntime140", "concrt140")

# Thành phần của Windows, tuyệt đối không đóng gói kèm
WIN_NAMES = ("ucrtbase.dll",)
WIN_PREFIXES = ("api-ms-win-",)


a = Analysis(
    ['viewer_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


def _nen_giu(entry):
    """Giữ DLL nếu nó không phải loại hay lấy nhầm từ PATH của phần mềm khác."""
    ten = os.path.basename(entry[0]).lower()
    if ten in WIN_NAMES or ten.startswith(WIN_PREFIXES):
        return False        # UCRT/API set: luôn phải dùng bản của Windows
    if ten.startswith(RUNTIME_PREFIXES):
        # Giữ bản trong dự án/venv (ví dụ msvcp140-<hash>.dll numpy cần đúng tên
        # đó), bỏ bản vớ được từ PATH — thường là của JRE/Java hay phần mềm khác.
        return os.path.abspath(entry[1]).lower().startswith(GOC_DU_AN)
    return True


_bo_ra = [e for e in a.binaries if not _nen_giu(e)]
a.binaries = [e for e in a.binaries if _nen_giu(e)]
print("[spec] loai bo %d DLL ngoai (UCRT/API set/runtime C++ cu):" % len(_bo_ra))
for _e in _bo_ra:
    print("    - %s   <- %s" % (_e[0], _e[1]))

_co_san = {os.path.basename(e[0]).lower() for e in a.binaries}
for _ten in RUNTIME_NAMES:
    if _ten in _co_san:
        continue
    for _thu_muc in (PY_DIR, SHIBO_DIR):
        _nguon = os.path.join(_thu_muc, _ten)
        if os.path.exists(_nguon):
            a.binaries.append((_ten, _nguon, "BINARY"))
            print("[spec] them runtime C++: %s   <- %s" % (_ten, _nguon))
            break

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PhanMemXemAnh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # không nén: Qt/onnxruntime nén bằng UPX dễ lỗi khi chạy
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/app.ico'],
)
