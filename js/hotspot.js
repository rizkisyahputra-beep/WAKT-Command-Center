/**
 * ────────────────────────────────────────────────────────────────────────
 * MODUL GENERATOR HOTSPOT - STAMET WAKT COMMAND CENTER
 * ────────────────────────────────────────────────────────────────────────
 * Modul ini berfungsi untuk menembak API Backend, memecah Base64 ZIP/JSON
 * dan mengunduh file Dokumen Laporan (Word) & Gambar (PNG) secara simultan.
 */
// Contoh pemasangan sabuk pengaman di Javascript
function generateLaporanHotspot() {
    const inputGambar = document.getElementById('id-input-file-gambar-hotspot'); // sesuaikan dengan ID input Kapten
    
    // Cegat jika gambar belum diisi
    if (!inputGambar || !inputGambar.files || inputGambar.files.length === 0) {
        tampilkanNotifikasi("Peringatan", "Harap unggah gambar Peta Hotspot terlebih dahulu, Kapten!", "error");
        return; // Hentikan proses, jangan kirim ke Python
    }
    
    // Jika aman, lanjutkan proses pengiriman...
    // ...
}
// Fungsi Utama: Eksekusi Tarikan Data
async function tarikDataHotspot() {
    const tanggal = document.getElementById('input_tgl_hotspot').value;
    const nomorSurat = document.getElementById('input_nomor_hotspot').value;
    const prakirawan = document.getElementById('input_prakirawan_hotspot').value;
    const btn = document.getElementById('btnGenerateHotspot');

    // Validasi Form
    if (!tanggal || !nomorSurat) {
        tampilkanNotifikasi("Peringatan", "Tanggal dan Nomor Surat wajib diisi sebelum meng-generate dokumen!", "error");
        return;
    }

    // Ubah UI Tombol (Loading State)
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses Laporan...';
    btn.disabled = true;

    try {
        // Tembak API Backend
        const response = await fetch('/api/hotspot/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                tanggal: tanggal, 
                nomor_surat: nomorSurat, 
                prakirawan: prakirawan 
            })
        });

        const data = await response.json();

        // Cek Respon
        if (response.ok && data.status === "success") {
            // Tampilkan Notif Sukses (Menggunakan modal custom bawaan web Kapten)
            tampilkanNotifikasi("Berhasil!", `Laporan Hotspot untuk tanggal ${tanggal} berhasil digenerate. File akan segera diunduh.`, "success");
            
            // 1. Download Dokumen Laporan (Otomatis PDF)
            downloadBase64File(data.file_doc_b64, data.filename_doc, data.mime_doc);
            
            // 2. Download Gambar Peta (Beri jeda 500ms agar browser tidak panik & memblokir unduhan kedua)
            setTimeout(() => {
                downloadBase64File(data.file_img_b64, data.filename_img, "image/png");
            }, 500);
            
        } else {
            // Jika ada error dari sisi Python (Misal template hilang, atau server down)
            tampilkanNotifikasi("Gagal Generate", data.error || "Terjadi kesalahan pada mesin server.", "error");
        }

    } catch (error) {
        // Jika Python / Backend belum berjalan
        console.error("Hotspot API Error:", error);
        tampilkanNotifikasi("Koneksi Terputus", "Gagal menghubungi mesin server. Pastikan Server Python berjalan!", "error");
    } finally {
        // Kembalikan Tombol (Selesai Loading)
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Fungsi Pendukung: Mengubah Teks Base64 dari Server menjadi File Unduhan
function downloadBase64File(base64Data, filename, contentType) {
    const link = document.createElement('a');
    link.href = `data:${contentType};base64,${base64Data}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}