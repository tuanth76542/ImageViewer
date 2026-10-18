"""Test cho công cụ quản lý agent (tools/agents.py).

Công cụ này là "cơ chế quản lý" nhiều agent: bản gốc ở ``agents/agent-<tên>.md``,
bản OpenCode quét ở ``.opencode/agents/<tên>.md`` do lệnh ``sync`` sinh ra. Test
chạy trên thư mục tạm nên không đụng vào agent thật của dự án.
"""
import os

import pytest

from tools import agents as cc

pytestmark = pytest.mark.unit

MO_TA = "Agent thử nghiệm để kiểm tra công cụ quản lý agent"
THAN = "# Vai trò\n\nNội dung prompt đủ dài để không bị coi là quá ngắn. " * 2


@pytest.fixture
def thu_muc(tmp_path, monkeypatch):
    """Trỏ bản gốc và bản sinh vào thư mục tạm."""
    ng = tmp_path / "agents"
    dich = tmp_path / ".opencode" / "agents"
    ng.mkdir()
    monkeypatch.setattr(cc, "NGUON", str(ng))
    monkeypatch.setattr(cc, "DICH", str(dich))
    return ng, dich


def _viet_agent(ng, ten, mo_ta=MO_TA, mode="subagent", them=""):
    (ng / ("agent-%s.md" % ten)).write_text(
        "---\ndescription: %s\nmode: %s\n%s---\n\n%s\n" % (mo_ta, mode, them, THAN),
        encoding="utf-8")


# --------------------------------------------------------- đọc frontmatter
def test_giai_frontmatter_doc_dung_du_lieu():
    du_lieu, quy_tac, than = cc._giai_frontmatter(
        '---\ndescription: "Mô tả"\nmode: all\npermissions:\n'
        '  - action: read\n    resource: "*"\n    effect: allow\n'
        '  - action: shell\n    resource: "*"\n    effect: deny\n---\n\nThân.\n')

    assert du_lieu == {"description": "Mô tả", "mode": "all"}
    assert quy_tac == [{"action": "read", "resource": "*", "effect": "allow"},
                       {"action": "shell", "resource": "*", "effect": "deny"}]
    assert than.strip() == "Thân."


def test_giai_frontmatter_bo_qua_dong_chu_thich():
    du_lieu, _, _ = cc._giai_frontmatter(
        "---\n# chú thích\nmode: subagent\n---\n\nThân.\n")
    assert du_lieu == {"mode": "subagent"}


def test_giai_frontmatter_thieu_dong_dong_thi_bao_loi():
    with pytest.raises(ValueError):
        cc._giai_frontmatter("---\nmode: all\n\nThân.\n")


# ------------------------------------------------------------ kiểm tra
def test_kiem_tra_agent_hop_le(tmp_path, thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem")
    assert cc._kiem_tra_agent("thu-nghiem", str(ng / "agent-thu-nghiem.md")) == []


def test_kiem_tra_bat_loi_thieu_mo_ta_va_sai_mode(tmp_path, thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem", mo_ta="", mode="nhanh")
    loi = cc._kiem_tra_agent("thu-nghiem", str(ng / "agent-thu-nghiem.md"))
    assert any("description" in x for x in loi)
    assert any("mode" in x for x in loi)


def test_kiem_tra_bat_mo_ta_con_la_cho_trong(tmp_path, thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem", mo_ta="<mô tả việc agent làm>")
    loi = cc._kiem_tra_agent("thu-nghiem", str(ng / "agent-thu-nghiem.md"))
    assert any("chỗ trống" in x for x in loi)


def test_kiem_tra_bat_truong_v1(tmp_path, thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem", them="temperature: 0.2\n")
    loi = cc._kiem_tra_agent("thu-nghiem", str(ng / "agent-thu-nghiem.md"))
    assert any("V1" in x for x in loi)


def test_kiem_tra_bat_ten_va_than_qua_ngan(tmp_path, thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem", mo_ta=MO_TA)
    (ng / "agent-thu-nghiem.md").write_text(
        "---\ndescription: %s\nmode: all\n---\n\nngắn\n" % MO_TA, encoding="utf-8")

    loi = cc._kiem_tra_agent("Ten_Sai", str(ng / "agent-thu-nghiem.md"))
    assert any("không hợp lệ" in x for x in loi)
    assert any("quá ngắn" in x for x in loi)


# --------------------------------------------------------------- lệnh
def test_list_bao_chua_co_agent(thu_muc, capsys):
    assert cc.main(["list"]) == 0
    assert "Chưa có agent nào" in capsys.readouterr().out


def test_new_sinh_ban_va_bat_loi_cho_trong(thu_muc, capsys):
    ng, dich = thu_muc

    assert cc.main(["new", "thu-nghiem"]) == 0
    assert (ng / "agent-thu-nghiem.md").exists()
    assert (dich / "thu-nghiem.md").exists()          # đã sinh ngay
    assert (ng / "README.md").exists()                # bảng được sinh lại
    assert "chỗ <...>" in capsys.readouterr().out     # nói rõ phải điền gì

    # mẫu còn <...> nên check phải báo lỗi
    assert cc.main(["check"]) == 1

    # điền mô tả + thân rồi sync + check mới xanh
    _viet_agent(ng, "thu-nghiem")
    assert cc.main(["sync"]) == 0
    assert cc.main(["check"]) == 0


def test_new_tu_choi_ten_sai_va_ten_da_co(thu_muc):
    assert cc.main(["new", "Tên Có Dấu"]) == 1
    assert cc.main(["new", "thu-nghiem"]) == 0
    assert cc.main(["new", "thu-nghiem"]) == 1


def test_check_phat_hien_ban_sinh_bi_sua_tay(thu_muc, capsys):
    ng, dich = thu_muc
    cc.main(["new", "thu-nghiem"])
    _viet_agent(ng, "thu-nghiem")
    cc.main(["sync"])
    assert cc.main(["check"]) == 0

    with open(dich / "thu-nghiem.md", "a", encoding="utf-8") as f:
        f.write("sửa tay\n")

    assert cc.main(["check"]) == 1
    assert "sửa tay" in capsys.readouterr().out
    assert cc.main(["sync"]) == 0
    assert cc.main(["check"]) == 0


def test_check_phat_hien_ban_sinh_thua_va_readme_cu(thu_muc, capsys):
    ng, dich = thu_muc
    os.makedirs(dich, exist_ok=True)
    (dich / "khong-con-goc.md").write_text("---\nmode: all\n---\n", encoding="utf-8")

    assert cc.main(["check"]) == 1
    out = capsys.readouterr().out
    assert "thừa" in out


def test_sync_don_ban_sinh_thua(thu_muc):
    ng, dich = thu_muc
    cc.main(["new", "thu-nghiem"])
    assert (dich / "thu-nghiem.md").exists()

    os.remove(ng / "agent-thu-nghiem.md")
    assert cc.main(["sync"]) == 0
    assert not (dich / "thu-nghiem.md").exists()


def test_rename_doi_ten_ca_hai_ban(thu_muc):
    ng, dich = thu_muc
    cc.main(["new", "thu-nghiem"])
    _viet_agent(ng, "thu-nghiem")

    assert cc.main(["rename", "thu-nghiem", "doi-ten"]) == 0
    assert not (ng / "agent-thu-nghiem.md").exists()
    assert (ng / "agent-doi-ten.md").exists()
    assert not (dich / "thu-nghiem.md").exists()
    assert (dich / "doi-ten.md").exists()
    assert cc.main(["rename", "khong-co", "gi"]) == 1


def test_rm_xoa_ca_ban_sinh(thu_muc):
    ng, dich = thu_muc
    cc.main(["new", "thu-nghiem"])

    assert cc.main(["rm", "thu-nghiem"]) == 0
    assert not (ng / "agent-thu-nghiem.md").exists()
    assert not (dich / "thu-nghiem.md").exists()
    assert cc.main(["rm", "thu-nghiem"]) == 1          # xoá lần hai -> không có


def test_doc_sinh_bang_co_ten_agent(thu_muc):
    ng, _ = thu_muc
    _viet_agent(ng, "thu-nghiem")
    assert cc.main(["doc"]) == 0
    bang = (ng / "README.md").read_text(encoding="utf-8")
    assert "| `thu-nghiem` | subagent |" in bang
    assert "không chặn gì" in bang


def test_tom_tat_quyen_gon_dang_doc_duoc():
    quy_tac = [{"action": "edit", "resource": "*", "effect": "deny"},
               {"action": "edit", "resource": "tasks/*", "effect": "allow"},
               {"action": "shell", "resource": "*", "effect": "deny"},
               {"action": "read", "resource": "*", "effect": "allow"}]
    assert cc._tom_tat_quyen(quy_tac) == "edit (trừ tasks/*), shell"
    assert cc._tom_tat_quyen([]) == "không chặn gì"


def test_tom_tat_quyen_dem_lenh_cu_the():
    quy_tac = [{"action": "shell", "resource": "git push *--force*", "effect": "deny"},
               {"action": "shell", "resource": "git reset --hard*", "effect": "deny"},
               {"action": "shell", "resource": "git push * main*", "effect": "ask"},
               {"action": "subagent", "resource": "*", "effect": "deny"}]
    assert cc._tom_tat_quyen(quy_tac) == \
        "shell (2 lệnh chặn) +1 lệnh hỏi, subagent"
