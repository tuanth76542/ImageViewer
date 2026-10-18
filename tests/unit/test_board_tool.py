"""Test cho công cụ sinh bảng công việc (``tools/board.py``).

Bảng `tasks/BOARD.md` nhóm task theo `Trạng thái` để phiên chính thấy hàng đợi mà
không phải grep; tệp này **không commit** (`.gitignore`). Test chạy trên thư mục tạm.
"""
import pytest

from tools import board as bd
from tools import task as ct

pytestmark = pytest.mark.unit

DS = [
    {"ma": "TASK-001", "tep": "tasks/TASK-001-a.md", "trang_thai": "xong",
     "tieu_de": "Việc A"},
    {"ma": "TASK-002", "tep": "tasks/TASK-002-b.md", "trang_thai": "chờ làm",
     "tieu_de": "Việc B"},
    {"ma": "TASK-003", "tep": "tasks/TASK-003-c.md", "trang_thai": "lạ hoắc",
     "tieu_de": "Việc C"},
]


def test_nhom_theo_trang_thai_theo_thu_tu_vong_doi():
    nhom = bd.nhom_theo_trang_thai(DS)
    assert [tt for tt, _ in nhom] == ["chờ làm", "xong", bd.NHOM_KHAC]
    assert nhom[0][1][0]["ma"] == "TASK-002"
    assert nhom[-1][1][0]["ma"] == "TASK-003"


def test_viec_ke_tiep_lay_task_cho_lam():
    assert bd.viec_ke_tiep(DS)["ma"] == "TASK-002"
    assert bd.viec_ke_tiep([DS[0]]) is None


def test_sinh_board_khong_co_task():
    board = bd.sinh_board([])
    assert "không có task nào ở trạng thái `chờ làm`" in board
    assert "Chưa có task nào" in board
    assert "KHÔNG commit" in board


def test_sinh_board_co_du_nhom_va_viec_ke_tiep():
    board = bd.sinh_board(DS)
    assert "**Việc kế tiếp**: `TASK-002`" in board
    assert "## chờ làm — 1 task" in board
    assert "## xong — 1 task" in board
    assert "## %s — 1 task" % bd.NHOM_KHAC in board
    assert "| `TASK-001` | tasks/TASK-001-a.md | Việc A |" in board
    assert "3 task." in board
    assert "tools\\task.py new" in board


def test_sinh_board_thay_o_bang_bang_dau_gach(tmp_path):
    ds = [dict(DS[0], tieu_de="Việc | có gạch")]
    assert "Việc / có gạch" in bd.sinh_board(ds)


def test_ghi_board_tao_tep_va_main_tra_0(tmp_path, monkeypatch, capsys):
    thu_muc = tmp_path / "tasks"
    thu_muc.mkdir()
    (thu_muc / "MAU_TASK.md").write_text("mẫu\n", encoding="utf-8")
    (thu_muc / "TASK-001-viec-a.md").write_text(
        "# TASK-001 — Việc A\n\n- **Trạng thái**: chờ làm\n", encoding="utf-8")
    monkeypatch.setattr(ct, "THU_MUC_TASK", str(thu_muc))
    monkeypatch.setattr(bd, "BOARD", str(thu_muc / "BOARD.md"))

    assert bd.main([]) == 0
    noi_dung = (thu_muc / "BOARD.md").read_text(encoding="utf-8")
    assert "| `TASK-001` | tasks/TASK-001-viec-a.md | Việc A |" in noi_dung
    assert "Đã sinh" in capsys.readouterr().out
