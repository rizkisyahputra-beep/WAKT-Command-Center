async function prosesKonversiACS() {
    const fileInput = document.getElementById('file-pdf-acs');
    const file = fileInput.files[0];

    if (!file) {
        alert("Radar Error: Pilih file Excel mentah hasil convert-nya dulu, Kapten!");
        return;
    }

    const formData = new FormData();
    formData.append('file_excel', file); // Sekarang mengirim 'file_excel'

    const modalLoading = document.getElementById('modal-loading');
    if(modalLoading) modalLoading.classList.remove('hidden');

    try {
        const response = await fetch('/api/acs/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errText = await response.text();
            let errorMessage = "Gagal memproses Excel ACS";
            try {
                const errData = JSON.parse(errText);
                if (errData.error) errorMessage = errData.error;
            } catch (e) {
                errorMessage = "Server Python Crash / File Terkunci! \nCek terminal CMD.";
            }
            throw new Error(errorMessage);
        }

        let namaFile = "ACS_WAKT_FINAL.xlsx";
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            namaFile = disposition.split('filename=')[1].replace(/"/g, '');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = downloadUrl;
        a.download = namaFile;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        if(modalLoading) modalLoading.classList.add('hidden');
        if (typeof tampilkanNotifikasi === "function") {
            tampilkanNotifikasi("Sukses Besar!", `File ${namaFile} berhasil ditata dan diunduh!`, "success");
        } else {
            alert(`SUKSES! File ${namaFile} berhasil diunduh.`);
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