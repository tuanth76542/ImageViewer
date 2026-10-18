"""Test chỗ chứa models/ + cache của loc_nu khi chạy từ mã nguồn và từ .exe.

Đóng gói PyInstaller onefile sẽ giải nén vào thư mục tạm rồi xoá khi thoát, nên
nếu để models/ cạnh module thì mỗi lần mở app phải tải lại ~430MB và mất cache.
"""
import os

import pytest

import loc_nu

pytestmark = pytest.mark.unit


def test_chay_tu_ma_nguon_thi_de_canh_module():
    assert getattr(loc_nu.sys, "frozen", False) is False     # đang chạy pytest
    assert loc_nu._data_dir() == os.path.dirname(os.path.abspath(loc_nu.__file__))


def test_dong_goi_dung_thu_muc_nguoi_dung(tmp_path, monkeypatch):
    monkeypatch.setattr(loc_nu.sys, "frozen", True, raising=False)
    monkeypatch.setattr(loc_nu.sys, "executable",
                        str(tmp_path / "PhanMemXemAnh.exe"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    monkeypatch.delenv("APPDATA", raising=False)
    assert loc_nu._data_dir() == str(tmp_path / "appdata" / "PhanMemXemAnh")


def test_dong_goi_uu_tien_models_canh_file_exe(tmp_path, monkeypatch):
    # ai đó copy kèm thư mục models/ thì dùng luôn, không tải lại
    monkeypatch.setattr(loc_nu.sys, "frozen", True, raising=False)
    monkeypatch.setattr(loc_nu.sys, "executable",
                        str(tmp_path / "PhanMemXemAnh.exe"))
    (tmp_path / "models").mkdir()
    assert loc_nu._data_dir() == str(tmp_path)


def test_model_dir_lay_tu_thu_muc_du_lieu(tmp_path, monkeypatch):
    monkeypatch.setattr(loc_nu, "_data_dir", lambda: str(tmp_path))
    assert loc_nu._model_dir() == str(tmp_path / "models")


def test_cache_nam_trong_thu_muc_models():
    assert os.path.basename(loc_nu.MODEL_DIR) == "models"
    assert os.path.dirname(loc_nu.CACHE_PATH) == loc_nu.MODEL_DIR
