@echo off
color 0A
echo ================================================================
echo        MEMULAI INSTALASI MESIN COMMAND CENTER WAKT
echo ================================================================
echo.
echo [1/2] Memastikan mesin pip (installer) versi terbaru...
python -m pip install --upgrade pip
echo.
echo [2/2] Mengunduh dan memasang seluruh amunisi yang dibutuhkan...
echo (Pastikan laptop ini terhubung ke internet!)
echo.
python -m pip install Flask requests urllib3 openpyxl selenium webdriver-manager docxtpl python-docx pywin32 docx2pdf Pillow apscheduler
echo.
echo ================================================================
echo  INSTALASI SELESAI DAN SUKSES! 
echo  Semua perlengkapan tempur sudah terpasang di laptop ini.
echo.
echo  Silakan tekan tombol apa saja untuk menutup jendela ini,
echo  lalu klik ganda file 'web_run' untuk menyalakan server!
echo ================================================================
pause >nul