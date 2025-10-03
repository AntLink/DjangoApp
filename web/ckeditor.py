# CKEditor Configuration
CKEDITOR_BASE_URL = 'http://127.0.0.1:8090'
CKEDITOR_TOKEN_URL = '/api/auth/ckbox_login'
CKEDITOR_REFRESH_TOKEN_URL = '/api/auth/ckbox_token_refresh'
CKEDITOR_API_URL = 'http://127.0.0.1:8090/api'
CKEDITOR_LICENSE_KEY = 'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NTk3MDg3OTksImp0aSI6ImIxN2U4MjU4LTk5ZDUtNDVmZi1iOWUzLTg4ZDQ3ZjU4NjgwYyIsInVzYWdlRW5kcG9pbnQiOiJodHRwczovL3Byb3h5LWV2ZW50LmNrZWRpdG9yLmNvbSIsImRpc3RyaWJ1dGlvbkNoYW5uZWwiOlsiY2xvdWQiLCJkcnVwYWwiLCJzaCJdLCJ3aGl0ZUxhYmVsIjp0cnVlLCJsaWNlbnNlVHlwZSI6InRyaWFsIiwiZmVhdHVyZXMiOlsiKiJdLCJ2YyI6ImZlYjNiOWNlIn0.EmbwFs2lmAIeb0tVL7H4is7Stp-_Q8RWVZQMlpqdoo4tKuc8HTwwK_5cAL3sUxfx4F_SLE9mUWoJUmsVN736Sg'

# AI Configuration
CKEDITOR_AI_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
CKEDITOR_AI_MODEL = 'glm-4.5-flash'
CKEDITOR_AI_TEMPERATURE = 0.8
CKEDITOR_AI_TOP_P = 1
CKEDITOR_AI_API_KEY = '09ac094bc293454b94457cf556ee8616.opW0YYeFQce1AA0m'

# Toolbar Configuration - Simplified to avoid plugin loading issues
CKEDITOR_TOOLBAR_ITEMS = [
    'heading', '|', 'bold', 'italic', 'underline', 'strikethrough', '|',
    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
    'link', 'bulletedList', 'numberedList', 'outdent', 'indent', '|',
    'blockQuote', 'insertTable', '|', 'sourceEditing', 'fullscreen', '|',
    'findAndReplace', 'emoji', 'specialCharacters', 'horizontalLine', 'pageBreak', 'removeFormat'
]

CKEDITOR_FONT_SIZE_OPTIONS = [10, 12, 14, 'default', 18, 20, 22]
CKEDITOR_PLACEHOLDER = 'Type or paste your content here!'