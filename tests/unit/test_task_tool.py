"""Test cho công cụ cấp mã task (``tools/task.py``).

Công cụ này chống **trùng mã** `TASK-NNN` giữa các phiên (ADR-0015): quét tệp trên
đĩa và trên các nhánh local/remote rồi cấp số nhỏ nhất còn trống, tệp sinh ra lấy
từ mẫu ``tasks/MAU_TASK.md``. Test chạy trên thư mục tạm nên không đụng task thật.
"""
import datetime
import os
from types import SimpleNamespace

import pytest

from tools import task as ct

pytestmark = pytest.mark.unit

MAU_THU = """<!-- mẫu thử -->
# TASK-NNN — <Tên việc>

- **Ngày tạo**: <YYYY-MM-DD>
- **Trạng thái**: chờ làm

## 1. Yêu cầu gốc

> <chép nguyên văn>

## 9. Việc cần làm

- [ ] <bước 1>

## Kết quả thực hiện (R2)

## Kết quả V&V (R3)

## Cổng phát hành (R4)
"""


def _ket(stdout="", returncode=0):
    return SimpleNamespace(returncode=returncode, stdout=stdout)


def _ghi_task(thu_muc, so, trang_thai="chờ làm", tieu_de="Việc thử"):
    ten = "TASK-%03d-viec-thu.md" % so
    (thu_muc / ten).write_text(
        "# TASK-%03d — %s\n\n- **Trạng thái**: %s\n" % (so, tieu_de, trang_thai),
        encoding="utf-8")
    return thu_muc / ten


@pytest.fixture
def thu_muc_task(tmp_path, monkeypatch):
    """Trỏ thư mục `tasks/` + mẫu vào thư mục tạm và bỏ qua quét nhánh git thật."""
    thu_muc = tmp_path / "tasks"
    thu_muc.mkdir()
    mau = thu_muc / "MAU_TASK.md"
    mau.write_text(MAU_THU, encoding="utf-8")
    monkeypatch.setattr(ct, "THU_MUC_TASK", str(thu_muc))
    monkeypatch.setattr(ct, "MAU_TASK", str(mau))
    monkeypatch.setattr(ct, "so_tren_git", lambda: set())
    return thu_muc, mau


# ------------------------------------------------------------------- tên tệp
def test_slug_bo_dau_va_ky_tu_la():
    assert ct._slug("Hiển dần kết quả lọc nữ") == "hien-dan-ket-qua-loc-nu"
    assert ct._slug("Sửa xoay ảnh bị lệch") == "sua-xoay-anh-bi-lech"
    assert ct._slug("A/B__c  d") == "a-b-c-d"
    assert ct._slug("   ") == ""


def test_slug_cat_bot_ten_qua_dai():
    assert len(ct._slug("x" * 200)) == ct.TEN_TEP_TOI_DA


# ------------------------------------------------------------------ cấp mã
def test_new_cap_so_nho_nhat_con_trong(thu_muc_task, capsys):
    thu_muc, _ = thu_muc_task
    for so in (1, 2, 3):
        _ghi_task(thu_muc, so)

    assert ct.main(["new", "thu nghiem"]) == 0
    assert (thu_muc / "TASK-004-thu-nghiem.md").exists()
    assert "TASK-004" in capsys.readouterr().out

    assert ct.main(["new", "thu nghiem lan hai"]) == 0
    assert (thu_muc / "TASK-005-thu-nghiem-lan-hai.md").exists()


def test_new_quet_ca_so_tren_nhanh_mo(thu_muc_task, monkeypatch):
    """Số đã dùng ở nhánh khác cũng phải bị coi là đã dùng."""
    thu_muc, _ = thu_muc_task
    for so in (1, 2, 3):
        _ghi_task(thu_muc, so)
    monkeypatch.setattr(ct, "so_tren_git", lambda: {4})

    assert ct.main(["new", "thu nghiem"]) == 0
    assert (thu_muc / "TASK-005-thu-nghiem.md").exists()


def test_new_dien_ma_ngay_va_trang_thai_cho_lam(thu_muc_task):
    thu_muc, _ = thu_muc_task
    assert ct.main(["new", "Việc thử"]) == 0

    noi_dung = (thu_muc / "TASK-001-viec-thu.md").read_text(encoding="utf-8")
    assert datetime.date.today().isoformat() in noi_dung
    assert "TASK-NNN" not in noi_dung
    assert "<Tên việc>" not in noi_dung
    assert "# TASK-001 — Việc thử" in noi_dung
    assert "**Trạng thái**: chờ làm" in noi_dung


def test_new_sinh_du_muc_cua_mau_that(thu_muc_task):
    """Tệp sinh ra phải có đủ mọi mục của mẫu thật đang dùng trong dự án."""
    thu_muc, mau = thu_muc_task
    mau_that = os.path.join(ct.GOC_DU_AN, "tasks", "MAU_TASK.md")
    mau_noi_dung = ct._doc(mau_that)
    mau.write_text(mau_noi_dung, encoding="utf-8")

    assert ct.main(["new", "thu nghiem"]) == 0
    sinh = (thu_muc / "TASK-001-thu-nghiem.md").read_text(encoding="utf-8")

    def muc(text):
        return [d for d in text.splitlines() if d.startswith("## ")]

    assert muc(sinh) == muc(mau_noi_dung)
    assert "## Kết quả V&V (R3)" in muc(sinh)


def test_new_tu_choi_khi_thieu_mau(thu_muc_task, capsys):
    _, mau = thu_muc_task
    os.remove(mau)

    assert ct.main(["new", "thu nghiem"]) == 1
    assert "Thiếu mẫu" in capsys.readouterr().out


def test_new_tu_choi_ten_rong(thu_muc_task, capsys):
    assert ct.main(["new", "#$%"]) == 1
    assert "không dùng được" in capsys.readouterr().out


def test_new_tu_choi_khi_tep_da_ton_tai(thu_muc_task, monkeypatch, capsys):
    thu_muc, _ = thu_muc_task
    _ghi_task(thu_muc, 1)
    monkeypatch.setattr(ct, "_ma_ke_tiep", lambda da_dung=None: 1)

    assert ct.main(["new", "việc thử"]) == 1
    assert "Đã có" in capsys.readouterr().out


# ------------------------------------------------------------- đọc danh sách
def test_danh_sach_task_doc_trang_thai_va_tieu_de(thu_muc_task):
    thu_muc, _ = thu_muc_task
    _ghi_task(thu_muc, 2, trang_thai="chờ V&V", tieu_de="Việc B")
    _ghi_task(thu_muc, 1, trang_thai="xong", tieu_de="Việc A")
    (thu_muc / "ghi-chu.md").write_text("không phải task\n", encoding="utf-8")

    ds = ct.danh_sach_task()
    assert [x["ma"] for x in ds] == ["TASK-001", "TASK-002"]
    assert ds[0]["trang_thai"] == "xong"
    assert ds[1]["trang_thai"] == "chờ V&V"
    assert ds[1]["tieu_de"] == "Việc B"            # đã bỏ tiền tố mã
    assert ds[0]["tep"] == "tasks/TASK-001-viec-thu.md"


def test_danh_sach_task_thieu_dong_trang_thai(thu_muc_task):
    thu_muc, _ = thu_muc_task
    (thu_muc / "TASK-007-khong-ro.md").write_text("# TASK-007 — Lạ\n",
                                                  encoding="utf-8")
    ds = ct.danh_sach_task()
    assert ds[0]["trang_thai"] == "(không rõ)"
    assert ds[0]["tieu_de"] == "Lạ"


def test_list_in_ma_va_trang_thai(thu_muc_task, capsys):
    thu_muc, _ = thu_muc_task
    _ghi_task(thu_muc, 1, trang_thai="xong")

    assert ct.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "TASK-001" in out and "xong" in out and "1 task." in out


def test_list_khi_chua_co_task(thu_muc_task, capsys):
    assert ct.main(["list"]) == 0
    assert "Chưa có task nào" in capsys.readouterr().out


# ------------------------------------------------------------------ git
def test_so_tren_dia_bo_qua_tep_khac(tmp_path):
    _ghi_task(tmp_path, 3)
    (tmp_path / "MAU_TASK.md").write_text("mẫu\n", encoding="utf-8")
    (tmp_path / "TASK-abc-x.md").write_text("lạ\n", encoding="utf-8")

    assert ct.so_tren_dia(str(tmp_path)) == {3}
    assert ct.so_tren_dia(str(tmp_path / "khong-co")) == set()


def test_ma_ke_tiep_lay_so_nho_nhat_con_trong():
    assert ct._ma_ke_tiep({1, 2, 4}) == 3
    assert ct._ma_ke_tiep(set()) == 1


def test_so_tren_git_quet_moi_nhanh(monkeypatch):
    def gia(lenh, **k):
        if "for-each-ref" in lenh:
            return _ket("main\norigin/main\nfeature/task-009-x\n")
        if "feature/task-009-x" in lenh:
            return _ket("tasks/TASK-009-x.md\ntasks/MAU_TASK.md\n")
        return _ket("tasks/TASK-001-a.md\ntasks/BOARD.md\n")

    monkeypatch.setattr(ct.subprocess, "run", gia)
    assert ct.so_tren_git() == {1, 9}


def test_so_tren_git_bo_qua_nhanh_loi(monkeypatch):
    def gia(lenh, **k):
        if "for-each-ref" in lenh:
            return _ket("main\n")
        return _ket("", returncode=128)

    monkeypatch.setattr(ct.subprocess, "run", gia)
    assert ct.so_tren_git() == set()


def test_so_tren_git_khong_co_git(monkeypatch):
    def gia(*a, **k):
        raise OSError("không có git")

    monkeypatch.setattr(ct.subprocess, "run", gia)
    assert ct._git(["status"]) is None
    assert ct.so_tren_git() == set()


def test_so_tren_git_git_loi_tra_none(monkeypatch):
    monkeypatch.setattr(ct.subprocess, "run", lambda *a, **k: _ket("", returncode=1))
    assert ct._git(["rev-parse", "x"]) is None
