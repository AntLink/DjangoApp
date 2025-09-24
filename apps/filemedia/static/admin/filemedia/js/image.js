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

// ==================== IMAGE PREVIEW FUNCTIONS ====================
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

        var img = document.createElement('img');
        img.src = imageSrc;
        img.alt = imageAlt || 'Image Preview';

        imageContainer.appendChild(img);

        // Zoom controls
        var zoomControls = document.createElement('div');
        zoomControls.className = 'image-preview-zoom-controls';

        var zoomOutBtn = document.createElement('button');
        zoomOutBtn.className = 'zoom-btn';
        zoomOutBtn.innerHTML = '-';
        zoomOutBtn.title = 'Zoom Out';

        var zoomResetBtn = document.createElement('button');
        zoomResetBtn.className = 'zoom-btn';
        zoomResetBtn.innerHTML = '⟲';
        zoomResetBtn.title = 'Reset Zoom';

        var zoomInBtn = document.createElement('button');
        zoomInBtn.className = 'zoom-btn';
        zoomInBtn.innerHTML = '+';
        zoomInBtn.title = 'Zoom In';

        zoomControls.appendChild(zoomOutBtn);
        zoomControls.appendChild(zoomResetBtn);
        zoomControls.appendChild(zoomInBtn);

        // Tombol close
        var closeBtn = document.createElement('button');
        closeBtn.className = 'image-preview-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Close (Esc)';

        // Tombol previous
        var prevBtn = document.createElement('button');
        prevBtn.className = 'image-preview-prev';
        prevBtn.innerHTML = '&#10094;';
        prevBtn.title = 'Previous (Left Arrow)';

        // Tombol next
        var nextBtn = document.createElement('button');
        nextBtn.className = 'image-preview-next';
        nextBtn.innerHTML = '&#10095;';
        nextBtn.title = 'Next (Right Arrow)';

        // Image counter
        var counter = document.createElement('div');
        counter.className = 'image-preview-counter';

        modalContent.appendChild(imageContainer);
        modalContent.appendChild(closeBtn);
        modalContent.appendChild(prevBtn);
        modalContent.appendChild(nextBtn);
        modalContent.appendChild(counter);
        modalContent.appendChild(zoomControls);
        modal.appendChild(modalContent);

        document.body.appendChild(modal);

        // Event listeners
        closeBtn.addEventListener('click', closeImagePreview);
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeImagePreview();
            }
        });

        prevBtn.addEventListener('click', showPreviousImage);
        nextBtn.addEventListener('click', showNextImage);

        // Zoom controls
        zoomOutBtn.addEventListener('click', function() {
            zoomImage(-zoomStep);
        });

        zoomResetBtn.addEventListener('click', function() {
            resetZoom();
        });

        zoomInBtn.addEventListener('click', function() {
            zoomImage(zoomStep);
        });

        // Mouse wheel zoom
        imageContainer.addEventListener('wheel', function(e) {
            e.preventDefault();

            // Determine zoom direction
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
        img.addEventListener('dragstart', function(e) {
            e.preventDefault();
        });

        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeImagePreview();
                document.removeEventListener('keydown', escHandler);
            } else if (e.key === 'ArrowLeft') {
                showPreviousImage();
            } else if (e.key === 'ArrowRight') {
                showNextImage();
            } else if (e.key === '0') {
                resetZoom();
            } else if (e.key === '+' || e.key === '=') {
                zoomImage(zoomStep);
            } else if (e.key === '-' || e.key === '_') {
                zoomImage(-zoomStep);
            }
        });

        // Reset zoom when image loads
        img.addEventListener('load', function() {
            resetZoom();
        });
    } else {
        var imageContainer = modal.querySelector('.image-preview-container');
        var img = modal.querySelector('img');
        if (img) {
            img.src = imageSrc;
            img.alt = imageAlt || 'Image Preview';
            // Reset zoom when image changes
            resetZoom();
        }
    }

    // Update counter
    updateImageCounter();

    // Update visibility tombol navigasi
    updateNavigationButtons();

    setTimeout(function() {
        modal.classList.add('show');
    }, 10);
}

function closeImagePreview() {
    var modal = document.getElementById('image-preview-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(function() {
            // modal.remove();
        }, 300);
    }
}

function showPreviousImage() {
    if (allImages.length > 0) {
        currentImageIndex = (currentImageIndex - 1 + allImages.length) % allImages.length;
        var image = allImages[currentImageIndex];
        showImagePreview(image.src, image.alt, currentImageIndex);
    }
}

function showNextImage() {
    if (allImages.length > 0) {
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
            // Sembunyikan tombol jika hanya ada satu gambar
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
    imageContainers.forEach(function(container) {
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

// ==================== GRID FUNCTIONS ====================
function reloadFreeWall() {
    var imageGrid = document.querySelector('#grid-preview');
    if (!imageGrid) return;

    var previews = imageGrid.querySelectorAll('.dz-preview');
    previews.forEach(function(preview) {
        preview.style.position = '';
        preview.style.width = '';
        preview.style.height = '';
        preview.style.left = '';
        preview.style.top = '';
    });

    imageGrid.style.height = '';
    imageGrid.classList.add('rearranging');

    setTimeout(function () {
        imageGrid.classList.remove('rearranging');
    }, 300);
}

// ==================== PREVIEW BUTTON FUNCTIONS ====================
function addPreviewButtonsToExistingItems() {
    var existingPreviews = document.querySelectorAll('.dz-preview');
    existingPreviews.forEach(function(preview, index) {
        // Cek apakah tombol preview sudah ada
        if (!preview.querySelector('.preview-btn')) {
            var imgActions = preview.querySelector('.img-actions span');
            if (imgActions) {
                // Tambahkan tombol preview dengan class yang sama seperti tombol lainnya
                var previewBtn = document.createElement('a');
                previewBtn.className = 'add-tooltip btn-link preview-btn';
                previewBtn.title = 'Preview';
                previewBtn.href = 'javascript:;';
                previewBtn.innerHTML = '<i class="demo-psi-layout-grid"></i>';

                // Tambahkan spasi sebelum tombol
                var space = document.createTextNode('&nbsp;');
                imgActions.appendChild(space);
                imgActions.appendChild(previewBtn);

                // Tambahkan event listener
                previewBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    var img = preview.querySelector('.card-img-top');
                    if (img && img.src) {
                        // Update array gambar sebelum menampilkan preview
                        updateAllImagesArray();

                        // Cari index gambar ini dalam array
                        var imageIndex = allImages.findIndex(function(image) {
                            return image.element === preview;
                        });

                        var originalImage = img.getAttribute('data-image') || img.src;
                        showImagePreview(originalImage, img.alt, imageIndex);
                    }
                });

                // Inisialisasi tooltip
                previewBtn.addEventListener('mouseenter', function () {
                    var title = previewBtn.getAttribute('title');
                    if (title) {
                        var tooltipDiv = document.createElement('div');
                        tooltipDiv.className = 'tooltip';
                        tooltipDiv.textContent = title;
                        document.body.appendChild(tooltipDiv);
                        var rect = previewBtn.getBoundingClientRect();
                        tooltipDiv.style.top = (rect.top - tooltipDiv.offsetHeight - 5) + 'px';
                        tooltipDiv.style.left = (rect.left + (rect.width - tooltipDiv.offsetWidth) / 2) + 'px';
                        previewBtn._tooltipElement = tooltipDiv;
                    }
                });

                previewBtn.addEventListener('mouseleave', function () {
                    if (previewBtn._tooltipElement) {
                        tooltipDiv._tooltipElement.remove();
                        previewBtn._tooltipElement = null;
                    }
                });
            }
        }
    });
}

// ==================== CHECKBOX FUNCTIONS ====================
function updateSelectAllCheckbox() {
    var selectAllCheckbox = document.getElementById('select-all');
    if (!selectAllCheckbox) return;

    var itemCheckboxes = document.querySelectorAll('.dz-preview .magic-checkbox');
    var checkedCheckboxes = document.querySelectorAll('.dz-preview .magic-checkbox:checked');

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
    var itemCheckboxes = document.querySelectorAll('.dz-preview .magic-checkbox');
    itemCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            updateSelectAllCheckbox();
        });
    });
}

// ==================== UPLOAD FUNCTIONS ====================
function createPreview(file) {
    console.log('Creating preview for:', file.name);
    var imageGrid = document.querySelector('#grid-preview');
    if (!imageGrid) {
        console.error('Image grid not found');
        return;
    }

    var id = (file.size + file.lastModified);

    var previewElement = document.createElement('div');
    previewElement.className = 'dz-preview img-' + id;
    previewElement.classList.add('uploading');
    previewElement.style.opacity = '0';

    previewElement.innerHTML =
        '<div class="file-control" style="width: 30px;">' +
        '<input type="checkbox" name="_selected_action" class="form-check-input magic-checkbox" id="list-' + id + '">' +
        '</div>' +
        '<img class="card-img-top" src="/static/admin/filemedia/img/no-thumb/td_100x100.png" alt="' + file.name + '">' +
        '<div class="img-actions">' +
        '<span style="font-size:14px;">' +
        '<a class="btn-link"  data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Change" href="#"><i class="demo-pli-pen-5"></i></a>&nbsp;' +
        '<a target="_blank" class="btn-link"  data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Download" href="javascript:;"><i class="demo-pli-download-from-cloud"></i></a>&nbsp;' +
        '<a class="btn-link"  data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Delete" href="#"><i class="demo-pli-trash"></i></a>&nbsp;' +
        '<a class="btn-link preview-btn"  data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="View Image" href="javascript:;"><i class="fa fa-eye"></i></a>' +
        '</span>' +
        '</div>';

    var uploadOverlay = document.createElement('div');
    uploadOverlay.className = 'upload-overlay';
    uploadOverlay.innerHTML =
        '<div class="custom-spinner"></div>' +
        '<div class="progress-text">0%</div>' +
        '<div class="progress">' +
        '<div class="progress-bar" role="progressbar" style="width: 0%"></div>' +
        '</div>';

    previewElement.insertBefore(uploadOverlay, previewElement.querySelector('.img-actions'));

    if (imageGrid.firstChild) {
        imageGrid.insertBefore(previewElement, imageGrid.firstChild);
    } else {
        imageGrid.appendChild(previewElement);
    }
    console.log('Preview element added to the beginning of grid');

    setTimeout(function () {
        previewElement.style.transition = 'opacity 0.3s ease';
        previewElement.style.opacity = '1';
    }, 10);

    if (typeof FileReader !== 'undefined') {
        var reader = new FileReader();
        reader.onload = function (e) {
            var img = previewElement.querySelector('img');
            if (img) {
                img.src = e.target.result;
            }
            reloadFreeWall();
        };
        reader.readAsDataURL(file);
    }

    var tooltips = previewElement.querySelectorAll('.add-tooltip');
    tooltips.forEach(function (tooltip) {
        tooltip.addEventListener('mouseenter', function () {
            var title = tooltip.getAttribute('title');
            if (title) {
                var tooltipDiv = document.createElement('div');
                tooltipDiv.className = 'tooltip';
                tooltipDiv.textContent = title;
                document.body.appendChild(tooltipDiv);
                var rect = tooltip.getBoundingClientRect();
                tooltipDiv.style.top = (rect.top - tooltipDiv.offsetHeight - 5) + 'px';
                tooltipDiv.style.left = (rect.left + (rect.width - tooltipDiv.offsetWidth) / 2) + 'px';
                tooltip._tooltipElement = tooltipDiv;
            }
        });

        tooltip.addEventListener('mouseleave', function () {
            if (tooltip._tooltipElement) {
                tooltip._tooltipElement.remove();
                tooltip._tooltipElement = null;
            }
        });
    });

    var previewBtn = previewElement.querySelector('.preview-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var img = previewElement.querySelector('.card-img-top');
            if (img && img.src) {
                showImagePreview(img.src, img.alt);
            }
        });
    }

    updateSelectAllCheckbox();
}

function uploadFile(file) {
    console.log('Uploading file:', file.name);
    var id = (file.size + file.lastModified);
    var previewElement = document.querySelector('.img-' + id);
    var progressBar = previewElement ? previewElement.querySelector('.progress-bar') : null;
    var uploadOverlay = previewElement ? previewElement.querySelector('.upload-overlay') : null;

    if (typeof imguploadURL === 'undefined') {
        console.error('imguploadURL is not defined');
        showNotification('danger', 'Upload URL is not configured');
        if (uploadOverlay) uploadOverlay.classList.remove('show');
        return;
    }
    console.log('Using upload URL:', imguploadURL);

    if (uploadOverlay) {
        uploadOverlay.classList.add('show');
    }

    var formData = new FormData();
    formData.append('image', file);
    formData.append('csrfmiddlewaretoken', getCsrftoken('csrftoken'));
    if (typeof taxID !== 'undefined') {
        formData.append("taxid", taxID);
    }

    var xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function (e) {
        if (e.lengthComputable && progressBar) {
            var percent = Math.round((e.loaded / e.total) * 100);
            progressBar.style.width = percent + '%';

            var progressText = previewElement.querySelector('.progress-text');
            if (progressText) {
                progressText.textContent = percent + '%';
            }
        }
    });

    xhr.addEventListener('load', function () {
        console.log('Upload completed, status:', xhr.status);
        console.log('Response headers:', xhr.getAllResponseHeaders());
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
                        var checkbox = previewElement.querySelector('.magic-checkbox');
                        if (checkbox) checkbox.value = response.imgid;
                        var img = previewElement.querySelector('img');
                        if (img) {
                            img.src = response.thmb.width100;
                            img.setAttribute('data-image', response.imgview_link);
                        }
                        var changeLink = previewElement.querySelector('.img-actions a:nth-child(1)');
                        if (changeLink) changeLink.href = response.imgchange_link;
                        var deleteLink = previewElement.querySelector('.img-actions a:nth-child(3)');
                        if (deleteLink) deleteLink.href = response.imgdelete_link;
                        var viewLink = previewElement.querySelector('.img-actions a:nth-child(2)');
                        if (viewLink) viewLink.href = response.imgview_link;

                        var previewBtn = previewElement.querySelector('.preview-btn');
                        if (previewBtn) {
                            previewBtn.addEventListener('click', function(e) {
                                e.preventDefault();
                                var originalImage = img.getAttribute('data-image') || img.src;
                                showImagePreview(originalImage, img.alt);
                            });
                        }
                    }

                    var imgFrom = document.querySelector('.img-from');
                    if (imgFrom) imgFrom.textContent = " 1 - " + response.imgcount;
                    var imgTo = document.querySelector('.img-to');
                    if (imgTo) imgTo.textContent = response.imgcount;

                    showNotification('success', 'Image uploaded successfully');
                } else {
                    if (previewElement) {
                        previewElement.style.transition = 'opacity 0.3s ease';
                        previewElement.style.opacity = '0';
                        setTimeout(function () {
                            previewElement.remove();
                            reloadFreeWall();
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

        reloadFreeWall();
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
        reloadFreeWall();
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
        reloadFreeWall();
        updateSelectAllCheckbox();
    });

    xhr.open('POST', imguploadURL, true);

    var csrfToken = getCsrftoken('csrftoken');
    if (csrfToken) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
    }

    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    xhr.send(formData);
    console.log('Upload request sent with headers:', {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
    });
}

function handleFiles(files) {
    console.log('Handling files:', files);
    Array.from(files).forEach(function (file) {
        console.log('Processing file:', file.name, file.type, file.size);
        if (!file.type.match('image.*')) {
            showNotification('danger', 'Only image files are allowed');
            return;
        }
        if (file.size > 128 * 1024 * 1024) {
            showNotification('danger', 'File is too large (max 128MB)');
            return;
        }
        createPreview(file);
        uploadFile(file);
    });
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');

    // Update array gambar saat halaman dimuat
    updateAllImagesArray();

    // Select All checkbox functionality
    var selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            var isChecked = this.checked;
            var itemCheckboxes = document.querySelectorAll('.dz-preview .magic-checkbox');
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
    var uploadButton = document.getElementById('add-image-grid');
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

    // Tambahkan tombol preview ke item yang sudah ada dan pasang event listener
    addPreviewButtonsToExistingItems();

    // Pasang event listener untuk tombol preview yang sudah ada (jika ada)
    var existingPreviewButtons = document.querySelectorAll('.preview-btn');
    existingPreviewButtons.forEach(function(button) {
        // Hapus event listener yang mungkin sudah ada
        button.removeEventListener('click', handlePreviewClick);
        // Tambahkan event listener baru
        button.addEventListener('click', handlePreviewClick);
    });

    // Inisialisasi tooltip untuk elemen yang sudah ada
    var tooltips = document.querySelectorAll('.add-tooltip');
    tooltips.forEach(function (tooltip) {
        tooltip.addEventListener('mouseenter', function () {
            var title = tooltip.getAttribute('title');
            if (title) {
                var tooltipDiv = document.createElement('div');
                tooltipDiv.className = 'tooltip';
                tooltipDiv.textContent = title;
                document.body.appendChild(tooltipDiv);
                var rect = tooltip.getBoundingClientRect();
                tooltipDiv.style.top = (rect.top - tooltipDiv.offsetHeight - 5) + 'px';
                tooltipDiv.style.left = (rect.left + (rect.width - tooltipDiv.offsetWidth) / 2) + 'px';
                tooltip._tooltipElement = tooltipDiv;
            }
        });

        tooltip.addEventListener('mouseleave', function () {
            if (tooltip._tooltipElement) {
                tooltip._tooltipElement.remove();
                tooltip._tooltipElement = null;
            }
        });
    });
});

// Fungsi handler untuk tombol preview
function handlePreviewClick(e) {
    e.preventDefault();
    var button = e.currentTarget;
    var preview = button.closest('.dz-preview');
    if (preview) {
        var img = preview.querySelector('.card-img-top');
        if (img && img.src) {
            // Update array gambar sebelum menampilkan preview
            updateAllImagesArray();

            // Cari index gambar ini dalam array
            var imageIndex = allImages.findIndex(function(image) {
                return image.element === preview;
            });

            var originalImage = img.getAttribute('data-image') || img.src;
            showImagePreview(originalImage, img.alt, imageIndex);
        }
    }
}

function updateAllImagesArray() {
    allImages = [];
    var previews = document.querySelectorAll('.dz-preview');
    previews.forEach(function(preview, index) {
        var img = preview.querySelector('.card-img-top');
        if (img && img.src) {
            allImages.push({
                src: img.getAttribute('data-image') || img.src,
                alt: img.alt,
                element: preview
            });
        }
    });
}