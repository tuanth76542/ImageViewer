"""Quản lý agent OpenCode của dự án (dùng: uv run python tools/agents.py <lệnh>).

Vì sao có 2 thư mục:

- ``agents/agent-<tên>.md``     — bản gốc, để người đọc và sửa tay (một tệp một agent);
- ``.opencode/agents/<tên>.md`` — bản OpenCode thật sự quét. Tên tệp = tên gọi
  agent, nên **thư mục này là bản sinh tự động**: đừng sửa tay, hãy sửa bản gốc
  rồi chạy ``sync`` (lệnh ``check`` sẽ phát hiện nếu hai bản bị lệch).

Lệnh:

    list                        liệt kê agent (chế độ, quyền chặn, đồng bộ?)
    new <tên>                   tạo agent mới từ mẫu rồi đồng bộ
    sync                        sinh lại .opencode/agents/ + agents/README.md
    check                       kiểm tra hợp lệ, phát hiện bản sinh bị lệch; bắt
                                thiếu/thừa vai so với 6 vai chuẩn (ADR-0017) và
                                mẫu task lệch nguồn (ADR-0015 mục 3)
    doc                         sinh lại bảng agent trong agents/README.md
    rename <tên-cũ> <tên-mới>   đổi tên agent
    rm <tên>                    xoá agent (cả bản sinh)

Tên agent: chữ thường không dấu, nối bằng gạch ngang (ví dụ ``task-planning``).
"""
import argparse
import os
import re
import sys

GOC_DU_AN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NGUON = os.path.join(GOC_DU_AN, "agents")                 # bản gốc
DICH = os.path.join(GOC_DU_AN, ".opencode", "agents")     # bản OpenCode quét
TIEN_TO = "agent-"
README = "README.md"

DANH_DAU = ("<!-- SINH TỰ ĐỘNG từ %s — đừng sửa tệp này: sửa bản gốc rồi chạy "
            "`uv run python tools/agents.py sync` -->")

TEN_HOP_LE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MODE_HOP_LE = ("primary", "subagent", "all")
HIEU_LUC_HOP_LE = ("allow", "ask", "deny")
# Các trường V1 không được dùng nữa (OpenCode V2 bỏ qua hoặc báo lỗi)
TRUONG_CU = ("temperature", "top_p", "prompt", "permission", "tools", "disable",
             "maxSteps")

# --- 6 vai chuẩn của dự án (ADR-0017) ---------------------------------------
# `check` bắt buộc thư mục agents/ của dự án có ĐÚNG bộ này: thiếu vai nào thì
# báo, và tên cũ `sw-release-qg-check` không được quay lại.
VAI_CHUAN = ("task-planning", "task-implementation", "task-vv",
             "sw-system-release", "sw-integrator", "sw-architect")
TEN_CU = "sw-release-qg-check"                 # tên R4 trước ADR-0017
VAI_R1 = "task-planning"

# --- mẫu task: một nguồn duy nhất (ADR-0015 mục 3) ---------------------------
# Mẫu nằm ở `tasks/MAU_TASK.md`; agent R1 chỉ TRỎ tới, không chép lại — hai bản
# chép tay thì sửa một bên là lệch, `check` bắt đúng lỗi đó.
MAU_TASK = os.path.join(GOC_DU_AN, "tasks", "MAU_TASK.md")
MAU_TASK_REF = "tasks/MAU_TASK.md"
MUC_MAU_TASK = ("## 1. Yêu cầu gốc", "## 2. Mục tiêu (đo được)", "## 3. Phạm vi",
                "## 4. Đã chốt với người dùng", "## 5. Còn mở",
                "## 6. Hướng làm & tệp dự kiến đụng tới",
                "## 7. Tiêu chí nghiệm thu", "## 8. Kiểm thử",
                "## 9. Việc cần làm", "## 10. Ghi chú / rủi ro")
TRANG_THAI_TASK = ("chờ làm", "đang làm", "chờ V&V", "đang V&V", "chờ release",
                   "xong", "tạm hoãn", "bỏ")
MUC_BAO_CAO_TASK = ("Kết quả thực hiện (R2)", "Kết quả V&V (R3)",
                    "Cổng phát hành (R4)")

MAU_AGENT = """---
# `description` là dòng quan trọng nhất: agent chính đọc nó để biết khi nào gọi
# agent này. Viết ngắn, nói rõ "làm gì" và "khi nào dùng".
description: <mô tả một dòng: agent làm gì và khi nào nên gọi>
# primary = chọn được làm agent chính | subagent = chỉ agent chính gọi
# all = cả hai (thường dùng `all` cho agent bạn muốn tự chọn trong danh sách)
mode: subagent
color: "#7b6cf0"
permissions:
  - action: read
    resource: "*"
    effect: allow
  - action: glob
    resource: "*"
    effect: allow
  - action: grep
    resource: "*"
    effect: allow
  - action: question
    resource: "*"
    effect: allow
  - action: shell
    resource: "*"
    effect: deny
  - action: subagent
    resource: "*"
    effect: deny
  - action: edit
    resource: "*"
    effect: deny
---

# Vai trò

<bạn là ai, làm đúng một việc gì>

# Khi nào chạy

- <tình huống nên gọi agent này>
- Bỏ qua khi: <tình huống không cần đến nó>

# Cách làm

1. <bước 1 — khảo sát gì trước>
2. <bước 2 — làm gì>
3. <bước 3 — kiểm tra lại thế nào>

# Trả lời

<trả lời ngắn gọn, tiếng Việt; nói rõ đã làm gì và còn gì chưa chắc>

# Nguyên tắc

- <điều không được làm / giới hạn, ví dụ: không sửa code sản phẩm>
"""


# ------------------------------------------------------------------ dọn chuỗi
def _chuan(text):
    """Chuẩn hoá kiểu xuống dòng để so sánh (Windows dùng CRLF)."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _doc(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return _chuan(f.read())


def _ghi(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_chuan(text))


def _bo_ngoac(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


# ------------------------------------------------------- đọc frontmatter/agent
def _khoi_frontmatter(text):
    """Trả (khối frontmatter, phần thân) — kiểm luôn hai dòng '---' bao quanh."""
    if not text.startswith("---"):
        raise ValueError("thiếu dòng '---' mở đầu frontmatter")
    ket_thuc = text.find("\n---", 3)
    if ket_thuc < 0:
        raise ValueError("thiếu dòng '---' đóng frontmatter")
    return text[3:ket_thuc], text[ket_thuc + 4:].lstrip("\n")


def _giai_khoi(khoi):
    """Trả (dữ liệu, quy tắc quyền) từ khối frontmatter.

    Chỉ hiểu đúng dạng frontmatter mà dự án dùng: các dòng ``khóa: giá trị`` và
    một danh sách ``permissions`` gồm các mục ``- action/resource/effect``. Khóa
    không có giá trị (như ``permissions:``) được bỏ qua.
    """
    du_lieu, quy_tac = {}, []
    for dong in khoi.splitlines():
        sach = dong.strip()
        if not sach or sach.startswith("#"):
            continue
        if sach.startswith("- "):                       # bắt đầu một luật quyền
            quy_tac.append({})
            _dat_khoa(quy_tac[-1], sach[2:])
        elif quy_tac and dong[:1] in (" ", "\t") and ":" in sach:
            _dat_khoa(quy_tac[-1], sach)                # resource:, effect:
        elif ":" in sach:
            khoa, gia_tri = sach.split(":", 1)
            gia_tri = _bo_ngoac(gia_tri.strip())
            if gia_tri:                                 # 'permissions:' không tính
                du_lieu[khoa.strip()] = gia_tri
    return du_lieu, quy_tac


def _giai_frontmatter(text):
    """Trả (dữ liệu, quy tắc quyền, phần thân) của một tệp agent."""
    khoi, than = _khoi_frontmatter(text)
    du_lieu, quy_tac = _giai_khoi(khoi)
    return du_lieu, quy_tac, than


def _dat_khoa(luat, sach):
    khoa, gia_tri = sach.split(":", 1)
    luat[khoa.strip()] = _bo_ngoac(gia_tri.strip())


def _danh_sach():
    """Tên các agent có bản gốc (đã sắp xếp)."""
    if not os.path.isdir(NGUON):
        return []
    ten = []
    for f in os.listdir(NGUON):
        if f.startswith(TIEN_TO) and f.endswith(".md"):
            ten.append(f[len(TIEN_TO):-3])
    return sorted(ten)


def _duong_dan_nguon(ten):
    return os.path.join(NGUON, TIEN_TO + ten + ".md")


def _duong_dan_dich(ten):
    return os.path.join(DICH, ten + ".md")


def _noi_dung_sinh(text, ten):
    """Nội dung bản sinh = bản gốc + dòng đánh dấu (để `check` phát hiện sửa tay)."""
    return (_chuan(text).rstrip("\n") + "\n\n"
            + DANH_DAU % ("agents/" + TIEN_TO + ten + ".md") + "\n")


def _tom_tat_quyen(quy_tac):
    """Tóm tắt ngắn, ví dụ: 'edit (trừ tasks/*), shell, subagent'
    hoặc 'shell (6 lệnh chặn) +3 lệnh hỏi, subagent'."""
    nhom = {}
    for luat in quy_tac:
        action = luat.get("action")
        if not action:
            continue
        muc = nhom.setdefault(action, {"deny": [], "ask": [], "allow": []})
        muc.setdefault(luat.get("effect", "allow"), []).append(
            luat.get("resource", ""))
    phan = []
    for action in sorted(nhom):
        chan = nhom[action]["deny"]
        hoi = nhom[action]["ask"]
        cho = nhom[action]["allow"]
        if not chan and not hoi:
            continue
        if "*" in chan:
            ngoai_le = [r for r in cho if r != "*"]
            mo = action + (" (trừ %s)" % ", ".join(ngoai_le) if ngoai_le else "")
            if len(chan) > 1:
                mo += " +%d lệnh chặn" % (len(chan) - 1)
        elif chan:
            mo = "%s (%d lệnh chặn)" % (action, len(chan))
        else:
            mo = action
        if hoi:
            mo += " +%d lệnh hỏi" % len(hoi)
        phan.append(mo)
    return ", ".join(phan) or "không chặn gì"


# ------------------------------------------------------------------- kiểm tra
def _kiem_tra_agent(ten, path):
    """Danh sách lỗi của một tệp agent (rỗng = hợp lệ)."""
    loi = []
    if not TEN_HOP_LE.match(ten):
        loi.append("tên '%s' không hợp lệ (chữ thường không dấu, nối bằng '-')" % ten)
    if len(ten) > 40:
        loi.append("tên quá dài (>40 ký tự)")
    try:
        text = _doc(path)
        khoi, than = _khoi_frontmatter(text)
        du_lieu, quy_tac = _giai_khoi(khoi)
    except ValueError as ex:
        return loi + [str(ex)]
    except OSError as ex:
        return loi + ["không đọc được: %s" % ex]

    mo_ta = du_lieu.get("description", "")
    if not mo_ta:
        loi.append("thiếu 'description' (agent chính cần nó để biết khi nào gọi)")
    elif "<" in mo_ta or ">" in mo_ta:
        loi.append("'description' còn là chỗ trống '<...>', chưa điền")

    mode = du_lieu.get("mode", "")
    if not mode:
        loi.append("thiếu 'mode' (primary | subagent | all)")
    elif mode not in MODE_HOP_LE:
        loi.append("'mode: %s' không hợp lệ (chỉ nhận %s)"
                   % (mode, ", ".join(MODE_HOP_LE)))

    for truong in TRUONG_CU:
        # tìm cả dạng khối (vd. 'tools:') nên soi thẳng khối frontmatter
        if re.search(r"^\s*%s\s*:" % truong, khoi, re.M):
            loi.append("'%s' là trường V1, OpenCode V2 không dùng — bỏ đi" % truong)

    for i, luat in enumerate(quy_tac, 1):
        thieu = [k for k in ("action", "resource", "effect") if not luat.get(k)]
        if thieu:
            loi.append("luật quyền %d thiếu %s" % (i, ", ".join(thieu)))
        elif luat["effect"] not in HIEU_LUC_HOP_LE:
            loi.append("luật quyền %d có effect '%s' không hợp lệ (chỉ nhận %s)"
                       % (i, luat["effect"], ", ".join(HIEU_LUC_HOP_LE)))

    if len(than.strip()) < 50:
        loi.append("phần thân (prompt) quá ngắn — cần nói rõ vai trò và cách làm")
    return loi


def _kiem_tra_tep_la():
    """Tệp trong agents/ không theo cú pháp agent-<tên>.md."""
    if not os.path.isdir(NGUON):
        return []
    return sorted(f for f in os.listdir(NGUON)
                  if f.endswith(".md") and not f.startswith(TIEN_TO)
                  and f != README)


def _doc_readme():
    return _doc(os.path.join(NGUON, README)) if os.path.exists(
        os.path.join(NGUON, README)) else None


# ------------------------------------------------- luật kiểm cấp dự án (6 vai)
def _la_du_an_that():
    """True khi đang soi chính ``agents/`` của dự án (test dùng thư mục tạm)."""
    return os.path.abspath(NGUON) == os.path.join(GOC_DU_AN, "agents")


def _kiem_tra_mau_task():
    """Lỗi của cặp `tasks/MAU_TASK.md` ↔ agent R1 (phải cùng một nguồn)."""
    if not os.path.exists(MAU_TASK):
        return ["thiếu %s — mẫu task là nguồn duy nhất cho R1 và tools/task.py"
                % MAU_TASK_REF]
    mau, loi = _doc(MAU_TASK), []
    for muc in MUC_MAU_TASK:
        if muc not in mau:
            loi.append("mẫu task thiếu mục '%s'" % muc)
    for muc in MUC_BAO_CAO_TASK:
        if muc not in mau:
            loi.append("mẫu task thiếu mục báo cáo '%s'" % muc)
    for trang_thai in TRANG_THAI_TASK:
        if "`%s`" % trang_thai not in mau:
            loi.append("mẫu task thiếu trạng thái '%s'" % trang_thai)

    path_r1 = _duong_dan_nguon(VAI_R1)
    if not os.path.exists(path_r1):
        loi.append("thiếu agent '%s' (R1) — vai duy nhất được tạo tasks/TASK-*.md"
                   % VAI_R1)
        return loi
    try:
        than_r1 = _giai_frontmatter(_doc(path_r1))[2]
    except ValueError as ex:
        return loi + ["%s: %s" % (VAI_R1, ex)]
    if MAU_TASK_REF not in than_r1:
        loi.append("agent '%s' không trỏ về mẫu dùng chung '%s' (ADR-0015 mục 3)"
                   % (VAI_R1, MAU_TASK_REF))
    if MUC_MAU_TASK[0] in than_r1:
        loi.append("agent '%s' chép lại mẫu task ('%s') — sửa mẫu ở %s rồi trỏ về, "
                   "đừng giữ hai bản (ADR-0015 mục 3)"
                   % (VAI_R1, MUC_MAU_TASK[0], MAU_TASK_REF))
    return loi


def _kiem_tra_du_an(ten_list):
    """Luật cấp dự án: đủ 6 vai (ADR-0017) + mẫu task dùng chung (ADR-0015)."""
    loi = []
    thieu = [v for v in VAI_CHUAN if v not in ten_list]
    thua = [v for v in ten_list if v not in VAI_CHUAN]
    if thieu:
        loi.append("thiếu vai chuẩn: %s (đủ 6 vai theo ADR-0017)"
                   % ", ".join(thieu))
    if thua:
        loi.append("có vai ngoài 6 vai chuẩn: %s — vai mới phải đi kèm ADR-0017"
                   % ", ".join(thua))
    if TEN_CU in ten_list:
        loi.append("tên cũ '%s' đã đổi thành 'sw-system-release' — đừng để quay lại "
                   "(ADR-0017)" % TEN_CU)
    return loi + _kiem_tra_mau_task()


# ------------------------------------------------------------------ các lệnh
def _sinh_readme():
    dong = [DANH_DAU % "tools/agents.py doc", "",
            "# agents/ — nơi chứa agent", "",
            "Mỗi agent là một tệp `agent-<tên>.md` (một tệp một agent). Tên tệp "
            "chính là tên gọi agent, nên viết chữ thường không dấu: "
            "`agent-task-planning.md` → gọi `task-planning`.", "",
            "Sửa xong thì chạy `uv run python tools/agents.py sync` để OpenCode "
            "thấy; `.opencode/agents/` là bản sinh tự động, không sửa tay.", ""]
    if not _danh_sach():
        dong += ["_Chưa có agent nào. Tạo mới:_", "",
                 "```bat", "uv run python tools/agents.py new <tên>", "```", ""]
    else:
        dong += ["| Agent | Chế độ | Quyền chặn | Mô tả |", "|---|---|---|---|"]
        for ten in _danh_sach():
            try:
                du_lieu, quy_tac, _ = _giai_frontmatter(_doc(_duong_dan_nguon(ten)))
            except (ValueError, OSError):
                dong.append("| `%s` | ? | ? | (lỗi frontmatter — chạy `check`) |" % ten)
                continue
            dong.append("| `%s` | %s | %s | %s |"
                        % (ten, du_lieu.get("mode", "?"),
                           _tom_tat_quyen(quy_tac),
                           (du_lieu.get("description", "") or "(chưa có mô tả)")
                           .replace("|", "/")))
        dong.append("")
    dong += ["## Lệnh quản lý", "",
             "```bat",
             "uv run python tools\\agents.py list            :: xem danh sách",
             "uv run python tools\\agents.py new <tên>      :: tạo agent mới từ mẫu",
             "uv run python tools\\agents.py sync           :: sinh bản cho OpenCode",
             "uv run python tools\\agents.py check          :: kiểm tra hợp lệ + lệch bản",
             "uv run python tools\\agents.py rename <cũ> <mới>",
             "uv run python tools\\agents.py rm <tên>",
             "```", ""]
    return "\n".join(dong)


def _sync(im_lang=False):
    """Sinh .opencode/agents/ từ agents/, trả (tạo, cập nhật, xoá)."""
    os.makedirs(DICH, exist_ok=True)
    ten_list = _danh_sach()
    tao, cap_nhat, xoa = [], [], []
    for ten in ten_list:
        mong_doi = _noi_dung_sinh(_doc(_duong_dan_nguon(ten)), ten)
        dich = _duong_dan_dich(ten)
        if not os.path.exists(dich):
            _ghi(dich, mong_doi)
            tao.append(ten)
        elif _doc(dich) != mong_doi:
            _ghi(dich, mong_doi)
            cap_nhat.append(ten)
    for f in sorted(os.listdir(DICH)):
        if not f.endswith(".md") or f == README:
            continue
        if f[:-3] not in ten_list:
            os.remove(os.path.join(DICH, f))
            xoa.append(f[:-3])

    _ghi(os.path.join(NGUON, README), _sinh_readme())
    if not im_lang:
        for nhan, ds in (("tạo mới", tao), ("cập nhật", cap_nhat), ("xoá", xoa)):
            if ds:
                print("  %s: %s" % (nhan, ", ".join(ds)))
        if not (tao or cap_nhat or xoa):
            print("  bản OpenCode đã khớp, không cần đổi")
        print("  đã sinh lại agents/README.md")
    return tao, cap_nhat, xoa


def _lenh_list():
    ten_list = _danh_sach()
    if not ten_list:
        print("Chưa có agent nào trong agents/. Tạo mới: "
              "uv run python tools\\agents.py new <tên>")
        return 0
    hang = []
    for ten in ten_list:
        try:
            du_lieu, quy_tac, than = _giai_frontmatter(_doc(_duong_dan_nguon(ten)))
            mode, mo_ta = du_lieu.get("mode", "?"), du_lieu.get("description", "")
            quyen = _tom_tat_quyen(quy_tac)
            so_dong = len(than.strip().splitlines())
        except (ValueError, OSError) as ex:
            mode, mo_ta, quyen, so_dong = "?", "LỖI: %s" % ex, "?", 0
        ban_sinh = os.path.join(DICH, ten + ".md")
        if not os.path.exists(ban_sinh):
            dong_bo = "thiếu"
        elif _doc(ban_sinh) != _noi_dung_sinh(_doc(_duong_dan_nguon(ten)), ten):
            dong_bo = "LỆCH"
        else:
            dong_bo = "ok"
        hang.append((ten, mode, quyen, dong_bo, str(so_dong), mo_ta))

    w_ten = max(len("AGENT"), max(len(h[0]) for h in hang))
    w_mode = max(len("CHẾ ĐỘ"), max(len(h[1]) for h in hang))
    w_quyen = min(max(len("QUYỀN CHẶN"), max(len(h[2]) for h in hang)), 42)
    w_db = max(len("BẢN OPENCODE"), max(len(h[3]) for h in hang))
    print("%-*s  %-*s  %-*s  %-*s  %5s  %s"
          % (w_ten, "AGENT", w_mode, "CHẾ ĐỘ", w_quyen, "QUYỀN CHẶN", w_db,
             "BẢN OPENCODE", "DÒNG", "MÔ TẢ"))
    for ten, mode, quyen, dong_bo, so_dong, mo_ta in hang:
        mo_ta_ngan = mo_ta if len(mo_ta) <= 58 else mo_ta[:55] + "..."
        print("%-*s  %-*s  %-*s  %-*s  %5s  %s"
              % (w_ten, ten, w_mode, mode, w_quyen, quyen[:w_quyen], w_db,
                 dong_bo, so_dong, mo_ta_ngan))
    print("\n%d agent. Bản gốc: agents/agent-<tên>.md · bản OpenCode: "
          ".opencode/agents/<tên>.md (sinh tự động)" % len(ten_list))
    return 0


def _lenh_new(ten):
    if not TEN_HOP_LE.match(ten) or len(ten) > 40:
        print("Tên '%s' không hợp lệ. Dùng chữ thường không dấu, nối bằng gạch "
              "ngang, ví dụ: test-writer" % ten)
        return 1
    path = _duong_dan_nguon(ten)
    if os.path.exists(path):
        print("Đã có agent '%s' (%s) — dùng 'rename' hoặc sửa trực tiếp." % (ten, path))
        return 1
    _ghi(path, MAU_AGENT)
    print("Đã tạo agents/%s%s.md" % (TIEN_TO, ten))
    _sync()
    print("\nViệc tiếp theo:")
    print("  1. Mở tệp, điền 'description' và phần thân (thay các chỗ <...>).")
    print("  2. Chạy: uv run python tools\\agents.py sync   (để OpenCode thấy agent)")
    print("  3. Chạy: uv run python tools\\agents.py check  (kiểm tra lại)")
    return 0


def _lenh_check():
    """Kiểm tra bản gốc + bản sinh. Không tự đồng bộ (nếu đồng bộ thì hết lệch)."""
    ten_list, loi_tat_ca = _danh_sach(), []
    for f in _kiem_tra_tep_la():
        loi_tat_ca.append(("agents/%s" % f,
                           ["không theo cú pháp '%s<tên>.md' — đổi tên hoặc chuyển "
                            "ra ngoài agents/" % TIEN_TO]))
    for ten in ten_list:
        path = _duong_dan_nguon(ten)
        loi = _kiem_tra_agent(ten, path)
        ban_sinh = _duong_dan_dich(ten)
        if not os.path.exists(ban_sinh):
            loi.append("thiếu bản sinh .opencode/agents/%s.md (chạy 'sync')" % ten)
        elif _doc(ban_sinh) != _noi_dung_sinh(_doc(path), ten):
            loi.append("bản sinh bị lệch hoặc bị sửa tay (chạy 'sync')")
        if loi:
            try:
                ten_hien_thi = os.path.relpath(path, GOC_DU_AN)
            except ValueError:
                ten_hien_thi = path  # khác ổ đĩa trên Windows: relpath không tính được
            loi_tat_ca.append((ten_hien_thi, loi))

    if os.path.isdir(DICH):
        thua = [f for f in sorted(os.listdir(DICH))
                if f.endswith(".md") and f != README and f[:-3] not in ten_list]
        if thua:
            loi_tat_ca.append((".opencode/agents/",
                               ["thừa %s — không còn bản gốc tương ứng (chạy 'sync')"
                                % ", ".join(thua)]))
    hien_tai = _doc_readme()
    if hien_tai is not None and hien_tai != _sinh_readme():
        loi_tat_ca.append(("agents/%s" % README,
                           ["bảng chưa cập nhật (chạy 'doc')"]))

    if _la_du_an_that():
        loi_du_an = _kiem_tra_du_an(ten_list)
        if loi_du_an:
            loi_tat_ca.append(("agents/ + %s" % MAU_TASK_REF, loi_du_an))

    if not loi_tat_ca:
        them = ", đủ 6 vai chuẩn (ADR-0017)" if _la_du_an_that() else ""
        print("OK: %d agent hợp lệ%s, bản OpenCode khớp bản gốc."
              % (len(ten_list), them))
        return 0
    print("PHÁT HIỆN %d chỗ có vấn đề:" % len(loi_tat_ca))
    for path, loi in loi_tat_ca:
        print("\n%s" % path)
        for item in loi:
            print("  - %s" % item)
    return 1


def _lenh_rename(cu, moi):
    if not os.path.exists(_duong_dan_nguon(cu)):
        print("Không có agent '%s'." % cu)
        return 1
    if not TEN_HOP_LE.match(moi):
        print("Tên mới '%s' không hợp lệ (chữ thường không dấu, nối bằng '-')." % moi)
        return 1
    if os.path.exists(_duong_dan_nguon(moi)):
        print("Đã có agent '%s'." % moi)
        return 1
    os.rename(_duong_dan_nguon(cu), _duong_dan_nguon(moi))
    cu_sinh = _duong_dan_dich(cu)
    if os.path.exists(cu_sinh):
        os.remove(cu_sinh)
    print("Đã đổi tên: %s -> %s" % (cu, moi))
    _sync()
    print("\nLưu ý: nhớ sửa chỗ nào đang gọi agent '%s' (AGENTS.md, README.md)." % cu)
    return 0


def _lenh_rm(ten):
    if not os.path.exists(_duong_dan_nguon(ten)):
        print("Không có agent '%s'." % ten)
        return 1
    os.remove(_duong_dan_nguon(ten))
    print("Đã xoá agents/%s%s.md" % (TIEN_TO, ten))
    _sync()
    return 0


def main(argv=None):
    try:
        # Console Windows mặc định cp1252 -> tiếng Việt sẽ lỗi khi in
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass                                  # nơi đã lo mã hoá sẵn (vd. pytest)
    p = argparse.ArgumentParser(
        prog="agents.py", description="Quản lý agent OpenCode của dự án")
    sub = p.add_subparsers(dest="lenh", required=True)
    sub.add_parser("list", help="liệt kê agent")
    sub.add_parser("sync", help="sinh .opencode/agents/ từ agents/")
    sub.add_parser("check", help="kiểm tra hợp lệ và phát hiện bản sinh lệch")
    sub.add_parser("doc", help="sinh lại bảng agent trong agents/README.md")
    for ten_lenh, giup in (("new", "tạo agent mới từ mẫu"),
                           ("rm", "xoá agent")):
        s = sub.add_parser(ten_lenh, help=giup)
        s.add_argument("ten")
    s = sub.add_parser("rename", help="đổi tên agent")
    s.add_argument("cu")
    s.add_argument("moi")
    args = p.parse_args(argv)

    if args.lenh == "list":
        return _lenh_list()
    if args.lenh == "sync":
        print("Đồng bộ agents/ -> .opencode/agents/")
        _sync()
        return 0
    if args.lenh == "check":
        return _lenh_check()
    if args.lenh == "doc":
        _ghi(os.path.join(NGUON, README), _sinh_readme())
        print("Đã sinh lại agents/%s" % README)
        return 0
    if args.lenh == "new":
        return _lenh_new(args.ten)
    if args.lenh == "rename":
        return _lenh_rename(args.cu, args.moi)
    if args.lenh == "rm":
        return _lenh_rm(args.ten)
    return 1


if __name__ == "__main__":
    sys.exit(main())
