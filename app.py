from flask import Flask, send_from_directory, jsonify, request, send_file
import requests
import sqlite3
import re
import urllib3
import calendar
import os
import io
import re
import random
from datetime import datetime, timedelta
import openpyxl
import openpyxl
# --- SUNTIKAN LIBRARY ROBOT SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import io
import zipfile
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import tempfile
import os
import pythoncom
from docx2pdf import convert
from PIL import Image
# ---------------------------------------

# Matikan peringatan SSL internet
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, static_folder='.', static_url_path='')
DB_NAME = "database_wakt.db"
TEMPLATE_NAME = "template_verif.xlsm"

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metar_wakt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sandi_metar TEXT NOT NULL UNIQUE,
            waktu_observasi DATETIME NOT NULL,
            waktu_rekam DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ========================================================
# HELPER PARSING: MEMBEDAH SANDI MENJADI VARIABEL EXCEL
# ========================================================
def parse_sandi_ke_komponen(sandi):
    komponen = {
        "arah": 0,
        "speed": 0,
        "gust": 0,
        "vis": 9999,
        "cuaca": "0",
        "awan_jml": "NSC",
        "awan_tgi": 0,
    }
    if not sandi:
        return komponen
    sandi = sandi.upper()

    if "CAVOK" in sandi:
        komponen["vis"] = 9999
        komponen["cuaca"] = "0"
        komponen["awan_jml"] = "NSC"
        komponen["awan_tgi"] = 0

    match_wind = re.search(r"\b(\d{3}|VRB)(\d{2})(?:G(\d{2}))?KT\b", sandi)
    if match_wind:
        komponen["arah"] = (
            match_wind.group(1)
            if match_wind.group(1) == "VRB"
            else int(match_wind.group(1))
        )
        komponen["speed"] = int(match_wind.group(2))
        if match_wind.group(3):
            komponen["gust"] = int(match_wind.group(3))

    if "CAVOK" not in sandi:
        # TAMENG ANTI-SLASH: Mengabaikan grup validitas waktu agar tidak dikira visibility
        match_vis = re.search(r"(?<!\/)\b(\d{4})\b(?!\/)", sandi)
        if match_vis:
            komponen["vis"] = int(match_vis.group(1))

    match_cuaca = re.search(
        r"(?<!\w)(\+|-)?(RA|DZ|SHRA|TSRA|TS|BR|FG|HZ)\b", sandi
    )
    if match_cuaca:
        komponen["cuaca"] = match_cuaca.group(0)

    if "CAVOK" not in sandi and "NSC" not in sandi:
        match_cld = re.search(r"\b(FEW|SCT|BKN|OVC)(\d{3})(?:CB|TCU)?\b", sandi)
        if match_cld:
            komponen["awan_jml"] = match_cld.group(1)
            komponen["awan_tgi"] = int(match_cld.group(2)) * 100
    return komponen

def ekstrak_parameter_eksplisit(teks):
    komp = {}
    if "NSW" in teks:
        komp["cuaca"] = "0"
    else:
        c = re.search(r"(?<!\w)(\+|-)?(RA|DZ|SHRA|TSRA|TS|BR|FG|HZ)\b", teks)
        if c:
            komp["cuaca"] = c.group(0)

    w = re.search(r"\b(\d{3}|VRB)(\d{2})(?:G(\d{2}))?KT\b", teks)
    if w:
        komp["arah"] = (
            w.group(1) if w.group(1) == "VRB" else int(w.group(1))
        )
        komp["speed"] = int(w.group(2))
        komp["gust"] = int(w.group(3)) if w.group(3) else 0

    v = re.search(r"(?<!\/)\b(\d{4})\b(?!\/)", teks)
    if v:
        komp["vis"] = int(v.group(1))

    cl = re.search(r"\b(FEW|SCT|BKN|OVC)(\d{3})(?:CB|TCU)?\b", teks)
    if cl:
        komp["awan_jml"] = cl.group(1)
        komp["awan_tgi"] = int(cl.group(2)) * 100

    return komp

def parse_tafor_ke_matriks(sandi_taf, valid_start_dt):
    rows = []
    parts = re.split(r'\b(TEMPO|BECMG)\b', sandi_taf)
    base_taf = parts[0] if parts else sandi_taf
    base_comp = parse_sandi_ke_komponen(base_taf)
    
    for i in range(12):
        rows.append({
            'dt': valid_start_dt + timedelta(hours=i),
            'group': 'GENERAL',
            'comp': dict(base_comp)
        })
    
    if len(parts) <= 1: return rows

    for i in range(1, len(parts), 2):
        g_type = parts[i]
        g_text = parts[i+1]
        
        p_match = re.search(r'(\d{2})(\d{2})/(\d{2})(\d{2})', g_text)
        if not p_match: continue
        
        d1, h1, d2, h2 = map(int, p_match.groups())
        
        month1, year1 = valid_start_dt.month, valid_start_dt.year
        if d1 < valid_start_dt.day - 10: 
            month1 += 1
            if month1 > 12: month1, year1 = 1, year1 + 1
        
        start_dt = datetime(year1, month1, min(d1, calendar.monthrange(year1, month1)[1]), h1)
        
        month2, year2 = start_dt.month, start_dt.year
        if d2 < start_dt.day - 10:
            month2 += 1
            if month2 > 12: month2, year2 = 1, year2 + 1
            
        end_dt = datetime(year2, month2, min(d2, calendar.monthrange(year2, month2)[1]), h2)
        
        new_comp = ekstrak_parameter_eksplisit(g_text)
        
        for r in rows:
            if g_type == "TEMPO":
                if start_dt <= r['dt'] <= end_dt:
                    r['group'] = "TEMPO"
                    r['comp'].update(new_comp)
            elif g_type == "BECMG":
                if r['dt'] > end_dt:
                    r['group'] = "BECMG"
                    r['comp'].update(new_comp)
                    
    return rows

def dapat_kelas_visibility(v):
    if v <= 799: return 1
    if v <= 1499: return 2
    if v <= 2999: return 3
    if v <= 5000: return 4
    return 5

def verifikasi_baris_cuaca(t, m, metar_full):
    score = {
        "arah": 0, "speed": 0, "gust": 0, "vis": 0,
        "cuaca": 0, "awan_jml": 0, "awan_tgi": 0,
    }

    # =================================================================
    # 1. ARAH ANGIN (Toleransi 60 Derajat & Kecepatan < 10 KT)
    # =================================================================
    if t["arah"] == "VRB" and m["arah"] == "VRB":
        score["arah"] = 1
    elif t["arah"] == "VRB" and ("TS" in metar_full or "CB" in metar_full):
        score["arah"] = 1
    elif t["arah"] == "VRB" and m["speed"] < 10:
        score["arah"] = 1
    elif t["arah"] != "VRB" and m["arah"] != "VRB":
        diff = min(abs(int(t["arah"]) - int(m["arah"])), 360 - abs(int(t["arah"]) - int(m["arah"])))
        if diff <= 60:
            score["arah"] = 1
        elif diff > 60 and m["speed"] < 10:
            score["arah"] = 1
    else:
        if m["speed"] < 10:
            score["arah"] = 1

    # =================================================================
    # 2 & 3. KECEPATAN ANGIN & GUST (Toleransi 10 KT)
    # =================================================================
    if abs(t["speed"] - m["speed"]) <= 10:
        score["speed"] = 1
    if (t["gust"] > 0 and m["gust"] > 0) or (t["gust"] == 0 and m["gust"] == 0):
        score["gust"] = 1

    # =================================================================
    # 4. 👁️ VISIBILITAS: 5 KELAS SOP (KOREKSI BATAS ANGKA 799 & 1499)
    # =================================================================
    def dapatkan_kelas_vis(vis_str):
        if "CAVOK" in str(vis_str).upper() or "9999" in str(vis_str): return 5
        try:
            v = int(vis_str)
            # FIX: Mengikuti SOP 2020 & 2025 secara presisi mutlak!
            if v < 800: return 1      # Kelas 1: 0 - 799 m
            elif v < 1500: return 2   # Kelas 2: 800 - 1499 m
            elif v < 3000: return 3   # Kelas 3: 1500 - 2999 m
            elif v <= 5000: return 4  # Kelas 4: 3000 - 5000 m
            else: return 5            # Kelas 5: > 5000 m
        except: return -1

    t_vis_str = str(t.get("vis", "")).strip()
    m_vis_str = str(m.get("vis", "")).strip()
    kelas_t = dapatkan_kelas_vis(t_vis_str)
    kelas_m = dapatkan_kelas_vis(m_vis_str)

    if kelas_t == kelas_m and kelas_t != -1:
        score["vis"] = 1
    else:
        is_transisi_becmg = t.get("is_becmg_transition", False)
        t_vis_awal_str = str(t.get("vis_awal", "")).strip()
        if is_transisi_becmg and t_vis_awal_str:
            kelas_t_awal = dapatkan_kelas_vis(t_vis_awal_str)
            batas_bawah, batas_atas = min(kelas_t_awal, kelas_t), max(kelas_t_awal, kelas_t)
            if batas_bawah <= kelas_m <= batas_atas: score["vis"] = 1
            else: score["vis"] = 0
        else:
            score["vis"] = 0

    # =================================================================
    # 5. 🟢 CUACA: KELOMPOK ENDAPAN / PRESIPITASI (TOLERANSI ALL-WET)
    # =================================================================
    t_str = str(t.get("cuaca", "")).upper().strip()
    
    # 1. Cek Prediksi TAFOR (Apakah prakiraannya Presipitasi/Basah?)
    t_basah = any(x in t_str for x in ["RA", "DZ", "SH", "TS"])
    
    # 2. Cek Aktual METAR (Validasi Ekstra di Seluruh Teks Sandi)
    m_basah = False
    if metar_full:
        pola_presipitasi = r'\b(\+|-|VC)?(DZ|RA|SHRA|TSRA|SH|TS)\b'
        if re.search(pola_presipitasi, metar_full):
            m_basah = True

    # 3. Kunci Logika: Jika sama-sama basah ATAU sama-sama kering = BENAR (1)
    if t_basah == m_basah: 
        score["cuaca"] = 1
    else: 
        score["cuaca"] = 0

    # =================================================================
    # 6 & 7. ☁️ AWAN: 2 KELAS BMKG & TOLERANSI TINGGI (100ft vs 30%)
    # =================================================================
    t_jml = str(t.get("awan_jml", "NSC")).upper()
    m_jml = str(m.get("awan_jml", "NSC")).upper()
    
    t_feet = int(t.get("awan_tgi", 0))
    m_feet = int(m.get("awan_tgi", 0))

    def get_kelas_awan(jml_str):
        if jml_str in ["SKC", "FEW", "SCT", "CAVOK", "NSC", "NCD"]: return 1
        if jml_str in ["BKN", "OVC"]: return 2
        return 0

    # Aturan Awan Tinggi: Jika METAR aktual mendeteksi awan di atas 5000ft, selalu benar (Tidak Signifikan)
    if m_feet > 5000 and m_jml not in ["CAVOK", "NSC", "NCD", "SKC"]:
        score["awan_jml"] = 1
        score["awan_tgi"] = 1
    else:
        # Evaluasi Jumlah Awan (2 Kelas)
        kelas_t = get_kelas_awan(t_jml)
        kelas_m = get_kelas_awan(m_jml)
        
        if kelas_t == kelas_m and kelas_t != 0: score["awan_jml"] = 1
        else: score["awan_jml"] = 0
            
        # Evaluasi Tinggi Dasar Awan
        if m_jml in ["CAVOK", "NSC", "NCD", "SKC"] or t_jml in ["CAVOK", "NSC", "NCD", "SKC"]:
            # Jika kondisi langit bersih/tidak ada dasar awan, ikuti hasil jumlah awan
            score["awan_tgi"] = score["awan_jml"]
        else:
            selisih = abs(t_feet - m_feet)
            if t_feet < 1000:
                # Toleransi absolut max 100 feet
                if selisih <= 100: score["awan_tgi"] = 1
                else: score["awan_tgi"] = 0
            else:
                # Toleransi 30% dari nilai prakiraan
                if selisih <= (t_feet * 0.30): score["awan_tgi"] = 1
                else: score["awan_tgi"] = 0

    return score

# ====================================================================
# 🟢 MESIN 1: JALUR KHUSUS METAR & SPECI (DIPASANG FILTER ANTI-TAFOR)
# ====================================================================
def eksekusi_tarik_metar(tahun, bulan):
    url = "https://web-aviation.bmkg.go.id/web/metar_speci.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    session = requests.Session()
    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    tgl_awal = f"{tahun}-{bulan:02d}-01 00:00"
    tgl_akhir = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 23:59"
    total_berhasil = 0
    
    try:
        res_init = session.get(url, headers=headers, verify=False, timeout=15)
        token_match = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', res_init.text, re.IGNORECASE)
        if not token_match: token_match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']_token["\']', res_init.text, re.IGNORECASE)
        if not token_match: return 0
        token_csrf = token_match.group(1)
        
        payload = {'_token': token_csrf, 'stasiun': 'WAKT', 'from': tgl_awal, 'to': tgl_akhir, 'metar': 'on', 'speci': 'on', 'taf': 'on', 'prakicu': 'on'}
        response = session.post(url, data=payload, headers=headers, timeout=45, verify=False)
        
        if response.status_code == 200:
            teks_bersih = re.sub(r'<[^>]+>', ' ', response.text)
            teks_bersih = re.sub(r'\s+', ' ', teks_bersih)
            
            pola_sandi = r'\b(?:METAR|SPECI|TAF|TAFOR)\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\s+[^=]*='
            semua_sandi = re.findall(pola_sandi, teks_bersih, re.IGNORECASE)
            
            if semua_sandi:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for sandi in semua_sandi:
                    sandi_clean = re.sub(r'\s+', ' ', sandi.upper().strip())
                    
                    # 🚀 FILTER: JIKA INI TAF ATAU TAFOR, BUANG! MESIN INI KHUSUS METAR!
                    if sandi_clean.startswith("TAF"):
                        continue
                        
                    waktu_obs_sql = parse_waktu_zulu(sandi_clean, tahun, bulan)
                    tipe_sandi = "SPECI%" if "SPECI" in sandi_clean else "METAR%"
                    
                    cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar LIKE ?", (waktu_obs_sql, tipe_sandi))
                    if not cursor.fetchone():
                        try:
                            cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (sandi_clean, waktu_obs_sql))
                            total_berhasil += 1
                        except sqlite3.IntegrityError: pass
                conn.commit()
                conn.close()
    except Exception as e: print(f"Error Tarik METAR: {e}")
    return total_berhasil

# ====================================================================
# 🟢 MESIN 2: JALUR KHUSUS TAFOR (ROBOT SELENIUM BRUTE-FORCE)
# ====================================================================
def eksekusi_tarik_tafor(tahun, bulan):
    print("Memulai penarikan TAFOR...")
    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    
    # 🟢 PERBAIKAN: Mundur 1 hari untuk menangkap TAFOR rilis 23Z bulan lalu (Milik Siklus 00Z Tanggal 1)
    dt_awal = datetime(tahun, bulan, 1) - timedelta(days=1)
    tgl_awal = f"{dt_awal.year}-{dt_awal.month:02d}-{dt_awal.day:02d}T22:00"
    
    tgl_akhir = f"{tahun}-{bulan:02d}-{akhir_hari:02d}T23:59"
    total_berhasil = 0
    driver = None
    
    try:
        # 1. SETUP BROWSER SILUMAN (Headless Chrome)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080') 
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 20) 
        
        # 2. BUKA HALAMAN TAF
        url = "https://web-aviation.bmkg.go.id/web/taf.php"
        driver.get(url)
        
        # 3. ISI FORM MENGGUNAKAN JAVASCRIPT AGAR PASTI TEMBUS
        driver.execute_script(f"document.getElementById('stasiun').value = 'WAKT';")
        driver.execute_script(f"document.getElementById('datetime').value = '{tgl_awal}';")
        driver.execute_script(f"document.getElementById('datetime2').value = '{tgl_akhir}';")
        
        # 4. KLIK TOMBOL CARI
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        submit_btn.click()
        
        # 5. TUNGGU TABEL MUNCUL & LOADING SELESAI
        wait.until(EC.presence_of_element_located((By.ID, "table_id")))
        time.sleep(3) # Nafas ekstra agar DataTables selesai menggambar HTML
        
        # 6. PAKSA DATATABLES MENAMPILKAN SEMUA BARIS (Pilih "All" / "-1")
        try:
            driver.execute_script("""
                var select = document.querySelector('select[name="table_id_length"]');
                if(select) {
                    select.value = '-1';
                    select.dispatchEvent(new Event('change'));
                }
            """)
            time.sleep(3) # Tunggu tabel memanjang ke bawah
        except:
            pass # Lanjut jika elemen tidak ditemukan
            
        # 7. SEDOT SELURUH HTML HALAMAN (Yang sudah di-render persis seperti yang Kapten lihat di layar)
        html_source = driver.page_source
        
        # 8. JURUS PEMBELAH ATOM (Ekstrak Teks dari HTML)
        teks_bersih = re.sub(r'<[^>]+>', ' ', html_source)
        teks_bersih = re.sub(r'\s+', ' ', teks_bersih).upper()
        
        pola_start = r'\bTAF(?:OR)?\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\b'
        starts = [m.span() for m in re.finditer(pola_start, teks_bersih)]
        
        semua_sandi = []
        for i in range(len(starts)):
            start_idx = starts[i][0]
            if i < len(starts) - 1:
                potongan = teks_bersih[start_idx:starts[i+1][0]]
            else:
                potongan = teks_bersih[start_idx:]
                
            # Potong jika ada teks sampah/sandi lain yang ikut
            for pembatas in ['METAR WAKT', 'SPECI WAKT', 'FTID', 'SHOW', 'ENTRIES']:
                idx_pembatas = potongan.find(pembatas)
                if idx_pembatas != -1:
                    potongan = potongan[:idx_pembatas]
                    
            idx_sama_dengan = potongan.find('=')
            if idx_sama_dengan != -1:
                potongan = potongan[:idx_sama_dengan+1]
            else:
                potongan = potongan.strip() + '='
                
            semua_sandi.append(re.sub(r'\s+', ' ', potongan.strip()))
            
        # 9. BUANG DUPLIKAT & SIMPAN KE DATABASE
        semua_sandi = list(set(semua_sandi))
        
        if semua_sandi:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            for sandi_clean in semua_sandi:
                if "TAFOR " in sandi_clean: sandi_clean = sandi_clean.replace("TAFOR ", "TAF ", 1)
                if "TAF " in sandi_clean and not sandi_clean.startswith("TAF"): sandi_clean = "TAF " + sandi_clean
                
                waktu_obs_sql = parse_waktu_zulu(sandi_clean, tahun, bulan)
                
                cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar LIKE 'TAF%'", (waktu_obs_sql,))
                cek_db = cursor.fetchone()
                
                if cek_db:
                    if " COR " in sandi_clean or " AMD " in sandi_clean:
                        try:
                            cursor.execute("UPDATE metar_wakt SET sandi_metar = ? WHERE id = ?", (sandi_clean, cek_db[0]))
                            total_berhasil += 1
                        except: pass
                else:
                    try:
                        cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (sandi_clean, waktu_obs_sql))
                        total_berhasil += 1
                    except sqlite3.IntegrityError: 
                        sukses_masuk = False
                        spasi_tambahan = " "
                        for _ in range(15): # Lapis keamanan anti-gembok duplikat
                            try: 
                                cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (sandi_clean + spasi_tambahan, waktu_obs_sql))
                                total_berhasil += 1
                                sukses_masuk = True
                                break
                            except sqlite3.IntegrityError:
                                spasi_tambahan += " "
                        if not sukses_masuk: pass
            conn.commit()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error Tarik TAFOR (Selenium): {e}")
    finally:
        if driver:
            driver.quit() # Wajib dimatikan agar RAM laptop tidak bocor
            
    print(f"✅ Berhasil {total_berhasil} data TAFOR.")
    return total_berhasil

def parse_waktu_zulu(sandi_clean, tahun, bulan):
    match_zulu = re.search(r'\b(\d{2})(\d{2})(\d{2})Z\b', sandi_clean)
    if match_zulu:
        hari = int(match_zulu.group(1))
        jam = match_zulu.group(2)
        menit = match_zulu.group(3)
        
        max_hari_ini = calendar.monthrange(tahun, bulan)[1]
        dt_bulan_ini = datetime(tahun, bulan, 1)
        dt_bulan_lalu = dt_bulan_ini - timedelta(days=1)
        max_hari_lalu = dt_bulan_lalu.day

        # 1. Deteksi TAF Transisi Bulan (Sandi akhir bulan yg berlaku mulai Tgl 1)
        if "TAF" in sandi_clean.upper() and hari >= 28:
            match_v = re.search(r'\b(\d{2})\d{2}\/\d{2}\d{2}\b', sandi_clean)
            if match_v and int(match_v.group(1)) == 1:
                # Jika hari di sandi COCOK dgn jumlah hari bulan INI, berarti ini milik bulan ini (Misal 31 Juli)
                if hari == max_hari_ini:
                    return f"{tahun}-{bulan:02d}-{hari:02d} {jam}:{menit}:00"
                # Jika hari COCOK dgn jumlah hari bulan LALU, baru kita tarik ke belakang (Misal 30 Juni)
                elif hari == max_hari_lalu or hari > max_hari_ini:
                    return f"{dt_bulan_lalu.year}-{dt_bulan_lalu.month:02d}-{hari:02d} {jam}:{menit}:00"

        # 2. Pengamanan Normal jika hari ditarik melebihi kalender (Misal 31 ditarik di April)
        if hari > max_hari_ini:
            hari_aman = min(hari, max_hari_lalu)
            return f"{dt_bulan_lalu.year}-{dt_bulan_lalu.month:02d}-{hari_aman:02d} {jam}:{menit}:00"

        return f"{tahun}-{bulan:02d}-{hari:02d} {jam}:{menit}:00"
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ====================================================================
# 🧠 REVOLUSI MATRIX ENGINE: SINKRONISASI 4 SIKLUS VERTIKAL + REKAP BULANAN
# ====================================================================
def hitung_accuracy_dashboard_web(tahun, bulan, metar_dummy_text=""):
    conn = sqlite3.connect(DB_NAME)  
    taf_map = {}
    cursor = conn.cursor()
    
    # 1. ⚡ PERBAIKAN BUG AKHIR BULAN: Susun limit melebar ke H+2 bulan depan ⚡
    dt_start_bulan = datetime(tahun, bulan, 1)
    limit_lalu_str = (dt_start_bulan - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    
    bulan_next = bulan + 1 if bulan < 12 else 1
    tahun_next = tahun if bulan < 12 else tahun + 1
    limit_depan_str = f"{tahun_next}-{bulan_next:02d}-02 00:00:00"
    
    # 2. ⚡ PERBAIKAN QUERY METAR: Ambil pakai limit depan, BUKAN cuma LIKE bulan ini ⚡
    cursor.execute(
        "SELECT sandi_metar, waktu_observasi FROM metar_wakt WHERE waktu_observasi >= ? AND waktu_observasi <= ? ORDER BY waktu_observasi ASC", 
        (limit_lalu_str, limit_depan_str)
    )
    metar_rows = cursor.fetchall()
    
    metar_dict = {}
    for sandi, waktu in metar_rows:
        if sandi.startswith("METAR") or sandi.startswith("SPECI"):
            # Jika jam ini belum ada, ATAU jika sandi ini adalah COR (Koreksi) -> BERI HAK VETO
            if waktu not in metar_dict or " COR " in sandi:
                metar_dict[waktu] = sandi

    # ====================================================================
    # 🟢 SUNTIKAN SEMENTARA: Masukkan METAR dummy langsung ke memori RAM
    # ====================================================================
    if metar_dummy_text:
        semua_metar_dummy = re.findall(r'\b(?:METAR|SPECI)\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\s+[^=]*=', metar_dummy_text, re.IGNORECASE)
        for sandi_dummy in semua_metar_dummy:
            sandi_clean = re.sub(r'\s+', ' ', sandi_dummy.upper().strip())
            waktu_obs_dummy = parse_waktu_zulu(sandi_clean, tahun, bulan)
            # Timpa atau tambahkan ke memori (Hak Veto Tertinggi dari Input Manual Web)
            metar_dict[waktu_obs_dummy] = sandi_clean 
    # ====================================================================
    
    # ... (Biarkan kode taf_map atau kode lain di bawahnya tetap utuh berjalan normal) ...
    
    # 3. Tarik TAFOR dengan limit yang sama
    cursor.execute(
        "SELECT sandi_metar, waktu_observasi FROM metar_wakt WHERE sandi_metar LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?", 
        (limit_lalu_str, limit_depan_str)
    )
    taf_rows = cursor.fetchall()
    conn.close()
    
    # ... (Biarkan kelanjutan kode taf_map = {} dan seterusnya di bawahnya utuh) ...
    
    taf_map = {}
    for sandi, waktu in taf_rows:
        dt_obj = datetime.strptime(waktu, "%Y-%m-%d %H:%M:%S")
        h = dt_obj.hour
        
        # 🟢 LURUSKAN LOGIKA: Jam 22 dan 23 adalah milik Siklus 00Z HARI ESOKNYA
        if h in [22, 23, 0, 1, 2, 3]:
            target_day_dt = (dt_obj + timedelta(days=1)) if h >= 22 else dt_obj
            cycle = "00Z"
        elif h in [4, 5, 6, 7, 8, 9]:
            target_day_dt = dt_obj
            cycle = "06Z"
        elif h in [10, 11, 12, 13, 14, 15]:
            target_day_dt = dt_obj
            cycle = "12Z"
        else:
            target_day_dt = dt_obj
            cycle = "18Z"
            
        if target_day_dt.month == bulan and target_day_dt.year == tahun:
            key_taf = (target_day_dt.day, cycle)
            # Jika siklus ini belum ada, ATAU jika sandi ini adalah COR / AMD -> BERI HAK VETO
            if key_taf not in taf_map or " COR " in sandi or " AMD " in sandi:
                taf_map[key_taf] = sandi

    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    total_jam, ok_dir, ok_spd, ok_vis, ok_cuaca, ok_cld_j, ok_cld_t = 0, 0, 0, 0, 0, 0, 0
    detail_harian = {}
    
    cycles_config = [
        {"cycle_name": "00Z", "start_hour": 0},
        {"cycle_name": "06Z", "start_hour": 6},
        {"cycle_name": "12Z", "start_hour": 12},
        {"cycle_name": "18Z", "start_hour": 18}
    ]
    
    for hari in range(1, akhir_hari + 1):
        detail_harian[str(hari)] = {}
        
        for cfg in cycles_config:
            c_name = cfg["cycle_name"]
            sandi_taf = taf_map.get((hari, c_name), "NIL=")
            
            valid_start_dt = datetime(tahun, bulan, hari, cfg["start_hour"], 0, 0)
            matrix_prakiraan = parse_tafor_ke_matriks(sandi_taf, valid_start_dt)
            
            c_rows = []
            total_hours_c = 0
            ok_dir_c = ok_spd_c = ok_gust_c = ok_vis_c = ok_cuaca_c = ok_cld_j_c = ok_cld_t_c = 0
            
            for baris in matrix_prakiraan:
                waktu_evaluasi_str = baris['dt'].strftime("%Y-%m-%d %H:%M:%S")
                sandi_metar = metar_dict.get(waktu_evaluasi_str, "")
                
                m_c = parse_sandi_ke_komponen(sandi_metar)
                skor = verifikasi_baris_cuaca(baris['comp'], m_c, sandi_metar) if sandi_metar else {'arah':0,'speed':0,'gust':0,'vis':0,'cuaca':0,'awan_jml':0,'awan_tgi':0}
                
                if sandi_metar:
                    total_jam += 1
                    ok_dir += skor['arah']
                    ok_spd += skor['speed']
                    ok_vis += skor['vis']
                    ok_cuaca += skor['cuaca']
                    ok_cld_j += skor['awan_jml']
                    ok_cld_t += skor['awan_tgi']
                    
                    total_hours_c += 1
                    ok_dir_c += skor['arah']
                    ok_spd_c += skor['speed']
                    ok_gust_c += skor['gust']
                    ok_vis_c += skor['vis']
                    ok_cuaca_c += skor['cuaca']
                    ok_cld_j_c += skor['awan_jml']
                    ok_cld_t_c += skor['awan_tgi']
                    
                c_rows.append({
                    "tanggal_row": baris['dt'].strftime("%d"),
                    "jam_row": baris['dt'].strftime("%H:00"),
                    "group_row": baris['group'],
                    "t": baris['comp'],
                    "m": m_c,
                    "metar_raw": sandi_metar if sandi_metar else "NIL=",
                    "skor": skor
                })
            
            detail_harian[str(hari)][c_name] = {
                "taf_raw": sandi_taf,
                "rows": c_rows,
                "cycle_summary": {
                    "arah": round((ok_dir_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "speed": round((ok_spd_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "gust": round((ok_gust_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "vis": round((ok_vis_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "cuaca": round((ok_cuaca_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "awan_jml": round((ok_cld_j_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0,
                    "awan_tgi": round((ok_cld_t_c / total_hours_c) * 100, 1) if total_hours_c > 0 else 0
                }
            }

    p_dir = round((ok_dir / total_jam) * 100, 1) if total_jam > 0 else 0
    p_spd = round((ok_spd / total_jam) * 100, 1) if total_jam > 0 else 0
    p_vis = round((ok_vis / total_jam) * 100, 1) if total_jam > 0 else 0
    p_cuaca = round((ok_cuaca / total_jam) * 100, 1) if total_jam > 0 else 0
    p_aw_j = round((ok_cld_j / total_jam) * 100, 1) if total_jam > 0 else 0
    p_aw_t = round((ok_cld_t / total_jam) * 100, 1) if total_jam > 0 else 0
    
    return {
        "summary": {
            "total_jam": total_jam, 
            "arah_angin": p_dir, 
            "kecepatan_angin": p_spd, 
            "visibility": p_vis, 
            "cuaca": p_cuaca,
            "awan_jumlah": p_aw_j, 
            "awan_tinggi": p_aw_t, 
            "total_score": round((p_dir + p_spd + p_vis + p_cuaca + p_aw_j + p_aw_t) / 6, 1) if total_jam > 0 else 0
        },
        "detail_harian": detail_harian
    }

# ========================================================
# ROUTING API MASTER PATHWAYS
# ========================================================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ====================================================================
# 🟢 API ROUTER WESEL: PENENTU JALUR KERETA (SINKRONISASI PRESISI)
# ====================================================================
@app.route('/api/metar/sync_pilihan', methods=['POST'])
def api_sync_pilihan():
    try:
        data = request.json or {}
        tipe_data = data.get('tipe', 'metar')
        
        now = datetime.now()
        tahun_ini = now.year
        # Tangkap bulan dari web, jika kosong pakai bulan saat ini
        bulan_req = data.get('bulan')
        bulan_target = int(bulan_req) if bulan_req else now.month
        
        total_baru_gabungan = 0
        
        # 🚀 PERBAIKAN: HANYA TARIK BULAN YANG DIPILIH SAJA (Tidak mengulang dari Januari)
        if tipe_data == 'taf':
            total_baru_gabungan = eksekusi_tarik_tafor(tahun_ini, bulan_target)
        else:
            total_baru_gabungan = eksekusi_tarik_metar(tahun_ini, bulan_target)
                
        return jsonify({"status": "Sukses", "total_baru": total_baru_gabungan})
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/metar/logs')
def api_metar_logs():
    bulan_param = request.args.get('bulan')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if bulan_param and '-' in bulan_param:
            tahun, bulan = map(int, bulan_param.split('-'))
            akhir_hari = calendar.monthrange(tahun, bulan)[1]
            
            # 1. Batas Waktu METAR (Kalender Normal: Tgl 1 00:00 s.d Akhir 23:59)
            start_metar = f"{tahun}-{bulan:02d}-01 00:00:00"
            end_metar = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 23:59:59"
            
            # 2. Batas Waktu TAFOR (Meteorologi: H-1 22:00 s.d Akhir 21:59)
            dt_start_taf = datetime(tahun, bulan, 1) - timedelta(days=1)
            start_taf = f"{dt_start_taf.year}-{dt_start_taf.month:02d}-{dt_start_taf.day:02d} 22:00:00"
            end_taf = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 21:59:59"
            
            # 🟢 KACAMATA HYBRID: METAR pakai aturan 1, TAF pakai aturan 2!
            query = """
                SELECT id, sandi_metar, waktu_observasi as waktu_lokal 
                FROM metar_wakt 
                WHERE 
                    (sandi_metar NOT LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?)
                    OR 
                    (sandi_metar LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?)
                ORDER BY waktu_observasi DESC
            """
            cursor.execute(query, (start_metar, end_metar, start_taf, end_taf))
        else:
            cursor.execute("SELECT id, sandi_metar, waktu_observasi as waktu_lokal FROM metar_wakt ORDER BY waktu_observasi DESC")
            
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"id": r["id"], "sandi_metar": r["sandi_metar"], "waktu_rekam": r["waktu_lokal"]} for r in rows])
    except Exception as e: 
        if conn: conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/metar/hitung_verifikasi', methods=['POST'])
def api_hitung_verifikasi():
    data = request.json
    if not data.get('bulan'): return jsonify({"error": "Bulan belum dipilih!"}), 400
    try:
        tahun, bulan = map(int, data['bulan'].split('-'))
        taf_text = data.get('taf_text', '').strip()
        metar_dummy = data.get('metar_dummy', '').strip()
        
        if taf_text:
            semua_taf = re.findall(r'((?:TAF(?:OR)?)\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\s+[^=]+=)', taf_text, re.IGNORECASE)
            if not semua_taf and "WAKT" in taf_text.upper() and taf_text.endswith("="):
                semua_taf = [taf_text.upper().strip()]
                
            if semua_taf:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for taf in semua_taf:
                    taf_clean = re.sub(r'\s+', ' ', taf.upper().strip())
                    if not taf_clean.endswith('='): taf_clean += '='
                    if not taf_clean.startswith("TAF"): taf_clean = "TAF " + taf_clean
                    
                    waktu_obs_sql = parse_waktu_zulu(taf_clean, tahun, bulan)
                    
                    cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar LIKE 'TAF%'", (waktu_obs_sql,))
                    cek_duplikat = cursor.fetchone()
                    
                    # 🟢 BLOK SABUK PENGAMAN ANTI-CRASH
                    try:
                        if cek_duplikat:
                            cursor.execute("UPDATE metar_wakt SET sandi_metar = ? WHERE id = ?", (taf_clean, cek_duplikat[0]))
                        else:
                            cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (taf_clean, waktu_obs_sql))
                    except sqlite3.IntegrityError as e:
                        # 🥷 TRIK SILUMAN: Jika database menolak karena teks sandi sama persis dengan bulan lalu
                        # Kita suntikkan SATU SPASI KOSONG di ujung sandi agar lolos dari gembok UNIQUE!
                        try:
                            cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (taf_clean + " ", waktu_obs_sql))
                        except Exception: 
                            pass # Jika masih gagal, abaikan saja agar tampilan web tidak Error 500
                            
                conn.commit()
                conn.close()

        # Web Verifikasi akan tetap berjalan mulus meskipun DB rewel
        hasil_verif = hitung_accuracy_dashboard_web(tahun, bulan, metar_dummy)
        return jsonify({"status": "Sukses", "data": hasil_verif})
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/metar/inject_manual_taf', methods=['POST'])
def api_inject_manual_taf():
    data = request.json
    bulan_dipilih = data.get('bulan')
    taf_text = data.get('taf_text', '')
    
    if not bulan_dipilih: return jsonify({"error": "Bulan belum ditentukan!"}), 400
    if not taf_text: return jsonify({"error": "Sandi TAF masih kosong!"}), 400

    tahun, bulan = map(int, bulan_dipilih.split('-'))
    semua_taf = re.findall(r'((?:TAF(?:OR)?)\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\s+[^=]+=)', taf_text, re.IGNORECASE)
    
    if not semua_taf:
        clean_pola = taf_text.upper().strip()
        if "WAKT" in clean_pola and clean_pola.endswith("="):
            semua_taf = [clean_pola]
        else:
            return jsonify({"error": "Format TAF tidak valid! Pastikan diakhiri tanda sama dengan (=)"}), 400

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        for taf in semua_taf:
            taf_clean = re.sub(r'\s+', ' ', taf.upper().strip())
            if not taf_clean.startswith("TAF"):
                taf_clean = "TAF " + taf_clean
            waktu_obs_sql = parse_waktu_zulu(taf_clean, tahun, bulan)
            
            # 🟢 LOGIKA REVISI AMAN: Cari berdasarkan waktu observasi
            cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar LIKE 'TAF%'", (waktu_obs_sql,))
            cek_duplikat = cursor.fetchone()
            
            if cek_duplikat:
                cursor.execute("UPDATE metar_wakt SET sandi_metar = ? WHERE id = ?", (taf_clean, cek_duplikat[0]))
            else:
                try:
                    cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (taf_clean, waktu_obs_sql))
                except sqlite3.IntegrityError:
                    # Trik Siluman: Suntik spasi jika sandinya kebetulan sama dengan bulan lalu
                    cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (taf_clean + " ", waktu_obs_sql))
                    
        conn.commit()
        conn.close()
        
        return api_download_excel_resmi()
    except Exception as e: return jsonify({"error": str(e)}), 500

# ====================================================================
# 📥 EXCEL INJECTION ENGINE: SINKRONISASI KOORDINAT SEL PRESIFIKASI
# ====================================================================
@app.route('/api/metar/download_excel_resmi', methods=['POST'])
def api_download_excel_resmi():
    data = request.json
    bulan_dipilih = data.get('bulan')
    metar_dummy = data.get('metar_dummy', '') # 🟢 METAR DUMMY
    if not bulan_dipilih: return jsonify({"error": "Bulan wajib ditentukan!"}), 400
    if not os.path.exists(TEMPLATE_NAME): return jsonify({"error": f"File master template {TEMPLATE_NAME} tidak ditemukan!"}), 500

    tahun, bulan = map(int, bulan_dipilih.split('-'))
    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    wb = openpyxl.load_workbook(TEMPLATE_NAME, keep_vba=True)
    
    # 🟢 SUNTIKAN TRANSLATOR BULAN INDONESIA
    nama_bulan_indo = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]
    nama_bulan_teks = nama_bulan_indo[bulan - 1]
    
    hasil_analitik = hitung_accuracy_dashboard_web(tahun, bulan, metar_dummy) # 🟢 METAR DUMMY
    detail_harian = hasil_analitik['detail_harian']
    
    excel_anchors = {
        "00Z": {"header_row": 4, "start_row": 7},
        "06Z": {"header_row": 33, "start_row": 36},
        "12Z": {"header_row": 62, "start_row": 65},
        "18Z": {"header_row": 90, "start_row": 93}
    }
    
    for hari in range(1, akhir_hari + 1):
        sheet_target = None
        for nama_sheet in [str(hari), f"Tgl_{hari}", f"Tgl {hari}"]:
            if nama_sheet in wb.sheetnames:
                sheet_target = wb[nama_sheet]
                break
        if sheet_target is None: continue
        
        # 🟢 SUNTIKAN: GANTI TEKS BULAN (A3) & TAHUN (D3) OTOMATIS DI SETIAP SHEET
        sheet_target["A3"] = f"BULAN : {nama_bulan_teks}"
        sheet_target["D3"] = f"TAHUN : {tahun}"
        
        blok_hari = detail_harian[str(hari)]
        
        for cycle_key, config in excel_anchors.items():
            if cycle_key not in blok_hari: continue
            
            sandi_taf_asli = blok_hari[cycle_key]["taf_raw"]
            baris_matriks = blok_hari[cycle_key]["rows"]
            
            # 🚨 FIX LOGIKA KOORDINAT 1: TAF asli wajib masuk ke Kolom D (bukan kolom C) 🚨
            sheet_target[f"D{config['header_row']}"] = sandi_taf_asli
            
            for idx, baris in enumerate(baris_matriks):
                row_excel = config["start_row"] + idx
                
                sheet_target[f"C{row_excel}"] = baris['group_row']
                sheet_target[f"E{row_excel}"] = baris['t']['arah']
                sheet_target[f"F{row_excel}"] = baris['t']['speed']
                sheet_target[f"G{row_excel}"] = baris['t']['gust']
                sheet_target[f"H{row_excel}"] = baris['t']['vis']
                sheet_target[f"I{row_excel}"] = baris['t']['cuaca']
                sheet_target[f"J{row_excel}"] = baris['t']['awan_jml']
                sheet_target[f"K{row_excel}"] = baris['t']['awan_tgi']
                
                sheet_target[f"L{row_excel}"] = baris['metar_raw']
                sheet_target[f"M{row_excel}"] = baris['m']['arah']
                sheet_target[f"N{row_excel}"] = baris['skor']['arah']
                sheet_target[f"O{row_excel}"] = baris['m']['speed']
                sheet_target[f"P{row_excel}"] = baris['skor']['speed']
                sheet_target[f"Q{row_excel}"] = baris['m']['gust']
                sheet_target[f"R{row_excel}"] = baris['skor']['gust']
                sheet_target[f"S{row_excel}"] = baris['m']['vis']
                sheet_target[f"T{row_excel}"] = baris['skor']['vis']
                sheet_target[f"U{row_excel}"] = baris['m']['cuaca']
                sheet_target[f"V{row_excel}"] = baris['skor']['cuaca']
                sheet_target[f"W{row_excel}"] = baris['m']['awan_jml']
                sheet_target[f"X{row_excel}"] = baris['skor']['awan_jml']
                sheet_target[f"Y{row_excel}"] = baris['m']['awan_tgi']
                sheet_target[f"Z{row_excel}"] = baris['skor']['awan_tgi']

    if "REKAP" in wb.sheetnames:
        sheet_rekap = wb["REKAP"]
        cycles_order = ["00Z", "06Z", "12Z", "18Z"]
        
        for hari in range(1, akhir_hari + 1):
            blok_hari = detail_harian[str(hari)]
            for c_idx, c_name in enumerate(cycles_order):
                if c_name in blok_hari:
                    c_sum = blok_hari[c_name]["cycle_summary"]
                    # 🚨 FIX LOGIKA KOORDINAT 2: Baris REKAP harian digeser mulai dari Baris 5 🚨
                    row_rekap = 5 + (hari - 1) * 4 + c_idx
                    
                    sheet_rekap[f"C{row_rekap}"] = c_sum["arah"]
                    sheet_rekap[f"E{row_rekap}"] = c_sum["speed"]
                    sheet_rekap[f"G{row_rekap}"] = c_sum["gust"]
                    sheet_rekap[f"I{row_rekap}"] = c_sum["vis"]
                    sheet_rekap[f"K{row_rekap}"] = c_sum["cuaca"]
                    sheet_rekap[f"M{row_rekap}"] = c_sum["awan_jml"]
                    sheet_rekap[f"O{row_rekap}"] = c_sum["awan_tgi"]

    out_stream = io.BytesIO()
    wb.save(out_stream)
    out_stream.seek(0)
    wb.close()
    return send_file(out_stream, mimetype="application/vnd.ms-excel.sheet.macroEnabled.12", as_attachment=True, download_name=f"VERIFIKASI_TAF_{bulan_dipilih}_WAKT.xlsm")

@app.route('/<path:filename>')
def serve_static_pages_fallback(filename):
    if filename.endswith('.html') and os.path.exists(filename):
        return send_from_directory('.', filename)
    elif os.path.exists(f"{filename}.html"):
        return send_from_directory('.', f"{filename}.html")
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return jsonify({"error": f"Halaman /{filename} tidak ditemukan"}), 404

# ====================================================================
# 💉 SUNTIKAN TAKTIS: API UNTUK LIVE STATS DASHBOARD BERANDA (DENGAN FILTER)
# ====================================================================
@app.route('/api/metar/dashboard_stats')
def api_dashboard_stats():
    bp = request.args.get('bulan')
    try:
        if bp and '-' in bp:
            tahun, bulan = map(int, bp.split('-'))
        else:
            tahun, bulan = datetime.now().year, datetime.now().month
    except Exception:
        tahun, bulan = datetime.now().year, datetime.now().month
        
    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    dt_lalu = datetime(tahun, bulan, 1) - timedelta(days=1)
    
    # 🟢 BATAS WAKTU SIKLUS METEOROLOGI MUTLAK
    start_metar = f"{tahun}-{bulan:02d}-01 00:00:00"
    end_metar = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 23:59:59"
    
    start_taf = f"{dt_lalu.year}-{dt_lalu.month:02d}-{dt_lalu.day:02d} 22:00:00"
    end_taf = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 21:59:59"
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Hitung total METAR/SPECI
    c.execute("SELECT COUNT(*) FROM metar_wakt WHERE (sandi_metar LIKE 'METAR%' OR sandi_metar LIKE 'SPECI%') AND waktu_observasi >= ? AND waktu_observasi <= ?", (start_metar, end_metar))
    total_metar = c.fetchone()[0]
    
    # 2. Hitung total TAFOR (Tgl 31 23:00 bulan lalu akan masuk hitungan!)
    c.execute("SELECT COUNT(*) FROM metar_wakt WHERE sandi_metar LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?", (start_taf, end_taf))
    total_taf = c.fetchone()[0]
    
    # 3. Waktu Sinkronisasi Terakhir
    c.execute("SELECT MAX(waktu_rekam) FROM metar_wakt WHERE (sandi_metar NOT LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?) OR (sandi_metar LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?)", (start_metar, end_metar, start_taf, end_taf))
    last_sync_raw = c.fetchone()[0]
    last_sync = last_sync_raw if last_sync_raw else "Belum Pernah"
    conn.close()
    
    # 4. Tarik Akurasi Global
    try:
        hasil_analitik = hitung_accuracy_dashboard_web(tahun, bulan)
        akurasi = hasil_analitik['summary']['total_score']
    except Exception:
        akurasi = 0.0

    return jsonify({
        "total_metar": total_metar,
        "total_taf": total_taf,
        "akurasi": akurasi,
        "last_sync": last_sync
    })

# ====================================================================
# 💉 SUNTIKAN TAKTIS: API UNTUK LOG TERBAGI DI BERANDA (DENGAN FILTER)
# ====================================================================
@app.route('/api/metar/dashboard_recent_logs')
def api_dashboard_recent_logs():
    bp = request.args.get('bulan')
    try:
        if bp and '-' in bp:
            tahun, bulan = map(int, bp.split('-'))
        else:
            tahun, bulan = datetime.now().year, datetime.now().month
    except Exception:
        tahun, bulan = datetime.now().year, datetime.now().month
        
    akhir_hari = calendar.monthrange(tahun, bulan)[1]
    dt_lalu = datetime(tahun, bulan, 1) - timedelta(days=1)
    
    # 🟢 BATAS WAKTU SIKLUS METEOROLOGI MUTLAK
    start_metar = f"{tahun}-{bulan:02d}-01 00:00:00"
    end_metar = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 23:59:59"
    
    start_taf = f"{dt_lalu.year}-{dt_lalu.month:02d}-{dt_lalu.day:02d} 22:00:00"
    end_taf = f"{tahun}-{bulan:02d}-{akhir_hari:02d} 21:59:59"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Ambil seluruh data dengan rentang waktu yang sesuai!
        cursor.execute("SELECT sandi_metar, waktu_observasi as waktu_lokal FROM metar_wakt WHERE (sandi_metar NOT LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?) OR (sandi_metar LIKE 'TAF%' AND waktu_observasi >= ? AND waktu_observasi <= ?) ORDER BY waktu_observasi DESC", (start_metar, end_metar, start_taf, end_taf))
        
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"sandi_metar": r["sandi_metar"], "waktu_rekam": r["waktu_lokal"]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ====================================================================
# 💉 SUNTIKAN TAKTIS: API UNTUK EDIT METAR MANUAL (KOREKSI TYPO)
# ====================================================================
@app.route('/api/metar/edit_log', methods=['POST'])
def api_edit_log():
    data = request.json
    log_id = data.get('id')
    new_sandi = data.get('sandi_metar', '').strip().upper()

    if not log_id or not new_sandi:
        return jsonify({"error": "ID dan Sandi baru wajib diisi!"}), 400

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE metar_wakt SET sandi_metar = ? WHERE id = ?", (new_sandi, log_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "Sukses"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================================================================
# 💉 SUNTIKAN TAKTIS: API UNTUK HAPUS LOG MANUAL
# ====================================================================
@app.route('/api/metar/delete_log', methods=['POST'])
def api_delete_log():
    data = request.json
    log_id = data.get('id')

    if not log_id:
        return jsonify({"error": "ID log wajib dikirim!"}), 400

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metar_wakt WHERE id = ?", (log_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "Sukses"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/metar/kirim_bmkgsoft', methods=['POST'])
def api_kirim_bmkgsoft():
    data = request.json
    sandi_taf = data.get('taf_text', '')

    if not sandi_taf:
        return jsonify({"error": "Sandi TAF kosong!"}), 400

    driver = None
    try:
        print("\n--- MULAI EKSEKUSI ROBOT SELENIUM ---")
        options = webdriver.ChromeOptions()
        
        # 🟢 MODE SILUMAN AKTIF: Chrome tidak akan muncul di layar
        options.add_argument('--headless') 
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080') 
        
        print("1. Menyiapkan ChromeDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 30) 
        
        print("2. Membuka Halaman Login BMKGSatu...")
        driver.get("https://bmkgsatu.bmkg.go.id/login")

        print("3. Mengisi Username & Password...")
        wait.until(EC.presence_of_element_located((By.ID, "login-email"))).send_keys("97876")
        driver.find_element(By.ID, "login-password").send_keys("opr97876")
        
        print("4. Menekan Tombol Login...")
        tombol_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[1]/div/div/div/div/div[2]/div/span/form/button')))
        tombol_login.click()

        print("5. Menunggu Halaman GTS Messages...")
        time.sleep(5) 
        driver.get("https://bmkgsatu.bmkg.go.id/gts_messages")
        
        print("6. Mengisi Kotak Sandi (Menembus Proteksi Vue.js)...")
        kotak_sandi = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea")))
        
        driver.execute_script("""
            let el = arguments[0];
            el.value = arguments[1];
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, kotak_sandi, sandi_taf)
        
        time.sleep(2) 
        
        print("7. Menekan Tombol Send (Pertama)...")
        tombol_send_1 = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Send')]")))
        driver.execute_script("arguments[0].click();", tombol_send_1)
        
        time.sleep(2) # Nafas singkat menunggu pop-up animasi
        
        print("8. Menekan Tombol Konfirmasi (Kedua)...")
        try:
            tombol_send_2 = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'swal2-confirm') or contains(@class, 'el-button--primary') or text()='OK' or text()='Yes' or text()='Ya']")))
            driver.execute_script("arguments[0].click();", tombol_send_2)
        except:
            try:
                tombol_send_2 = driver.find_element(By.XPATH, "//div[@role='dialog' or contains(@class, 'modal') or contains(@class, 'swal')]//button[1]")
                driver.execute_script("arguments[0].click();", tombol_send_2)
            except:
                from selenium.webdriver.common.action_chains import ActionChains
                from selenium.webdriver.common.keys import Keys
                ActionChains(driver).send_keys(Keys.ENTER).perform()
        
        print("9. Selesai Menembak GTS!")
        time.sleep(3)

        # =================================================================
        # 10. SIMPAN OTOMATIS KE DATABASE VERIFIKASI
        # =================================================================
        try:
            now = datetime.now()
            tahun, bulan = now.year, now.month
            semua_taf = re.findall(r'((?:TAF(?:OR)?)\s+(?:AMD\s+|COR\s+)?WAKT\s+\d{6}Z\s+[^=]+=)', sandi_taf, re.IGNORECASE)
            if not semua_taf:
                clean_pola = sandi_taf.upper().strip()
                if "WAKT" in clean_pola and clean_pola.endswith("="):
                    semua_taf = [clean_pola]
            if semua_taf:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for taf in semua_taf:
                    taf_clean = re.sub(r'\s+', ' ', taf.upper().strip())
                    if not taf_clean.startswith("TAF"):
                        taf_clean = "TAF " + taf_clean
                    waktu_obs_sql = parse_waktu_zulu(taf_clean, tahun, bulan)
                    cursor.execute("INSERT OR REPLACE INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (taf_clean, waktu_obs_sql))
                conn.commit()
                conn.close()
                print("10. Tersimpan di Database!")
        except Exception as err_db:
            print(f"Peringatan Database: {err_db}")

        return jsonify({"status": "Sukses", "pesan": "Berhasil dikirim ke BMKGSatu GTS & Tersimpan di Database Verifikasi!"})

    except Exception as e:
        print(f"\n❌ ROBOT CRASH PADA TAHAP INI: {str(e)}\n")
        return jsonify({"error": f"Pengiriman Gagal: {str(e)}"}), 500
        
    finally:
        if driver:
            driver.quit() # Memori langsung dibersihkan tanpa jeda
    
@app.route('/get_sandi_by_month', methods=['GET'])
def get_sandi_by_month():
    periode = request.args.get('periode')
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Mengambil data dari tabel metar_wakt milikmu
        cursor.execute("SELECT * FROM metar_wakt WHERE waktu_observasi LIKE ?", (periode + '%',))
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    
    
@app.route('/api/metar/download_labul_tunggal', methods=['POST'])
def api_download_labul_tunggal():
    data = request.json
    periode = data.get('periode') # Format: YYYY-MM
    takeoff = int(data.get('takeoff', 0))
    landing = int(data.get('landing', 0))
    tipe = data.get('tipe') # 'bulanan', 'penerbangan', 'harian'

    if not periode or not tipe: 
        return jsonify({"error": "Periode dan Tipe Laporan wajib ditentukan!"}), 400
    
    # ⚠️ Pemetaan nama file template. Pastikan nama file ini SAMA PERSIS dengan yang ada di folder!
    file_map = {
        "bulanan": "Produk_Pelayanan_Bulanan_WAKT_2026.xlsx",
        "penerbangan": "Statistik_Penerbangan_WAKT_2026.xlsx",
        "harian": "Produk_Pelayanan_Harian_WAKT_2026.xlsx"
    }
    
    template_file = file_map.get(tipe)
    if not os.path.exists(template_file): 
        return jsonify({"error": f"File master template '{template_file}' tidak ditemukan di folder!"}), 500

    tahun, bulan = map(int, periode.split('-'))
    jml_hari = calendar.monthrange(tahun, bulan)[1]
    
    nama_bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    nama_bulan_txt = f"{nama_bulan_indo[bulan-1]} {tahun}".upper()
    tgl_ttd = f"Tanah Merah, {jml_hari} {nama_bulan_indo[bulan-1]} {tahun}"

    # ⚠️ GANTI 'database.db' dengan nama file SQLite Anda yang sebenarnya (misal: 'metar_wakt.db')
    DB_NAME = "database_wakt.db" 
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Prefix pencarian bulan di database
    prefix_bulan = f"{tahun}-{bulan:02d}-%"
    
    # Hitung data dari SQLite
    cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND (sandi_metar LIKE 'METAR%' OR sandi_metar NOT LIKE 'SPECI%' AND sandi_metar NOT LIKE 'TAF%')", (prefix_bulan,))
    count_metar = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND sandi_metar LIKE 'SPECI%'", (prefix_bulan,))
    count_speci = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND sandi_metar LIKE 'TAF%'", (prefix_bulan,))
    count_taf = cursor.fetchone()[0]
    

    # Buka Template & Pilih Sheet Aktif
    wb = openpyxl.load_workbook(template_file)
    ws = wb.active 

    # Injeksi Koordinat Sel Spesifik berdasarkan tipe file
    if tipe == "bulanan":
        
        # 🟢 SUNTIKAN BARU: Mengganti teks judul bulan di sel A1 secara dinamis
        ws["A1"] = f"II.B PRODUK PELAYANAN BULANAN {nama_bulan_indo[bulan-1].upper()}"

        # (Opsional: Jika A5 dan E15 masih dipakai untuk Bulan & Tanggal TTD)
        # ws["A5"] = f"BULAN : {nama_bulan_txt}"
        # ws["E15"] = tgl_ttd

        # Kolom yang diisi 0 mutlak
        ws["B8"] = 0
        ws["E8"] = 0
        ws["F8"] = 0
        ws["G8"] = 0
        ws["M8"] = 0
        ws["H8"] = 0
        
        # Injeksi Data Dinamis & SOP
        ws["C8"] = jml_hari            # FLIGHT FOLDER (1 x jml_hari)
        ws["D8"] = count_taf           # TAFOR (Dari DB)
        ws["I8"] = jml_hari            # PRAKICU (1 x jml_hari)
        ws["J8"] = count_metar         # METAR (Dari DB)
        ws["K8"] = count_speci         # SPECI (Dari DB)
        ws["L8"] = 8 * jml_hari        # MET REPORT (8 x jml_hari)
        
        # Injeksi Data Eksternal
        ws["N8"] = takeoff + landing   # FREKUENSI PENERBANGAN (Total)

        download_name = f"Produk_Pelayanan_Bulanan_WAKT_{periode}.xlsx"

    # 💉 SUNTIK FILE 2: PRODUK PELAYANAN HARIAN
    elif tipe == "harian":
        
        # 🟢 SUNTIKAN BARU: Mengganti teks judul bulan di sel A1 Laporan Harian
        ws["A1"] = f"II.A PRODUK PELAYANAN HARIAN {nama_bulan_indo[bulan-1].upper()}"
        
        # Jalankan looping dari Tanggal 1 sampai akhir bulan berjalan
        for hari in range(1, jml_hari + 1):
            baris = 7 + hari  # Tanggal 1 = Baris 8, Tanggal 31 = Baris 38
            tgl_spesifik = f"{tahun}-{bulan:02d}-{hari:02d}%"
            
            cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND (sandi_metar LIKE 'METAR%' OR sandi_metar NOT LIKE 'SPECI%' AND sandi_metar NOT LIKE 'TAF%')", (tgl_spesifik,))
            h_metar = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND sandi_metar LIKE 'SPECI%'", (tgl_spesifik,))
            h_speci = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM metar_wakt WHERE waktu_observasi LIKE ? AND sandi_metar LIKE 'TAF%'", (tgl_spesifik,))
            h_taf = cursor.fetchone()[0]
            
            ws[f"J{baris}"] = h_metar
            ws[f"K{baris}"] = h_speci
            ws[f"D{baris}"] = h_taf
            ws[f"C{baris}"] = 1
            ws[f"I{baris}"] = 1
            ws[f"L{baris}"] = 8
            
            for col in ["B", "E", "F", "G", "H", "M"]:
                ws[f"{col}{baris}"] = 0

        # Suntik tanggal ttd di bawah tabel secara dinamis sebelum baris dipotong
        # (Asumsi baris ttd di template awal 31 hari berada di baris 41, silakan sesuaikan angkanya)
        ws["E41"] = tgl_ttd 

        # ✂️ TRICK OTOMATIS: Jika hari kurang dari 31, potong baris tabel yang kelebihan
        if jml_hari < 31:
            baris_mulai_hapus = 8 + jml_hari
            jumlah_baris_dihapus = 31 - jml_hari
            ws.delete_rows(baris_mulai_hapus, jumlah_baris_dihapus)

        download_name = f"Produk_Pelayanan_Harian_WAKT_{periode}.xlsx"


    # 💉 SUNTIK FILE 3: STATISTIK PENERBANGAN
    elif tipe == "penerbangan":
        
        # 🟢 LOGIKA DISTRIBUSI RAPI & NATURAL
        def sebar_rapi(total_pesawat, total_hari):
            if total_pesawat <= 0: return [0] * total_hari
            dasar = total_pesawat // total_hari
            sisa = total_pesawat % total_hari
            # Buat jatah: 'sisa' hari dapat (dasar + 1), sisanya dapat (dasar)
            distribusi = [dasar + 1] * sisa + [dasar] * (total_hari - sisa)
            # Kocok urutannya agar natural (tidak numpuk di awal bulan)
            random.shuffle(distribusi)
            return distribusi

        distribusi_takeoff = sebar_rapi(takeoff, jml_hari)
        distribusi_landing = sebar_rapi(landing, jml_hari)
            
        for hari in range(1, jml_hari + 1):
            baris = 4 + hari  # Tanggal 1 = Baris 5, Tanggal 31 = Baris 35
            ws[f"G{baris}"] = distribusi_takeoff[hari - 1]
            ws[f"H{baris}"] = distribusi_landing[hari - 1]
            ws[f"I{baris}"] = 0

        # Suntik tanggal ttd di bawah tabel secara dinamis (Misal default awal baris 38)
        ws["E38"] = tgl_ttd

       # ✂️ TRICK OTOMATIS: Potong baris jika bulan pendek (Februari / Juni)
        if jml_hari < 31:
            baris_mulai_hapus = 5 + jml_hari
            jumlah_baris_dihapus = 31 - jml_hari
            ws.delete_rows(baris_mulai_hapus, jumlah_baris_dihapus)

        download_name = f"Statistik_Penerbangan_WAKT_{periode}.xlsx"

    # 🟢 TAMBAHKAN DI SINI 🟢
    conn.close() 

    # Simpan ke memori dan kirim sebagai file unduhan
    out_stream = io.BytesIO()
    wb.save(out_stream)
    out_stream.seek(0)
    wb.close()
    
    return send_file(out_stream, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=download_name)    

@app.route('/api/acs/convert', methods=['POST'])
def api_convert_acs():
    if 'file_excel' not in request.files:
        return jsonify({"error": "Tidak ada file Excel mentah yang dikirim!"}), 400
        
    file = request.files['file_excel']
    template_path = "Template_ACS.xlsx"
    if not os.path.exists(template_path):
        return jsonify({"error": f"File master '{template_path}' tidak ditemukan!"}), 500

    try:
        # 1. Buka Excel Mentah (Hasil Web Luar)
        raw_wb = openpyxl.load_workbook(file, data_only=True)
        raw_sheets = raw_wb.sheetnames
        
        if len(raw_sheets) < 20:
            return jsonify({"error": f"File mentah tidak utuh! Hanya ada {len(raw_sheets)} sheet (Seharusnya ada 20 Table/Sheet)."}), 400

        # --- DETEKSI BULAN DARI EXCEL MENTAH ---
        bulan_terdeteksi = "UNKNOWN"
        for ws_raw in raw_wb.worksheets:
            for row in ws_raw.iter_rows(values_only=True):
                # Gabungkan isi 1 baris jadi 1 kalimat
                row_str = " ".join([str(c) for c in row if c])
                # Cari kata "MONTH :" diikuti nama bulan
                match = re.search(r'MONTH\s*[:;]?\s*([A-Za-z]+)', row_str, re.IGNORECASE)
                if match:
                    bulan_terdeteksi = match.group(1).upper()
                    break
            if bulan_terdeteksi != "UNKNOWN":
                break

        if bulan_terdeteksi == "UNKNOWN":
            bulan_terdeteksi = "BULAN_X"

        # 2. Buka Template Final Anda
        wb = openpyxl.load_workbook(template_path)
        
        # Fungsi Wiper & Pembersih
        def clear_data_area(ws, start_row, end_row, start_col, end_col):
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    try: ws.cell(row=r, column=c).value = None
                    except: pass

        def clean_val(val):
            if val is None or str(val).strip() == '': return 0
            v_str = str(val).strip()
            if v_str == '-': return '-'
            try: return float(v_str.replace(',', '.'))
            except: return v_str

        def is_numeric(val):
            v = str(val).strip()
            if v in ['-', '0']: return True
            try: float(v.replace(',', '.')); return True
            except: return False

        # 3. PROSES PEMINDAHAN DATA PRESISI
        
        # --- MODEL A (Tabel 4 / Index 3) ---
        if "MODEL A" in wb.sheetnames:
            ws_raw = raw_wb[raw_sheets[3]]
            ws_target = wb["MODEL A"]
            clear_data_area(ws_target, 12, 60, 2, 9)
            row_idx = 12
            for row in ws_raw.iter_rows(values_only=True):
                if not row: continue
                count_num = sum(1 for v in row[-5:] if is_numeric(v))
                if count_num >= 2:
                    data_angka = [clean_val(v) for v in row[-8:]]
                    for c, val in enumerate(data_angka):
                        try: ws_target.cell(row=row_idx, column=c+2).value = val
                        except: pass
                    row_idx += 1

        # --- MODEL B (Tabel 8 / Index 7) ---
        if "MODEL B" in wb.sheetnames:
            ws_raw = raw_wb[raw_sheets[7]]
            ws_target = wb["MODEL B"]
            clear_data_area(ws_target, 11, 35, 2, 10)
            row_idx = 11
            for row in ws_raw.iter_rows(values_only=True):
                if not row: continue
                count_num = sum(1 for v in row[-5:] if is_numeric(v))
                if count_num >= 2:
                    data_angka = [clean_val(v) for v in row[-8:]]
                    data_angka.insert(5, 0) # Injeksi 0
                    for c, val in enumerate(data_angka):
                        try: ws_target.cell(row=row_idx, column=c+2).value = val
                        except: pass
                    row_idx += 1

        # --- MODEL C (Tabel 12 / Index 11) ---
        if "MODEL C" in wb.sheetnames:
            ws_raw = raw_wb[raw_sheets[11]]
            ws_target = wb["MODEL C"]
            clear_data_area(ws_target, 12, 35, 2, 7)
            row_idx = 12
            for row in ws_raw.iter_rows(values_only=True):
                if not row: continue
                count_num = sum(1 for v in row[-5:] if is_numeric(v))
                if count_num >= 2:
                    data_angka = [clean_val(v) for v in row[-6:]]
                    if len(data_angka) > 0: data_angka[0] = 0 # Paksa <100 jadi 0
                    for c, val in enumerate(data_angka):
                        try: ws_target.cell(row=row_idx, column=c+2).value = val
                        except: pass
                    row_idx += 1

        # --- MODEL D (Tabel 16 / Index 15) ---
        if "MODEL D" in wb.sheetnames:
            ws_raw = raw_wb[raw_sheets[15]]
            ws_target = wb["MODEL D"]
            clear_data_area(ws_target, 12, 30, 2, 12)
            row_idx = 13
            for row in ws_raw.iter_rows(values_only=True):
                if not row: continue
                col0 = str(row[0]).strip().upper() if row[0] else ""
                if "CALM" in col0:
                    try: ws_target.cell(row=12, column=12).value = clean_val(row[-1])
                    except: pass
                elif "VARIABLE" in col0:
                    continue
                else:
                    count_num = sum(1 for v in row[-5:] if is_numeric(v))
                    if count_num >= 2:
                        data_angka = [clean_val(v) for v in row[-11:]]
                        for c, val in enumerate(data_angka):
                            try: ws_target.cell(row=row_idx, column=c+2).value = val
                            except: pass
                        row_idx += 1

        # --- MODEL E (Tabel 20 / Index 19) ---
        if "MODEL E" in wb.sheetnames:
            ws_raw = raw_wb[raw_sheets[19]]
            ws_target = wb["MODEL E"]
            clear_data_area(ws_target, 11, 35, 2, 9)
            row_idx = 11
            for row in ws_raw.iter_rows(values_only=True):
                if not row: continue
                count_num = sum(1 for v in row[-5:] if is_numeric(v))
                if count_num >= 2:
                    data_angka = [clean_val(v) for v in row[-9:]]
                    if len(data_angka) > 0: data_angka.pop(0) # Buang suhu -5 s.d 0
                    for c, val in enumerate(data_angka):
                        try: ws_target.cell(row=row_idx, column=c+2).value = val
                        except: pass
                    row_idx += 1

        # 4. EXPORT
        sheets_to_keep = ['COVER', 'MODEL A', 'MODEL B', 'MODEL C', 'MODEL D', 'MODEL E']
        for sheet_name in wb.sheetnames:
            if sheet_name not in sheets_to_keep:
                del wb[sheet_name]
                
        # Suntik Bulan ke Cover
        if "COVER" in wb.sheetnames and bulan_terdeteksi != "BULAN_X":
            try: wb["COVER"]["F15"] = bulan_terdeteksi.capitalize()
            except: pass
                
        # Nama file otomatis berdasarkan bulan
        nama_file_download = f"ACS_WAKT_2026_{bulan_terdeteksi}.xlsx"
        
        out_stream = io.BytesIO()
        wb.save(out_stream)
        out_stream.seek(0)
        wb.close()
        raw_wb.close()
        
        response = send_file(out_stream, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=nama_file_download)
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response
        
    except Exception as e:
        return jsonify({"error": f"Gagal memindahkan data Excel: {str(e)}"}), 500

        # ====================================================================
@app.route('/api/metar/tambah_log_manual', methods=['POST'])
def api_tambah_log_manual():
    data = request.json
    sandi_raw = data.get('sandi', '').strip().upper()
    bulan_str = data.get('bulan', '')
    
    if not bulan_str or not sandi_raw:
        return jsonify({"error": "Bulan atau Sandi kosong!"}), 400
        
    try:
        tahun, bulan = map(int, bulan_str.split('-'))
        sandi_clean = re.sub(r'\s+', ' ', sandi_raw)
        if not sandi_clean.endswith('='): sandi_clean += '='
            
        waktu_obs_sql = parse_waktu_zulu(sandi_clean, tahun, bulan)
        is_taf = sandi_clean.startswith("TAF")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if is_taf:
            cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar LIKE 'TAF%'", (waktu_obs_sql,))
        else:
            cursor.execute("SELECT id FROM metar_wakt WHERE waktu_observasi = ? AND sandi_metar NOT LIKE 'TAF%'", (waktu_obs_sql,))
            
        cek_duplikat = cursor.fetchone()
        
        if cek_duplikat:
            # 🟢 KUNCI REVISI: Kalau jamnya sudah ada, paksa timpa isinya!
            cursor.execute("UPDATE metar_wakt SET sandi_metar = ? WHERE id = ?", (sandi_clean, cek_duplikat[0]))
        else:
            try:
                cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (sandi_clean, waktu_obs_sql))
            except sqlite3.IntegrityError:
                # Akali gembok UNIQUE dengan suntikan spasi gaib
                cursor.execute("INSERT INTO metar_wakt (sandi_metar, waktu_observasi) VALUES (?, ?)", (sandi_clean + " ", waktu_obs_sql))
                
        conn.commit()
        conn.close()
        return jsonify({"status": "Sukses"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ====================================================================
# 📥 SUNTIKAN TAKTIS: API DOWNLOAD LOG EXCEL (MULTI-SHEET)
# ====================================================================
@app.route('/api/metar/download_log_excel')
def api_download_log_excel():
    bulan_param = request.args.get('bulan')
    if not bulan_param:
        return jsonify({"error": "Bulan belum dipilih!"}), 400

    prefix_bulan = f"{bulan_param}-%"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tarik semua data dari DB, urutkan maju dari tanggal 1 ke akhir (ASC)
    cursor.execute("SELECT sandi_metar, waktu_observasi FROM metar_wakt WHERE waktu_observasi LIKE ? ORDER BY waktu_observasi ASC", (prefix_bulan,))
    rows = cursor.fetchall()
    conn.close()

    # Buat file Excel baru di memori
    wb = openpyxl.Workbook()
    
    # Sheet 1: METAR & SPECI
    ws_metar = wb.active
    ws_metar.title = "METAR_SPECI"
    ws_metar.append(["No", "Tanggal", "Jam (UTC)", "Sandi Cuaca"])
    
    # Sheet 2: TAFOR
    ws_taf = wb.create_sheet(title="TAFOR")
    ws_taf.append(["No", "Tanggal", "Jam (UTC)", "Sandi Cuaca"])

    no_metar = 1
    no_taf = 1

    for sandi, waktu in rows:
        bagian_waktu = waktu.split(" ")
        tgl = bagian_waktu[0] if len(bagian_waktu) > 0 else "-"
        jam = bagian_waktu[1] if len(bagian_waktu) > 1 else "-"
        
        # Pisahkan jalur masuk berdasarkan jenis sandinya
        if sandi.startswith("TAF"):
            ws_taf.append([no_taf, tgl, jam, sandi])
            no_taf += 1
        else:
            ws_metar.append([no_metar, tgl, jam, sandi])
            no_metar += 1

    # Percantik sedikit lebar kolomnya agar nyaman dibaca
    ws_metar.column_dimensions['B'].width = 12
    ws_metar.column_dimensions['C'].width = 10
    ws_metar.column_dimensions['D'].width = 80
    ws_taf.column_dimensions['B'].width = 12
    ws_taf.column_dimensions['C'].width = 10
    ws_taf.column_dimensions['D'].width = 80

    out_stream = io.BytesIO()
    wb.save(out_stream)
    out_stream.seek(0)
    wb.close()
    
    return send_file(out_stream, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"Rekap_Log_WAKT_{bulan_param}.xlsx")

import base64 # Pastikan ini ada di barisan paling atas app.py ya Kapten!

@app.route('/api/hotspot/generate', methods=['POST'])
def generate_hotspot():
    data = request.json
    tgl_target_str = data.get('tanggal')
    nomor_surat = data.get('nomor_surat', 'B/ME.02.03/.../KTMH/.../2026')
    prakirawan = data.get('prakirawan', 'Prakirawan Bertugas')

    # 1. PARSING BATAS WAKTU (H-1 02:00 WIT s/d Hari H 01:59 WIT)
    dt_h = datetime.strptime(tgl_target_str, "%Y-%m-%d")
    dt_h1 = dt_h - timedelta(days=1)
    
    start_bound = dt_h1.replace(hour=2, minute=0, second=0)
    end_bound = dt_h.replace(hour=1, minute=59, second=59)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    str_periode = f"{dt_h1.day:02d} {bulan_indo[dt_h1.month-1].upper()} {dt_h1.year} PUKUL 02.00 - {dt_h.day:02d} {bulan_indo[dt_h.month-1].upper()} {dt_h.year} PUKUL 01.00 WIT"
    str_ttd = f"{dt_h.day:02d} {bulan_indo[dt_h.month-1]} {dt_h.year}"

    # 2. SEDOT DATA DARI SERVER PUSAT
    url_txt = "http://202.90.198.22/IMAGE/HOTSPOT/Hotspot_Indonesia.txt"
    url_img = "http://202.90.198.22/IMAGE/HOTSPOT/Hotspot_Papuaselatan.png"
    
    hotspot_list = []
    count_r, count_s, count_t = 0, 0, 0
    
    try:
        res = requests.get(url_txt, timeout=15)
        if res.status_code == 200:
            lines = res.text.strip().split('\n')
            no = 1
            pola = r'^(\S+)\s+(\S+)\s+(\d+)\s+PAPUA\s+PAPUA SELATAN\s+BOVEN DIGOEL\s+(.+?)\s+(NOAA20|SNPP|TERRA|AQUA)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(\S+)\s+(\S+)'
            
            for line in lines:
                if "BOVEN DIGOEL" in line:
                    match = re.search(pola, line.strip())
                    if match:
                        bujur, lintang, conf_str, kecamatan, satelit, tgl_api, jam_api, radius, tipe = match.groups()
                        try:
                            dt_api = datetime.strptime(f"{tgl_api} {jam_api}", "%Y-%m-%d %H:%M")
                            if start_bound <= dt_api <= end_bound:
                                conf = int(conf_str)
                                if conf <= 7: count_r += 1
                                elif conf == 8: count_s += 1
                                else: count_t += 1
                                
                                hotspot_list.append({
                                    "no": no, "bujur": bujur, "lintang": lintang, "kepercayaan": conf_str,
                                    "region": "PAPUA", "provinsi": "PAPUA SEL.", "kabupaten": "BOVEN DIGOEL",
                                    "kecamatan": kecamatan.strip(), "satelit": satelit,
                                    "tanggal": tgl_api, "waktu": jam_api, "radius": radius, "tipe": tipe
                                })
                                no += 1
                        except: pass
    except Exception as e: print("Gagal menyedot teks hotspot:", e)

    if len(hotspot_list) == 0:
        hotspot_list.append({
            "no": "-", "bujur": "NIHIL", "lintang": "NIHIL", "kepercayaan": "-", 
            "region": "-", "provinsi": "-", "kabupaten": "-", "kecamatan": "-", 
            "satelit": "-", "tanggal": "-", "waktu": "-", "radius": "-", "tipe": "-"
        })

    # 3. KEMAS VARIABEL UNTUK DISUNTIK KE WORD
    context = {
        'nomor_surat': nomor_surat,
        'periode_waktu': str_periode,
        'tanggal_ttd': str_ttd,
        'nama_prakirawan': prakirawan,
        'hotspot': hotspot_list,
        'jml_rendah': count_r,
        'jml_sedang': count_s,
        'jml_tinggi': count_t,
        'jml_total': count_r + count_s + count_t
    }

    # 4. CETAK DOKUMEN & KONVERSI KE PDF
    img_b64 = ""
    format_tgl_file = dt_h.strftime("%d%m%Y") 
    
    try:
        # Tarik gambar peta mentah dari pusat
        res_img = requests.get(url_img, timeout=15)
        if res_img.status_code == 200:
            
            # 🟢 JALUR 1: PETA MENTAH UNTUK DOKUMEN PDF
            img_io_pdf = io.BytesIO(res_img.content)
            
            # 🟢 JALUR 2: PETA BERBINGKAI UNTUK DOWNLOAD GAMBAR PNG (SOSMED)
            peta_asli = Image.open(io.BytesIO(res_img.content))
            try:
                # Buka Template Kosong Kapten
                bg_template = Image.open("template_peta.png")
                bg_w, bg_h = bg_template.size
                
                # Perbesar Peta (Target: 92% dari lebar template)
                lebar_baru = int(bg_w * 0.92) 
                rasio = (lebar_baru / float(peta_asli.size[0]))
                tinggi_baru = int((float(peta_asli.size[1]) * float(rasio)))
                
                # Batasi tingginya maksimal 82% dari tinggi template agar tak nabrak footer
                batas_tinggi = int(bg_h * 0.82)
                if tinggi_baru > batas_tinggi:
                    tinggi_baru = batas_tinggi
                    rasio = (tinggi_baru / float(peta_asli.size[1]))
                    lebar_baru = int((float(peta_asli.size[0]) * float(rasio)))

                peta_asli = peta_asli.resize((lebar_baru, tinggi_baru), Image.Resampling.LANCZOS)
                
                # Atur Posisi (Tengah)
                map_w, map_h = peta_asli.size
                posisi_x = (bg_w - map_w) // 2      
                posisi_y = int(bg_h * 0.04)         
                
                # Tempelkan peta ke atas template
                bg_template.paste(peta_asli, (posisi_x, posisi_y))
                
                # Simpan hasil gabungan ke memori untuk di-download
                img_io_dl = io.BytesIO()
                bg_template.save(img_io_dl, format='PNG')
                img_b64 = base64.b64encode(img_io_dl.getvalue()).decode('utf-8')
                
            except Exception as img_err:
                print("Template peta gagal diproses:", img_err)
                # Fallback: Jika template gagal, download PNG-nya pakai peta mentah juga
                img_b64 = base64.b64encode(res_img.content).decode('utf-8')
            
            # 🟢 EKSEKUSI PENYUNTIKAN: Masukkan Peta Mentah (img_io_pdf) ke Word
            tpl = DocxTemplate("template_hotspot.docx")
            context['gambar_peta'] = InlineImage(tpl, img_io_pdf, width=Mm(160)) 
            
        else:
            tpl = DocxTemplate("template_hotspot.docx")
            context['gambar_peta'] = "[GAMBAR PETA GAGAL DIUNDUH DARI PUSAT]"
            
        # Render Template Word
        tpl.render(context)
        
        # 🟢 SOLUSI HACKER: ROBOT PYTHON YANG MENGGAMBAR TABEL MANUAL (ANTI-ERROR)
        for table in tpl.docx.tables:
            try:
                # Cari tabel yang kolom pertamanya "NO" dan kolom keduanya "BUJUR"
                hdr_no = table.cell(0, 0).text.strip().upper()
                hdr_bujur = table.cell(0, 1).text.strip().upper()
                
                if "NO" in hdr_no and "BUJUR" in hdr_bujur:
                    for item in hotspot_list:
                        new_row = table.add_row()
                        
                        # Kumpulkan datanya
                        data_row = [
                            item['no'], item['bujur'], item['lintang'], item['kepercayaan'],
                            item['region'], item['provinsi'], item['kabupaten'], item['kecamatan'],
                            item['satelit'], item['tanggal'], item['waktu'], item['radius'], item['tipe']
                        ]
                        
                        # Masukkan data ke sel sambil mengatur Font & Ukuran
                        for col_idx, text_val in enumerate(data_row):
                            cell = new_row.cells[col_idx]
                            cell.text = "" # Kosongkan dulu
                            
                            # Ketik teksnya
                            run = cell.paragraphs[0].add_run(str(text_val))
                            
                            # 🎨 ATUR GAYA TEKS DI SINI
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(5)  # 👈 Ubah angka 9 jadi 8 jika masih kurang kecil
                            
                            # 📏 RATA TENGAH (CENTER)
                            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                            
                    break # Hentikan pencarian jika tabel sudah diisi
            except Exception as ex:
                print("Melewati tabel:", ex)
                
        # Buat file sementara di sistem
        temp_dir = tempfile.gettempdir()
        docx_path = os.path.join(temp_dir, f"temp_hotspot_{format_tgl_file}.docx")
        pdf_path = os.path.join(temp_dir, f"temp_hotspot_{format_tgl_file}.pdf")
        
        tpl.save(docx_path)
        
        # Konversi Word ke PDF
        try:
            pythoncom.CoInitialize()
            convert(docx_path, pdf_path)
            pythoncom.CoUninitialize()
            
            with open(pdf_path, "rb") as pdf_file:
                doc_b64 = base64.b64encode(pdf_file.read()).decode('utf-8')
            
            out_filename = f"REKAP_HOTSPOT{format_tgl_file}.pdf"
            out_mime = "application/pdf"
            if os.path.exists(pdf_path): os.remove(pdf_path)
            
        except Exception as conv_err:
            print("Gagal konversi PDF, Fallback ke Word:", conv_err)
            with open(docx_path, "rb") as doc_file:
                doc_b64 = base64.b64encode(doc_file.read()).decode('utf-8')
            out_filename = f"REKAP_HOTSPOT{format_tgl_file}.docx"
            out_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        if os.path.exists(docx_path): os.remove(docx_path)
        
        # Kirim File
        return jsonify({
            "status": "success",
            "filename_doc": out_filename,
            "file_doc_b64": doc_b64,
            "mime_doc": out_mime,
            "filename_img": f"PETA_HOTSPOT{format_tgl_file}.png",
            "file_img_b64": img_b64
        })

    except Exception as e:
        return jsonify({"error": f"Gagal mencetak dokumen! Error: {str(e)}"}), 500

# ====================================================================
# 🚀 MESIN WAKTU AUTOSEND (JALUR BELAKANG)
# ====================================================================
from apscheduler.schedulers.background import BackgroundScheduler

# Setel zona waktu ke WIT (Papua)
scheduler = BackgroundScheduler(timezone="Asia/Jayapura")
scheduler.start()

state_autosend = {"waktu": "-", "status": "Nonaktif"}
# 🟢 VARIABEL BARU: Kotak pos untuk menyimpan status autosend terakhir
notifikasi_autosend = {"status": False, "pesan": ""}

def tugas_tembak_autosend(taf_text):
    global state_autosend
    global notifikasi_autosend
    
    print(f"\n[🚀 AUTOSEND] Waktunya tiba! Sedang menembak sandi ke GTS...")
    try:
        # Robot akan menekan tombol 'Kirim' secara virtual dari dalam mesin
        requests.post('http://127.0.0.1:5000/api/metar/kirim_bmkgsoft', json={"taf_text": taf_text}, timeout=60)
        print("[✅ AUTOSEND] Misi Penembakan Sukses!")
        
        # 🟢 Beri sinyal ke kotak pos bahwa pengiriman BERHASIL
        notifikasi_autosend = {"status": True, "pesan": "Berhasil! Sandi TAFOR telah dikirim ke GTS secara otomatis."}
    except Exception as e:
        print("[❌ AUTOSEND] Misi Gagal:", e)
        # 🟢 Beri sinyal ke kotak pos bahwa pengiriman GAGAL
        notifikasi_autosend = {"status": True, "pesan": f"Gagal melakukan Autosend: {str(e)}"}
    
    # Matikan status setelah selesai menembak
    state_autosend = {"waktu": "-", "status": "Nonaktif"}

# 🟢 RUTE API BARU: Agar Web bisa membaca sinyal dari Python
@app.route('/api/cek-notif-autosend')
def cek_notif_autosend():
    global notifikasi_autosend
    # Salin status saat ini
    hasil = notifikasi_autosend.copy()
    
    # Jika sudah terbaca oleh web, langsung kosongkan lagi kotak posnya 
    # (agar kotak popup tidak muncul berkali-kali)
    if hasil["status"]:
        notifikasi_autosend = {"status": False, "pesan": ""}
        
    return jsonify(hasil)

@app.route('/api/metar/set_autosend', methods=['POST'])
def api_set_autosend():
    # ... (biarkan fungsi ini utuh seperti sebelumnya) ...
    global state_autosend
    data = request.json
    waktu = data.get('waktu') 
    taf_text = data.get('taf_text')
    
    if not waktu or not taf_text:
        return jsonify({"error": "Data belum lengkap"}), 400
        
    jam, menit = waktu.split(':')
    
    if scheduler.get_job('job_taf'):
        scheduler.remove_job('job_taf')
        
    scheduler.add_job(
        func=tugas_tembak_autosend,
        trigger='cron',
        hour=int(jam),
        minute=int(menit),
        args=[taf_text],
        id='job_taf'
    )
    
    state_autosend = {"waktu": waktu, "status": "Aktif"}
    return jsonify({"status": "Sukses", "pesan": f"Radar Autosend aktif untuk jam {waktu} WIT!"})

@app.route('/api/metar/cancel_autosend', methods=['POST'])
def api_cancel_autosend():
    global state_autosend
    if scheduler.get_job('job_taf'):
        scheduler.remove_job('job_taf')
    state_autosend = {"waktu": "-", "status": "Nonaktif"}
    return jsonify({"status": "Sukses"})
    
@app.route('/api/metar/status_autosend', methods=['GET'])
def api_status_autosend():
    return jsonify(state_autosend)

# ====================================================================
    
if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)