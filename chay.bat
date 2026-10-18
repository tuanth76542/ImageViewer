@echo off
REM Chay Phan Mem Xem Anh (giao dien Qt) bang uv
uv run python "%~dp0viewer_qt.py" %*
if errorlevel 1 pause
