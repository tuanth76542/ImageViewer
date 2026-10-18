@echo off
REM Dong goi thanh file .exe bang uv + PyInstaller.
REM Dung PhanMemXemAnh.spec (loc DLL runtime C++/UCRT bi gom nham theo PATH - xem
REM chu thich trong spec; khong doi sang lenh pyinstaller truc tiep).
uv sync
uv run --with pyinstaller pyinstaller --noconfirm PhanMemXemAnh.spec
echo.
echo Xong! File .exe nam trong thu muc dist\PhanMemXemAnh.exe
pause
