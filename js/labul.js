// Fungsi Helper taktis untuk mendownload file tunggal dari server blob
async function requestDownloadFileLabul(periode, takeoff, landing, tipe) {
    const response = await fetch('/api/metar/download_labul_tunggal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            periode: periode,
            takeoff: takeoff,
            landing: landing,
            tipe: tipe
        })
    });

    if (!response.ok) {
        // Ambil respons sebagai teks mentah dulu (berjaga-jaga jika isinya HTML)
        const errText = await response.text(); 
        try {
            // Coba terjemahkan sebagai JSON
            const errData = JSON.parse(errText);
            throw new Error(errData.error || `Gagal mengunduh file tipe ${tipe}`);
        } catch (e) {
            // Jika gagal diterjemahkan (artinya yang datang adalah HTML Error 500)
            console.error("Fatal Server Error:", errText);
            throw new Error(`Server Python mengalami Crash saat memproses file ${tipe}! Cek terminal CMD app.py untuk melihat penyebab pastinya.`);
        }
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    // Penamaan file hasil download disesuaikan tipenya
    const namaFileSistem = {
        "bulanan": `Produk_Pelayanan_Bulanan_WAKT_${periode}.xlsx`,
        "penerbangan": `Statistik_Penerbangan_WAKT_${periode}.xlsx`,
        "harian": `Produk_Pelayanan_Harian_WAKT_${periode}.xlsx`
    };

    a.href = downloadUrl;
    a.download = namaFileSistem[tipe];
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
}

async function generateLabulMisi1() {
    const elBulan = document.getElementById('labul-bulan');
    const elTahun = document.getElementById('labul-tahun');
    const elTakeoff = document.getElementById('atc-takeoff');
    const elLanding = document.getElementById('atc-landing');

    if (!elBulan || !elTahun || !elTakeoff || !elLanding) {
        alert("Radar Error: Form komponen HTML tidak ditemukan!");
        return;
    }

    const periode = `${elTahun.value}-${elBulan.value}`; 
    const atcTakeoff = parseInt(elTakeoff.value) || 0;
    const atcLanding = parseInt(elLanding.value) || 0;

    const modalLoading = document.getElementById('modal-loading');
    if(modalLoading) modalLoading.classList.remove('hidden');

    try {
        // 🚀 EKSEKUSI BERANTAI DENGAN DELAY 1 DETIK (Mengakali Security Browser)
        await requestDownloadFileLabul(periode, atcTakeoff, atcLanding, "bulanan");
        await new Promise(resolve => setTimeout(resolve, 1000)); // Jeda 1 detik
        
        await requestDownloadFileLabul(periode, atcTakeoff, atcLanding, "penerbangan");
        await new Promise(resolve => setTimeout(resolve, 1000)); // Jeda 1 detik
        
        await requestDownloadFileLabul(periode, atcTakeoff, atcLanding, "harian");

        if(modalLoading) modalLoading.classList.add('hidden');
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Sukses Besar!", "3 File Laporan Excel terpisah berhasil didownload!", "success");
        } else {
            alert("SUKSES! 3 File Excel Laporan Pelayanan berhasil didownload!");
        }

    } catch (error) {
        console.error(error);
        if(modalLoading) modalLoading.classList.add('hidden');
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Gagal Operasi", error.message, "error");
        } else {
            alert(`Error: ${error.message}`);
        }
    }
}