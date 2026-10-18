"""Bảng màu / QSS dùng chung cho giao diện tối."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


DARK_QSS = """
* { font-family: "Segoe UI"; }
QMainWindow, QDialog { background: #101014; }
QGraphicsView { background: #101014; border: none; }

/* ---- thanh điều khiển nổi ---- */
QWidget#overlayBar {
    background: rgba(30, 30, 37, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
}
QWidget#overlayBar QPushButton {
    background: transparent; color: #e9e9f0; border: none;
    border-radius: 9px; padding: 7px 11px; font-size: 14px;
}
QWidget#overlayBar QPushButton:hover { background: rgba(255, 255, 255, 0.13); }
QWidget#overlayBar QPushButton:pressed { background: rgba(255, 255, 255, 0.22); }
QWidget#overlayBar QPushButton[active="true"] { background: #7c3aed; color: #fff; }
QLabel#zoomPct {
    color: #ffffff; font-size: 12px; font-weight: 600; min-width: 50px;
    qproperty-alignment: AlignCenter;
}
QFrame#sep { color: rgba(255, 255, 255, 0.13); }

/* ---- thẻ thông tin (dưới trái) ---- */
QWidget#infoPill {
    background: rgba(30, 30, 37, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
}
QLabel#infoName { color: #f4f4f8; font-size: 13px; font-weight: 600; }
QLabel#infoMeta { color: #9aa0ab; font-size: 11px; }

/* ---- thông báo nổi (toast) ---- */
QWidget#toast {
    background: rgba(30, 30, 37, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
}
QWidget#toast QLabel { color: #ececf2; font-size: 12px; }

/* ---- màn hình chào ---- */
QWidget#welcomeCard { background: transparent; }
QLabel#welcomeIcon { font-size: 46px; }
QLabel#welcomeTitle { color: #f2f2f7; font-size: 20px; font-weight: 700; }
QLabel#welcomeSub { color: #949aa5; font-size: 13px; }
QPushButton#welcomeBtn {
    background: #6d5bd0; color: #fff; border: none; border-radius: 10px;
    padding: 10px 20px; font-size: 13px;
}
QPushButton#welcomeBtn:hover { background: #7d6bea; }

/* ---- hộp thoại ---- */
QDialog QPushButton {
    background: #33333c; color: #fff; border: none; border-radius: 8px;
    padding: 8px 14px; font-size: 13px;
}
QDialog QPushButton:hover { background: #45454f; }
QDialog QLabel { color: #e6e6ec; }
QWidget#helpCard {
    background: #1a1a20; border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}
QLabel#helpTitle { color: #f4f4f8; font-size: 17px; font-weight: 700; }
QLabel#helpKey {
    color: #c9b8ff; font-size: 12px; font-weight: 600;
    background: #262632; border-radius: 7px; padding: 5px 9px;
}
QLabel#helpDesc { color: #cfd2d9; font-size: 12px; }
/* ---- thanh điều khiển slideshow ---- */
QWidget#slideBar {
    background: rgba(20, 20, 25, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}
QWidget#slideBar QPushButton {
    background: transparent; color: #eaeaf0; border: none;
    border-radius: 9px; padding: 8px 12px; font-size: 15px;
}
QWidget#slideBar QPushButton:hover { background: rgba(255, 255, 255, 0.14); }
QWidget#slideBar QPushButton:pressed { background: rgba(255, 255, 255, 0.24); }
QWidget#slideBar QLabel { color: #b9bdc7; font-size: 12px; }
QWidget#slideBar QPushButton:checked {
    background: #7b6cf0; color: #ffffff; font-weight: 600;
}
QLabel#slideCount { color: #ffffff; font-weight: 600; font-size: 12px; }
QProgressDialog { background: #16161a; }
"""


def _glass(name):
    """QWidget nền bán trong suốt (bo góc) theo QSS."""
    w = QWidget()
    w.setObjectName(name)
    w.setAttribute(Qt.WA_StyledBackground, True)
    return w
