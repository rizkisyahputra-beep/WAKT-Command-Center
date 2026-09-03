// ==========================================
// CORE ENGINE: OTOMATISASI NARASI & TATA LETAK
// ==========================================
function updateSemuanya() {
    let elHari = document.getElementById('inHari');
    if (!elHari) return; // Mencegah error jika dijalankan di tab lain

    let hari = elHari.value;
    let tanggalAsli = document.getElementById('inTanggal').value;
    let umum = document.getElementById('inUmum').value.toLowerCase();
    let intensitas = document.getElementById('inHujan').value;
    
    let cPagi = document.getElementById('inCuacaPagi').value.replace(/_/g, ' ').replace(' Malam', '').toLowerCase();
    let cSiang = document.getElementById('inCuacaSiang').value.replace(/_/g, ' ').replace(' Malam', '').toLowerCase();
    let cMalam = document.getElementById('inCuacaMalam').value.replace(/_/g, ' ').replace(' Malam', '').toLowerCase();
    let cDini = document.getElementById('inCuacaDiniHari').value.replace(/_/g, ' ').replace(' Malam', '').toLowerCase();
    
    let sMin = document.getElementById('inSuhuMin').value; let sMax = document.getElementById('inSuhuMax').value;
    let lMin = document.getElementById('inLembapMin').value; let lMax = document.getElementById('inLembapMax').value;
    let aDari = document.getElementById('inAnginDari').value; let aKe = document.getElementById('inAnginMenuju').value;
    let aSpeed = document.getElementById('inAnginSpeed').value; let peringatan = document.getElementById('inPeringatan').value;

    // UPDATE TANGGAL GLOBAL (HURUF BESAR SEMUA UNTUK JUDUL)
    let teksTanggal = "BERLAKU UNTUK " + hari.toUpperCase() + ", " + tanggalAsli.toUpperCase();
    if(document.getElementById('outTanggal2')) document.getElementById('outTanggal2').innerText = teksTanggal;
    if(document.getElementById('outTanggal3')) document.getElementById('outTanggal3').innerText = teksTanggal;

    // UPDATE SLIDE 2 (DATA INFOGRAFIS)
    if(document.getElementById('outSuhu')) document.getElementById('outSuhu').innerText = `${sMin} - ${sMax}°C`;
    if(document.getElementById('outLembap')) document.getElementById('outLembap').innerText = `${lMin} - ${lMax}%`;
    if(document.getElementById('outAngin')) document.getElementById('outAngin').innerHTML = `${aDari.toUpperCase()} - ${aKe.toUpperCase()}<br>${aSpeed} KM/JAM`;
    if(document.getElementById('outPeringatan')) document.getElementById('outPeringatan').innerText = peringatan.toUpperCase();

    // FORMAT TANGGAL UNTUK NARASI (Bulan ditulis biasa/kapital awal saja)
    let tanggalNarasi = tanggalAsli.toLowerCase().replace(/\b\w/g, s => s.toUpperCase());
    let teksHujan = intensitas !== "" ? ` hingga terdapat hujan dengan intensitas ${intensitas}` : "";
    
    // GENERATE NARASI
    let narasi1 = `Kondisi cuaca untuk wilayah Tanah Merah dan sekitarnya pada ${hari}, ${tanggalNarasi} diperkirakan umumnya ${umum}${teksHujan}, dengan detil waktu prakiraan kondisi cuaca sebagai berikut: \n\nPada Pagi hari kondisi cuaca diprakirakan ${cPagi}, Kemudian pada siang hari cuaca diprakirakan ${cSiang}. Selanjutnya untuk malam hari cuaca diprakirakan ${cMalam} dan untuk dini hari cuaca diprakirakan ${cDini}.`;
    let narasi2 = `Adapun beberapa parameter cuaca untuk hari ini diprakirakan sebagai berikut: Pertama untuk suhu udara berkisar dari ${sMin} hingga ${sMax} derajat Celsius, kemudian kelembaban udara berkisar ${lMin} hingga ${lMax} persen, serta untuk arah angin diprakirakan bergerak dominan dari arah ${aDari} menuju ${aKe} dengan kecepatan mencapai ${aSpeed} Kilo meter per jam.\nPeringatan Dini: ${peringatan}`;
    
    if(document.getElementById('inNarasi1')) {
        document.getElementById('inNarasi1').value = narasi1; document.getElementById('outNarasi1').innerText = narasi1;
        document.getElementById('inNarasi2').value = narasi2; document.getElementById('outNarasi2').innerText = narasi2;
    }
}

function updateIkon(inputId, iconId, textId) {
    const elInput = document.getElementById(inputId);
    if (!elInput) return;
    const value = elInput.value; 
    if(document.getElementById(iconId)) {
        document.getElementById(iconId).src = value + ".png";
        let teksTampil = value.replace(/_/g, ' ').replace(' Malam', '');
        document.getElementById(textId).innerText = teksTampil.toUpperCase();
    }
}

// EVENT LISTENER ENGINE PRAKICU
document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // 🟢 SUNTIKAN ROBOT KALENDER OTOMATIS DI SINI
    // ==========================================
    const elPilihTanggal = document.getElementById('inPilihTanggal');
    if(elPilihTanggal) {
        // Setel ke hari ini saat pertama kali web dibuka
        if(!elPilihTanggal.value) {
            const hariIni = new Date();
            const yyyy = hariIni.getFullYear();
            const mm = String(hariIni.getMonth() + 1).padStart(2, '0');
            const dd = String(hariIni.getDate()).padStart(2, '0');
            elPilihTanggal.value = `${yyyy}-${mm}-${dd}`;
        }
        
        // Fungsi untuk merakit format tanggal & hari
        const prosesTanggal = () => {
            if(!elPilihTanggal.value) return;
            const dateObj = new Date(elPilihTanggal.value);
            const hariArray = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
            const bulanArray = ['JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI', 'JULI', 'AGUSTUS', 'SEPTEMBER', 'OKTOBER', 'NOVEMBER', 'DESEMBER'];
            
            document.getElementById('inHari').value = hariArray[dateObj.getDay()];
            
            // 🟢 JURUS ZERO PADDING (01, 02, 03...):
            const tglString = String(dateObj.getDate()).padStart(2, '0');
            document.getElementById('inTanggal').value = `${tglString} ${bulanArray[dateObj.getMonth()]} ${dateObj.getFullYear()}`;
            
            updateSemuanya(); // Segarkan canvas & narasi otomatis
        };

        // Eksekusi saat user mengklik/memilih tanggal di kalender
        elPilihTanggal.addEventListener('change', prosesTanggal);
        // Eksekusi paksa saat web pertama kali dimuat
        prosesTanggal();
    }
    // ==========================================

    // KODE ASLIMU BERLANJUT DI BAWAH SINI
    if(document.getElementById('inNarasi1')) {
        document.getElementById('inNarasi1').addEventListener('input', function(e) { document.getElementById('outNarasi1').innerText = e.target.value; });
        document.getElementById('inNarasi2').addEventListener('input', function(e) { document.getElementById('outNarasi2').innerText = e.target.value; });

        const daftarInputPrakicu = ['inHari', 'inTanggal', 'inUmum', 'inHujan', 'inCuacaPagi', 'inCuacaSiang', 'inCuacaMalam', 'inCuacaDiniHari', 'inSuhuMin', 'inSuhuMax', 'inLembapMin', 'inLembapMax', 'inAnginDari', 'inAnginMenuju', 'inAnginSpeed', 'inPeringatan'];
        
        daftarInputPrakicu.forEach(id => {
            const el = document.getElementById(id);
            if(el) {
                el.addEventListener('input', function() {
                    updateSemuanya();
                    if(id.startsWith('inCuaca')) {
                        if(id === 'inCuacaPagi') updateIkon('inCuacaPagi', 'iconPagi', 'teksPagi');
                        if(id === 'inCuacaSiang') updateIkon('inCuacaSiang', 'iconSiang', 'teksSiang');
                        if(id === 'inCuacaMalam') updateIkon('inCuacaMalam', 'iconMalam', 'teksMalam');
                        if(id === 'inCuacaDiniHari') updateIkon('inCuacaDiniHari', 'iconDiniHari', 'teksDiniHari');
                    }
                });
            }
        });
    }
});


// ====================================================================
// 📥 FITUR DOWNLOAD HD (SISTEM KARANTINA IFRAME - OPTIMIZED FILE SIZE)
// ====================================================================

// Menambahkan parameter format dan kualitas agar ukuran file PDF bisa dikontrol
async function tangkapDiRuangKarantina(elementId, skala, format = 'image/png', kualitas = 1.0) {
    return new Promise((resolve, reject) => {
        const elemenAsli = document.getElementById(elementId);
        if(!elemenAsli) {
            reject("Elemen HTML tidak ditemukan"); return;
        }
        
        // 1. Buat Ruangan Kaca (Iframe) rahasia
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.top = '-9999px'; // Sembunyikan jauh di atas layar
        iframe.style.width = '800px';
        iframe.style.height = '800px';
        document.body.appendChild(iframe);

        const doc = iframe.contentWindow.document;
        
        // 2. Suntikkan HTML & CSS murni
        doc.open();
        doc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    /* CSS SUCI TANPA TAILWIND */
                    body { margin: 0; padding: 0; font-family: 'times new roman', sans-serif; }
                    .slide-cuaca { 
                        position: relative; 
                        width: 800px; 
                        height: 800px; 
                        overflow: hidden; 
                        background-color: white; 
                    }
                    .bg-template { 
                        position: absolute; 
                        top: 0; 
                        left: 0; 
                        width: 100%; 
                        height: 100%; 
                        display: block; 
                        object-fit: cover;
                        z-index: 1;
                    }
                    .teks-absolut { 
                        position: absolute; 
                        z-index: 10; 
                    }
                    /* Pastikan ikon tidak melar */
                    img.teks-absolut { max-width: none; }
                </style>
            </head>
            <body>
                ${elemenAsli.outerHTML}
                
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <script>
                    window.onload = function() {
                        // Beri waktu 0.5 detik agar gambar/font termuat sempurna
                        setTimeout(() => {
                            html2canvas(document.getElementById('${elementId}'), {
                                scale: ${skala},
                                useCORS: true,
                                allowTaint: true,
                                backgroundColor: '#ffffff'
                            }).then(canvas => {
                                // Kirim hasil jepretan keluar ruangan kaca dengan format kompresi dinamis
                                window.parent.postMessage({ 
                                    id: '${elementId}', 
                                    gambarBase64: canvas.toDataURL('${format}', ${kualitas}) 
                                }, '*');
                            }).catch(err => {
                                window.parent.postMessage({ id: '${elementId}', error: err.message }, '*');
                            });
                        }, 500); 
                    };
                </script>
            </body>
            </html>
        `);
        doc.close();

        // 3. Tangkap hasil jepretan yang dilempar dari dalam ruangan kaca
        const penangkapPesan = (event) => {
            if (event.data && event.data.id === elementId) {
                window.removeEventListener('message', penangkapPesan); // Matikan radio
                document.body.removeChild(iframe); // Hancurkan ruangan kaca
                if(event.data.error) {
                    reject(event.data.error);
                } else {
                    resolve(event.data.gambarBase64); // Selesai!
                }
            }
        };
        window.addEventListener('message', penangkapPesan);
    });
}

// EKSEKUSI TOMBOL DOWNLOAD (DIBUNGKUS DOMContentLoaded AGAR AMAN)
document.addEventListener("DOMContentLoaded", () => {
    const btnDownloadGambar = document.getElementById('btnDownloadGambar');
    const btnDownloadPDF = document.getElementById('btnDownloadPDF');

    // UNTUK GAMBAR (Sekarang format JPEG terkompresi agar file ringan!)
    if(btnDownloadGambar) {
        btnDownloadGambar.addEventListener('click', async function() {
            const btn = this; const teksAsli = btn.innerText; 
            btn.innerText = "⏳ Loading..."; btn.disabled = true;
            
            try {
                // 1. Tangkap tanggal dari input, hilangkan spasi awal/akhir, ganti spasi tengah jadi underscore
                let namaTanggal = document.getElementById('inTanggal').value.trim().replace(/\s+/g, '_');
                if (!namaTanggal) namaTanggal = "Hari_Ini"; // Jaga-jaga kalau kosong

                // 🟢 OPERASI DIET: Skala turun ke 3 (Cukup HD), format JPEG, kualitas 85% (0.85)
                const gambarJadi = await tangkapDiRuangKarantina('slide2', 3, 'image/jpeg', 0.85); 
                
                const link = document.createElement('a');
                // 🟢 Ekstensi diubah dari .png menjadi .jpg
                link.download = `Prakicu_WAKT_${namaTanggal}.jpg`;
                link.href = gambarJadi; 
                link.click();
            } catch (err) {
                alert("Gagal mengunduh gambar."); console.error(err);
            } finally {
                btn.innerText = teksAsli; btn.disabled = false;
            }
        });
    }

    // UNTUK PDF (4 SLIDE - SEKARANG DIKOMPRESI SUPER RINGAN!)
    if(btnDownloadPDF) {
        btnDownloadPDF.addEventListener('click', async function() {
            const btn = this; const teksAsli = btn.innerText; 
            btn.innerText = "⏳ Loading..."; btn.disabled = true;
            
            try {
                // 1. Tangkap tanggal dari input
                let namaTanggal = document.getElementById('inTanggal').value.trim().replace(/\s+/g, '_');
                if (!namaTanggal) namaTanggal = "Hari_Ini";

                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF('p', 'px', [800, 800]); 
                const slides = ['slide1', 'slide2', 'slide3', 'slide4'];
                
                for (let i = 0; i < slides.length; i++) {
                    const gambarJadi = await tangkapDiRuangKarantina(slides[i], 2, 'image/jpeg', 0.7); 
                    pdf.addImage(gambarJadi, 'JPEG', 0, 0, 800, 800, undefined, 'FAST');
                    if (i < slides.length - 1) pdf.addPage();
                }
                
                // 2. 💉 SUNTIKAN NAMA FILE DINAMIS SAAT SAVE PDF
                pdf.save(`Prakicu_WAKT_${namaTanggal}.pdf`);
            } catch (err) {
                alert("Gagal mengunduh PDF."); console.error(err);
            } finally {
                btn.innerText = teksAsli; btn.disabled = false;
            }
        });
    }
});