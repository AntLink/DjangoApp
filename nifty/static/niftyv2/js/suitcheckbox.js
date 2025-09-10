function initCheckboxSelect() {
    const selectAllCheckboxes = document.querySelectorAll('.select-all');
    const magicCheckboxes = document.querySelectorAll('.magic-checkbox');

    // Loop setiap "select-all"
    selectAllCheckboxes.forEach(selectAllCheckbox => {
        selectAllCheckbox.addEventListener('click', function () {
            if (this.checked) {
                magicCheckboxes.forEach(checkbox => checkbox.checked = true);
            } else {
                magicCheckboxes.forEach(checkbox => checkbox.checked = false);
            }

            // Sinkronkan semua select-all agar status sama
            selectAllCheckboxes.forEach(cb => cb.checked = this.checked);
        });
    });

    // Event listener untuk setiap checkbox individual
    magicCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('click', function () {
            const allChecked = Array.from(magicCheckboxes).every(cb => cb.checked);

            // Update semua "select-all" supaya konsisten
            selectAllCheckboxes.forEach(cb => cb.checked = allChecked);
        });
    });
}

// Inisialisasi
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCheckboxSelect);
} else {
    initCheckboxSelect();
}
