document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("id_birth_date");
    const btn = document.getElementById("id-date-picker");
    if (input && btn) {
        // buat instance MCDatepicker untuk input
        const picker = MCDatepicker.create({
            el: "#id_birth_date",
            dateFormat: "YYYY-MM-DD",
            bodyType: "modal" // bisa "inline" kalau mau selalu tampil
        });

        // buka datepicker ketika tombol diklik
        btn.addEventListener("click", function () {
            picker.open();
        });
    }
});