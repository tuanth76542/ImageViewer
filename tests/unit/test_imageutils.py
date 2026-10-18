"""Test đơn vị cho phần đọc ảnh / chuyển đổi ảnh (xemanh.imageutils)."""
import os

import pytest
from PIL import Image

from xemanh import imageutils

pytestmark = pytest.mark.unit


def test_exts_dung_dinh_dang_ho_tro():
    assert {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif",
            ".ico"} == imageutils.EXTS
    assert ".txt" not in imageutils.EXTS


def test_list_images_loc_dung_ext_va_sap_xep(tmp_path):
    (tmp_path / "b.PNG").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "c.txt").write_text("x")
    (tmp_path / "note.md").write_text("x")
    (tmp_path / "sub").mkdir()  # thư mục con -> bỏ qua
    imgs = imageutils.list_images_in_folder(str(tmp_path))
    assert [os.path.basename(p) for p in imgs] == ["a.jpg", "b.PNG"]


def test_list_images_thu_muc_khong_ton_tai():
    assert imageutils.list_images_in_folder("khong-ton-tai-xyz") == []


def test_list_images_bo_qua_file_trong_thu_muc_con(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "sau.jpg").write_bytes(b"x")
    assert imageutils.list_images_in_folder(str(tmp_path)) == []


def test_pil_to_qimage_giu_kich_thuoc_va_mau(tmp_path):
    p = tmp_path / "a.png"
    Image.new("RGB", (7, 5), (10, 20, 30)).save(p)
    with Image.open(p) as im:
        q = imageutils.pil_to_qimage(im.convert("RGB"))
    assert (q.width(), q.height()) == (7, 5)
    c = q.pixelColor(0, 0)
    assert (c.red(), c.green(), c.blue()) == (10, 20, 30)


def test_pil_to_qimage_tu_chuyen_sang_rgb():
    # ảnh xám (mode "L") phải được chuyển sang RGB, không lỗi
    q = imageutils.pil_to_qimage(Image.new("L", (4, 3), 128))
    assert not q.isNull()
    assert (q.width(), q.height()) == (4, 3)
    assert q.pixelColor(0, 0).red() == 128


def test_pil_to_qimage_giu_du_lieu_sau_khi_anh_bi_xoa():
    # hàm phải copy buffer, không giữ con trỏ vào ảnh PIL đã hủy
    im = Image.new("RGB", (16, 16), (1, 2, 3))
    q = imageutils.pil_to_qimage(im)
    del im
    assert q.pixelColor(15, 15).blue() == 3
