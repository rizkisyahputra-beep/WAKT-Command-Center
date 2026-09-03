import subprocess
import threading
import time
import re
import sys
import os
import json
import urllib.request
import urllib.parse

# =====================================================================
# 🟢 1. KONFIGURASI AMUNISI FONNTE KAPTEN
# =====================================================================
TOKEN_FONNTE = "9y5fnm9hNEMcs5BJswHj"

# 🎯 DAFTAR BROADCAST SASARAN (Bisa Nomor HP atau ID Grup)
DAFTAR_TARGET_WA = [
    "62895325618829", # <-- Anggota Piket A
]

PORT_WEB = "5000"

# 🛡️ TAMENG ISOLASI WINDOWS
IS_WINDOWS = (sys.platform == "win32")
BLAST_SHIELD_FLAG = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW) if IS_WINDOWS else 0
# =====================================================================

def kirim_notif_fonnte(pesan_teks):
    """Jurus Peluru Shotgun: Menembak 1 kali langsung meledak ke sasaran"""
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": TOKEN_FONNTE}
    sasaran_shotgun = ",".join(DAFTAR_TARGET_WA)

    print(f"\n📤 [SHOTGUN BROADCAST]: Mengirim 1 paket ke {len(DAFTAR_TARGET_WA)} sasaran sekaligus...")

    payload = {
        "target": sasaran_shotgun, 
        "message": pesan_teks,
        "countryCode": "62",
        "delay": "3" 
    }

    data_post = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data_post, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            jawaban = json.loads(response.read().decode("utf-8"))
            if jawaban.get("status") == True or jawaban.get("status") == "true":
                print("   ┗━ 📲 [MISI SUKSES]: Paket diterima pusat Fonnte! Sedang didistribusikan ke seluruh HP...\n")
            else:
                print(f"   ┗━ ❌ [DITOLAK]: {jawaban.get('reason', 'Kesalahan API')}\n")
    except Exception as e:
        print(f"   ┗━ ❌ [GAGAL KONEKSI]: {e}\n")

# =====================================================================
# 🧠 SATPAM 1: PENJAGA MESIN FLASK (app.py)
# =====================================================================
def satpam_flask():
    while True:
        try:
            print("\n🧠 [SATPAM FLASK]: Menghidupkan mesin utama app.py...")
            proses_flask = subprocess.Popen(
                [sys.executable, "app.py"],
                creationflags=BLAST_SHIELD_FLAG
            )
            proses_flask.wait()
            print("\n💥 [KODE MERAH]: app.py mendadak tewas! Menyuntikkan adrenalin dalam 3 detik...")
        except Exception as e:
            print(f"\n⚠️ [SATPAM FLASK ERROR]: {e}")
        time.sleep(3)

# =====================================================================
# 🌐 SATPAM 2: PENJAGA JEMBATAN CLOUDFLARE (AIR-GAPPED MODE)
# =====================================================================
def satpam_tunnel():
    link_terakhir = ""
    file_log = "tunnel.log"
    
    perintah_tunnel = [
        "cloudflared.exe",
        "tunnel",
        "--url",
        f"http://localhost:{PORT_WEB}",
    ]

    while True:
        print("\n🌐 [SATPAM TUNNEL]: Membuka gerbang Cloudflare Tunnel (Mode Ruang Kedap)...")
        
        # 1. Bersihkan buku catatan lama sebelum prajurit baru bekerja
        try:
            with open(file_log, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass

        log_handle = None
        proses_tunnel = None

        try:
            # 2. Buka file log sebagai tujuan tulis cloudflared
            log_handle = open(file_log, "a", encoding="utf-8")

            # 3. JALANKAN CLOUDFLARE TANPA PIPA! Semua suara dibuang ke file tunnel.log
            proses_tunnel = subprocess.Popen(
                perintah_tunnel,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=BLAST_SHIELD_FLAG
            )

            # 4. Jenderal mengawasi dari balik kaca dengan membaca file tunnel.log
            with open(file_log, "r", encoding="utf-8", errors="ignore") as f_read:
                # Selama proses cloudflared masih hidup (belum mati/crash)
                while proses_tunnel.poll() is None:
                    baris = f_read.readline()
                    
                    # Jika belum ada tulisan baru di log, tunggu 0.5 detik lalu cek lagi
                    if not baris:
                        time.sleep(0.5)
                        continue
                    
                    # Cek apakah ada link publik yang muncul di catatan
                    cocok = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", baris)
                    if cocok:
                        link_baru = cocok.group(0)
                        if link_baru != link_terakhir:
                            link_terakhir = link_baru
                            print(f"\n🚀 [LINK PUBLIK AKTIF]: {link_baru}")

                            pesan_broadcast = (
                                f"*🚨 RADAR WAKT ONLINE (FONNTE) 🚨*\n\n"
                                f"Link Command Center telah diperbarui otomatis oleh sistem:\n\n"
                                f"🔗 {link_baru}\n\n"
                                f"_Sistem siap menerima input sandi cuaca harian._"
                            )
                            kirim_notif_fonnte(pesan_broadcast)
                            
        except Exception as e:
            print(f"\n⚠️ [SATPAM TUNNEL ERROR]: {e}")
            
        finally:
            # Tutup handle file log secara aman
            if log_handle:
                try:
                    log_handle.close()
                except Exception:
                    pass
            # Pastikan sisa proses zombie dibersihkan
            if proses_tunnel and proses_tunnel.poll() is None:
                try:
                    proses_tunnel.terminate()
                except Exception:
                    pass

        print("\n💥 [KODE MERAH]: Cloudflare terputus/mati! Membangkitkan ulang dalam 5 detik...")
        time.sleep(5)

# =====================================================================
# 👑 KOMANDAN UTAMA PENGGERAK THREAD
# =====================================================================
if __name__ == "__main__":
    print("=========================================================")
    print("🛡️  GOD-MODE WATCHDOG WAKT + FONNTE ARTILERY BEROPERASI")
    print("=========================================================")
    print("[!] Tekan Ctrl + C di jendela ini jika Kapten ingin mematikan total.\n")

    thread_flask = threading.Thread(target=satpam_flask, daemon=True)
    thread_tunnel = threading.Thread(target=satpam_tunnel, daemon=True)

    thread_flask.start()
    time.sleep(3)
    thread_tunnel.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Sistem dimatikan oleh Komandan.")
        sys.exit(0)