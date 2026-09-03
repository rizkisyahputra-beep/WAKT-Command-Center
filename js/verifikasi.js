let DATA_GLOBAL_VERIF_CACHE = null;
let APPS_CURRENT_DAY_ACTIVE = "1";
let DATA_BUFFER_CSV = [];

// 🟢 MEMORI SILUMAN UNTUK MENYIMPAN SANDI SETELAH KOTAK DIKOSONGKAN
let CACHE_TAF_TEXT = "";

// 🟢 KUNCI BRANKAS LOKER DUMMY (Unik per bulan agar tidak saling timpa)
function getKunciLokerDummy() {
    const el = document.getElementById('input-bulan-verif');
    return "WAKT_METAR_DUMMY_" + (el ? el.value : "default");
}

function dapatkanEkstraktorTextareaTAF() {
    return document.getElementById('inTaforManual') || 
           document.getElementById('taf_text') || 
           document.getElementById('input-taf') || 
           document.querySelector('textarea');
}

// ====================================================================
// 🟢 FUNGSI PANEL RAHASIA (METAR DUMMY)
// ====================================================================
window.togglePanelMetarDummy = function() {
    const panel = document.getElementById('panel-metar-dummy');
    if(panel) panel.classList.toggle('hidden');
};

// 🔥 UBAHAN 1: Tombol Ungu menyimpan ke Hard-Disk Laptop + Langsung Hitung Ulang
window.simpanMetarDummyKeMemori = function() {
    const elMetarDummy = document.getElementById('in-metar-dummy');
    if (elMetarDummy && elMetarDummy.value.trim() !== "") {
        const teksBaru = elMetarDummy.value.trim();
        const kunci = getKunciLokerDummy();
        
        let laci = localStorage.getItem(kunci) || "";
        localStorage.setItem(kunci, laci ? laci + "\n" + teksBaru : teksBaru);
        
        elMetarDummy.value = ""; 
        togglePanelMetarDummy(); 
        
        hitungVerifikasiOtomatisSatuKlik(); // Paksa langsung update matrix saat itu juga
        
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Diamankan!", "METAR Dummy berhasil disimpan permanen ke memori lokal.", "success");
        } else {
            alert("METAR Dummy tersimpan di memori lokal!");
        }
    } else {
        alert("Kotak METAR masih kosong!");
    }
};

// ====================================================================
// 🟢 FUNGSI VERIFIKASI UTAMA (DENGAN MEMORI SILUMAN)
// ====================================================================
async function hitungVerifikasiOtomatisSatuKlik() {
    const bulan = document.getElementById('input-bulan-verif').value;
    if (!bulan) { alert("Silahkan tentukan bulan verifikasi!"); return; }

    const elTextarea = dapatkanEkstraktorTextareaTAF();
    let tafText = elTextarea && elTextarea.value.trim() !== "" ? elTextarea.value.trim() : CACHE_TAF_TEXT;

    // Sedot sisa ketikan di kotak ungu kalau Kapten lupa klik tombol ungu
    const elMetarDummy = document.getElementById('in-metar-dummy');
    if (elMetarDummy && elMetarDummy.value.trim() !== "") {
        const sisa = elMetarDummy.value.trim();
        const kunci = getKunciLokerDummy();
        let laci = localStorage.getItem(kunci) || "";
        localStorage.setItem(kunci, laci ? laci + "\n" + sisa : sisa);
        elMetarDummy.value = ""; 
    }
    
    let metarDummyText = localStorage.getItem(getKunciLokerDummy()) || "";
    
    if (!tafText) { alert("Sandi TAFOR belum dimasukkan!"); return; }

    const modal = document.getElementById('modal-loading'); 
    if(modal) {
        document.getElementById('loading-title').innerText = "Menghitung Matrix Web..."; 
        modal.classList.remove('hidden');
    }
    
    try {
        const response = await fetch('/api/metar/hitung_verifikasi', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ bulan: bulan, taf_text: tafText, metar_dummy: metarDummyText }) 
        });
        const hasil = await response.json(); 
        if(modal) modal.classList.add('hidden');
        
        if (hasil.status === "Sukses") {
            if(elTextarea) elTextarea.value = "";
            if(elMetarDummy) elMetarDummy.value = "";
            CACHE_TAF_TEXT = tafText;

            DATA_GLOBAL_VERIF_CACHE = hasil.data.detail_harian;
            
            if(document.getElementById('v-dir')) document.getElementById('v-dir').innerText = hasil.data.summary.arah_angin + "%";
            if(document.getElementById('v-spd')) document.getElementById('v-spd').innerText = hasil.data.summary.kecepatan_angin + "%";
            if(document.getElementById('v-vis')) document.getElementById('v-vis').innerText = hasil.data.summary.visibility + "%";
            if(document.getElementById('v-weather')) document.getElementById('v-weather').innerText = hasil.data.summary.cuaca + "%";
            if(document.getElementById('v-cld-jml')) document.getElementById('v-cld-jml').innerText = hasil.data.summary.awan_jumlah + "%";
            if(document.getElementById('v-cld-tgi')) document.getElementById('v-cld-tgi').innerText = hasil.data.summary.awan_tinggi + "%";
            if(document.getElementById('v-total')) document.getElementById('v-total').innerText = hasil.data.summary.total_score + "%";
            
            populasiNavigasiHariKustomExcel(Object.keys(DATA_GLOBAL_VERIF_CACHE).length);
            renderLembarKerjaHariExcelAktif(APPS_CURRENT_DAY_ACTIVE);
        } else {
            alert("Gagal memproses matrix: " + hasil.error);
        }
    } catch(e) { 
        if(modal) modal.classList.add('hidden'); 
        alert("Koneksi ke server terputus."); 
    }
}

async function suntikDataManualDanDownloadExcel() {
    const bulan = document.getElementById('input-bulan-verif').value;
    if (!bulan) {
        if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Peringatan", "Tentukan Bulan Laporan terlebih dahulu!", "error");
        else alert("Tentukan Bulan Laporan terlebih dahulu!");
        return;
    }

    const elManual = dapatkanEkstraktorTextareaTAF();
    let tafText = elManual ? elManual.value.trim() : "";

    // Amankan isi kotak METAR Dummy jika ada isinya
    const elMetarDummy = document.getElementById('in-metar-dummy');
    if (elMetarDummy && elMetarDummy.value.trim() !== "") {
        const sisa = elMetarDummy.value.trim();
        const kunci = getKunciLokerDummy();
        let laci = localStorage.getItem(kunci) || "";
        localStorage.setItem(kunci, laci ? laci + "\n" + sisa : sisa);
        elMetarDummy.value = "";
    }
    
    let metarDummyText = localStorage.getItem(getKunciLokerDummy()) || "";

    const modal = document.getElementById('modal-loading'); 
    if(modal) { document.getElementById('loading-title').innerText = "Mempersiapkan File Excel..."; modal.classList.remove('hidden'); }
    
    try {
        let urlEndpoint = '/api/metar/download_excel_resmi';
        let payload = { bulan: bulan, metar_dummy: metarDummyText };

        // 🟢 JALUR PINTAR: Jika ada input manual TAF, alihkan jalurnya ke API Injeksi
        if (tafText !== "") {
            if (!tafText.includes("WAKT")) {
                if(modal) modal.classList.add('hidden');
                if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Input Tidak Valid", "Harap paste minimal satu sandi TAFOR WAKT yang sah!", "error");
                else alert("Harap paste sandi TAFOR WAKT yang sah!");
                return;
            }
            urlEndpoint = '/api/metar/inject_manual_taf';
            payload.taf_text = tafText;
        }

        const response = await fetch(urlEndpoint, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(payload) 
        });
        
        if (!response.ok) { 
            const err = await response.json(); 
            if(modal) modal.classList.add('hidden'); 
            if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Error Server", err.error, "error");
            else alert("Error Server: " + err.error);
            return; 
        }

        if(elManual) elManual.value = "";
        if(elMetarDummy) elMetarDummy.value = "";

        const blob = await response.blob(); 
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a'); 
        a.href = url; 
        a.download = `VERIFIKASI_TAF_${bulan}_WAKT.xlsm`;
        document.body.appendChild(a); 
        a.click(); 
        document.body.removeChild(a); 
        window.URL.revokeObjectURL(url);
        
        if(modal) modal.classList.add('hidden');
        
        // 🟢 POP-UP SUKSES PROFESIONAL
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Berhasil!", "File Excel Verifikasi TAF berhasil diunduh.", "success");
        }
    } catch (err) { 
        if(modal) modal.classList.add('hidden'); 
        if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Koneksi Terputus", "Gagal mengunduh Excel.", "error");
        else alert("Gagal mengunduh Excel.");
    }
}

function populasiNavigasiHariKustomExcel(totalHari) {
    const container = document.getElementById('container-nav-hari-excel');
    if(!container) return;
    container.innerHTML = "";
    
    const btnRekap = document.createElement('button');
    btnRekap.innerHTML = "📊 LIHAT REKAP BULANAN";
    btnRekap.onclick = () => { selectActiveExcelSheetDay("REKAP"); };
    btnRekap.className = (APPS_CURRENT_DAY_ACTIVE === "REKAP")
        ? "col-span-2 py-2 mb-2 text-center rounded-lg font-bold text-xs bg-blue-700 text-white border border-blue-800 shadow-md block w-full"
        : "col-span-2 py-2 mb-2 text-center rounded-lg font-bold text-xs bg-slate-800 text-slate-100 hover:bg-slate-700 transition-all block w-full";
    container.appendChild(btnRekap);

    for (let i = 1; i <= totalHari; i++) {
        const btn = document.createElement('button');
        btn.innerText = `Tgl ${i}`; btn.id = `btn-sheet-day-${i}`;
        btn.onclick = () => { selectActiveExcelSheetDay(String(i)); };
        btn.className = (String(i) === APPS_CURRENT_DAY_ACTIVE) 
            ? "py-1.5 text-center rounded-lg font-bold text-xs bg-emerald-600 text-white border border-emerald-700 shadow-sm"
            : "py-1.5 text-center rounded-lg font-medium text-xs bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100 transition-all";
        container.appendChild(btn);
    }
}

function selectActiveExcelSheetDay(dayStr) {
    APPS_CURRENT_DAY_ACTIVE = dayStr;
    populasiNavigasiHariKustomExcel(DATA_GLOBAL_VERIF_CACHE ? Object.keys(DATA_GLOBAL_VERIF_CACHE).length : 28);
    renderLembarKerjaHariExcelAktif(APPS_CURRENT_DAY_ACTIVE);
}

function renderLembarKerjaHariExcelAktif(dayStr) {
    if (!DATA_GLOBAL_VERIF_CACHE) return;
    const tbody = document.getElementById('matrix-sheet-tbody-excel'); 
    if(!tbody) return;
    tbody.innerHTML = "";
    
    const colorSkor = (val) => val === 1 ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800";
    const listSiklus = ["00Z", "06Z", "12Z", "18Z"];

    if (dayStr === "REKAP") {
        if(document.getElementById('label-hari-aktif-sheet')) document.getElementById('label-hari-aktif-sheet').innerText = "📊 Lembar Ringkasan Rekap Bulanan (Sheet REKAP)";
        
        Object.keys(DATA_GLOBAL_VERIF_CACHE).forEach(hariKey => {
            listSiklus.forEach(siklusKey => {
                if (!DATA_GLOBAL_VERIF_CACHE[hariKey][siklusKey]) return;
                const c_sum = DATA_GLOBAL_VERIF_CACHE[hariKey][siklusKey].cycle_summary;
                
                const tr = document.createElement('tr');
                tr.className = "hover:bg-blue-50/40 divide-x divide-slate-300 text-[11px] h-9 border-b border-slate-300 font-semibold text-center";
                tr.innerHTML = `
                    <td class="font-bold text-blue-900 bg-slate-50">${String(hariKey).padStart(2, '0')}</td>
                    <td class="font-bold text-emerald-700 bg-slate-50">${siklusKey}</td>
                    <td class="text-slate-400 text-[10px] font-bold">RECAP</td>
                    <td colspan="8" class="bg-slate-50/50 text-slate-400 text-right pr-4 text-[10px] uppercase tracking-wider">Akurasi Siklus ➔</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.arah}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.speed}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.gust}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.vis}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.cuaca}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.awan_jml}%</td>
                    <td colspan="2" class="bg-emerald-100 text-emerald-900 font-black">${c_sum.awan_tgi}%</td>
                `;
                tbody.appendChild(tr);
            });
        });
        return;
    }

    if (!DATA_GLOBAL_VERIF_CACHE[dayStr]) return;
    if(document.getElementById('label-hari-aktif-sheet')) document.getElementById('label-hari-aktif-sheet').innerText = `Tgl_${dayStr} (Lembar Evaluasi Harian)`;
    
    listSiklus.forEach(siklusKey => {
        if (!DATA_GLOBAL_VERIF_CACHE[dayStr][siklusKey]) return;
        const dataSiklus = DATA_GLOBAL_VERIF_CACHE[dayStr][siklusKey];
        const trHeader = document.createElement('tr');
        trHeader.className = "bg-slate-100 font-bold border-b border-t border-slate-300 h-8 text-[11px]";
        trHeader.innerHTML = `
            <td colspan="3" class="text-left px-3 text-emerald-700 font-bold">SIKLUS TAFOR ${siklusKey}</td>
            <td colspan="24" class="text-left px-2 font-mono font-bold text-slate-700 bg-emerald-50/50 select-all">Prakiraan : ${dataSiklus.taf_raw}</td>
        `;
        tbody.appendChild(trHeader);
        
        dataSiklus.rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50 divide-x divide-slate-300 text-[11px] h-9 border-b border-slate-300 text-center";
            tr.innerHTML = `
                <td class="font-sans font-medium text-slate-500">${row.tanggal_row}</td>
                <td class="font-sans text-slate-600">${row.jam_row}</td>
                <td class="font-sans text-slate-400 text-[10px]">${row.group_row}</td>
                <td>${row.t.arah}</td><td>${row.t.speed}</td><td>${row.t.gust}</td><td>${row.t.vis}</td><td>${row.t.cuaca}</td><td>${row.t.awan_jml}</td><td>${row.t.awan_tgi}</td>
                <td class="text-left px-2 font-mono text-[10px] text-blue-800 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap select-all" title="${row.metar_raw}">${row.metar_raw}</td>
                <td>${row.m.arah}</td><td class="${colorSkor(row.skor.arah)}">${row.skor.arah}</td>
                <td>${row.m.speed}</td><td class="${colorSkor(row.skor.speed)}">${row.skor.speed}</td>
                <td>${row.m.gust}</td><td class="${colorSkor(row.skor.gust)}">${row.skor.gust}</td>
                <td>${row.m.vis}</td><td class="${colorSkor(row.skor.vis)}">${row.skor.vis}</td>
                <td>${row.m.cuaca}</td><td class="${colorSkor(row.skor.cuaca)}">${row.skor.cuaca}</td>
                <td>${row.m.awan_jml}</td><td class="${colorSkor(row.skor.awan_jml)}">${row.skor.awan_jml}</td>
                <td>${row.m.awan_tgi}</td><td class="${colorSkor(row.skor.awan_tgi)}">${row.skor.awan_tgi}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

// ====================================================================
// 🟢 FUNGSI DATABASE LOG (PINTU DARURAT MANUAL)
// ====================================================================
let CACHED_LOGS_DATA = []; 
let CURRENT_LOG_TAB = 'METAR'; 

async function loadDatabaseLogsFromServer() {
    try {
        const elBulan = document.getElementById('input-bulan');
        const bulan = elBulan ? elBulan.value : "";
        const response = await fetch(`/api/metar/logs?bulan=${bulan}`); 
        const data = await response.json();
        CACHED_LOGS_DATA = data; 
        
        const totalMetar = data.filter(row => row.sandi_metar.includes("METAR") || row.sandi_metar.includes("SPECI")).length;
        const totalTaf = data.filter(row => row.sandi_metar.includes("TAF")).length;
        
        const badgeMetar = document.getElementById('total-metar'); if(badgeMetar) badgeMetar.innerText = totalMetar;
        const badgeTaf = document.getElementById('total-taf'); if(badgeTaf) badgeTaf.innerText = totalTaf;
        renderLogsByTab();
    } catch (err) { console.log(err); }
}

function renderLogsByTab() {
    const tbody = document.getElementById('tabel-log');
    if (!tbody) return;
    let filteredData = [];
    if (CURRENT_LOG_TAB === 'METAR') {
        filteredData = CACHED_LOGS_DATA.filter(row => row.sandi_metar.includes("METAR") || row.sandi_metar.includes("SPECI"));
    } else {
        filteredData = CACHED_LOGS_DATA.filter(row => row.sandi_metar.includes("TAF"));
    }
    
    const badgeTotal = document.getElementById('total-row');
    if(badgeTotal) badgeTotal.innerText = filteredData.length;
    
    if (filteredData.length === 0) { 
        tbody.innerHTML = `<tr><td colspan="3" class="text-center py-12 text-slate-400 font-medium">Tidak ada data ${CURRENT_LOG_TAB} di bulan ini.</td></tr>`; 
        return; 
    }
    
    tbody.innerHTML = filteredData.map((row, index) => {
        let warningTag = "";
        let isMetar = row.sandi_metar.includes("METAR") || row.sandi_metar.includes("SPECI");
        if (isMetar) {
            let s = row.sandi_metar;
            let hasCloud = /FEW|SCT|BKN|OVC|NSC|NCD|CAVOK/.test(s);
            let hasVis = /\b\d{4}\b/.test(s) || s.includes("CAVOK");
            let hasTrend = /NOSIG|TEMPO|BECMG/.test(s); 
            let hasWeather = /([-+])?(RA|TS|DZ|SH|GR|GS|HZ|BR|FG|FU|SQ)/.test(s);
            let missing = [];
            if (!hasVis) missing.push("VIS");
            if (!hasCloud) missing.push("AWAN");
            if (!hasTrend && !hasWeather) missing.push("NOSIG");
            if (missing.length > 0) warningTag = `<span class="bg-red-100 text-red-700 border border-red-200 text-[10px] px-2 py-0.5 rounded-md font-black ml-2 animate-pulse">⚠️ KURANG: ${missing.join(' & ')}</span>`;
        }

        return `
        <tr class="hover:bg-slate-50/80 group">
            <td class="py-3 px-6 text-center text-slate-400 font-mono w-16">${index + 1}</td>
            <td class="py-3 px-6 text-slate-600 font-semibold font-mono w-48">${row.waktu_rekam}</td>
            <td class="py-3 px-6 relative">
                <div class="flex items-center justify-between gap-4">
                    <span class="${isMetar ? 'bg-blue-50/60 text-blue-800 border border-blue-100' : 'bg-emerald-50/60 text-emerald-800 border border-emerald-100'} font-mono px-3 py-1.5 rounded-lg block w-full tracking-wide select-all">
                        ${row.sandi_metar} ${warningTag}
                    </span>
                    <div class="opacity-0 group-hover:opacity-100 flex items-center gap-2 shrink-0 transition-all">
                        <button onclick="editLogManual(${row.id}, '${row.sandi_metar.replace(/'/g, "\\'")}')" class="bg-amber-100 hover:bg-amber-200 text-amber-700 border border-amber-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-all">✏️ Edit</button>
                        <button onclick="hapusLogManual(${row.id})" class="bg-red-100 hover:bg-red-200 text-red-700 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-all">🗑️ Hapus</button>
                    </div>
                </div>
            </td>
        </tr>`;
    }).join('');
}

window.setLogTab = function(tabName) {
    CURRENT_LOG_TAB = tabName;
    const btnMetar = document.getElementById('tab-log-metar');
    const btnTaf = document.getElementById('tab-log-taf');
    if (tabName === 'METAR') {
        btnMetar.className = "px-5 py-2.5 text-sm font-black border-b-2 border-blue-600 text-blue-600 transition-all flex items-center gap-2";
        btnTaf.className = "px-5 py-2.5 text-sm font-medium border-b-2 border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 transition-all flex items-center gap-2";
    } else {
        btnTaf.className = "px-5 py-2.5 text-sm font-black border-b-2 border-emerald-600 text-emerald-600 transition-all flex items-center gap-2";
        btnMetar.className = "px-5 py-2.5 text-sm font-medium border-b-2 border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 transition-all flex items-center gap-2";
    }
    renderLogsByTab();
}

window.editLogManual = async function(id, sandiLama) {
    const sandiBaru = prompt("KOREKSI SANDI (Gunakan HURUF KAPITAL):", sandiLama);
    if (!sandiBaru || sandiBaru === sandiLama) return;
    try {
        const response = await fetch('/api/metar/edit_log', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, sandi_metar: sandiBaru.trim().toUpperCase() })
        });
        const result = await response.json();
        if (result.status === "Sukses") { loadDatabaseLogsFromServer(); } else { alert("Gagal: " + result.error); }
    } catch (e) { alert("Error koneksi server."); }
};

window.hapusLogManual = async function(id) {
    if (!confirm("Hapus sandi ini secara permanen dari database lokal?")) return;
    try {
        const response = await fetch('/api/metar/delete_log', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        const result = await response.json();
        if (result.status === "Sukses") { loadDatabaseLogsFromServer(); } else { alert("Gagal: " + result.error); }
    } catch (e) { alert("Error koneksi server."); }
};

// 🟢 JS PERBAIKAN: Sekarang dia punya telinga untuk menerima 'tipeData'
window.mulaiSinkronisasiInternetGrosir = async function(tipeData = 'metar') {
    const bulanInput = document.getElementById('input-bulan').value;
    if (!bulanInput) return alert("Pilih bulan di kalender terlebih dahulu!");

    // Ekstrak tahun dan bulan dari kalender
    const [tahunStr, bulanStr] = bulanInput.split('-');
    const tahun = parseInt(tahunStr);
    const bulan = parseInt(bulanStr);

    const modal = document.getElementById('modal-loading'); 
    let labelTeks = tipeData === 'taf' ? "Menarik TAFOR..." : "Menarik METAR...";
    if(modal) { document.getElementById('loading-title').innerText = labelTeks; modal.classList.remove('hidden'); }
    
    try {
        // 🚀 SEKARANG DIA MENGIRIM TIPE, TAHUN, DAN BULAN KE PYTHON!
        const payloadKirim = { tipe: tipeData, tahun: tahun, bulan: bulan };
        const response = await fetch('/api/metar/sync_pilihan', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(payloadKirim) 
        });
        const hasil = await response.json(); 
        if(modal) modal.classList.add('hidden');
        
        if (hasil.status === "Sukses") { 
            // 🟢 PANGGIL POP-UP PROFESIONAL
            if (typeof tampilkanNotifikasi === "function") {
                tampilkanNotifikasi("Sinkronisasi Berhasil!", `Ditemukan ${hasil.total_baru} sandi ${tipeData.toUpperCase()} baru.`, "success");
            } else {
                alert(`Berhasil memperbarui database! Ditemukan ${hasil.total_baru} sandi ${tipeData.toUpperCase()} baru.`); 
            }
            
            // Pindah tab otomatis sesuai yang ditarik
            setLogTab(tipeData === 'taf' ? 'TAF' : 'METAR');
            loadDatabaseLogsFromServer(); 
        } else {
            // 🔴 PANGGIL POP-UP ERROR PROFESIONAL
            if (typeof tampilkanNotifikasi === "function") {
                tampilkanNotifikasi("Sinkronisasi Gagal", hasil.error, "error");
            } else {
                alert("Gagal: " + hasil.error);
            }
        }
    } catch(e) { 
        if(modal) modal.classList.add('hidden'); 
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Koneksi Terputus", "Gagal melakukan sinkronisasi otomatis ke server.", "error");
        } else {
            alert("Gagal melakukan sinkronisasi otomatis."); 
        }
    }
};

// ====================================================================
// 🟢 FIX: FUNGSI DOWNLOAD EXCEL (MULTI-SHEET METAR & TAFOR)
// ====================================================================
function downloadCSV() {
    // Tetap menggunakan nama fungsi downloadCSV agar HTML tombol tidak perlu diubah
    const elBulan = document.getElementById('input-bulan');
    const bulan = elBulan ? elBulan.value : "";
    
    if (!bulan) {
        alert("Pilih bulan terlebih dahulu di kalender!");
        return;
    }
    
    if (!CACHED_LOGS_DATA || CACHED_LOGS_DATA.length === 0) {
        alert("Tidak ada data di bulan ini untuk di-download!");
        return;
    }

    // Alihkan langsung ke mesin Python penjahit Excel kita!
    window.location.href = `/api/metar/download_log_excel?bulan=${bulan}`;
}

window.togglePanelManualDb = function() {
    const panel = document.getElementById('panel-input-manual-db');
    if(panel) panel.classList.toggle('hidden');
};

window.simpanLogManualDb = async function() {
    const sandi = document.getElementById('in-manual-db').value;
    const bulan = document.getElementById('input-bulan').value;
    
    // 🔴 UPGRADE POP-UP PERINGATAN KOSONG
    if (!bulan) {
        if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Peringatan", "Pilih bulan di kalender atas terlebih dahulu!", "error");
        else alert("Pilih bulan di kalender atas terlebih dahulu!");
        return;
    }
    if (!sandi || !sandi.includes("WAKT")) {
        if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Input Tidak Valid", "Harap masukkan sandi WAKT yang valid (Jangan lupa akhiri dengan tanda '=').", "error");
        else alert("Harap masukkan sandi WAKT yang valid!");
        return;
    }

    const modal = document.getElementById('modal-loading');
    if(modal) { document.getElementById('loading-title').innerText = "Menyimpan Sandi Manual..."; modal.classList.remove('hidden'); }

    try {
        const res = await fetch('/api/metar/tambah_log_manual', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sandi: sandi, bulan: bulan })
        });
        const out = await res.json();
        if(modal) modal.classList.add('hidden');

        if (out.status === "Sukses") {
            document.getElementById('in-manual-db').value = ''; 
            togglePanelManualDb(); 
            loadDatabaseLogsFromServer(); 
            
            // 🟢 UPGRADE POP-UP SUKSES
            if (typeof tampilkanNotifikasi === "function") {
                tampilkanNotifikasi("Berhasil Diamankan!", "Sandi manual berhasil disuntikkan ke dalam database lokal.", "success");
            } else { 
                alert("Sandi berhasil ditambahkan!");
            }
        } else { 
            if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Gagal Menyimpan", out.error, "error");
            else alert("Gagal: " + out.error); 
        }
    } catch (e) { 
        if(modal) modal.classList.add('hidden'); 
        if (typeof tampilkanNotifikasi === "function") tampilkanNotifikasi("Koneksi Terputus", "Gagal menghubungi server Python!", "error");
        else alert("Gagal menghubungi server!"); 
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const inputBulanLog = document.getElementById('input-bulan');
    if (inputBulanLog) {
        if (!inputBulanLog.value) {
            const sekarang = new Date();
            const yyyy = sekarang.getFullYear();
            const mm = String(sekarang.getMonth() + 1).padStart(2, '0');
            inputBulanLog.value = `${yyyy}-${mm}`;
        }
        inputBulanLog.addEventListener('change', loadDatabaseLogsFromServer);
    }
    loadDatabaseLogsFromServer();

    const inputBulanVerif = document.getElementById('input-bulan-verif');
    if (inputBulanVerif) {
        if (!inputBulanVerif.value) {
            const sekarang = new Date();
            const yyyy = sekarang.getFullYear();
            const mm = String(sekarang.getMonth() + 1).padStart(2, '0');
            inputBulanVerif.value = `${yyyy}-${mm}`;
        }
        inputBulanVerif.addEventListener('change', muatMatrixDatabase);
        setTimeout(muatMatrixDatabase, 500); 
    }

    const btnHitung = document.getElementById('btn-hitung-matrix') || document.getElementById('btnHitungMatrix') || document.querySelector('button[onclick*="hitung"]');
    if(btnHitung) { btnHitung.removeAttribute('onclick'); btnHitung.addEventListener('click', hitungVerifikasiOtomatisSatuKlik); }

    const btnDownloadExcel = document.getElementById('btn-download-excel') || document.getElementById('btnDownloadExcel') || document.querySelector('button[onclick*="DownloadExcel"]') || document.querySelector('button[onclick*="suntikDataManual"]');
    if(btnDownloadExcel) { btnDownloadExcel.removeAttribute('onclick'); btnDownloadExcel.addEventListener('click', suntikDataManualDanDownloadExcel); }
});

window.hitungVerifikasiOtomatisSatuKlik = hitungVerifikasiOtomatisSatuKlik;
window.suntikDataManualDanDownloadExcel = suntikDataManualDanDownloadExcel;

// 🔥 UBAHAN 2: Tombol MUAT (Wiper) menyedot kembali stiker brankas lokal!
window.muatMatrixDatabase = async function() {
    const bulan = document.getElementById('input-bulan-verif').value;
    if (!bulan) return;

    const modal = document.getElementById('modal-loading'); 
    if(modal) {
        document.getElementById('loading-title').innerText = "Memuat Matrix Database..."; 
        modal.classList.remove('hidden');
    }
    
    try {
        const response = await fetch('/api/metar/hitung_verifikasi', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ bulan: bulan, taf_text: "", metar_dummy: localStorage.getItem(getKunciLokerDummy()) || "" }) 
        });
        const hasil = await response.json(); 
        if(modal) modal.classList.add('hidden');
        
        if (hasil.status === "Sukses") {
            DATA_GLOBAL_VERIF_CACHE = hasil.data.detail_harian;
            
            if(document.getElementById('v-dir')) document.getElementById('v-dir').innerText = hasil.data.summary.arah_angin + "%";
            if(document.getElementById('v-spd')) document.getElementById('v-spd').innerText = hasil.data.summary.kecepatan_angin + "%";
            if(document.getElementById('v-vis')) document.getElementById('v-vis').innerText = hasil.data.summary.visibility + "%";
            if(document.getElementById('v-weather')) document.getElementById('v-weather').innerText = hasil.data.summary.cuaca + "%";
            if(document.getElementById('v-cld-jml')) document.getElementById('v-cld-jml').innerText = hasil.data.summary.awan_jumlah + "%";
            if(document.getElementById('v-cld-tgi')) document.getElementById('v-cld-tgi').innerText = hasil.data.summary.awan_tinggi + "%";
            if(document.getElementById('v-total')) document.getElementById('v-total').innerText = hasil.data.summary.total_score + "%";
            
            populasiNavigasiHariKustomExcel(Object.keys(DATA_GLOBAL_VERIF_CACHE).length);
            renderLembarKerjaHariExcelAktif(APPS_CURRENT_DAY_ACTIVE);
        } else {
            alert("Gagal memuat matrix: " + hasil.error);
        }
    } catch(e) { 
        if(modal) modal.classList.add('hidden'); 
    }
};

// ====================================================================
// 🟢 FITUR ASISTEN SUPERVISOR: RADAR DATA METAR BOLONG
// ====================================================================
window.bukaRadarMetarKosong = function() {
    const bulanInput = document.getElementById('input-bulan').value;
    if (!bulanInput) return alert("Pilih bulan di kalender terlebih dahulu!");

    const [tahunStr, bulanStr] = bulanInput.split('-');
    const tahun = parseInt(tahunStr);
    const bulan = parseInt(bulanStr);

    const metarLogs = CACHED_LOGS_DATA.filter(row => row.sandi_metar.includes("METAR") || row.sandi_metar.includes("SPECI"));
    const setWaktuAda = new Set(metarLogs.map(row => {
        return row.waktu_rekam.substring(0, 13);
    }));

    const sekarang = new Date();
    let batasHari = new Date(tahun, bulan, 0).getDate(); 
    let batasJam = 23; 

    if (tahun === sekarang.getUTCFullYear() && bulan === (sekarang.getUTCMonth() + 1)) {
        batasHari = sekarang.getUTCDate(); 
        batasJam = sekarang.getUTCHours(); 
    }

    let totalBolong = 0;
    let htmlHasil = `<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 max-h-[60vh] overflow-y-auto p-1 custom-scroll">`;

    for (let d = 1; d <= batasHari; d++) {
        const dayStr = String(d).padStart(2, '0');
        const maxH = (d === batasHari && tahun === sekarang.getUTCFullYear() && bulan === (sekarang.getUTCMonth() + 1)) ? batasJam : 23;

        for (let h = 0; h <= maxH; h++) {
            const hourStr = String(h).padStart(2, '0');
            const cekKunci = `${tahunStr}-${bulanStr}-${dayStr} ${hourStr}`;

            if (!setWaktuAda.has(cekKunci)) {
                totalBolong++;
                htmlHasil += `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-2 flex items-center justify-between shadow-sm">
                        <span class="text-red-700 font-bold text-[11px]">Tgl ${dayStr}</span>
                        <span class="bg-red-600 text-white px-2 py-0.5 rounded text-[10px] font-black tracking-wider">${hourStr}:00Z</span>
                    </div>
                `;
            }
        }
    }
    htmlHasil += `</div>`;

    if (totalBolong === 0) {
        htmlHasil = `
            <div class="bg-emerald-50 text-emerald-700 border border-emerald-200 p-6 rounded-xl text-center flex flex-col items-center justify-center mt-4 shadow-inner">
                <span class="text-4xl mb-2">🎉</span>
                <span class="font-black text-lg">LUAR BIASA!</span>
                <span class="font-medium text-xs mt-1">Tidak ada data METAR yang kosong satupun sampai jam ini.</span>
            </div>
        `;
    }

    const overlayId = "modal-radar-kosong";
    let oldOverlay = document.getElementById(overlayId);
    if (oldOverlay) oldOverlay.remove();

    const overlay = document.createElement('div');
    overlay.id = overlayId;
    overlay.className = "fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[999] flex justify-center items-center p-4 transition-all opacity-0";
    overlay.innerHTML = `
        <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl flex flex-col transform scale-95 transition-all" id="${overlayId}-box">
            <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-2xl">
                <div class="flex items-center gap-3">
                    <div class="bg-amber-100 p-2 rounded-lg text-amber-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg></div>
                    <div>
                        <h3 class="font-black text-slate-800 tracking-wide text-sm">RADAR DATA KOSONG (BLANK SPOT)</h3>
                        <p class="text-[10px] text-slate-500 font-medium">Bulan: ${tahunStr}-${bulanStr} | Ditemukan <span class="text-red-600 font-bold">${totalBolong} data</span> hilang.</p>
                    </div>
                </div>
                <button onclick="document.getElementById('${overlayId}').remove()" class="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-all outline-none">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            
            <div class="p-6">
                ${htmlHasil}
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    
    setTimeout(() => {
        overlay.classList.remove('opacity-0');
        document.getElementById(`${overlayId}-box`).classList.remove('scale-95');
    }, 10);
};

// ====================================================================
// 🟢 FITUR ASISTEN SUPERVISOR: RADAR DATA TAFOR BOLONG
// ====================================================================
window.bukaRadarTafKosong = function() {
    const bulanInput = document.getElementById('input-bulan').value;
    if (!bulanInput) return alert("Pilih bulan di kalender terlebih dahulu!");

    const [tahunStr, bulanStr] = bulanInput.split('-');
    const tahun = parseInt(tahunStr);
    const bulan = parseInt(bulanStr);

    const tafLogs = CACHED_LOGS_DATA.filter(row => row.sandi_metar.includes("TAF"));
    const setWaktuAda = new Set(tafLogs.map(row => {
        return row.waktu_rekam.substring(0, 13);
    }));

    const sekarang = new Date();
    let batasHari = new Date(tahun, bulan, 0).getDate(); 
    
    if (tahun === sekarang.getUTCFullYear() && bulan === (sekarang.getUTCMonth() + 1)) {
        batasHari = sekarang.getUTCDate(); 
    }

    let totalBolong = 0;
    let htmlHasil = `<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 max-h-[60vh] overflow-y-auto p-1 custom-scroll">`;

    // Siklus TAFOR harian (Lokal / Label di Radar): 23:00, 05:00, 11:00, 17:00
    const siklusTaf = ["23", "05", "11", "17"];

    for (let d = 1; d <= batasHari; d++) {
        const dayStr = String(d).padStart(2, '0');

        siklusTaf.forEach(hourStr => {
            
            // 🟢 PERBAIKAN LOGIKA: Abaikan siklus 23:00Z di tanggal akhir bulan, karena itu untuk tanggal 1 bulan depan!
            if (d === batasHari && hourStr === "23") {
                return;
            }

            // Abaikan siklus yang belum waktunya rilis hari ini
            if (d === batasHari && tahun === sekarang.getUTCFullYear() && bulan === (sekarang.getUTCMonth() + 1)) {
                if (parseInt(hourStr) > sekarang.getUTCHours()) return;
            }

            let keysToCheck = [];
            let baseHour = parseInt(hourStr);

            // 🟢 FIX KAPTEN: Loop otomatis menyapu dari H-2 sampai H+4 (Total 7 Jam Pengecekan!)
            for (let offset = -2; offset <= 4; offset++) {
                // Pakai Date.UTC agar pergantian hari atau bulan dihitung otomatis oleh mesin!
                let dObj = new Date(Date.UTC(tahun, bulan - 1, parseInt(dayStr), baseHour + offset, 0, 0));
                
                let cY = dObj.getUTCFullYear();
                let cM = String(dObj.getUTCMonth() + 1).padStart(2, '0');
                let cD = String(dObj.getUTCDate()).padStart(2, '0');
                let cH = String(dObj.getUTCHours()).padStart(2, '0');
                
                keysToCheck.push(`${cY}-${cM}-${cD} ${cH}`);
            }

            let found = false;
            for (let key of keysToCheck) {
                if (setWaktuAda.has(key)) found = true;
            }

            if (!found) {
                totalBolong++;
                htmlHasil += `
                    <div class="bg-orange-50 border border-orange-200 rounded-lg p-2 flex items-center justify-between shadow-sm">
                        <span class="text-orange-700 font-bold text-[11px]">Tgl ${dayStr}</span>
                        <span class="bg-orange-600 text-white px-2 py-0.5 rounded text-[10px] font-black tracking-wider">${hourStr}:00Z</span>
                    </div>
                `;
            }
        });
    }
    htmlHasil += `</div>`;

    if (totalBolong === 0) {
        htmlHasil = `
            <div class="bg-emerald-50 text-emerald-700 border border-emerald-200 p-6 rounded-xl text-center flex flex-col items-center justify-center mt-4 shadow-inner">
                <span class="text-4xl mb-2">🎉</span>
                <span class="font-black text-lg">LUAR BIASA!</span>
                <span class="font-medium text-xs mt-1">Tidak ada siklus TAFOR yang kosong.</span>
            </div>
        `;
    }

    const overlayId = "modal-radar-kosong-taf";
    let oldOverlay = document.getElementById(overlayId);
    if (oldOverlay) oldOverlay.remove();

    const overlay = document.createElement('div');
    overlay.id = overlayId;
    overlay.className = "fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[999] flex justify-center items-center p-4 transition-all opacity-0";
    overlay.innerHTML = `
        <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl flex flex-col transform scale-95 transition-all" id="${overlayId}-box">
            <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-2xl">
                <div class="flex items-center gap-3">
                    <div class="bg-orange-100 p-2 rounded-lg text-orange-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg></div>
                    <div>
                        <h3 class="font-black text-slate-800 tracking-wide text-sm">RADAR TAFOR KOSONG</h3>
                        <p class="text-[10px] text-slate-500 font-medium">Bulan: ${tahunStr}-${bulanStr} | Ditemukan <span class="text-red-600 font-bold">${totalBolong} siklus</span> hilang.</p>
                    </div>
                </div>
                <button onclick="document.getElementById('${overlayId}').remove()" class="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-all outline-none">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="p-6">
                ${htmlHasil}
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    setTimeout(() => {
        overlay.classList.remove('opacity-0');
        document.getElementById(`${overlayId}-box`).classList.remove('scale-95');
    }, 10);
};