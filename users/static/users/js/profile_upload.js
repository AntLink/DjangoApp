// accounts/static/accounts/js/profile_upload.js
document.addEventListener('DOMContentLoaded', function () {
    // Fungsi untuk inisialisasi semua widget upload
    function initializeUploadWidgets() {
        const uploadWidgets = document.querySelectorAll('.profile-container');

        uploadWidgets.forEach(function (widget) {
            const input = widget.querySelector('input[type="file"]');
            const preview = widget.querySelector('[id$="-preview"]');
            const progressContainer = widget.querySelector('[id$="-progress"]');
            const progressPercent = progressContainer.querySelector('[id$="-percent"]');
            const progressText = progressContainer.querySelector('[id$="-text"]');

            if (!input) return;

            // Event listener untuk klik pada widget
            widget.addEventListener('click', function () {
                input.click();
            });

            // Event listener untuk perubahan file input
            input.addEventListener('change', function (e) {
                if (e.target.files && e.target.files[0]) {
                    const file = e.target.files[0];

                    // Validasi file
                    if (!file.type.match('image.*')) {
                        alert('Silakan pilih file gambar (JPG, PNG)');
                        return;
                    }

                    if (file.size > 5 * 1024 * 1024) {
                        alert('Ukuran file terlalu besar. Maksimal 5MB.');
                        return;
                    }

                    // Preview gambar
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        preview.src = e.target.result;
                    };
                    reader.readAsDataURL(file);

                    // Upload file
                    uploadFile(file, progressContainer, progressPercent, progressText);
                }
            });
        });
    }

    function uploadFile(file, progressContainer, progressPercent, progressText) {
        progressContainer.style.display = 'flex';

        // FormData untuk mengirim file
        const formData = new FormData();
        formData.append('photo', file);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // XMLHttpRequest untuk upload dengan progress tracking
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/users/myuser/upload-profile-image/', true);

        // Event listener untuk progress upload
        xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                updateProgress(percentComplete, progressPercent, progressText);
            }
        });

        // Event listener untuk completion
        xhr.addEventListener('load', function (e) {
            try {
                const response = JSON.parse(xhr.responseText);

                if (response.success) {
                    // Upload sukses
                    updateProgress(100, progressPercent, progressText);
                    progressText.textContent = 'Upload selesai!';

                    // Perbarui gambar preview dengan URL baru
                    const preview = document.querySelector('.profile-image');
                    if (preview) {
                        // Tambahkan timestamp untuk menghindari cache browser
                        preview.src = response.image_url + '?t=' + new Date().getTime();
                    }

                    // Sembunyikan progress setelah 1 detik
                    setTimeout(function () {
                        progressContainer.style.display = 'none';
                    }, 1000);
                } else {
                    // Upload gagal
                    alert('Upload gagal: ' + response.error);
                    progressContainer.style.display = 'none';
                }
            } catch (e) {
                // Error parsing JSON
                alert('Terjadi kesalahan saat memproses response server.');
                progressContainer.style.display = 'none';
            }
        });

        // Event listener untuk error
        xhr.addEventListener('error', function () {
            alert('Terjadi kesalahan jaringan saat mengupload file.');
            progressContainer.style.display = 'none';
        });

        // Kirim request
        xhr.send(formData);
    }


    // Update progress
    function updateProgress(percent, progressPercent, progressText) {
        const roundedPercent = Math.round(percent);
        progressPercent.textContent = `${roundedPercent}%`;
        progressText.textContent = `Mengupload: ${roundedPercent}%`;
    }

    // Dapatkan CSRF token
    function getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;

        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');

            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();

                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        return cookieValue;
    }

    // Inisialisasi widget
    initializeUploadWidgets();
});