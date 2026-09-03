function inisialisasiFormTafor() {
    const elBulan = document.getElementById('inRilisBulan');
    if(!elBulan) return;
    const namaBulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
    const bulanSkrg = new Date().getUTCMonth();
    for (let i = 0; i < 12; i++) elBulan.options.add(new Option(namaBulan[i], i, i === bulanSkrg, i === bulanSkrg));
    perbaruiDropdownTanggal(true);
}

function perbaruiDropdownTanggal(awalLahir = false) {
    const bulanVal = parseInt(document.getElementById('inRilisBulan')?.value || "0");
    const elTanggal = document.getElementById('inRilisTgl');
    if (!elTanggal) return;
    let valSebelumnya = awalLahir ? new Date().getUTCDate() : parseInt(elTanggal.value || "1");
    let tahunSkrg = new Date().getUTCFullYear();
    let maxTgl = new Date(Date.UTC(tahunSkrg, bulanVal + 1, 0)).getUTCDate();
    elTanggal.innerHTML = "";
    for(let i = 1; i <= maxTgl; i++) elTanggal.options.add(new Option(i < 10 ? "0"+i : ""+i, i < 10 ? "0"+i : ""+i));
    if (valSebelumnya > maxTgl) valSebelumnya = maxTgl;
    elTanggal.value = valSebelumnya < 10 ? "0"+valSebelumnya : valSebelumnya;
    hitungOtomatisWaktuBerlaku();
}

function hitungOtomatisWaktuBerlaku() {
    const blnVal = parseInt(document.getElementById('inRilisBulan')?.value || "0");
    const tglVal = parseInt(document.getElementById('inRilisTgl')?.value || "1");
    const jamStr = document.getElementById('inRilisJam')?.value || "0000";
    const jamVal = parseInt(jamStr.substring(0, 2)); 

    const type = document.getElementById('inType')?.value || "TAF";

    const tahunSkrg = new Date().getUTCFullYear();
    let dtRilis = new Date(Date.UTC(tahunSkrg, blnVal, tglVal, jamVal, 0, 0));
    let dtStart = new Date(dtRilis.getTime() + (1 * 60 * 60 * 1000));
    let dtEnd = new Date(dtStart.getTime() + (24 * 60 * 60 * 1000));

    if (type === "TAF") {
        if(document.getElementById('inValidTglStart')) document.getElementById('inValidTglStart').value = String(dtStart.getUTCDate()).padStart(2, '0');
        if(document.getElementById('inValidJamStart')) document.getElementById('inValidJamStart').value = String(dtStart.getUTCHours()).padStart(2, '0');
        if(document.getElementById('inValidTglEnd')) document.getElementById('inValidTglEnd').value = String(dtEnd.getUTCDate()).padStart(2, '0');
        if(document.getElementById('inValidJamEnd')) document.getElementById('inValidJamEnd').value = String(dtEnd.getUTCHours()).padStart(2, '0');
    } else if (type === "TAF AMD") {
        dtStart = dtRilis; 
        if(document.getElementById('inValidTglStart')) document.getElementById('inValidTglStart').value = String(dtStart.getUTCDate()).padStart(2, '0');
        if(document.getElementById('inValidJamStart')) document.getElementById('inValidJamStart').value = String(dtStart.getUTCHours()).padStart(2, '0');
    }

    updateDropdownTrend('inTrend1JamStart', 'inTrend1JamEnd', dtStart);
    updateDropdownTrend('inTrend2JamStart', 'inTrend2JamEnd', dtStart);

    prosesGenerateTaforSam();
}

function ubahModeSandiTaf() {
    const type = document.getElementById('inType')?.value || "TAF";
    const inputTglStart = document.getElementById('inValidTglStart');
    const inputJamStart = document.getElementById('inValidJamStart');
    const inputTglEnd = document.getElementById('inValidTglEnd');
    const inputJamEnd = document.getElementById('inValidJamEnd');

    if(!inputTglStart || !inputJamStart || !inputTglEnd || !inputJamEnd) return;

    if (type === "TAF") {
        inputTglStart.disabled = true; inputJamStart.disabled = true;
        inputTglEnd.disabled = true; inputJamEnd.disabled = true;
        inputTglStart.classList.add('bg-slate-100', 'text-slate-500');
        inputJamStart.classList.add('bg-slate-100', 'text-slate-500');
        inputTglEnd.classList.add('bg-slate-100', 'text-slate-500');
        inputJamEnd.classList.add('bg-slate-100', 'text-slate-500');
        hitungOtomatisWaktuBerlaku();
    } else {
        inputTglStart.disabled = false; inputJamStart.disabled = false;
        inputTglEnd.disabled = false; inputJamEnd.disabled = false;
        inputTglStart.classList.remove('bg-slate-100', 'text-slate-500');
        inputJamStart.classList.remove('bg-slate-100', 'text-slate-500');
        inputTglEnd.classList.remove('bg-slate-100', 'text-slate-500');
        inputJamEnd.classList.remove('bg-slate-100', 'text-slate-500');
        
        if (type === "TAF AMD") {
            inputTglStart.value = document.getElementById('inRilisTgl')?.value || "01";
            inputJamStart.value = (document.getElementById('inRilisJam')?.value || "0000").substring(0, 2);
        }
        prosesGenerateTaforSam();
    }
}

function updateDropdownTrend(idStart, idEnd, dtStart) {
    const elStart = document.getElementById(idStart); 
    const elEnd = document.getElementById(idEnd);
    if (!elStart || !elEnd) return;
    const valStartLama = elStart.value; const valEndLama = elEnd.value;

    elStart.innerHTML = ""; elEnd.innerHTML = "";
    
    for(let i = 0; i <= 24; i++) {
        let dtLoop = new Date(dtStart.getTime() + (i * 60 * 60 * 1000));
        let gabung = `${String(dtLoop.getUTCDate()).padStart(2,'0')}${String(dtLoop.getUTCHours()).padStart(2,'0')}`;
        elStart.options.add(new Option(gabung, gabung)); 
        elEnd.options.add(new Option(gabung, gabung));
    }
    if(valStartLama) elStart.value = valStartLama;
    if(valEndLama) elEnd.value = valEndLama;
    if(!elStart.value && elStart.options.length > 0) elStart.selectedIndex = 0;
    if(!elEnd.value && elEnd.options.length > 0) elEnd.selectedIndex = 0;
}

function handleTrendToggleVisibility(idx) {
    const val = document.getElementById(`inTrend${idx}Type`)?.value || "NIL";
    const panel = document.getElementById(`panelTrend${idx}Options`);
    if(panel) panel.style.display = val === "NIL" ? "none" : "flex";
    prosesGenerateTaforSam();
}

// 🟢 HELPER ANGIN TREND (ZERO-NULL EXCEPTION)
function formatTrendWind(dirId, spdId, gustId) {
    let dir = document.getElementById(dirId)?.value?.trim();
    let spd = document.getElementById(spdId)?.value?.trim();
    let gust = document.getElementById(gustId)?.value?.trim();
    
    if (!dir || !spd) return ""; 
    
    dir = String(dir).padStart(3, '0');
    let spdVal = parseInt(spd) || 0;
    let spdFormatted = spdVal >= 100 ? "P99" : String(spdVal).padStart(2, '0');
    
    let gustStr = "";
    if (gust && parseInt(gust) > 0) {
        let gustVal = parseInt(gust);
        let gustFormatted = gustVal >= 100 ? "P99" : String(gustVal).padStart(2, '0');
        gustStr = "G" + gustFormatted;
    }
    return `${dir}${spdFormatted}${gustStr}KT`;
}

// 🟢 OTAK UTAMA PERAKIT TAFOR (ANTI-CRASH)
function prosesGenerateTaforSam() {
    try {
        const type = document.getElementById('inType')?.value || "TAF"; 
        const icao = document.getElementById('inIcao')?.value || "WAKT";
        const tglRilis = document.getElementById('inRilisTgl')?.value || "01"; 
        const jamRilis = (document.getElementById('inRilisJam')?.value || "0000").substring(0, 2);
        const startTgl = document.getElementById('inValidTglStart')?.value || "01"; 
        const startJam = document.getElementById('inValidJamStart')?.value || "00";
        const endTgl = document.getElementById('inValidTglEnd')?.value || "02"; 
        const endJam = document.getElementById('inValidJamEnd')?.value || "00";
        
        let windDir = document.getElementById('inWindDir')?.value || "000";
        windDir = String(windDir).padStart(3, '0');

        let windSpdInput = parseInt(document.getElementById('inWindSpd')?.value || "0"); 
        let windSpd = windSpdInput >= 100 ? "P99" : String(windSpdInput).padStart(2, '0');
        
        let windGustInput = document.getElementById('inWindGust')?.value;
        let windGustStr = "";
        if (windGustInput && parseInt(windGustInput) > 0) {
            let gustVal = parseInt(windGustInput);
            let gustFormatted = gustVal >= 100 ? "P99" : String(gustVal).padStart(2, '0');
            windGustStr = "G" + gustFormatted;
        }

        let finalWindStr = windDir + windSpd + windGustStr + "KT";

        const vis = document.getElementById('inVisibility')?.value || "9999"; 
        const wth = document.getElementById('inCuacaGroup')?.value || "NIL";
        const cldJml = document.getElementById('inAwanJumlah')?.value || "NSC"; 
        let cldTgiRaw = document.getElementById('inAwanTinggi')?.value;
        const cldTyp = document.getElementById('inAwanType')?.value || "NIL";
        
        let cldTgi = "000";
        if(cldTgiRaw) { let num = Math.floor(parseInt(cldTgiRaw) / 100); cldTgi = num < 10 ? "00" + num : (num < 100 ? "0" + num : num); }

        const wmoHeader = `FTID40 ${icao} ${tglRilis}${jamRilis}00`;
        
        let strBase = `${wmoHeader}\n${type} ${icao} ${tglRilis}${jamRilis}00Z ${startTgl}${startJam}/${endTgl}${endJam} ${finalWindStr} ${vis}`;
        
        if (wth !== "NIL") strBase += ` ${wth}`;
        if (cldJml === "NSC") { strBase += ` NSC`; } else { strBase += ` ${cldJml}${cldTgi}`; if (cldTyp !== "NIL") strBase += `${cldTyp}`; }
        
        // 🟢 PERAKITAN TREND 1
        const t1T = document.getElementById('inTrend1Type')?.value || "NIL";
        if (t1T !== "NIL") {
            const t1JS = document.getElementById('inTrend1JamStart')?.value || ""; 
            const t1JE = document.getElementById('inTrend1JamEnd')?.value || "";
            const t1Wind = formatTrendWind('inTrend1WindDir', 'inTrend1WindSpd', 'inTrend1WindGust');
            const t1V = document.getElementById('inTrend1Vis')?.value || "NIL"; 
            const t1W = document.getElementById('inTrend1Cuaca')?.value || "NIL";
            const t1CJ = document.getElementById('inTrend1AwanJumlah')?.value || "NIL"; 
            let t1CTgRaw = document.getElementById('inTrend1AwanTinggi')?.value;
            const t1CTy = document.getElementById('inTrend1AwanType')?.value || "NIL";
            
            strBase += ` \n${t1T} ${t1JS}/${t1JE}`;
            if (t1Wind !== "") strBase += ` ${t1Wind}`;
            if (t1V !== "NIL") strBase += ` ${t1V}`; 
            if (t1W !== "NIL") strBase += ` ${t1W}`;
            if (t1CJ !== "NIL") {
                let t1CTg = "000"; if (t1CTgRaw) { let num2 = Math.floor(parseInt(t1CTgRaw) / 100); t1CTg = num2 < 10 ? "00" + num2 : (num2 < 100 ? "0" + num2 : num2); }
                strBase += ` ${t1CJ}${t1CTg}`; if (t1CTy !== "NIL") strBase += `${t1CTy}`;
            }
        }
        
        // 🟢 PERAKITAN TREND 2
        const t2T = document.getElementById('inTrend2Type')?.value || "NIL";
        if (t2T !== "NIL") {
            const t2JS = document.getElementById('inTrend2JamStart')?.value || ""; 
            const t2JE = document.getElementById('inTrend2JamEnd')?.value || "";
            const t2Wind = formatTrendWind('inTrend2WindDir', 'inTrend2WindSpd', 'inTrend2WindGust');
            const t2V = document.getElementById('inTrend2Vis')?.value || "NIL"; 
            const t2W = document.getElementById('inTrend2Cuaca')?.value || "NIL";
            const t2CJ = document.getElementById('inTrend2AwanJumlah')?.value || "NIL"; 
            let t2CTgRaw = document.getElementById('inTrend2AwanTinggi')?.value;
            const t2CTy = document.getElementById('inTrend2AwanType')?.value || "NIL";
            
            strBase += ` \n${t2T} ${t2JS}/${t2JE}`;
            if (t2Wind !== "") strBase += ` ${t2Wind}`;
            if (t2V !== "NIL") strBase += ` ${t2V}`; 
            if (t2W !== "NIL") strBase += ` ${t2W}`;
            if (t2CJ !== "NIL") {
                let t2CTg = "000"; if (t2CTgRaw) { let num3 = Math.floor(parseInt(t2CTgRaw) / 100); t2CTg = num3 < 10 ? "00" + num3 : (num3 < 100 ? "0" + num3 : num3); }
                strBase += ` ${t2CJ}${t2CTg}`; if (t2CTy !== "NIL") strBase += `${t2CTy}`;
            }
        }
        
        strBase += "="; 
        const box = document.getElementById('taforOutputBox');
        if(box) box.innerText = strBase; 
        jalankanValidasiSandiAuto(strBase);
    } catch (err) { 
        console.error("ERROR GENERATOR TAFOR:", err); 
    }
}

function jalankanValidasiSandiAuto(sandi) {
    const vCard = document.getElementById('typoValidationCard'); 
    const vList = document.getElementById('typoValidationList'); 
    if (!vCard || !vList) return;
    vList.innerHTML = ""; let errors = [];
    if (!sandi.includes("KT")) errors.push("Grup angin kehilangan unit 'KT'.");
    if (!sandi.endsWith("=")) errors.push("Sandi TAFOR wajib ditutup tanda '='.");
    if (errors.length > 0) { errors.forEach(err => { let li = document.createElement('li'); li.innerText = err; vList.appendChild(li); }); vCard.classList.remove('hidden'); } else { vCard.classList.add('hidden'); }
}

// 1. FUNGSI PENYIMPAN RIWAYAT (Versi Kebal Error HTTP)
function salinKodeKeClipboardDanRekap() {
    const box = document.getElementById('taforOutputBox');
    if (!box) return;
    const hasilText = box.innerText;

    // Simpan ke Tabel Riwayat Log
    let logs = JSON.parse(localStorage.getItem('wakt_tafor_logs')) || []; 
    let w = new Date();
    let timestamp = `${w.getDate()}/${w.getMonth()+1}/${w.getFullYear()} ${String(w.getHours()).padStart(2,'0')}:${String(w.getMinutes()).padStart(2,'0')}`;
    logs.unshift({ time: timestamp, sandi: hasilText }); 
    if(logs.length > 20) logs.pop();
    localStorage.setItem('wakt_tafor_logs', JSON.stringify(logs)); 
    muatTabelLogRecapDariStorage();

    // Coba salin ke clipboard secara diam-diam (Abaikan jika browser memblokir IP Lokal)
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(hasilText).catch(e => {});
    }
}

function muatTabelLogRecapDariStorage() {
    let logs = JSON.parse(localStorage.getItem('wakt_tafor_logs')) || []; const tbody = document.getElementById('recapTableBody'); 
    if(!tbody) return; tbody.innerHTML = "";
    if(logs.length === 0) { tbody.innerHTML = `<tr><td class="text-center py-6 text-slate-400">Belum ada riwayat sandi.</td></tr>`; return; }
    logs.forEach(log => { tbody.innerHTML += `<tr class="hover:bg-slate-50"><td class="py-3 px-4 w-32 align-top text-xs text-slate-400 font-bold">${log.time}</td><td class="py-3 px-4"><span class="font-mono text-blue-700 bg-blue-50 px-2 py-1 rounded block whitespace-pre-wrap select-all">${log.sandi}</span></td></tr>`; });
}

function kosongkanSemuaLogHistory() {
    if(confirm("Yakin ingin menghapus history?")) { localStorage.removeItem('wakt_tafor_logs'); muatTabelLogRecapDariStorage(); }
}

// 2. FUNGSI KIRIM SUPER SIMPEL (Terkirim / Gagal Saja)
async function kirimKeBMKGSoft() {
    const box = document.getElementById('taforOutputBox');
    const hasilText = box ? box.innerText : "";
    
    if (!hasilText || hasilText === "Hasil..." || !hasilText.includes("TAF")) {
        tampilkanNotifikasi("Peringatan", "Generate TAFOR terlebih dahulu!", "error");
        return;
    }

    const btn = document.getElementById('btnKirimBMKG');
    const teksAsli = btn ? btn.innerText : "Kirim";
    if(btn) { btn.innerText = "⏳ Mengirim..."; btn.disabled = true; }

    try {
        const response = await fetch('/api/metar/kirim_bmkgsoft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ taf_text: hasilText })
        });

        const result = await response.json();
        
        if (result.status === "Sukses") {
            salinKodeKeClipboardDanRekap(); // Simpan ke log tabel bawah
            tampilkanNotifikasi("Sukses", "Sandi TAFOR berhasil terkirim!", "success");
        } else {
            tampilkanNotifikasi("Gagal", "Sandi TAFOR gagal terkirim.", "error");
        }
    } catch (err) {
        // Jika server python mati
        tampilkanNotifikasi("Gagal", "Sandi TAFOR gagal terkirim.", "error");
    } finally {
        if(btn) { btn.innerText = teksAsli; btn.disabled = false; }
    }
}

// =======================================================
// 🚀 REMOTE CONTROL AUTOSEND PYTHON (JALUR BELAKANG)
// =======================================================

// 1. MENGIRIM PERINTAH AUTOSEND KE PYTHON
window.aktifkanAutosend = async function() {
    const timeInput = document.getElementById('waktu-autosend').value;
    const box = document.getElementById('taforOutputBox');
    const tafText = box ? box.innerText : "";
    
    if (!timeInput) {
        tampilkanNotifikasi("Peringatan", "Pilih jam autosend terlebih dahulu!", "error");
        return;
    }
    if (!tafText || tafText.includes("Hasil...")) {
        tampilkanNotifikasi("Peringatan", "Generate TAFOR terlebih dahulu!", "error");
        return;
    }

    try {
        const response = await fetch('/api/metar/set_autosend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ waktu: timeInput, taf_text: tafText })
        });
        const data = await response.json();
        
        if(data.status === "Sukses") {
            document.getElementById('status-autosend').innerHTML = `⏳ Autosend Aktif: <b>${timeInput} WIT</b> (Browser aman ditutup)`;
            document.getElementById('status-autosend').className = "text-xs font-bold text-amber-700 bg-amber-100 px-3 py-2 rounded-lg border border-amber-300 flex-1 text-center";
            document.getElementById('btn-batal-autosend').classList.remove('hidden');
            tampilkanNotifikasi("Autosend Aktif", data.pesan, "success");
        }
    } catch (e) {
        tampilkanNotifikasi("Error", "Gagal menghubungi mesin server", "error");
    }
};

// 2. MEMBATALKAN PERINTAH DI PYTHON
window.batalkanAutosend = async function() {
    try {
        await fetch('/api/metar/cancel_autosend', { method: 'POST' });
        document.getElementById('status-autosend').innerHTML = "Menunggu instruksi...";
        document.getElementById('status-autosend').className = "text-xs font-bold text-slate-500 bg-white px-3 py-2 rounded-lg border flex-1 text-center";
        document.getElementById('btn-batal-autosend').classList.add('hidden');
        document.getElementById('waktu-autosend').value = "";
    } catch (e) {}
};

// 3. (FUNGSI BARU) MENGECEK STATUS JIKA KAPTEN ME-REFRESH WEB
async function cekStatusAutosendRemote() {
    try {
        const response = await fetch('/api/metar/status_autosend');
        const data = await response.json();
        if(data.status === "Aktif") {
            document.getElementById('waktu-autosend').value = data.waktu;
            document.getElementById('status-autosend').innerHTML = `⏳ Autosend Aktif: <b>${data.waktu} WIT</b> (Browser aman ditutup)`;
            document.getElementById('status-autosend').className = "text-xs font-bold text-amber-700 bg-amber-100 px-3 py-2 rounded-lg border border-amber-300 flex-1 text-center";
            document.getElementById('btn-batal-autosend').classList.remove('hidden');
        }
    } catch (e) {}
}

// Panggil fungsi cek ini setiap kali web dibuka (Sinkronisasi dengan server)
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(cekStatusAutosendRemote, 1000);
});