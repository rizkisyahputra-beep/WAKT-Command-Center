from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import math
import requests
import schedule
import os
import sys
from datetime import datetime, timezone

# --- PENGUNCI DIREKTORI (ANTI-AMNESIA SAAT STARTUP) ---
direktori_aktif = os.path.dirname(os.path.abspath(__file__))
os.chdir(direktori_aktif)
# ------------------------------------------------------

# =====================================================================
# 1. KONFIGURASI OPERASIONAL & PARAMETER STASIUN
# =====================================================================
URL_LOGIN = "https://bmkgsatu.bmkg.go.id/login"  
URL_EXTRACT_GTS = "https://bmkgsatu.bmkg.go.id/extractgts"  

USERNAME_BMKG = "97876"
PASSWORD_BMKG = "opr97876"
KODE_WMOID    = "97876"

# Konfigurasi Target Distribusi (Grup WhatsApp)
WA_NOMOR_ATC  = "120363119988423222@g.us"

# --- MODUL PEMULIHAN STATUS PENGIRIMAN TERAKHIR ---
FILE_LOG_WAKTU = "last_processed.txt"
if os.path.exists(FILE_LOG_WAKTU):
    with open(FILE_LOG_WAKTU, "r") as f:
        LAST_PROCESSED_TIME = f.read().strip()
    print(f"[{datetime.now()}] [INFO] Memori status diakses. Pemrosesan terakhir tercatat pada jam: {LAST_PROCESSED_TIME}")
else:
    LAST_PROCESSED_TIME = ""

# =====================================================================
# IDENTIFIKATOR LOKASI ELEMEN ANTARMUKA WEB (XPATH)
# =====================================================================
XPATH_KOLOM_USER    = '//*[@id="login-email"]'
XPATH_KOLOM_PASS    = '//*[@id="login-password"]'
XPATH_TOMBOL_LOGIN  = '//*[@id="app"]/div[1]/div/div/div/div/div[2]/div/span/form/button'
XPATH_TYPE_MESSAGE  = '//*[@id="vs2__combobox"]/div[1]/input' 
XPATH_KOLOM_CCCC    = '//*[@id="cccc"]' 
XPATH_KOLOM_WMOID   = '//*[@id="wmoid"]' 
XPATH_KOLOM_TANGGAL = '//*[@id="app"]/div[1]/div[3]/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[3]/input' 
XPATH_TOMBOL_FILTER = '//*[@id="app"]/div[1]/div[3]/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[5]/button'

# =====================================================================
# 2. FUNGSI KONVERSI DATA METEOROLOGI STASIUN
# =====================================================================
def hitung_kelembapan(temp, dew):
    atas = math.exp((17.625 * dew) / (243.04 + dew))
    bawah = math.exp((17.625 * temp) / (243.04 + temp))
    return round(100 * (atas / bawah))

def dekode_tekanan_synop(sandi_grup):
    p = int(sandi_grup)
    if p < 5000: p += 10000
    return p / 10

def pembulatan_met(nilai):
    if nilai == "N/A": return "N/A"
    return int(nilai + 0.5) if nilai >= 0 else int(nilai - 0.5)

def pembulatan_tekanan(nilai):
    if nilai == "N/A": return "N/A"
    return int(math.floor(nilai))

def terjemahkan_cuaca_synop(ww_code):
    ww = int(ww_code)
    if ww in [0, 1, 2, 3]: return "CLOUDY"
    elif ww in [4, 5]: return "HAZE"
    elif ww == 10: return "MIST"
    elif ww == 13: return "LIGHTING"
    elif ww in [14, 15, 16]: return "VCSH"
    elif ww == 17: return "THUNDERSTORM NO PREC"
    elif ww == 18: return "SQUALLS"
    elif ww == 19: return "FUNNEL CLOUD"
    elif 40 <= ww <= 49: return "FOG"
    elif ww in [50, 51]: return "LIGHT DRIZZLE"
    elif ww in [52, 53]: return "MODERATE DRIZZLE"
    elif ww in [54, 55]: return "HEAVY DRIZZLE"
    elif ww == 58: return "LIGHT DRIZZLE RAIN"
    elif ww == 59: return "HEAVY DRIZZLE RAIN"
    elif ww in [60, 61]: return "LIGHT RAIN"
    elif ww in [62, 63]: return "MODERATE RAIN"
    elif ww in [64, 65]: return "HEAVY RAIN"
    elif 66 <= ww <= 69: return "RAIN AND SNOW"
    elif 70 <= ww <= 79: return "SNOW"
    elif ww == 80: return "LIGHT SHOWER RAIN"
    elif ww in [81, 82]: return "HEAVY SHOWER RAIN"
    elif ww in [83, 84]: return "SHOWER RAIN AND SNOW"
    elif 85 <= ww <= 88: return "SNOW SHOWERS"
    elif ww in [89, 90]: return "HAIL SHOWERS"
    elif 91 <= ww <= 94: return "THUNDERSTORM WITH RAIN"
    elif ww == 95: return "THUNDERSTORM WITH RAIN"
    elif ww in [96, 97]: return "HEAVY THUNDERSTORM WITH RAIN"
    elif ww in [98, 99]: return "HEAVY THUNDERSTORM WITH SAND/HAIL"
    else: return "CLOUDY"

def kirim_ke_whatsapp(pesan_report):
    url_gateway = "http://localhost:3000/send"
    try:
        response = requests.post(url_gateway, json={'target': WA_NOMOR_ATC, 'message': pesan_report}, timeout=20)
        res_data = response.json()
        print(f"[{datetime.now()}] [INFO] Respons Server Gateway: {res_data}")
        
        if res_data.get('status') == True or res_data.get('status') == 'blocked':
            return True
        return False
    except Exception as e:
        print(f"[{datetime.now()}] [KESALAHAN] Gagal membangun koneksi ke Server Gateway: {e}")
        return False

# =====================================================================
# 3. MODUL INTI EKSTRAKSI DAN PEMROSESAN DATA
# =====================================================================
def ambil_dan_proses_synop():
    global LAST_PROCESSED_TIME
    
    waktu_utc_sekarang = datetime.now(timezone.utc)
    current_hour_utc = waktu_utc_sekarang.hour
    hari_ini_utc = waktu_utc_sekarang.strftime("%Y-%m-%d")

    if not (current_hour_utc >= 20 or current_hour_utc <= 8): return

    current_time_key = f"{hari_ini_utc}_{current_hour_utc}"
    if current_time_key == LAST_PROCESSED_TIME: 
        return

    print(f"[{datetime.now()}] [PROSES] Mengevaluasi ketersediaan data SYNOP jam {current_hour_utc:02d}.00 UTC...")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 15)
    
    try:
        # Otentikasi dan Pemfilteran Data 
        driver.get(URL_LOGIN)
        wait.until(EC.presence_of_element_located((By.XPATH, XPATH_KOLOM_USER))).send_keys(USERNAME_BMKG)
        driver.find_element(By.XPATH, XPATH_KOLOM_PASS).send_keys(PASSWORD_BMKG)
        driver.find_element(By.XPATH, XPATH_TOMBOL_LOGIN).click()
        time.sleep(4)

        driver.get(URL_EXTRACT_GTS)
        time.sleep(5)

        # ==========================================================
        # PROSES PENGISIAN FILTER (ADAPTIF)
        # ==========================================================
        for xpath, val in [(XPATH_TYPE_MESSAGE, "SINOPTIK"), (XPATH_KOLOM_CCCC, "wakt"), (XPATH_KOLOM_WMOID, KODE_WMOID), (XPATH_KOLOM_TANGGAL, f"{hari_ini_utc} to {hari_ini_utc}")]:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                el.click()
                time.sleep(1)
                el.send_keys(Keys.CONTROL + "a")
                el.send_keys(Keys.BACKSPACE)
                
                el.send_keys(val)
                
                if xpath == XPATH_TYPE_MESSAGE and current_hour_utc == 0:
                    time.sleep(1.5) 
                    el.send_keys(Keys.ARROW_DOWN) 
                    time.sleep(0.5)
                else:
                    time.sleep(1) 
                    
                el.send_keys(Keys.ENTER)
            except Exception as e:
                print(f"[PERINGATAN] Robot gagal mengisi filter '{val}'.")
        # ==========================================================

        driver.find_element(By.XPATH, XPATH_TOMBOL_FILTER).click()
        
        # --- PERBAIKAN WAKTU TUNGGU ADAPTIF ---
        if current_hour_utc == 0:
            print("[PROSES] Jam sibuk (00 UTC) terdeteksi. Menunggu 20 detik agar web BMKG merender data...")
            time.sleep(20)
        else:
            print("[PROSES] Menunggu 8 detik untuk pemuatan data standar...")
            time.sleep(8)

        # =====================================================================
        # EKSTRAKSI DATA (ADAPTIF: MODE SNIPER 00 UTC vs MODE NORMAL)
        # =====================================================================
        if current_hour_utc == 0:
            print("[PROSES] Mengaktifkan Mode Sniper (Memindai seluruh kotak data web)...")
            
            # Pastikan elemen stasiun minimal muncul di halaman
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{KODE_WMOID}')]")))
                time.sleep(2)
            except:
                print("[STATUS] Halaman belum memuat data. Menunggu siklus berikutnya.")
                return
            
            # --- KUNCI PERBAIKAN: MENCARI KE DALAM SEMUA KOTAK TEXTAREA ---
            semua_textarea = driver.find_elements(By.TAG_NAME, "textarea")
            teks_sandi_mentah = ""
            jam_str = f"{current_hour_utc:02d}"
            
            # Regex pemburu sandi AAXX (Mengambil dari AAXX sampai tanda =)
            pola_sandi = r'(AAXX\s+\d{2}' + jam_str + r'\d\s+' + KODE_WMOID + r'.*?=)'
            
            for elemen in semua_textarea:
                isi_teks = elemen.get_attribute("value")
                if isi_teks:
                    # Periksa apakah di dalam kotak ini ada AAXX jam 00
                    match_aaxx = re.search(pola_sandi, isi_teks, re.DOTALL)
                    if match_aaxx:
                        teks_sandi_mentah = match_aaxx.group(1).replace('\n', ' ')
                        break # Ditemukan! Hentikan pencarian
                        
            if not teks_sandi_mentah:
                print(f"[DEBUG] Penolakan Data: Kotak sandi SYNOP 'AAXX' jam {jam_str} belum ditemukan di antara {len(semua_textarea)} kotak yang ada.")
                return
            
        else:
            # --- MODE NORMAL (UNTUK JAM SELAIN 00 UTC) ---
            elemen_sandi = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="textarea-sandi"]')))
            teks_sandi_mentah = elemen_sandi.text if elemen_sandi.text else elemen_sandi.get_attribute("value")
            
            if not teks_sandi_mentah.strip(): 
                print("[STATUS] Kotak hasil web BMKG masih kosong. Menunggu siklus pemantauan berikutnya.")
                return

            match_jam_sandi = re.search(r'AAXX \d{2}(\d{2})\d', teks_sandi_mentah)
            if not match_jam_sandi:
                cuplikan_teks = teks_sandi_mentah.strip()[:80].replace('\n', ' ')
                print(f"[DEBUG] Penolakan Data: Sandi 'AAXX' tidak ditemukan! Teks web: '{cuplikan_teks}...'")
                return
                
            jam_sandi_web = int(match_jam_sandi.group(1))
            if jam_sandi_web != current_hour_utc:
                print(f"[DEBUG] Penolakan Data: Ketidaksesuaian Waktu! Web menampilkan data jam {jam_sandi_web:02d} UTC.")
                return
        # =====================================================================

        print(f"\n[INFO] Sandi SYNOP berhasil diamankan! Memulai translasi jam {current_hour_utc:02d}.00 UTC...")

        sec1 = teks_sandi_mentah.split('333')[0]
        tokens = sec1.split() 

        wmo_idx = -1
        for i, t in enumerate(tokens):
            if KODE_WMOID in t:
                wmo_idx = i
                break

        if wmo_idx == -1: return

        # Parameter Visibilitas
        ind_token = tokens[wmo_idx + 1] if (wmo_idx + 1) < len(tokens) else ""
        vis_format = "8 KM"  
        h_code_fallback = "3"
        if ind_token and len(ind_token) == 5:
            h_code_fallback = ind_token[2]
            if ind_token[3:5].isdigit():
                kode_vis = int(ind_token[3:5])
                if 0 <= kode_vis <= 50: vis_format = f"{kode_vis / 10:g} KM"
                elif 56 <= kode_vis <= 80: vis_format = f"{kode_vis - 50} KM"
                elif kode_vis == 98: vis_format = "20 KM"
                elif kode_vis == 99: vis_format = ">= 50 KM"

        # Parameter Arah dan Kecepatan Angin
        angin_token = tokens[wmo_idx + 2] if (wmo_idx + 2) < len(tokens) else ""
        angin_format = "000/00 KT"
        n_oktas = "9"
        
        pointer_sisa = wmo_idx + 3
        grup_badai = ""
        if pointer_sisa < len(tokens) and tokens[pointer_sisa].startswith("00") and len(tokens[pointer_sisa]) == 5:
            grup_badai = tokens[pointer_sisa]
            pointer_sisa += 1 

        if angin_token and len(angin_token) == 5:
            n_oktas = angin_token[0]
            if angin_token[1:3].isdigit() and angin_token[3:5].isdigit():
                arah_int = int(angin_token[1:3])
                kec = int(angin_token[3:5])
                
                if kec == 99 and grup_badai:
                    kec = int(grup_badai[2:]) if grup_badai[2:].isdigit() else 99
                elif 50 <= arah_int <= 86:
                    arah_int -= 50
                    kec += 100
                    
                arah_str = f"{arah_int:02d}0"
                angin_format = f"{arah_str}/{kec:02d} KT"
                if arah_str == "000" and kec == 0:
                    angin_format = "000/00 KT"

        temp_token, dew_token, qfe_token, qnh_token, ww_token = "", "", "", "", ""
        for t in tokens[pointer_sisa:]:
            if len(t) == 5:
                if t.startswith("1"): temp_token = t
                elif t.startswith("2"): dew_token = t
                elif t.startswith("3"): qfe_token = t
                elif t.startswith("4"): qnh_token = t
                elif t.startswith("7"): ww_token = t

        weather_format = "CLOUDY"
        supplementary_format = "NIL"
        
        if ww_token and ww_token[1:3].isdigit():
            ww_val = int(ww_token[1:3])
            if 20 <= ww_val <= 29:
                weather_format = "CLOUDY" 
                map_recent = {
                    20: "RECENT DRIZZLE", 21: "RECENT RAIN", 22: "RECENT SNOW",
                    23: "RECENT RAIN AND SNOW", 24: "RECENT FREEZING RAIN",
                    25: "RECENT SHOWER RAIN", 26: "RECENT SHOWER SNOW",
                    27: "RECENT HAIL", 28: "RECENT FOG", 29: "RECENT THUNDERSTORM"
                }
                supplementary_format = map_recent.get(ww_val, "NIL")
            else:
                weather_format = terjemahkan_cuaca_synop(ww_val)
                supplementary_format = "NIL"
        else:
            weather_format = "CLOUDY"
            supplementary_format = "NIL"

        # Parameter Suhu dan Kelembapan Relatif
        if temp_token and dew_token and temp_token[2:].isdigit() and dew_token[2:].isdigit():
            t_val = int(temp_token[2:]) / 10
            temp = -t_val if temp_token[1] == '1' else t_val
            d_val = int(dew_token[2:]) / 10
            dew = -d_val if dew_token[1] == '1' else d_val
            kelembapan = f"{hitung_kelembapan(temp, dew)}%"
            suhu_dew_format = f"{pembulatan_met(temp)}/{pembulatan_met(dew)}"
        else:
            kelembapan, suhu_dew_format = "N/A", "N/A"

        # Parameter Tekanan Udara QFE dan QNH
        if qfe_token and qfe_token[1:].isdigit():
            qfe_val = dekode_tekanan_synop(qfe_token[1:])
            qfe_format = str(pembulatan_tekanan(qfe_val))
        else:
            qfe_format, qfe_val = "N/A", "N/A"

        if qnh_token and qnh_token[1:].isdigit():
            qnh_val = dekode_tekanan_synop(qnh_token[1:])
            qnh_format = str(pembulatan_tekanan(qnh_val))
        else:
            qnh_format = str(pembulatan_tekanan(qfe_val + 3)) if qfe_val != "N/A" else "N/A"

        # Ekstraksi Data Spesifik Awan Konvektif (Seksi 333)
        cloud_format = ""
        sec3_match = re.search(r'333\s+(.*)', teks_sandi_mentah)
        
        if sec3_match:
            sec3_text = sec3_match.group(1)
            ada_tcu = bool(re.search(r'\b808\d{2}\b', sec3_text))
            ada_cb  = bool(re.search(r'\b809\d{2}\b', sec3_text))
            
            awan_groups = re.findall(r'\b8(\d)(\d)(\d{2})\b', sec3_text)
            if awan_groups:
                layers = []
                for ns_str, c_str, hs_str in awan_groups:
                    ns, c, hs = int(ns_str), int(c_str), int(hs_str)
                    if ns == 0 or c not in [6, 7, 8, 9]: continue 
                        
                    if ns in [1, 2]: amt = "FEW"
                    elif ns in [3, 4]: amt = "SCT"
                    elif ns in [5, 6, 7]: amt = "BKN"
                    elif ns == 8: amt = "OVC"
                    else: continue
                    
                    if hs <= 50: tinggi = hs * 100
                    elif 56 <= hs <= 80:
                        meter = (hs - 50) * 1000
                        tinggi = int(round(meter * 3.28084 / 100.0)) * 100
                    else: continue 
                        
                    tipe = ""
                    if c == 9: 
                        tipe = " CB" 
                    elif c == 8 and ada_tcu:
                        tipe = " TCU"
                    layers.append(f"{amt} {tinggi} FT{tipe}")
                
                if layers: cloud_format = ", ".join(layers)

        if not cloud_format:
            map_n = {"0": "SKC", "1": "FEW", "2": "FEW", "3": "SCT", "4": "SCT", "5": "BKN", "6": "BKN", "7": "BKN", "8": "OVC", "9": "OVC", "/": "BKN"}
            cloud_amt = map_n.get(n_oktas, 'BKN')
            if cloud_amt == "SKC":
                cloud_format = "SKC" 
            else:
                map_h = {"0": "100", "1": "200", "2": "500", "3": "900", "4": "1500", "5": "3000", "6": "4500", "7": "6000", "8": "7500", "9": ">8000"}
                cloud_ht = map_h.get(h_code_fallback, "900")
                cloud_format = f"{cloud_amt} {cloud_ht} FT"

        # Penyusunan Format Akhir Laporan QAM
        tanggal_format = waktu_utc_sekarang.strftime("%d/%m/%Y")
        jam_format = waktu_utc_sekarang.strftime("%H.%M UTC") 

        met_report_qam = f"""```
MET REPORT (QAM)
AREA          : WAKT
DATE          : {tanggal_format}
TIME          : {jam_format}
---------------------------------
WIND          : {angin_format}
VIS           : {vis_format}
WEATHER       : {weather_format}
CLOUD         : {cloud_format}
TT/TD/RH      : {suhu_dew_format}/{kelembapan}
QNH           : {qnh_format}
QFE           : {qfe_format}
SUPPLEMENTARY : {supplementary_format}
REMARKS       : NIL
```"""

        print(met_report_qam)
        
        # Validasi Kelancaran Transmisi untuk Penguncian Memori Log
        if kirim_ke_whatsapp(met_report_qam):
            LAST_PROCESSED_TIME = current_time_key
            with open(FILE_LOG_WAKTU, "w") as f:
                f.write(current_time_key)
            print(f"[{datetime.now()}] [STATUS] Transmisi berhasil. Pemrosesan data jam {current_hour_utc:02d}.00 UTC direkam pada sistem.")
        else:
            print(f"[{datetime.now()}] [PERINGATAN] Transmisi ditolak/gagal. Retensi instruksi aktif untuk percobaan ulang pada siklus pemantauan berikutnya.")

    except Exception as e:
        print(f"[KESALAHAN SISTEM] Terjadi kendala teknis pada proses penarikan data: {e}")
    finally:
        driver.quit()

# 4. PROTOKOL TERMINASI SESI (STANDBY MODE)
def masuk_mode_tidur():
    print(f"\n[{datetime.now()}] [INFO] Batas waktu operasional stasiun telah tercapai.")
    print("[PROSES] Mengirimkan instruksi inisiasi mode siaga kepada Server Gateway...")
    try:
        requests.post("http://localhost:3000/sleep", timeout=10)
    except:
        pass
    
    print("[STATUS] Instruksi terkirim. Memulai proses terminasi modul ekstraksi Python...")
    time.sleep(3)
    os.system('taskkill /fi "WindowTitle eq Modul Ekstraksi*" /f /t')
    os._exit(0)

# Konfigurasi Interval Pemantauan (Siklus 1 Menit)
schedule.every(1).minutes.do(ambil_dan_proses_synop)
print("=========================================================")
print(" Modul Pemrosesan dan Transmisi Data Beroperasi Penuh.   ")
print(" Sistem aktif memantau pembaruan data secara berkala.    ")
print("=========================================================")
ambil_dan_proses_synop()

while True:
    schedule.run_pending()
    
    # Pengaturan Jadwal Terminasi Otomatis (08.30 UTC)
    now_utc = datetime.now(timezone.utc)
    if now_utc.hour == 8 and now_utc.minute == 30:
        masuk_mode_tidur()
        
    time.sleep(1)