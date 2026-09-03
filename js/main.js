function switchView(viewId) {
    document.getElementById('view-beranda').classList.add('hidden');
    document.getElementById('view-prakicu').classList.add('hidden');
    document.getElementById('view-tafor').classList.add('hidden');
    document.getElementById('view-database').classList.add('hidden');
    document.getElementById('view-verifikasi').classList.add('hidden');
    document.getElementById('view-labul').classList.add('hidden');
    document.getElementById('view-acs').classList.add('hidden');
    document.getElementById('view-hotspot').classList.add('hidden');
    document.getElementById(viewId).classList.remove('hidden');
    
    // 🟢 SUNTIKAN 1: Tambahkan 'nav-acs' dan 'nav-hotspot' ke dalam daftar pembersihan warna
    const navIds = ['nav-beranda', 'nav-prakicu', 'nav-tafor', 'nav-database', 'nav-verifikasi', 'nav-labul', 'nav-acs', 'nav-hotspot'];
    navIds.forEach(id => {
        const el = document.getElementById(id);
        if(el) el.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-all";
    });

    // 🟢 SUNTIKAN 2: Tambahkan rute untuk 'view-acs' dan 'view-hotspot' agar dikenali sistem pewarnaan
    const mappingNav = { 
        'view-beranda': 'nav-beranda', 
        'view-prakicu': 'nav-prakicu', 
        'view-tafor': 'nav-tafor', 
        'view-database': 'nav-database', 
        'view-verifikasi': 'nav-verifikasi', 
        'view-labul': 'nav-labul',
        'view-acs': 'nav-acs',
        'view-hotspot': 'nav-hotspot'
    };
    
    const navAktif = document.getElementById(mappingNav[viewId]);
    if(navAktif) {
        navAktif.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all bg-blue-50 text-blue-600 border-r-4 border-blue-600";
    }
}

function runningGlobalTimingEngine() {
    const sekarang = new Date();
    document.getElementById('txtClockUTC').innerText = `${String(sekarang.getUTCHours()).padStart(2,'0')}:${String(sekarang.getUTCMinutes()).padStart(2,'0')}:${String(sekarang.getUTCSeconds()).padStart(2,'0')} UTC`;
    const objekWIT = new Date(sekarang.getTime() + (9 * 60 * 60 * 1000));
    document.getElementById('txtClockWIT').innerText = `${String(objekWIT.getUTCHours()).padStart(2,'0')}:${String(objekWIT.getUTCMinutes()).padStart(2,'0')}:${String(objekWIT.getUTCSeconds()).padStart(2,'0')} WIT`;
}

// Inisialisasi Utama Saat Web Dibuka
document.addEventListener("DOMContentLoaded", () => {
    setInterval(runningGlobalTimingEngine, 1000); 
    
    // Inisialisasi Database
    if(typeof loadDatabaseLogsFromServer === "function") loadDatabaseLogsFromServer();
    
    // Inisialisasi Tanggal Laporan
    const skrg = new Date(); 
    if(document.getElementById('input-bulan')) {
        document.getElementById('input-bulan').value = `${skrg.getFullYear()}-${String(skrg.getMonth()+1).padStart(2,'0')}`;
        document.getElementById('input-bulan-verif').value = `${skrg.getFullYear()}-${String(skrg.getMonth()+1).padStart(2,'0')}`;
    }

    // Inisialisasi Prakicu
    if(typeof updateSemuanya === "function") {
        updateSemuanya(); updateIkon('inCuacaPagi', 'iconPagi', 'teksPagi'); 
        updateIkon('inCuacaSiang', 'iconSiang', 'teksSiang'); 
        updateIkon('inCuacaMalam', 'iconMalam', 'teksMalam'); 
        updateIkon('inCuacaDiniHari', 'iconDiniHari', 'teksDiniHari');
    }

    // Inisialisasi TAFOR
    if(typeof inisialisasiFormTafor === "function") {
        inisialisasiFormTafor(); muatTabelLogRecapDariStorage();
    }
});