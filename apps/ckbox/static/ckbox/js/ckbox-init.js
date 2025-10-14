function destroyCKBox() {
    try {
        // Cek apakah ada instance CKBox
        const ckboxElement = document.querySelector('#ckbox');
        if (ckboxElement) {
            console.log('Destroying CKBox instance...');
            // Kosongkan elemen CKBox
            ckboxElement.innerHTML = '';
            ckboxInstance = null;
        }
    } catch (error) {
        console.log(`Error destroying CKBox: ${error.message}`);
    }
}

// Function to load CKBox in the content area
async function loadCKBoxInContent() {
    try {
        console.log('Loading CKBox in content area...');
        // Ensure we have a valid token
        const token = await tm.getTokenForCKBox();
        if (!token) {
            console.log('No valid token available, showing login');
            showLoginOverlay();
            return;
        }
        console.log(`Using token: ${token.substring(0, 20)}...`);
        // Mount CKBox to the content area
        CKBox.mount(document.querySelector('#ckbox'), {
            tokenUrl: createTokenUrlFunction(),
            onTokenRefresh: createTokenRefreshFunction(),
            onChoose: function (data) {
                console.log('Files selected from CKBox');
                console.log('Selected files:', data);
            },
            onError: function (error) {
                console.log(`CKBox error: ${error.message}`);
                console.error('CKBox error details:', error);
                // Check if error is related to authentication
                if (error.message.includes('token') || error.message.includes('authentication') || error.message.includes('unauthorized')) {
                    console.log('Authentication error, showing login form');
                    showLoginOverlay();
                } else {
                    alert(`Error with CKBox: ${error.message}`);
                }
            }
        });

        console.log('CKBox mounted successfully in content area');
    } catch (error) {
        console.log(`Error loading CKBox in content area: ${error.message}`);
        console.error('CKBox loading error:', error);
        showLoginOverlay();
    }
}

function handleLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('ckbox-username').value;
    const password = document.getElementById('ckbox-password').value;
    const debugDiv = document.getElementById('login-debug');
    const debugAlert = debugDiv.querySelector('.alert');

    debugDiv.classList.remove('d-none');
    debugAlert.textContent = 'Attempting login...';
    debugAlert.className = 'alert alert-info small';

    tm.login(username, password)
        .then(() => {
            debugAlert.textContent = 'Login successful! Reloading CKBox...';
            debugAlert.className = 'alert alert-success small';
            setTimeout(() => {
                const overlay = document.querySelector('.ck-login-overlay');
                if (overlay) {
                    overlay.remove();
                }
                loadCKBoxInContent();
            }, 1000);
        })
        .catch(error => {
            debugAlert.textContent = `Login failed: ${error.message}`;
            debugAlert.className = 'alert alert-danger small';
        });
}

function showLoginOverlay() {
    const existingOverlay = document.querySelector('.ck-login-overlay');
    if (!existingOverlay) {
        destroyCKBox();
        const overlay = document.createElement('div');
        overlay.className = 'ck-login-overlay ck-login-overlay';
        overlay.innerHTML = `
                 <style>
                    .ck-login-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        z-index: 999999 !important;
                    }
                    .ck-login-overlay .modal {
                        z-index: 1000000 !important;
                    }
                    .ck-login-overlay .modal-backdrop {
                        z-index: 999998 !important;
                    }
                </style>
                <div class="modal fade show d-block" tabindex="-1" role="dialog">
                    <div class="modal-dialog modal-dialog-centered" role="document">
                        <div class="modal-content">
                            <div class="modal-header border-0">
                                <h5 class="modal-title">Login To Your System</h5>
                            </div>
                            <div class="modal-body">
                                <form id="ckbox-login-form">
                                    <div class="mb-3">
                                        <label for="ckbox-username" class="form-label">Username</label>
                                        <input type="text" class="form-control" id="ckbox-username">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ckbox-password" class="form-label">Password</label>
                                        <input type="password" class="form-control" id="ckbox-password">
                                    </div>
                                    <div class="d-flex justify-content-end">
                                        <button type="submit" class="btn btn-primary">Login</button>
                                    </div>
                                </form>
                                <div class="mt-3 d-none" id="login-debug">
                                    <div class="alert alert-info small"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-backdrop fade show"></div>
            `;

        document.body.appendChild(overlay);
        // Tambahkan event listener untuk form login
        const loginForm = document.getElementById('ckbox-login-form');
        if (loginForm) {
            // Hapus event listener yang ada sebelumnya untuk mencegah duplikasi
            loginForm.removeEventListener('submit', handleLoginSubmit);
            // Tambahkan event listener baru
            loginForm.addEventListener('submit', handleLoginSubmit);
        }

    }
}


// Initialize the application after CKBox is loaded
function initializeApp() {
    initializeTokenManager();
    console.log('App fully loaded, checking authentication...');
    const token = tm.getToken();
    if (token && tm.isTokenValid()) {
        console.log('User authenticated, loading CKBox in content area...');
        // Load CKBox in content area after a short delay
        setTimeout(() => {
            loadCKBoxInContent();
        }, 1000);
    } else {
        console.log('User not authenticated, showing login form...');
        showLoginOverlay();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (typeof CKBox !== 'undefined') {
        console.log('CKBox is available');
        initializeApp();
    } else {
        console.log('CKBox script loaded but CKBox is not available');
    }
});