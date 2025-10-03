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
    }

    getToken() {
        const tokenData = localStorage.getItem('ckbox_token');
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
        localStorage.setItem('ckbox_token', JSON.stringify(tokenData));
        console.log(`Token saved to localStorage. Access expires: ${new Date(expiry).toLocaleString()}, Refresh expires: ${new Date(refreshExpiry).toLocaleString()}`);

        this.token = token;
        this.refreshToken = refreshToken;
        this.tokenExpiry = expiry;
        this.refreshTokenExpiry = refreshExpiry;

        this.setAutoRefresh();
    }

    clearToken() {
        localStorage.removeItem('ckbox_token');
        this.token = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
        this.refreshTokenExpiry = null;
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }
        console.log('Token cleared');
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
                this.clearToken();

                // Reject all queued promises
                this.refreshQueue.forEach(({reject}) => reject(new Error('Token refresh failed')));
                this.refreshQueue = [];

                this.isRefreshing = false;
                return null;
            }
        } catch (error) {
            console.log(`Error refreshing token: ${error.message}`);
            this.clearToken();

            // Reject all queued promises
            this.refreshQueue.forEach(({reject}) => reject(error));
            this.refreshQueue = [];

            this.isRefreshing = false;
            return null;
        }
    }

    async getTokenForCKBox() {
        let token = this.getToken();

        if (!token || !this.isTokenValid()) {
            console.log('Token not valid, attempting refresh...');
            token = await this.refreshAccessToken();
        }

        if (!token) {
            throw new Error('Unable to retrieve a token from the callback.');
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
let tm;

function initializeTokenManager() {
    tm = new TokenManager({
        tokenUrl: config.tokenUrl,
        refreshTokenUrl: config.refreshTokenUrl
    });
}

// Create token URL function for CKBox
function createTokenUrlFunction() {
    return async () => {
        try {
            console.log('CKBox requesting token...');
            // Selalu coba dapatkan token terbaru dari manager
            let token = await tm.getTokenForCKBox();
            console.log('CKBox token obtained successfully');
            return token;
        } catch (error) {
            console.log(`CKBox token error: ${error.message}`);
            showLoginOverlay();
            return null;
        }
    };
}

// Create token refresh function for CKBox
function createTokenRefreshFunction() {
    return async (oldToken) => {
        try {
            console.log('CKBox refreshing token...');
            console.log(`Old token: ${oldToken ? oldToken.substring(0, 0) + '...' : 'null'}`);

            // Refresh token menggunakan token manager
            const newToken = await tm.refreshAccessToken();

            if (newToken) {
                console.log('CKBox token refreshed successfully');
                console.log('New CKBox token:', newToken.substring(0, 20) + '...');
                return newToken;
            }


            throw new Error('Token refresh failed');
        } catch (error) {
            console.log(`CKBox token refresh error: ${error.message}`);
            console.log(`Show Llogin Overlay`);
            showLoginOverlay();
            return null;
        }
    };
}