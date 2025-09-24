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
    // Create the HTML structure similar to existing items
    previewElement.innerHTML =
        '<div class="file-control" style="width: 30px;">' +
        '<input type="checkbox" name="_selected_action" class="form-check-input magic-checkbox" id="list-' + id + '">' +
        '</div>' +
        '<div class="file-settings dropdown">' +
        '<button class="btn btn-icon" data-bs-toggle="dropdown" type="button" aria-expanded="false">' +
        '<i class="demo-psi-dot-vertical"></i>' +
        '</button>' +
        '<ul class="dropdown-menu">' +
        '<li><a class="btn-link" href="#"><i class="demo-pli-pen-5"></i> Change</a></li>' +
        '<li><a class="btn-link" href="#"><i class="demo-pli-trash"></i> Delete</a></li>' +
        '<li><a target="_blank" class="btn-link download-link" href="javascript:;"><i class="demo-pli-download-from-cloud"></i> Download</a></li>' +
        '</ul>' +
        '</div>' +
        '<div class="file-details">' +
        '<div class="media-block">' +
        '<div class="media-left">' +
        '<div style="position: relative; width: 50px; height: 50px;">' +
        '<img class="img-responsive" style="width:50px; height:50px; object-fit: cover; border-radius: 0.375rem; border: 1px solid #dee2e6;" src="/static/admin/filemedia/img/no-thumb/td_100x100.png" alt="' + file.name + '">' +
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
    // Add preview button functionality
    var img = previewElement.querySelector('.media-left img');
    if (img) {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function(e) {
            e.preventDefault();
            // Get download link for preview
            var downloadLink = previewElement.querySelector('.download-link');
            if (downloadLink && downloadLink.href) {
                showImagePreview(downloadLink.href, img.alt);
            }
        });
    }
    // Show upload overlay immediately
    var uploadOverlay = previewElement.querySelector('.upload-overlay');
    if (uploadOverlay) {
        uploadOverlay.classList.add('show');
    }
    // Read file as data URL for preview
    if (typeof FileReader !== 'undefined') {
        var reader = new FileReader();
        reader.onload = function (e) {
            var img = previewElement.querySelector('img');
            if (img) {
                img.src = e.target.result;
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
    if (typeof imguploadURL === 'undefined') {
        console.error('imguploadURL is not defined');
        showNotification('danger', 'Upload URL is not configured');
        if (uploadOverlay) uploadOverlay.classList.remove('show');
        return;
    }
    console.log('Using upload URL:', imguploadURL);
    var formData = new FormData();
    formData.append('image', file);
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
                        if (checkbox) checkbox.value = response.imgid;
                        // Update image
                        var img = previewElement.querySelector('img');
                        if (img) {
                            img.src = response.thmb.width100;
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
                        // Update action links
                        var changeLink = previewElement.querySelector('.dropdown-menu li:first-child a');
                        if (changeLink) changeLink.href = response.imgchange_link;
                        var deleteLink = previewElement.querySelector('.dropdown-menu li:nth-child(2) a');
                        if (deleteLink) deleteLink.href = response.imgdelete_link;
                        var downloadLink = previewElement.querySelector('.download-link');
                        if (downloadLink) downloadLink.href = response.imgview_link;

                        // Re-attach event listeners for the uploaded image
                        setupImagePreviewListeners(previewElement);
                    }
                    // Update counters if they exist
                    var imgFrom = document.querySelector('.img-from');
                    if (imgFrom) imgFrom.textContent = " 1 - " + response.imgcount;
                    var imgTo = document.querySelector('.img-to');
                    if (imgTo) imgTo.textContent = response.imgcount;

                    // Update all images array after successful upload
                    updateAllImagesArray();

                    showNotification('success', 'Image uploaded successfully');
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
    xhr.open('POST', imguploadURL, true);
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
// ==================== PREVIEW BUTTON FUNCTIONS ====================
function setupImagePreviewListeners(item) {
    var img = item.querySelector('.media-left img');
    if (img) {
        img.style.cursor = 'pointer';
        // Remove any existing event listener to avoid duplicates
        img.removeEventListener('click', handleImageClick);
        // Add the event listener
        img.addEventListener('click', handleImageClick);
    }
}

function handleImageClick(e) {
    e.preventDefault();
    var item = e.currentTarget.closest('li');
    if (item) {
        // Get download link for preview
        var downloadLink = item.querySelector('.file-settings .dropdown-menu li:last-child a');
        if (downloadLink && downloadLink.href && downloadLink.href !== 'javascript:;') {
            // Update array gambar sebelum menampilkan preview
            updateAllImagesArray();
            // Cari index gambar ini dalam array
            var imageIndex = allImages.findIndex(function(image) {
                return image.element === item;
            });
            var img = item.querySelector('.media-left img');
            showImagePreview(downloadLink.href, img.alt, imageIndex);
        }
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
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');
    // Update array gambar saat halaman dimuat
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
    // Upload functionality - Updated to use add-image-list button
    var fileInput = document.getElementById('file-input');
    var uploadButton = document.getElementById('add-image-list');
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

    // Tambahkan event listener untuk klik pada gambar untuk semua item yang ada
    var imageItems = document.querySelectorAll('#list-items li');
    imageItems.forEach(function(item) {
        setupImagePreviewListeners(item);
    });

    // Initialize Bootstrap dropdowns
    var dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    dropdownElements.forEach(function(element) {
        new bootstrap.Dropdown(element);
    });
});
function updateAllImagesArray() {
    allImages = [];
    var items = document.querySelectorAll('#list-items li');
    items.forEach(function(item) {
        // Skip item yang sedang di-upload
        if (item.classList.contains('uploading')) {
            return;
        }
        // Get download link for preview
        var downloadLink = item.querySelector('.file-settings .dropdown-menu li:last-child a');
        if (downloadLink && downloadLink.href && downloadLink.href !== 'javascript:;') {
            var img = item.querySelector('.media-left img');
            if (img && img.src) {
                // Cek apakah gambar sudah ada di array untuk menghindari duplikasi
                var imageExists = allImages.some(function(image) {
                    return image.src === downloadLink.href;
                });
                if (!imageExists) {
                    allImages.push({
                        src: downloadLink.href,
                        alt: img.alt || 'Image',
                        element: item
                    });
                }
            }
        }
    });
    console.log('Total images in array:', allImages.length);
}