// ==================== GLOBAL VARIABLES ====================
var allImages = [];
var currentImageIndex = 0;
var currentZoom = 1;
var minZoom = 0.1;
var maxZoom = 3;
var zoomStep = 0.2;
var isDragging = false;
var startX, startY;
var initialImageX = 0, initialImageY = 0;

// ==================== HELPER FUNCTIONS ====================
function getCsrftoken(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function gettext(text) {
    return text;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Fungsi untuk memeriksa apakah file adalah gambar berdasarkan data-type, nama file, atau URL
function isImageFile(imgElement, url, fileName) {
    // Periksa data-type terlebih dahulu
    if (imgElement && imgElement.dataset.type) {
        var imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
        var lowerType = imgElement.dataset.type.toLowerCase();
        return imageTypes.includes(lowerType);
    }
    // Periksa ekstensi file di nama file
    if (fileName) {
        var imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
        var lowerFileName = fileName.toLowerCase();
        for (var i = 0; i < imageExtensions.length; i++) {
            if (lowerFileName.indexOf(imageExtensions[i]) !== -1) {
                return true;
            }
        }
    }
    // Periksa kelas elemen
    if (imgElement && imgElement.classList.contains('image-file')) {
        // Jika memiliki kelas image-file, periksa juga nama file untuk memastikan
        var altText = imgElement.alt || '';
        if (altText) {
            var imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
            var lowerAlt = altText.toLowerCase();
            for (var i = 0; i < imageExtensions.length; i++) {
                if (lowerAlt.indexOf(imageExtensions[i]) !== -1) {
                    return true;
                }
            }
        }
    }
    // Periksa ekstensi file di URL
    if (!url) return false;
    var imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
    var lowerUrl = url.toLowerCase();
    for (var i = 0; i < imageExtensions.length; i++) {
        if (lowerUrl.indexOf(imageExtensions[i]) !== -1) {
            return true;
        }
    }
    // Periksa nama file di URL
    var urlFileName = url.split('/').pop();
    if (urlFileName) {
        for (var i = 0; i < imageExtensions.length; i++) {
            if (urlFileName.indexOf(imageExtensions[i]) !== -1) {
                return true;
            }
        }
    }
    return false;
}

// Fungsi untuk memeriksa tipe file
function getFileType(url, fileName, mimeType) {
    // Periksa berdasarkan MIME type
    if (mimeType) {
        if (mimeType.startsWith('image/')) return 'image';
        if (mimeType.startsWith('video/')) return 'video';
        if (mimeType === 'application/pdf') return 'pdf';
        if (mimeType.includes('word') || mimeType.includes('document') ||
            mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return 'word';
        if (mimeType.includes('excel') || mimeType.includes('spreadsheet') ||
            mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') return 'excel';
        if (mimeType.includes('powerpoint') || mimeType.includes('presentation') ||
            mimeType === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') return 'powerpoint';
        if (mimeType.startsWith('text/')) return 'text';
    }

    // Periksa berdasarkan ekstensi file
    if (!url && !fileName) return 'unknown';

    var fileUrl = url || fileName;
    var lowerUrl = fileUrl.toLowerCase();

    // Ekstensi gambar
    if (lowerUrl.includes('.jpg') || lowerUrl.includes('.jpeg') ||
        lowerUrl.includes('.png') || lowerUrl.includes('.gif') ||
        lowerUrl.includes('.bmp') || lowerUrl.includes('.webp') ||
        lowerUrl.includes('.svg')) {
        return 'image';
    }

    // Ekstensi video
    if (lowerUrl.includes('.mp4') || lowerUrl.includes('.webm') ||
        lowerUrl.includes('.ogg') || lowerUrl.includes('.mov') ||
        lowerUrl.includes('.avi') || lowerUrl.includes('.mkv') ||
        lowerUrl.includes('.flv') || lowerUrl.includes('.wmv')) {
        return 'video';
    }

    // Ekstensi PDF
    if (lowerUrl.includes('.pdf')) {
        return 'pdf';
    }

    // Ekstensi Word
    if (lowerUrl.includes('.doc') || lowerUrl.includes('.docx')) {
        return 'word';
    }

    // Ekstensi Excel
    if (lowerUrl.includes('.xls') || lowerUrl.includes('.xlsx')) {
        return 'excel';
    }

    // Ekstensi PowerPoint
    if (lowerUrl.includes('.ppt') || lowerUrl.includes('.pptx')) {
        return 'powerpoint';
    }

    // Ekstensi teks
    if (lowerUrl.includes('.txt') || lowerUrl.includes('.csv') ||
        lowerUrl.includes('.json') || lowerUrl.includes('.xml') ||
        lowerUrl.includes('.html') || lowerUrl.includes('.htm') ||
        lowerUrl.includes('.css') || lowerUrl.includes('.js') ||
        lowerUrl.includes('.md') || lowerUrl.includes('.log') ||
        lowerUrl.includes('.py')) {
        return 'text';
    }

    return 'unknown';
}

// Fungsi untuk mendapatkan icon berdasarkan tipe file
function getFileIcon(fileType) {
    if (!fileType) return 'file';
    var lowerType = fileType.toLowerCase();
    if (lowerType.startsWith('image/')) return 'image';
    if (lowerType.startsWith('video/')) return 'video';
    if (lowerType.startsWith('audio/')) return 'audio';
    if (lowerType.includes('pdf')) return 'pdf';
    if (lowerType.includes('word') || lowerType.includes('document')) return 'word';
    if (lowerType.includes('excel') || lowerType.includes('spreadsheet')) return 'excel';
    if (lowerType.includes('powerpoint') || lowerType.includes('presentation')) return 'powerpoint';
    if (lowerType.includes('zip') || lowerType.includes('rar') || lowerType.includes('tar')) return 'archive';
    if (lowerType.includes('text')) return 'text';
    return 'file';
}

// Fungsi untuk mendapatkan kelas icon Font Awesome berdasarkan tipe file
function getFileIconClass(fileType) {
    var icon = getFileIcon(fileType);
    var iconClasses = {
        'image': 'fas fa-file-image',
        'video': 'fas fa-file-video',
        'audio': 'fas fa-file-audio',
        'pdf': 'fas fa-file-pdf',
        'word': 'fas fa-file-word',
        'excel': 'fas fa-file-excel',
        'powerpoint': 'fas fa-file-powerpoint',
        'archive': 'fas fa-file-archive',
        'text': 'fas fa-file-alt',
        'file': 'fas fa-file'
    };
    return iconClasses[icon] || iconClasses['file'];
}

// Fungsi untuk mengatur link aksi file
function setupFileActionLinks(item, response) {
    // Get action links
    var changeLink = item.querySelector('.dropdown-menu li:first-child a');
    var deleteLink = item.querySelector('.dropdown-menu li:nth-child(2) a');
    var downloadLink = item.querySelector('.dropdown-menu li:last-child a');

    // Setup Change link
    if (changeLink) {
        if (response && response.change_link) {
            changeLink.href = response.change_link;
            changeLink.removeAttribute('disabled');
            changeLink.style.opacity = '1';
            changeLink.style.pointerEvents = 'auto';
        } else {
            changeLink.href = '#';
            changeLink.setAttribute('disabled', 'disabled');
            changeLink.style.opacity = '0.5';
            changeLink.style.pointerEvents = 'none';
        }
    }

    // Setup Delete link
    if (deleteLink) {
        if (response && response.delete_link) {
            deleteLink.href = response.delete_link;
            deleteLink.removeAttribute('disabled');
            deleteLink.style.opacity = '1';
            deleteLink.style.pointerEvents = 'auto';
        } else {
            deleteLink.href = '#';
            deleteLink.setAttribute('disabled', 'disabled');
            deleteLink.style.opacity = '0.5';
            deleteLink.style.pointerEvents = 'none';
        }
    }

    // Setup Download link
    if (downloadLink) {
        if (response && response.download_link) {
            downloadLink.href = response.download_link;
            downloadLink.removeAttribute('disabled');
            downloadLink.style.opacity = '1';
            downloadLink.style.pointerEvents = 'auto';
        } else {
            downloadLink.href = '#';
            downloadLink.setAttribute('disabled', 'disabled');
            downloadLink.style.opacity = '0.5';
            downloadLink.style.pointerEvents = 'none';
        }
    }
}

// ==================== IMAGE PREVIEW FUNCTIONS ====================
// Modifikasi fungsi showImagePreview untuk mendukung semua tipe file
function showImagePreview(imageSrc, imageAlt, index) {
    // Update current index jika disediakan
    if (index !== undefined) {
        currentImageIndex = index;
    }
    var modal = document.getElementById('image-preview-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'image-preview-modal';
        modal.className = 'image-preview-modal';
        var modalContent = document.createElement('div');
        modalContent.className = 'image-preview-content';
        // Image container with scroll
        var imageContainer = document.createElement('div');
        imageContainer.className = 'image-preview-container';
        // Tentukan tipe file
        var fileType = getFileType(imageSrc, imageAlt);
        console.log('Creating preview for type:', fileType, 'with URL:', imageSrc);

        // Tambahkan konten berdasarkan tipe file
        switch (fileType) {
            case 'image':
                var img = document.createElement('img');
                img.src = imageSrc;
                img.alt = imageAlt || 'Image Preview';
                imageContainer.appendChild(img);
                break;
            case 'video':
                var video = document.createElement('video');
                video.src = imageSrc;
                video.className = 'image-preview-video';
                video.controls = true;
                video.autoplay = false;
                video.preload = 'metadata';
                imageContainer.appendChild(video);
                break;
            case 'pdf':
                // Coba gunakan PDF.js jika tersedia
                if (typeof pdfjsLib !== 'undefined') {
                    var pdfCanvas = document.createElement('canvas');
                    pdfCanvas.className = 'image-preview-pdf-canvas';
                    imageContainer.appendChild(pdfCanvas);
                    var loadingTask = pdfjsLib.getDocument(imageSrc);
                    loadingTask.promise.then(function (pdf) {
                        console.log('PDF loaded');
                        // Fetch the first page
                        pdf.getPage(1).then(function (page) {
                            console.log('Page loaded');
                            var scale = 1.5;
                            var viewport = page.getViewport({scale: scale});
                            // Prepare canvas using PDF page dimensions
                            var context = pdfCanvas.getContext('2d');
                            pdfCanvas.height = viewport.height;
                            pdfCanvas.width = viewport.width;
                            // Render PDF page into canvas context
                            var renderContext = {
                                canvasContext: context,
                                viewport: viewport
                            };
                            var renderTask = page.render(renderContext);
                            renderTask.promise.then(function () {
                                console.log('Page rendered');
                            });
                        });
                    }).catch(function (error) {
                        console.error('Error loading PDF:', error);
                        // Fallback ke iframe jika PDF.js gagal
                        var iframe = document.createElement('iframe');
                        iframe.src = imageSrc;
                        iframe.className = 'image-preview-pdf-iframe';
                        iframe.title = 'PDF Preview';
                        imageContainer.innerHTML = '';
                        imageContainer.appendChild(iframe);
                    });
                } else {
                    // Gunakan iframe untuk PDF
                    var iframe = document.createElement('iframe');
                    iframe.src = imageSrc;
                    iframe.className = 'image-preview-pdf-iframe';
                    iframe.title = 'PDF Preview';
                    imageContainer.appendChild(iframe);
                }
                break;
            case 'word':
            case 'excel':
            case 'powerpoint':
                // PERUBAHAN: Hapus preview untuk file Office, hanya sediakan download
                var officeDiv = document.createElement('div');
                officeDiv.className = 'office-download-only';
                officeDiv.innerHTML =
                    '<div class="office-download-container">' +
                    '<i class="fas fa-file-' + (fileType === 'word' ? 'word' : fileType === 'excel' ? 'excel' : 'powerpoint') + ' office-icon"></i>' +
                    '<h3>' + (fileType.charAt(0).toUpperCase() + fileType.slice(1)) + ' Document</h3>' +
                    '<p>Preview tidak tersedia untuk dokumen ' + (fileType.charAt(0).toUpperCase() + fileType.slice(1)) + '</p>' +
                    '<a href="' + imageSrc + '" download class="btn btn-primary office-download-btn">' +
                    '<i class="fas fa-download"></i> Download File' +
                    '</a>' +
                    '</div>';
                imageContainer.appendChild(officeDiv);
                break;
            case 'text':
                var textContainer = document.createElement('div');
                textContainer.className = 'image-preview-text';
                textContainer.innerHTML = '<div class="text-loading">Loading text file...</div>';
                imageContainer.appendChild(textContainer);
                // Fetch the text file
                fetch(imageSrc)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.text();
                    })
                    .then(text => {
                        textContainer.innerHTML = '<pre class="text-content">' + text + '</pre>';
                    })
                    .catch(error => {
                        console.error('Error loading text file:', error);
                        textContainer.innerHTML = '<div class="text-error">Error loading text file: ' + error.message + '</div>';
                    });
                break;
            default:
                var unknownDiv = document.createElement('div');
                unknownDiv.className = 'image-preview-unknown';
                unknownDiv.innerHTML = '<i class="fas fa-file"></i><p>Preview not available for this file type</p><a href="' + imageSrc + '" download class="btn btn-primary">Download File</a>';
                imageContainer.appendChild(unknownDiv);
        }

        // Zoom controls (hanya untuk gambar)
        if (fileType === 'image') {
            var zoomControls = document.createElement('div');
            zoomControls.className = 'image-preview-zoom-controls';
            var zoomOutBtn = document.createElement('button');
            zoomOutBtn.className = 'zoom-btn';
            zoomOutBtn.innerHTML = '<i class="fas fa-search-minus"></i>';
            zoomOutBtn.title = 'Zoom Out';
            var zoomResetBtn = document.createElement('button');
            zoomResetBtn.className = 'zoom-btn';
            zoomResetBtn.innerHTML = '<i class="fas fa-compress"></i>';
            zoomResetBtn.title = 'Reset Zoom';
            var zoomInBtn = document.createElement('button');
            zoomInBtn.className = 'zoom-btn';
            zoomInBtn.innerHTML = '<i class="fas fa-search-plus"></i>';
            zoomInBtn.title = 'Zoom In';
            zoomControls.appendChild(zoomOutBtn);
            zoomControls.appendChild(zoomResetBtn);
            zoomControls.appendChild(zoomInBtn);
            modalContent.appendChild(zoomControls);
            // Event listeners untuk zoom
            zoomOutBtn.addEventListener('click', function () {
                zoomImage(-zoomStep);
            });
            zoomResetBtn.addEventListener('click', function () {
                resetZoom();
            });
            zoomInBtn.addEventListener('click', function () {
                zoomImage(zoomStep);
            });
            // Mouse wheel zoom
            imageContainer.addEventListener('wheel', function (e) {
                e.preventDefault();
                var delta = e.deltaY > 0 ? -zoomStep : zoomStep;
                zoomImage(delta);
            });
            // Image drag functionality
            imageContainer.addEventListener('mousedown', startDragging);
            imageContainer.addEventListener('mousemove', drag);
            imageContainer.addEventListener('mouseup', endDragging);
            imageContainer.addEventListener('mouseleave', endDragging);
            // Touch events for mobile
            imageContainer.addEventListener('touchstart', startDragging);
            imageContainer.addEventListener('touchmove', drag);
            imageContainer.addEventListener('touchend', endDragging);
            // Prevent image drag
            var img = imageContainer.querySelector('img');
            if (img) {
                img.addEventListener('dragstart', function (e) {
                    e.preventDefault();
                });
                // Reset zoom when image loads
                img.addEventListener('load', function () {
                    resetZoom();
                });
            }
        }

        // Tombol close
        var closeBtn = document.createElement('button');
        closeBtn.className = 'image-preview-close';
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.title = 'Close (Esc)';
        // Tombol previous
        var prevBtn = document.createElement('button');
        prevBtn.className = 'image-preview-prev';
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.title = 'Previous (Left Arrow)';
        // Tombol next
        var nextBtn = document.createElement('button');
        nextBtn.className = 'image-preview-next';
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.title = 'Next (Right Arrow)';
        // Image counter
        var counter = document.createElement('div');
        counter.className = 'image-preview-counter';

        modalContent.appendChild(imageContainer);
        modalContent.appendChild(closeBtn);
        modalContent.appendChild(prevBtn);
        modalContent.appendChild(nextBtn);
        modalContent.appendChild(counter);

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Event listeners
        closeBtn.addEventListener('click', closeImagePreview);
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeImagePreview();
            }
        });
        prevBtn.addEventListener('click', showPreviousImage);
        nextBtn.addEventListener('click', showNextImage);
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeImagePreview();
                document.removeEventListener('keydown', escHandler);
            } else if (e.key === 'ArrowLeft') {
                showPreviousImage();
            } else if (e.key === 'ArrowRight') {
                showNextImage();
            } else if (fileType === 'image') {
                if (e.key === '0') {
                    resetZoom();
                } else if (e.key === '+' || e.key === '=') {
                    zoomImage(zoomStep);
                } else if (e.key === '-' || e.key === '_') {
                    zoomImage(-zoomStep);
                }
            }
        });
    } else {
        var imageContainer = modal.querySelector('.image-preview-container');
        if (imageContainer) {
            // Kosongkan container
            imageContainer.innerHTML = '';
            // Tentukan tipe file
            var fileType = getFileType(imageSrc, imageAlt);

            // Tambahkan konten berdasarkan tipe file
            switch (fileType) {
                case 'image':
                    var img = document.createElement('img');
                    img.src = imageSrc;
                    img.alt = imageAlt || 'Image Preview';
                    imageContainer.appendChild(img);
                    // Reset zoom when image loads
                    img.addEventListener('load', function () {
                        resetZoom();
                    });
                    break;
                case 'video':
                    var video = document.createElement('video');
                    video.src = imageSrc;
                    video.className = 'image-preview-video';
                    video.controls = true;
                    video.autoplay = false;
                    video.preload = 'metadata';
                    imageContainer.appendChild(video);
                    break;
                case 'pdf':
                    // Coba gunakan PDF.js jika tersedia
                    if (typeof pdfjsLib !== 'undefined') {
                        var pdfCanvas = document.createElement('canvas');
                        pdfCanvas.className = 'image-preview-pdf-canvas';
                        imageContainer.appendChild(pdfCanvas);
                        var loadingTask = pdfjsLib.getDocument(imageSrc);
                        loadingTask.promise.then(function (pdf) {
                            console.log('PDF loaded');
                            // Fetch the first page
                            pdf.getPage(1).then(function (page) {
                                console.log('Page loaded');
                                var scale = 1.5;
                                var viewport = page.getViewport({scale: scale});
                                // Prepare canvas using PDF page dimensions
                                var context = pdfCanvas.getContext('2d');
                                pdfCanvas.height = viewport.height;
                                pdfCanvas.width = viewport.width;
                                // Render PDF page into canvas context
                                var renderContext = {
                                    canvasContext: context,
                                    viewport: viewport
                                };
                                var renderTask = page.render(renderContext);
                                renderTask.promise.then(function () {
                                    console.log('Page rendered');
                                });
                            });
                        }).catch(function (error) {
                            console.error('Error loading PDF:', error);
                            // Fallback ke iframe jika PDF.js gagal
                            var iframe = document.createElement('iframe');
                            iframe.src = imageSrc;
                            iframe.className = 'image-preview-pdf-iframe';
                            iframe.title = 'PDF Preview';
                            imageContainer.innerHTML = '';
                            imageContainer.appendChild(iframe);
                        });
                    } else {
                        // Gunakan iframe untuk PDF
                        var iframe = document.createElement('iframe');
                        iframe.src = imageSrc;
                        iframe.className = 'image-preview-pdf-iframe';
                        iframe.title = 'PDF Preview';
                        imageContainer.appendChild(iframe);
                    }
                    break;
                case 'word':
                case 'excel':
                case 'powerpoint':
                    // PERUBAHAN: Hapus preview untuk file Office, hanya sediakan download
                    var officeDiv = document.createElement('div');
                    officeDiv.className = 'office-download-only';
                    officeDiv.innerHTML =
                        '<div class="office-download-container">' +
                        '<i class="fas fa-file-' + (fileType === 'word' ? 'word' : fileType === 'excel' ? 'excel' : 'powerpoint') + ' office-icon"></i>' +
                        '<h3>' + (fileType.charAt(0).toUpperCase() + fileType.slice(1)) + ' Document</h3>' +
                        '<p>Preview tidak tersedia untuk dokumen ' + (fileType.charAt(0).toUpperCase() + fileType.slice(1)) + '</p>' +
                        '<a href="' + imageSrc + '" download class="btn btn-primary office-download-btn">' +
                        '<i class="fas fa-download"></i> Download File' +
                        '</a>' +
                        '</div>';
                    imageContainer.appendChild(officeDiv);
                    break;
                case 'text':
                    var textContainer = document.createElement('div');
                    textContainer.className = 'image-preview-text';
                    textContainer.innerHTML = '<div class="text-loading">Loading text file...</div>';
                    imageContainer.appendChild(textContainer);
                    // Fetch the text file
                    fetch(imageSrc)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.text();
                        })
                        .then(text => {
                            textContainer.innerHTML = '<pre class="text-content">' + text + '</pre>';
                        })
                        .catch(error => {
                            console.error('Error loading text file:', error);
                            textContainer.innerHTML = '<div class="text-error">Error loading text file: ' + error.message + '</div>';
                        });
                    break;
                default:
                    var unknownDiv = document.createElement('div');
                    unknownDiv.className = 'image-preview-unknown';
                    unknownDiv.innerHTML = '<i class="fas fa-file"></i><p>Preview not available for this file type</p><a href="' + imageSrc + '" download class="btn btn-primary">Download File</a>';
                    imageContainer.appendChild(unknownDiv);
            }

            // Tampilkan/sembunyikan zoom controls berdasarkan tipe file
            var zoomControls = modal.querySelector('.image-preview-zoom-controls');
            if (zoomControls) {
                zoomControls.style.display = fileType === 'image' ? 'flex' : 'none';
            }
        }
    }

    // Update counter
    updateImageCounter();
    // Update visibility tombol navigasi
    updateNavigationButtons();
    setTimeout(function () {
        modal.classList.add('show');
    }, 10);
}

// PERUBAHAN: Modifikasi fungsi handleImageClick untuk file Office
function handleImageClick(e) {
    e.preventDefault();
    var item = e.currentTarget.closest('li');
    if (!item) return;

    var mediaLeft = item.querySelector('.media-left');
    if (!mediaLeft) return;

    var img = mediaLeft.querySelector('img');
    var iconContainer = mediaLeft.querySelector('.file-icon-container');
    var downloadLink = item.querySelector('.file-settings .dropdown-menu li:last-child a');
    var fileNameElement = item.querySelector('.file-name');
    var fileName = fileNameElement ? fileNameElement.textContent : '';

    // Dapatkan tipe file
    var fileType = getFileType(downloadLink ? downloadLink.href : null, fileName);

    // Untuk file Office, langsung download tanpa preview
    if (fileType === 'word' || fileType === 'excel' || fileType === 'powerpoint') {
        if (downloadLink && downloadLink.href) {
            // Buat link download sementara
            var tempLink = document.createElement('a');
            tempLink.href = downloadLink.href;
            tempLink.download = fileName;
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
            return;
        }
    }

    // Update array gambar sebelum menampilkan preview
    updateAllImagesArray();

    // Cari index gambar ini dalam array
    var imageIndex = allImages.findIndex(function (image) {
        return image.element === item;
    });

    // Dapatkan ID file dari checkbox value
    var checkbox = item.querySelector('input[type="checkbox"]');
    var fileId = checkbox ? checkbox.value : null;

    // Buat URL preview
    var previewUrl = '';
    if (fileId && (fileType === 'pdf')) {
        // Gunakan endpoint preview untuk PDF
        previewUrl = '/filemedia/file/' + fileId + '/file-preview/';
    } else if (img && img.dataset.src) {
        previewUrl = img.dataset.src;
    } else if (iconContainer && iconContainer.querySelector('i') && iconContainer.querySelector('i').dataset.src) {
        previewUrl = iconContainer.querySelector('i').dataset.src;
    } else if (downloadLink && downloadLink.href) {
        previewUrl = downloadLink.href;
    }

    console.log('Preview URL:', previewUrl);
    console.log('File type:', fileType);

    if (previewUrl) {
        showImagePreview(previewUrl, fileName, imageIndex);
    }
}

function closeImagePreview() {
    var modal = document.getElementById('image-preview-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(function () {
            // modal.remove();
        }, 300);
    }
}

function showPreviousImage() {
    if (allImages.length > 1) {
        currentImageIndex = (currentImageIndex - 1 + allImages.length) % allImages.length;
        var image = allImages[currentImageIndex];
        showImagePreview(image.src, image.alt, currentImageIndex);
    }
}

function showNextImage() {
    if (allImages.length > 1) {
        currentImageIndex = (currentImageIndex + 1) % allImages.length;
        var image = allImages[currentImageIndex];
        showImagePreview(image.src, image.alt, currentImageIndex);
    }
}

function updateImageCounter() {
    var modal = document.getElementById('image-preview-modal');
    if (modal && allImages.length > 0) {
        var counter = modal.querySelector('.image-preview-counter');
        if (counter) {
            // Pastikan currentImageIndex valid
            if (currentImageIndex < 0) {
                currentImageIndex = 0;
            } else if (currentImageIndex >= allImages.length) {
                currentImageIndex = allImages.length - 1;
            }
            counter.textContent = (currentImageIndex + 1) + ' / ' + allImages.length;
        }
    }
}

function updateNavigationButtons() {
    var modal = document.getElementById('image-preview-modal');
    if (modal) {
        var prevBtn = modal.querySelector('.image-preview-prev');
        var nextBtn = modal.querySelector('.image-preview-next');
        if (allImages.length <= 1) {
            // Sembunyikan tombol jika hanya ada satu gambar atau tidak ada gambar
            if (prevBtn) prevBtn.style.display = 'none';
            if (nextBtn) nextBtn.style.display = 'none';
        } else {
            // Tampilkan tombol
            if (prevBtn) prevBtn.style.display = 'flex';
            if (nextBtn) nextBtn.style.display = 'flex';
        }
    }
}

// Drag functions
function startDragging(e) {
    isDragging = true;
    var imageContainer = e.currentTarget;
    // Get mouse or touch position
    if (e.type === 'mousedown') {
        startX = e.pageX;
        startY = e.pageY;
    } else if (e.type === 'touchstart') {
        startX = e.touches[0].pageX;
        startY = e.touches[0].pageY;
    }
    // Get current image transform
    var img = imageContainer.querySelector('img');
    if (!img) return;

    var transform = window.getComputedStyle(img).transform;
    if (transform && transform !== 'none') {
        var values = transform.split('(')[1].split(')')[0].split(',');
        initialImageX = parseFloat(values[4]);
        initialImageY = parseFloat(values[5]);
    } else {
        initialImageX = 0;
        initialImageY = 0;
    }
    imageContainer.classList.add('dragging');
}

function drag(e) {
    if (!isDragging) return;
    e.preventDefault();
    var imageContainer = e.currentTarget;
    var img = imageContainer.querySelector('img');
    if (!img) return;

    // Get mouse or touch position
    var x, y;
    if (e.type === 'mousemove') {
        x = e.pageX;
        y = e.pageY;
    } else if (e.type === 'touchmove') {
        x = e.touches[0].pageX;
        y = e.touches[0].pageY;
    }
    // Calculate distance moved
    var walkX = (x - startX);
    var walkY = (y - startY);
    // Apply transform to image
    img.style.transform = `translate(${initialImageX + walkX}px, ${initialImageY + walkY}px)`;
}

function endDragging() {
    isDragging = false;
    var imageContainers = document.querySelectorAll('.image-preview-container');
    imageContainers.forEach(function (container) {
        container.classList.remove('dragging');
    });
}

// Zoom functions
function zoomImage(delta) {
    var modal = document.getElementById('image-preview-modal');
    if (!modal) return;
    var imageContainer = modal.querySelector('.image-preview-container');
    if (!imageContainer) return;
    // Calculate new zoom level
    var newZoom = currentZoom + delta;
    // Clamp zoom level
    newZoom = Math.max(minZoom, Math.min(maxZoom, newZoom));
    // Apply zoom to image container
    currentZoom = newZoom;
    imageContainer.style.transform = `scale(${currentZoom})`;
    // Update zoom buttons state
    updateZoomButtons();
}

function resetZoom() {
    currentZoom = 1;
    var modal = document.getElementById('image-preview-modal');
    if (!modal) return;
    var imageContainer = modal.querySelector('.image-preview-container');
    if (imageContainer) {
        imageContainer.style.transform = `scale(${currentZoom})`;
    }
    // Reset image position
    var img = modal.querySelector('img');
    if (img) {
        img.style.transform = 'translate(0, 0)';
    }
    updateZoomButtons();
}

function updateZoomButtons() {
    var modal = document.getElementById('image-preview-modal');
    if (!modal) return;
    var zoomOutBtn = modal.querySelector('.zoom-btn:first-child');
    var zoomInBtn = modal.querySelector('.zoom-btn:last-child');
    if (zoomOutBtn) {
        zoomOutBtn.disabled = currentZoom <= minZoom;
        zoomOutBtn.style.opacity = currentZoom <= minZoom ? '0.5' : '1';
    }
    if (zoomInBtn) {
        zoomInBtn.disabled = currentZoom >= maxZoom;
        zoomInBtn.style.opacity = currentZoom >= maxZoom ? '0.5' : '1';
    }
}

// ==================== NOTIFICATION FUNCTIONS ====================
function showNotification(type, message) {
    console.log('Showing notification:', type, message);
    var notification = document.createElement('div');
    notification.className = 'notification notification-' + type;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.opacity = '0';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(function () {
        notification.style.transition = 'opacity 0.3s ease';
        notification.style.opacity = '1';
    }, 10);
    setTimeout(function () {
        notification.style.opacity = '0';
        setTimeout(function () {
            notification.remove();
        }, 300);
    }, 5000);
}

// ==================== UPLOAD FUNCTIONS ====================
function createPreview(file) {
    console.log('Creating preview for:', file.name);
    var listItems = document.querySelector('#list-items');
    if (!listItems) {
        console.error('List items container not found');
        return;
    }
    var id = (file.size + file.lastModified);
    var previewElement = document.createElement('li');
    previewElement.className = 'file-item img-' + id;
    previewElement.classList.add('uploading');
    previewElement.style.opacity = '0';
    // Dapatkan tipe file
    var fileType = getFileType(null, file.name, file.type);
    // Ekstrak ekstensi file
    var fileExtension = file.name.split('.').pop().toLowerCase();
    // Dapatkan kelas icon Font Awesome
    var iconClass = getFileIconClass(file.type);
    // Create the HTML structure similar to existing items
    previewElement.innerHTML =
        '<div class="file-control" style="width: 30px;">' +
        '<input type="checkbox" name="_selected_action" class="form-check-input magic-checkbox" id="list-' + id + '">' +
        '</div>' +
        '<div class="file-settings dropdown">' +
        '<button class="btn btn-icon" data-bs-toggle="dropdown" type="button" aria-expanded="false">' +
        '<i class="fas fa-ellipsis-v"></i>' +
        '</button>' +
        '<ul class="dropdown-menu">' +
        '<li><a class="btn-link" href="#"><i class="fas fa-edit"></i> Change</a></li>' +
        '<li><a class="btn-link" href="#"><i class="fas fa-trash"></i> Delete</a></li>' +
        '<li><a target="_blank" class="btn-link download-link" href="javascript:;"><i class="fas fa-download"></i> Download</a></li>' +
        '</ul>' +
        '</div>' +
        '<div class="file-details">' +
        '<div class="media-block">' +
        '<div class="media-left">' +
        '<div style="position: relative; width: 50px; height: 50px;">' +
        (fileType === 'image' ?
                '<img data-type="' + fileExtension + '" data-src="" class="img-responsive image-file" style="width:50px; height:50px; object-fit: cover; border-radius: 0.375rem; border: 1px solid #dee2e6;" src="" alt="' + file.name + '">' :
                '<div class="file-icon-container" style="width:50px; height:50px; display: flex; align-items: center; justify-content: center; border-radius: 0.375rem; border: 1px solid #dee2e6; background-color: #f8f9fa;"><i class="' + iconClass + '" style="font-size: 24px; color: #6c757d;" data-type="' + fileExtension + '"></i></div>'
        ) +
        '<div class="upload-overlay">' +
        '<div class="custom-spinner"></div>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '<div class="media-body">' +
        '<p class="file-name">' + file.name + '</p>' +
        '<small>Uploading... | ' + formatFileSize(file.size) + '</small>' +
        '</div>' +
        '</div>' +
        '</div>';
    // Add to the beginning of the list
    if (listItems.firstChild) {
        listItems.insertBefore(previewElement, listItems.firstChild);
    } else {
        listItems.appendChild(previewElement);
    }
    console.log('Preview element added to the beginning of list');
    setTimeout(function () {
        previewElement.style.transition = 'opacity 0.3s ease';
        previewElement.style.opacity = '1';
    }, 10);
    // Initialize dropdown for the new element
    var dropdownElement = previewElement.querySelector('[data-bs-toggle="dropdown"]');
    if (dropdownElement) {
        new bootstrap.Dropdown(dropdownElement);
    }
    // Setup preview button functionality untuk semua tipe file
    setupImagePreviewListeners(previewElement);
    // Show upload overlay immediately
    var uploadOverlay = previewElement.querySelector('.upload-overlay');
    if (uploadOverlay) {
        uploadOverlay.classList.add('show');
    }
    // Read file as data URL for preview
    if (typeof FileReader !== 'undefined') {
        var reader = new FileReader();
        reader.onload = function (e) {
            if (fileType === 'image') {
                var img = previewElement.querySelector('img');
                if (img) {
                    img.src = e.target.result;
                    img.setAttribute('data-src', e.target.result);
                }
            }
        };
        reader.readAsDataURL(file);
    }
    updateSelectAllCheckbox();
}

function uploadFile(file) {
    console.log('Uploading file:', file.name);
    var id = (file.size + file.lastModified);
    var previewElement = document.querySelector('.img-' + id);
    var uploadOverlay = previewElement ? previewElement.querySelector('.upload-overlay') : null;
    // Cek apakah menggunakan imguploadURL atau fileUploadURL
    var uploadURL = typeof imguploadURL !== 'undefined' ? imguploadURL :
        (typeof fileUploadURL !== 'undefined' ? fileUploadURL : null);
    if (!uploadURL) {
        console.error('Upload URL is not defined');
        showNotification('danger', 'Upload URL is not configured');
        if (uploadOverlay) uploadOverlay.classList.remove('show');
        return;
    }
    console.log('Using upload URL:', uploadURL);
    var formData = new FormData();
    // Coba dengan 'image' dulu, jika gagal mungkin server mengharapkan 'file'
    formData.append('file', file);
    formData.append('csrfmiddlewaretoken', getCsrftoken('csrftoken'));
    if (typeof taxID !== 'undefined') {
        formData.append("taxid", taxID);
    }
    var xhr = new XMLHttpRequest();
    xhr.addEventListener('load', function () {
        console.log('Upload completed, status:', xhr.status);
        console.log('Response:', xhr.responseText);
        if (uploadOverlay) {
            uploadOverlay.classList.remove('show');
        }
        if (xhr.status >= 200 && xhr.status < 300) {
            try {
                var response = JSON.parse(xhr.responseText);
                if (response.status) {
                    if (previewElement) {
                        previewElement.classList.remove('uploading');
                        // Update checkbox value
                        var checkbox = previewElement.querySelector('.magic-checkbox');
                        if (checkbox) checkbox.value = response.id; // Menggunakan response.id
                        // Update image
                        var isImage = file.type.match('image.*');
                        var fileExtension = file.name.split('.').pop().toLowerCase();
                        var iconClass = getFileIconClass(file.type);
                        // Update file preview based on type
                        var mediaLeft = previewElement.querySelector('.media-left');
                        if (mediaLeft) {
                            if (isImage) {
                                // For image files, create img element
                                mediaLeft.innerHTML =
                                    '<div style="position: relative; width: 50px; height: 50px;">' +
                                    '<img data-type="' + fileExtension + '" data-src="' + (response.data_src || '') + '" class="img-responsive image-file" style="width:50px; height:50px; object-fit: cover; border-radius: 0.375rem; border: 1px solid #dee2e6;" src="' +
                                    (response.data_src || '') + '" alt="' + (response.filename || file.name) + '">' +
                                    '<div class="upload-overlay">' +
                                    '<div class="custom-spinner"></div>' +
                                    '</div>' +
                                    '</div>';
                                // Add click event listener for image preview
                                var img = mediaLeft.querySelector('img');
                                if (img) {
                                    img.style.cursor = 'pointer';
                                    img.addEventListener('click', function (e) {
                                        e.preventDefault();
                                        // Use data-src for preview if available
                                        var imageSrc = img.dataset.src || '';
                                        if (imageSrc) {
                                            showImagePreview(imageSrc, img.alt);
                                        }
                                    });
                                }
                            } else {
                                // For non-image files, create icon container
                                mediaLeft.innerHTML =
                                    '<div style="position: relative; width: 50px; height: 50px;">' +
                                    '<div class="file-icon-container" style="width:50px; height:50px; display: flex; align-items: center; justify-content: center; border-radius: 0.375rem; border: 1px solid #dee2e6; background-color: #f8f9fa;"><i class="' + iconClass + '" style="font-size: 24px; color: #6c757d;" data-type="' + fileExtension + '" data-src="' + (response.data_src || '') + '"></i></div>' +
                                    '<div class="upload-overlay">' +
                                    '<div class="custom-spinner"></div>' +
                                    '</div>' +
                                    '</div>';
                            }
                        }
                        // Update file details
                        var fileName = previewElement.querySelector('.file-name');
                        if (fileName) fileName.textContent = response.filename || file.name;
                        var fileMeta = previewElement.querySelector('.media-body small');
                        if (fileMeta) {
                            var date = new Date().toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                            fileMeta.textContent = date + ' | ' + formatFileSize(file.size);
                        }
                        // Update action links dengan fungsi baru
                        setupFileActionLinks(previewElement, response);
                        // Setup image preview listeners untuk semua tipe file
                        setupImagePreviewListeners(previewElement);
                    }
                    // Update counters if they exist
                    var imgFrom = document.querySelector('.img-from');
                    if (imgFrom) imgFrom.textContent = " 1 - " + response.imgcount;
                    var imgTo = document.querySelector('.img-to');
                    if (imgTo) imgTo.textContent = response.imgcount;
                    // Update all images array after successful upload
                    updateAllImagesArray();
                    showNotification('success', 'File uploaded successfully');
                } else {
                    if (previewElement) {
                        previewElement.style.transition = 'opacity 0.3s ease';
                        previewElement.style.opacity = '0';
                        setTimeout(function () {
                            previewElement.remove();
                            updateSelectAllCheckbox();
                        }, 300);
                    }
                    showNotification('danger', gettext(response.content));
                }
            } catch (e) {
                console.error('Error parsing response:', e);
                showNotification('danger', 'Error parsing server response');
            }
        } else {
            showNotification('danger', 'Upload failed with status ' + xhr.status);
        }
        updateSelectAllCheckbox();
    });
    xhr.addEventListener('error', function () {
        console.error('Network error during upload');
        if (uploadOverlay) {
            uploadOverlay.classList.remove('show');
        }
        if (previewElement) {
            previewElement.classList.remove('uploading');
        }
        showNotification('danger', 'Network error during upload');
        updateSelectAllCheckbox();
    });
    xhr.addEventListener('abort', function () {
        console.log('Upload aborted');
        if (uploadOverlay) {
            uploadOverlay.classList.remove('show');
        }
        if (previewElement) {
            previewElement.classList.remove('uploading');
        }
        showNotification('danger', 'Upload aborted');
        updateSelectAllCheckbox();
    });
    xhr.open('POST', uploadURL, true);
    var csrfToken = getCsrftoken('csrftoken');
    if (csrfToken) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
    }
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.send(formData);
}

function handleFiles(files) {
    console.log('Handling files:', files);
    Array.from(files).forEach(function (file) {
        console.log('Processing file:', file.name, file.type, file.size);
        // Hapus validasi yang hanya menerima file gambar
        // if (!file.type.match('image.*')) {
        //     showNotification('danger', 'Only image files are allowed');
        //     return;
        // }
        if (file.size > 128 * 1024 * 1024) {
            showNotification('danger', 'File is too large (max 128MB)');
            return;
        }
        createPreview(file);
        uploadFile(file);
    });
}

// ==================== PREVIEW BUTTON FUNCTIONS ====================
// Modifikasi fungsi setupImagePreviewListeners untuk mendukung semua tipe file
function setupImagePreviewListeners(item) {
    var mediaLeft = item.querySelector('.media-left');
    if (!mediaLeft) return;

    var img = mediaLeft.querySelector('img');
    var iconContainer = mediaLeft.querySelector('.file-icon-container');
    var downloadLink = item.querySelector('.file-settings .dropdown-menu li:last-child a');
    var fileNameElement = item.querySelector('.file-name');
    var fileName = fileNameElement ? fileNameElement.textContent : '';

    // Tambahkan event listener untuk preview
    if (img) {
        img.style.cursor = 'pointer';
        img.removeEventListener('click', handleImageClick);
        img.addEventListener('click', handleImageClick);
    } else if (iconContainer) {
        iconContainer.style.cursor = 'pointer';
        iconContainer.removeEventListener('click', handleImageClick);
        iconContainer.addEventListener('click', handleImageClick);
    }
}


// ==================== CHECKBOX FUNCTIONS ====================
function updateSelectAllCheckbox() {
    var selectAllCheckbox = document.getElementById('select-all');
    if (!selectAllCheckbox) return;
    var itemCheckboxes = document.querySelectorAll('#list-items .file-control input[type="checkbox"]');
    var checkedCheckboxes = document.querySelectorAll('#list-items .file-control input[type="checkbox"]:checked');
    if (itemCheckboxes.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
        return;
    }
    if (itemCheckboxes.length === checkedCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCheckboxes.length > 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
}

function setupItemCheckboxListeners() {
    var itemCheckboxes = document.querySelectorAll('#list-items .file-control input[type="checkbox"]');
    itemCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            updateSelectAllCheckbox();
        });
    });
}

// ==================== INITIALIZATION ====================
// Modifikasi fungsi updateAllImagesArray untuk menyimpan semua file
function updateAllImagesArray() {
    allImages = [];

    var listItems = document.querySelector('#list-items');
    if (!listItems) {
        console.error('List items container not found');
        return;
    }

    var items = listItems.querySelectorAll('li');
    if (!items || items.length === 0) {
        console.log('No items found in list');
        return;
    }

    items.forEach(function (item) {
        // Skip item yang sedang di-upload
        if (item.classList.contains('uploading')) {
            return;
        }

        var mediaLeft = item.querySelector('.media-left');
        if (!mediaLeft) return;

        var img = mediaLeft.querySelector('img');
        var iconContainer = mediaLeft.querySelector('.file-icon-container');
        var downloadLink = item.querySelector('.file-settings .dropdown-menu li:last-child a');
        var fileNameElement = item.querySelector('.file-name');
        var fileName = fileNameElement ? fileNameElement.textContent : '';

        // Dapatkan sumber file
        var fileSrc = '';
        if (img && img.dataset.src) {
            fileSrc = img.dataset.src;
        } else if (iconContainer && iconContainer.querySelector('i') && iconContainer.querySelector('i').dataset.src) {
            fileSrc = iconContainer.querySelector('i').dataset.src;
        } else if (downloadLink && downloadLink.href) {
            fileSrc = downloadLink.href;
        }

        if (fileSrc) {
            allImages.push({
                src: fileSrc,
                alt: fileName || 'File',
                element: item
            });
        }
    });

    console.log('Total files in array:', allImages.length);
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');

    // Update array file saat halaman dimuat
    updateAllImagesArray();

    // Select All checkbox functionality
    var selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            var isChecked = this.checked;
            var itemCheckboxes = document.querySelectorAll('#list-items .file-control input[type="checkbox"]');
            itemCheckboxes.forEach(function (checkbox) {
                checkbox.checked = isChecked;
            });
        });
        console.log('Select All checkbox initialized');
    } else {
        console.error('Select All checkbox not found');
    }

    // Upload functionality
    var fileInput = document.getElementById('file-input');
    var uploadButton = document.getElementById('add-files-list');
    console.log('fileInput element:', fileInput);
    console.log('uploadButton element:', uploadButton);

    if (fileInput && uploadButton) {
        console.log('Initializing upload functionality');
        uploadButton.addEventListener('click', function (e) {
            console.log('Upload button clicked');
            e.preventDefault();
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            console.log('Files selected:', this.files);
            if (this.files.length > 0) {
                handleFiles(this.files);
                this.value = '';
            }
        });
    } else {
        console.error('File input or upload button not found');
    }

    // Setup existing items
    setupItemCheckboxListeners();

    // Setup file action links for existing items
    var listItems = document.querySelector('#list-items');
    if (listItems) {
        var existingItems = listItems.querySelectorAll('li');
        existingItems.forEach(function (item) {
            // Check if item has valid links
            var changeLink = item.querySelector('.dropdown-menu li:first-child a');
            var deleteLink = item.querySelector('.dropdown-menu li:nth-child(2) a');
            var downloadLink = item.querySelector('.dropdown-menu li:last-child a');

            // If any link is undefined or invalid, disable it
            if (changeLink && (!changeLink.href || changeLink.href === 'javascript:;' || changeLink.href === '#')) {
                changeLink.setAttribute('disabled', 'disabled');
                changeLink.style.opacity = '0.5';
                changeLink.style.pointerEvents = 'none';
            }

            if (deleteLink && (!deleteLink.href || deleteLink.href === 'javascript:;' || deleteLink.href === '#')) {
                deleteLink.setAttribute('disabled', 'disabled');
                deleteLink.style.opacity = '0.5';
                deleteLink.style.pointerEvents = 'none';
            }

            if (downloadLink && (!downloadLink.href || downloadLink.href === 'javascript:;' || downloadLink.href === '#')) {
                downloadLink.setAttribute('disabled', 'disabled');
                downloadLink.style.opacity = '0.5';
                downloadLink.style.pointerEvents = 'none';
            }

            // Setup image preview listeners
            setupImagePreviewListeners(item);
        });
    }

    // Initialize Bootstrap dropdowns
    var dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    dropdownElements.forEach(function (element) {
        new bootstrap.Dropdown(element);
    });
});