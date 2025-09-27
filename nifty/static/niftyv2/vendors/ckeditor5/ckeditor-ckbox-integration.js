// ckeditor-ckbox-integration.js
class CKEditorCKBoxIntegration {
    constructor(editor, tokenManager) {
        this.editor = editor;
        this.tokenManager = tokenManager;
        this.loginOverlay = null;
    }

    // Inisialisasi CKBox dengan token manager
    initializeCKBox() {
        // Konfigurasi CKBox
        this.editor.config.set('ckbox', {
            tokenUrl: async () => {
                try {
                    return await this.tokenManager.getTokenForCKBox();
                } catch (error) {
                    console.error('Error getting token for CKBox:', error);
                    this.showLoginOverlay();
                    throw error;
                }
            },
            onTokenRefresh: async (oldToken) => {
                try {
                    const newToken = await this.tokenManager.refreshToken();
                    if (newToken) {
                        return newToken;
                    }
                    throw new Error('Token refresh failed');
                } catch (error) {
                    console.error('Error refreshing token for CKBox:', error);
                    this.showLoginOverlay();
                    throw error;
                }
            }
        });
    }

    // Tampilkan overlay login di dalam editor
    showLoginOverlay() {
        if (this.loginOverlay) {
            this.loginOverlay.remove();
        }

        // Buat overlay
        this.loginOverlay = document.createElement('div');
        this.loginOverlay.className = 'ck-login-overlay';
        this.loginOverlay.innerHTML = `
            <div class="ck-login-form">
                <h3>Login to CKEditor</h3>
                <form id="ckeditor-login-form">
                    <div class="ck-form-group">
                        <label>Username:</label>
                        <input type="text" id="ckeditor-username" required>
                    </div>
                    <div class="ck-form-group">
                        <label>Password:</label>
                        <input type="password" id="ckeditor-password" required>
                    </div>
                    <div class="ck-form-actions">
                        <button type="submit" class="ck-button ck-button-action">Login</button>
                        <button type="button" class="ck-button ck-button-cancel" id="cancel-login">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        // Tambahkan ke editor
        this.editor.ui.view.element.appendChild(this.loginOverlay);

        // Handle form submission
        document.getElementById('ckeditor-login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Handle cancel button
        document.getElementById('cancel-login').addEventListener('click', () => {
            this.hideLoginOverlay();
        });
    }

    // Sembunyikan overlay login
    hideLoginOverlay() {
        if (this.loginOverlay) {
            this.loginOverlay.remove();
            this.loginOverlay = null;
        }
    }

    // Handle login
    async handleLogin() {
        const username = document.getElementById('ckeditor-username').value;
        const password = document.getElementById('ckeditor-password').value;

        try {
            await this.tokenManager.login(username, password);
            this.hideLoginOverlay();

            // Reload CKEditor untuk menggunakan token baru
            this.reloadEditor();
        } catch (error) {
            alert('Login failed. Please check your credentials.');
        }
    }

    // Reload editor dengan konfigurasi baru
    reloadEditor() {
        const editorElement = this.editor.ui.view.element;
        const editorData = this.editor.getData();

        // Destroy editor saat ini
        this.editor.destroy();

        // Inisialisasi ulang editor
        this.initializeEditor(editorElement, editorData);
    }

    // Inisialisasi editor
    initializeEditor(element, initialData = '') {
        ClassicEditor
            .create(element, {
                initialData: initialData,
                plugins: [
                    Essentials,
                    Paragraph,
                    Heading,
                    Bold,
                    Italic,
                    Link,
                    List,
                    Indent,
                    IndentBlock,
                    BlockQuote,
                    Table,
                    TableToolbar,
                    MediaEmbed,
                    Image,
                    ImageToolbar,
                    ImageCaption,
                    ImageStyle,
                    ImageUpload,
                    CKBox
                ],
                toolbar: [
                    'ckbox', 'imageUpload', '|', 'heading', '|', 'bold', 'italic', '|', 'link', 'bulletedList', 'numberedList', '|', 'outdent', 'indent', '|', 'blockQuote', 'insertTable', '|', 'undo', 'redo'
                ],
                ckbox: {
                    tokenUrl: async () => {
                        try {
                            return await this.tokenManager.getTokenForCKBox();
                        } catch (error) {
                            console.error('Error getting token for CKBox:', error);
                            this.showLoginOverlay();
                            throw error;
                        }
                    },
                    onTokenRefresh: async (oldToken) => {
                        try {
                            const newToken = await this.tokenManager.refreshToken();
                            if (newToken) {
                                return newToken;
                            }
                            throw new Error('Token refresh failed');
                        } catch (error) {
                            console.error('Error refreshing token for CKBox:', error);
                            this.showLoginOverlay();
                            throw error;
                        }
                    }
                }
            })
            .then(editor => {
                this.editor = editor;
                console.log('Editor was initialized', editor);
            })
            .catch(error => {
                console.error('Error initializing editor:', error);
            });
    }
}

// Export integration class
window.CKEditorCKBoxIntegration = CKEditorCKBoxIntegration;