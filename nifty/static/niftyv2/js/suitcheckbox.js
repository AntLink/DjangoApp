// Fungsi untuk menangani event DOMContentLoaded
function initCheckboxSelect() {
    const selectAllCheckbox = document.getElementById('select-all');
    const magicCheckboxes = document.querySelectorAll('.magic-checkbox');

    // Event listener untuk checkbox "select-all"
    selectAllCheckbox.addEventListener('click', function () {
        if (this.checked) {
            // Centang semua checkbox
            magicCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
        } else {
            // Hapus centang semua checkbox
            magicCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
        }
    });

    // Event listener untuk setiap checkbox individual
    magicCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('click', function () {
            // Periksa apakah semua checkbox tercentang
            const allChecked = Array.from(magicCheckboxes).every(cb => cb.checked);

            // Perbarui status "select-all"
            selectAllCheckbox.checked = allChecked;
        });
    });
}

// Inisialisasi ketika dokumen telah dimuat
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCheckboxSelect);
} else {
    initCheckboxSelect();
}