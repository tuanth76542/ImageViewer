"""Test cho công cụ chạy cổng chất lượng local (``tools/gate.py``).

Cổng gồm: `pytest` → `pyflakes` (tệp .py đã sửa/thêm) → `compileall`; cờ `--exe`
thêm build `.exe` + `tools\\check_exe.py` (mặc định tắt cho nhanh — NF-P5). Test
dùng **runner giả** nên không thật sự chạy pytest/build.
"""
from types import SimpleNamespace

import pytest

from tools import gate as gt

pytestmark = pytest.mark.unit


def _runner(ma=0, da_chay=None):
    def _chay(lenh):
        if da_chay is not None:
            da_chay.append(lenh)
        return ma
    return _chay


def _runner_theo_buoc(mas):
    """Runner trả mã thoát lần lượt theo `mas` và ghi lại lệnh đã chạy."""
    da_chay = []

    def _chay(lenh):
        da_chay.append(lenh)
        return mas[len(da_chay) - 1]

    return _chay, da_chay


# --------------------------------------------------------------- chạy cổng
def test_chay_xanh_tra_0():
    da_chay = []
    assert gt.chay([("a", ["x"]), ("b", ["y"])], runner=_runner(0, da_chay)) == 0
    assert da_chay == [["x"], ["y"]]


def test_chay_do_thi_dung_lai_va_tra_ma_khac_0(capsys):
    runner, da_chay = _runner_theo_buoc([0, 3, 0])

    assert gt.chay([("a", ["x"]), ("b", ["y"]), ("c", ["z"])], runner=runner) == 3
    assert da_chay == [["x"], ["y"]]              # bước "c" không chạy
    assert "ĐỎ" in capsys.readouterr().out


def test_chay_ma_am_quy_ve_1():
    assert gt.chay([("a", ["x"])], runner=_runner(-1)) == 1
    assert gt.chay([("a", ["x"])], runner=_runner(None)) == 1


# ------------------------------------------------------------ bộ bước
def test_cac_buoc_mac_dinh_khong_them_buoc_nang():
    ten = [t for t, _ in gt.cac_buoc(tep=["tools/task.py"])]
    assert ten == ["pytest", "pyflakes", "compileall"]


def test_cac_buoc_bo_qua_pyflakes_khi_khong_co_tep_doi():
    assert [t for t, _ in gt.cac_buoc(tep=[])] == ["pytest"]


def test_cac_buoc_co_exe_them_build_va_check():
    buoc = dict(gt.cac_buoc(tep=[], exe=True))
    assert "build .exe" in buoc and "check .exe" in buoc
    assert "build_exe.bat" in buoc["build .exe"]
    assert buoc["check .exe"][-1].endswith("check_exe.py")


def test_lenh_pyflakes_va_compileall_dung_danh_sach_tep():
    assert gt._pyflakes(["a.py", "b.py"])[-2:] == ["a.py", "b.py"]
    assert gt._pyflakes(["a.py"])[:5] == ["uv", "run", "--with", "pyflakes", "python"]
    assert gt._compileall(["a.py"])[-1] == "a.py"


# -------------------------------------------------- tìm tệp .py đã sửa/thêm
def test_tep_py_da_doi_loc_duoi_py(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("không phải python\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("y = 2\n", encoding="utf-8")
    monkeypatch.setattr(gt, "GOC_DU_AN", str(tmp_path))

    def gia(lenh, **k):
        if lenh[0] == "rev-parse":
            return "abc\n"
        if lenh[0] == "diff":
            return "a.py\nb.txt\nda-mat.py\n"
        return "c.py\n"

    monkeypatch.setattr(gt, "_git", gia)
    assert gt.tep_py_da_doi() == ["a.py", "c.py"]     # b.txt lạc, da-mat.py đã xoá


def test_tep_py_da_doi_dung_head_khi_khong_co_main(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(gt, "GOC_DU_AN", str(tmp_path))
    da_hoi = []

    def gia(lenh, **k):
        da_hoi.append(lenh)
        return None if lenh[0] == "rev-parse" else "a.py\n"

    monkeypatch.setattr(gt, "_git", gia)
    assert gt.tep_py_da_doi() == ["a.py"]
    assert "HEAD" in da_hoi[1]


def test_git_doc_stdout_va_bao_loi(monkeypatch):
    monkeypatch.setattr(gt.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(returncode=0, stdout="abc\n"))
    assert gt._git(["status"]) == "abc\n"

    monkeypatch.setattr(gt.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(returncode=1, stdout="abc\n"))
    assert gt._git(["status"]) is None

    def gia(*a, **k):
        raise OSError("không có git")

    monkeypatch.setattr(gt.subprocess, "run", gia)
    assert gt._git(["status"]) is None
    assert gt.tep_py_da_doi() == []


# ------------------------------------------------------------------- main
def test_main_voi_runner_gia(monkeypatch, capsys):
    monkeypatch.setattr(gt, "tep_py_da_doi", lambda: ["tools/task.py"])
    runner, da_chay = _runner_theo_buoc([0, 0, 0])

    assert gt.main([], runner=runner) == 0
    assert len(da_chay) == 3
    assert "Tệp .py đã sửa/thêm (1)" in capsys.readouterr().out


def test_main_exe_them_hai_buoc(monkeypatch):
    monkeypatch.setattr(gt, "tep_py_da_doi", lambda: [])
    runner, da_chay = _runner_theo_buoc([0, 0, 0])

    assert gt.main(["--exe"], runner=runner) == 0
    assert len(da_chay) == 3                       # pytest + build + check
    assert any("build_exe.bat" in lenh for lenh in da_chay)


def test_main_bao_khi_khong_co_tep_py(monkeypatch, capsys):
    monkeypatch.setattr(gt, "tep_py_da_doi", lambda: [])
    assert gt.main([], runner=_runner(0)) == 0
    assert "bỏ qua pyflakes/compileall" in capsys.readouterr().out


def test_main_dung_o_buoc_do(monkeypatch):
    monkeypatch.setattr(gt, "tep_py_da_doi", lambda: ["tools/task.py"])
    runner, da_chay = _runner_theo_buoc([1, 0, 0])

    assert gt.main([], runner=runner) == 1
    assert len(da_chay) == 1                       # pytest đỏ -> dừng ngay
