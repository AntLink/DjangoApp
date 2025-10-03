class TokenManager {
    constructor(config = {}) {
        this.config = {
            tokenUrl: config.tokenUrl || '/api/auth/ckbox_login',
            refreshTokenUrl: config.refreshTokenUrl || '/api/auth/ckbox_token_refresh',
            ...config
        };
        this.token = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
        this.refreshTokenExpiry = null;
        this.refreshTimeout = null;
        this.isRefreshing = false;
        this.refreshQueue = [];
        this.isSessionExpired = false;
        this.shouldStopRetries = false; // Flag untuk menghentikan semua retry

        // Callback untuk menangani sesi expired
        this.onSessionExpired = config.onSessionExpired || (() => {
        });
    }

    getToken() {
        const tokenData = localStorage.getItem('ckeditor_token');
        console.log(`Getting token from localStorage: ${tokenData ? 'Found' : 'Not found'}`);
        if (tokenData) {
            try {
                const parsed = JSON.parse(tokenData);
                this.token = parsed.token;
                this.refreshToken = parsed.refreshToken;
                this.tokenExpiry = parsed.expiry;
                this.refreshTokenExpiry = parsed.refreshExpiry;
                console.log(`Token parsed. Valid: ${this.isTokenValid()}, Refresh valid: ${this.isRefreshTokenValid()}`);
                return this.token;
            } catch (e) {
                console.log(`Error parsing token data: ${e.message}`);
                this.clearToken();
            }
        }
        return null;
    }

    saveToken(token, refreshToken, expiry, refreshExpiry) {
        const tokenData = {
            token,
            refreshToken,
            expiry,
            refreshExpiry
        };
        localStorage.setItem('ckeditor_token', JSON.stringify(tokenData));
        console.log(`Token saved to localStorage. Access expires: ${new Date(expiry).toLocaleString()}, Refresh expires: ${new Date(refreshExpiry).toLocaleString()}`);

        this.token = token;
        this.refreshToken = refreshToken;
        this.tokenExpiry = expiry;
        this.refreshTokenExpiry = refreshExpiry;

        this.setAutoRefresh();
    }

    clearToken() {
        localStorage.removeItem('ckeditor_token');
        this.token = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
        this.refreshTokenExpiry = null;
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }
        this.isSessionExpired = true;
        this.shouldStopRetries = true; // Hentikan semua retry
        console.log('Token cleared');

        // Trigger callback ketika token dibersihkan
        this.onSessionExpired();
    }

    isTokenValid() {
        if (!this.tokenExpiry) return false;
        // Add a small buffer (5 seconds) to account for network latency
        const isValid = Date.now() < (this.tokenExpiry - 5000);
        console.log(`Token valid: ${isValid} (Current: ${new Date().toISOString()}, Expires: ${new Date(this.tokenExpiry).toISOString()})`);
        return isValid;
    }

    isRefreshTokenValid() {
        if (!this.refreshTokenExpiry) return false;
        const isValid = Date.now() < this.refreshTokenExpiry;
        console.log(`Refresh token valid: ${isValid}`);
        return isValid;
    }

    setAutoRefresh() {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }

        if (!this.tokenExpiry) return;

        // Try to refresh 30 seconds before expiry
        const refreshTime = Math.max(0, this.tokenExpiry - Date.now() - 30 * 1000);

        console.log(`Auto-refresh scheduled in ${Math.round(refreshTime / 1000)} seconds`);

        this.refreshTimeout = setTimeout(() => {
            this.refreshAccessToken();
        }, refreshTime);
    }

    async refreshAccessToken() {
        // Jika harus berhenti retry, langsung return null
        if (this.shouldStopRetries) {
            console.log('Should stop retries, returning null');
            this.isRefreshing = false;
            return null;
        }

        // If already refreshing, return the same promise
        if (this.isRefreshing) {
            console.log('Token refresh already in progress, adding to queue');
            return new Promise((resolve, reject) => {
                this.refreshQueue.push({resolve, reject});
            });
        }

        this.isRefreshing = true;
        console.log('Refreshing token...');

        if (!this.refreshToken || !this.isRefreshTokenValid()) {
            console.log('Refresh token not valid, clearing token');
            this.clearToken();
            this.isRefreshing = false;
            return null;
        }

        try {
            const url = `${config.baseUrl}${this.config.refreshTokenUrl}`;
            console.log(`Refreshing token at: ${url}`);

            const response = await fetch(url, {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({refresh: this.refreshToken})
            });

            console.log(`Refresh response status: ${response.status}`);

            if (response.ok) {
                const data = await response.json();
                console.log('Refresh successful, saving new token');

                // Calculate expiry times based on server response
                const tokenExpiry = Date.now() + (data.access_token_lifetime * 1000);
                const refreshExpiry = Date.now() + (data.refresh_token_lifetime * 1000);

                this.saveToken(
                    data.access,
                    data.refresh || this.refreshToken, // Use new refresh token if provided, otherwise keep the old one
                    tokenExpiry,
                    refreshExpiry
                );

                // Resolve all queued promises
                this.refreshQueue.forEach(({resolve}) => resolve(this.token));
                this.refreshQueue = [];

                this.isRefreshing = false;
                return this.token;
            } else {
                console.log(`Refresh failed with status ${response.status}`);

                // Reject all queued promises
                this.refreshQueue.forEach(({reject}) => reject(new Error('Token refresh failed')));
                this.refreshQueue = [];

                this.isRefreshing = false;
                // Clear token and trigger callback
                this.clearToken();
                return null;
            }
        } catch (error) {
            console.log(`Error refreshing token: ${error.message}`);

            // Reject all queued promises
            this.refreshQueue.forEach(({reject}) => reject(error));
            this.refreshQueue = [];

            this.isRefreshing = false;
            // Clear token and trigger callback
            this.clearToken();
            return null;
        }
    }

    async getTokenForCKBox() {
        // Jika harus berhenti retry, kembalikan null
        if (this.shouldStopRetries) {
            console.log('Should stop retries, returning null');
            return null;
        }

        if (this.isSessionExpired) {
            console.log('Session expired, returning null');
            return null;
        }

        let token = this.getToken();
        if (!token || !this.isTokenValid()) {
            console.log('Token not valid, attempting refresh...');
            token = await this.refreshAccessToken();

            // If refresh failed and we don't have a token, return null
            if (!token) {
                return null;
            }
        }
        return token;
    }

    async login(username, password) {
        console.log(`Attempting login for user: ${username}`);

        try {
            const url = `${config.baseUrl}${this.config.tokenUrl}`;
            console.log(`Login attempt at: ${url}`);

            const response = await fetch(url, {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username, password})
            });

            console.log(`Login response status: ${response.status}`);

            if (response.ok) {
                const data = await response.json();
                console.log('Login successful, saving tokens');

                // Calculate expiry times based on server response
                const tokenExpiry = Date.now() + (data.access_token_lifetime * 1000);
                const refreshExpiry = Date.now() + (data.refresh_token_lifetime * 1000);

                this.saveToken(
                    data.access,
                    data.refresh,
                    tokenExpiry,
                    refreshExpiry
                );

                this.isSessionExpired = false; // Reset flag sesi expired
                this.shouldStopRetries = false; // Reset flag stop retries
                return true;
            } else {
                let errorMessage = 'Login failed';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = await response.text();
                }
                console.log(`Login failed: ${errorMessage}`);
                throw new Error(errorMessage);
            }
        } catch (error) {
            console.log(`Login error: ${error.message}`);
            throw error;
        }
    }

    logout() {
        console.log('Logging out...');
        this.clearToken();
    }
}

// Initialize token manager
let tokenManager;

function initializeTokenManager() {
    tokenManager = new TokenManager({
        tokenUrl: config.tokenUrl,
        refreshTokenUrl: config.refreshTokenUrl,
        // Set callback untuk menangani sesi expired
        onSessionExpired: () => {
            console.log('Session expired callback triggered');
            if (!isShowingLogin) {
                isShowingLogin = true;
                destroyCKBox(); // Hancurkan CKBox sebelum menampilkan login
                showLoginOverlay();
            }
        }
    });
}

// Global variables to track CKBox state
let ckboxInstance = null;
let isShowingLogin = false;

// Create token URL function for CKBox
function createTokenUrlFunction() {
    return async () => {
        try {
            console.log('CKBox requesting token...');
            // Selalu coba dapatkan token terbaru dari manager
            let token = await tokenManager.getTokenForCKBox();

            // Jika token null, hentikan CKBox
            if (!token) {
                console.log('Token is null, destroying CKBox');
                if (!isShowingLogin) {
                    isShowingLogin = true;
                    destroyCKBox();
                    showLoginOverlay();
                }
                // Kembalikan string kosong atau nilai yang tidak valid
                return "";
            }

            console.log('CKBox token obtained successfully');
            console.log('CKBox token:', token ? token.substring(0, 20) + '...' : 'null');
            return token;
        } catch (error) {
            console.log(`CKBox token error: ${error.message}`);
            // Jika error, hentikan CKBox
            if (!isShowingLogin) {
                isShowingLogin = true;
                destroyCKBox();
                showLoginOverlay();
            }
            // Kembalikan string kosong atau nilai yang tidak valid
            return "";
        }
    };
}

// Create token refresh function for CKBox
function createTokenRefreshFunction() {
    console.log('run', 'createTokenRefreshFunction');
    return async (oldToken) => {
        try {
            const newToken = await tokenManager.refreshAccessToken();
            if (newToken) {
                return newToken;
            }
            // Jika refresh gagal, hentikan CKBox
            if (!isShowingLogin) {
                isShowingLogin = true;
                destroyCKBox();
                showLoginOverlay();
            }
            // Kembalikan string kosong atau nilai yang tidak valid
            return "";
        } catch (error) {
            console.log(`Token refresh error: ${error.message}`);
            // Jika error, hentikan CKBox
            if (!isShowingLogin) {
                isShowingLogin = true;
                destroyCKBox();
                showLoginOverlay();
            }
            // Kembalikan string kosong atau nilai yang tidak valid
            return "";
        }
    };
}

// Fungsi untuk menghancurkan instance CKBox
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

function showLoginOverlay() {
    const existingOverlay = document.querySelector('.ck-login-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    const overlay = document.createElement('div');
    overlay.className = 'ck-login-overlay ck-login-overlay';
    overlay.innerHTML = `
                <div class="modal fade show d-block" tabindex="-1" role="dialog">
                    <div class="modal-dialog modal-dialog-centered" role="document">
                        <div class="modal-content">
                            <div class="modal-header border-0">
                                <h5 class="modal-title">Login To Your System</h5>
                            </div>
                            <div class="modal-body">
                                <form id="ckeditor-login-form">
                                    <div class="mb-3">
                                        <label for="ckeditor-username" class="form-label">Username</label>
                                        <input type="text" class="form-control" id="ckeditor-username">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ckeditor-password" class="form-label">Password</label>
                                        <input type="password" class="form-control" id="ckeditor-password">
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
    const loginForm = document.getElementById('ckeditor-login-form');
    if (loginForm) {
        // Hapus event listener yang ada sebelumnya untuk mencegah duplikasi
        loginForm.removeEventListener('submit', handleLoginSubmit);
        // Tambahkan event listener baru
        loginForm.addEventListener('submit', handleLoginSubmit);
    }
}

// Fungsi penanganan login
function handleLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('ckeditor-username').value;
    const password = document.getElementById('ckeditor-password').value;
    const debugDiv = document.getElementById('login-debug');
    const debugAlert = debugDiv.querySelector('.alert');

    debugDiv.classList.remove('d-none');
    debugAlert.textContent = 'Attempting login...';
    debugAlert.className = 'alert alert-info small';

    tokenManager.login(username, password)
        .then(() => {
            debugAlert.textContent = 'Login successful! Reloading CKBox...';
            debugAlert.className = 'alert alert-success small';
            setTimeout(() => {
                const overlay = document.querySelector('.ck-login-overlay');
                if (overlay) {
                    overlay.remove();
                }
                isShowingLogin = false;
                loadCKBoxInContent();
            }, 1000);
        })
        .catch(error => {
            debugAlert.textContent = `Login failed: ${error.message}`;
            debugAlert.className = 'alert alert-danger small';
        });
}

// Function to load CKBox in the content area
async function loadCKBoxInContent() {
    try {
        console.log('Loading CKBox in content area...');
        // Ensure we have a valid token
        const token = await tokenManager.getTokenForCKBox();
        if (!token) {
            console.log('No valid token available, showing login');
            if (!isShowingLogin) {
                isShowingLogin = true;
                showLoginOverlay();
            }
            return;
        }
        console.log(`Using token: ${token.substring(0, 20)}...`);

        // Hancurkan instance yang ada jika ada
        destroyCKBox();

        // Mount CKBox to the content area
        ckboxInstance = CKBox.mount(document.querySelector('#ckbox'), {
            tokenUrl: createTokenUrlFunction(),
            onTokenRefresh: createTokenRefreshFunction(),
            assets: {
                list: {
                    pageSize: 55
                }
            },
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
                    if (!isShowingLogin) {
                        isShowingLogin = true;
                        destroyCKBox();
                        showLoginOverlay();
                    }
                } else {
                    alert(`Error with CKBox: ${error.message}`);
                }
            }
        });

        console.log('CKBox mounted successfully in content area');
    } catch (error) {
        console.log(`Error loading CKBox in content area: ${error.message}`);
        console.error('CKBox loading error:', error);
        // Hanya tampilkan login overlay untuk error spesifik
        if (error.message === 'Session expired' || error.message === 'Unable to retrieve a token from the callback.') {
            if (!isShowingLogin) {
                isShowingLogin = true;
                showLoginOverlay();
            }
        }
    }
}

// Initialize the application after CKBox is loaded
function initializeApp() {
    initializeTokenManager();
    console.log('App fully loaded, checking authentication...');
    const token = tokenManager.getToken();
    if (token && tokenManager.isTokenValid()) {
        console.log('User authenticated, loading CKBox in content area...');
        // Load CKBox in content area after a short delay
        setTimeout(() => {
            loadCKBoxInContent();
        }, 1000);
    } else {
        console.log('User not authenticated, showing login form...');
        isShowingLogin = true;
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