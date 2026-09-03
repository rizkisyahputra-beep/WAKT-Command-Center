@echo off
cd /d "%~dp0"
echo Membuka server dalam mode debug untuk melacak error...
echo -----------------------------------------------------
python app.py
pause