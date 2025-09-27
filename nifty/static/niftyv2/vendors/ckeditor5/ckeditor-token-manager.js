// ckeditor-token-manager.js
class CKEditorTokenManager {
    constructor(config = {}) {
        this.config = {
            tokenUrl: config.tokenUrl || '/api/auth/login/',
            refreshTokenUrl: config.refreshTokenUrl || '/api/auth/token_refresh/',
            loginUrl: config.loginUrl || '/login/',
            uploadUrl: config.uploadUrl || '/api/upload/',
            ...config
        };

        this.token = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
        this.refreshTokenExpiry = null;
        this.refreshTimeout = null;
    }

    // Ambil token dari localStorage
    getToken() {
        const tokenData = localStorage.getItem('ckeditor_token');
        if (tokenData) {
            try {
                const parsed = JSON.parse(tokenData);
                this.token = parsed.token;
                this.refreshToken = parsed.refreshToken;
                this.tokenExpiry = parsed.expiry;
                this.refreshTokenExpiry = parsed.refreshExpiry;
                return this.token;
            } catch (e) {
                console.error('Error parsing token data:', e);
                this.clearToken();
            }
        }
        return null;
    }

    // Simpan token ke localStorage
    saveToken(token, refreshToken, expiry, refreshExpiry) {
        const tokenData = {
            token,
            refreshToken,
            expiry,
            refreshExpiry
        };
        localStorage.setItem('ckeditor_token', JSON.stringify(tokenData));

        this.token = token;
        this.refreshToken = refreshToken;
        this.tokenExpiry = expiry;
        this.refreshTokenExpiry = refreshExpiry;

        // Set auto refresh
        this.setAutoRefresh();
    }

    // Hapus token dari localStorage
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
    }

    // Cek apakah token masih valid
    isTokenValid() {
        if (!this.tokenExpiry) return false;
        return Date.now() < this.tokenExpiry;
    }

    // Cek apakah refresh token masih valid
    isRefreshTokenValid() {
        if (!this.refreshTokenExpiry) return false;
        return Date.now() < this.refreshTokenExpiry;
    }

    // Set auto refresh token
    setAutoRefresh() {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }

        if (!this.tokenExpiry) return;

        // Refresh 5 menit sebelum expired
        const refreshTime = Math.max(0, this.tokenExpiry - Date.now() - 5 * 60 * 1000);

        this.refreshTimeout = setTimeout(() => {
            this.refreshToken();
        }, refreshTime);
    }

    // Refresh token
    async refreshToken() {
        if (!this.refreshToken || !this.isRefreshTokenValid()) {
            this.clearToken();
            this.redirectToLogin();
            return null;
        }

        try {
            const response = await fetch(this.config.refreshTokenUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({refresh: this.refreshToken})
            });

            if (response.ok) {
                const data = await response.json();
                this.saveToken(
                    data.access,
                    data.refresh,
                    Date.now() + 15 * 60 * 1000, // 15 menit
                    Date.now() + 7 * 24 * 60 * 60 * 1000 // 7 hari
                );
                return this.token;
            } else {
                this.clearToken();
                this.redirectToLogin();
                return null;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            this.clearToken();
            this.redirectToLogin();
            return null;
        }
    }

    // Redirect ke halaman login
    redirectToLogin() {
        window.location.href = this.config.loginUrl;
    }

    // Get token untuk CKBox
    async getTokenForCKBox() {
        // Coba ambil token dari localStorage
        let token = this.getToken();

        // Jika token tidak valid, coba refresh
        if (!token || !this.isTokenValid()) {
            token = await this.refreshToken();
        }

        if (!token) {
            throw new Error('Unable to retrieve a token from the callback.');
        }

        return token;
    }

    // Login
    async login(username, password) {
        try {
            const response = await fetch(this.config.tokenUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username, password})
            });

            if (response.ok) {
                const data = await response.json();
                this.saveToken(
                    data.access,
                    data.refresh,
                    Date.now() + 15 * 60 * 1000, // 15 menit
                    Date.now() + 7 * 24 * 60 * 60 * 1000 // 7 hari
                );
                return true;
            } else {
                throw new Error('Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    // Logout
    logout() {
        this.clearToken();
        this.redirectToLogin();
    }
}

// Export token manager
window.CKEditorTokenManager = CKEditorTokenManager;