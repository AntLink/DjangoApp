# CKEditor Configuration
CKEDITOR_BASE_URL = 'http://127.0.0.1:8090'
CKEDITOR_TOKEN_URL = '/api/auth/login'
CKEDITOR_REFRESH_TOKEN_URL = '/api/auth/token-refresh'
CKEDITOR_API_URL = 'http://127.0.0.1:8090/api'
CKEDITOR_LICENSE_KEY = '-'

# AI Configuration
CKEDITOR_AI_API_URL = 'https://api.z.ai/api/paas/v4/chat/completions'
CKEDITOR_AI_MODEL = 'glm-4.5-flash'
CKEDITOR_AI_TEMPERATURE = 0.8
CKEDITOR_AI_TOP_P = 1
CKEDITOR_AI_API_KEY = 'c043b4797fd245cf9d104dddda39a383.P8hW0m9To6Lf1rIC'

CKEDITOR_PLUGIN = []
CKEDITOR_EMOJI_LANG = 'http://127.0.0.1:8090/static/niftyv2/vendors/ckeditor5/emoji-en.json'

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

CKEDITOR_PLUGIN = [
    "AIAssistant", "OpenAITextAdapter", "SourceEditingEnhanced", "Alignment",
    "Autoformat", "AutoImage", "AutoLink", "Autosave", "BalloonToolbar", "BlockQuote",
    "BlockToolbar", "Bold", "Bookmark", "CKBox", "CKBoxImageEdit", "CloudServices",
    "Code", "CodeBlock", "Emoji", "Essentials", "FindAndReplace", "FontBackgroundColor",
    "FontColor", "FontFamily", "FontSize", "Fullscreen", "GeneralHtmlSupport",
    "Heading", "Highlight", "HorizontalLine", "ImageBlock", "ImageCaption",
    "ImageEditing", "ImageInline", "ImageInsert", "ImageInsertViaUrl", "ImageResize",
    "ImageStyle", "ImageTextAlternative", "ImageToolbar", "ImageUpload", "ImageUtils",
    "Indent", "IndentBlock", "Italic", "Link", "LinkImage", "List", "ListProperties",
    "MediaEmbed", "Mention", "PageBreak", "Paragraph", "ExportPdf", "ExportWord",
    "ImportWord", "PasteFromMarkdownExperimental", "PasteFromOffice", "PictureEditing",
    "PlainTableOutput", "RemoveFormat", "ShowBlocks", "SourceEditing", "SpecialCharacters",
    "SpecialCharactersArrows", "SpecialCharactersCurrency", "SpecialCharactersEssentials",
    "SpecialCharactersLatin", "SpecialCharactersMathematical", "SpecialCharactersText",
    "Strikethrough", "Subscript", "Superscript", "Table", "TableCaption",
    "TableCellProperties", "TableColumnResize", "TableLayout", "TableProperties",
    "TableToolbar", "TextTransformation", "TodoList", "Underline", "Typing"
]

CKEDITOR_CONFIG = {
    "toolbar": {
        "items": [
            "fullscreen", "|", "undo", "redo", "|",
            "importWord", "exportWord", "exportPdf", "SourceEditingEnhanced", "|",
            "aiCommands", "aiAssistant", "|", "heading", "sourceEditing", "showBlocks",
            "findAndReplace", "|", "insertImage", "CKBox", "mediaEmbed", "|",
            "insertTable", "insertTableLayout", "|", "alignment", "bulletedList",
            "numberedList", "todoList", "outdent", "indent", "|",
            "fontSize", "fontFamily", "fontColor", "fontBackgroundColor", "|",
            "bold", "italic", "underline", "strikethrough", "subscript", "superscript", "code",
            "removeFormat", "|", "emoji", "specialCharacters", "horizontalLine", "pageBreak",
            "link", "bookmark", "highlight", "blockQuote", "codeBlock"
        ],
        "shouldNotGroupWhenFull": False,
    },
    "plugins": [
        "AIAssistant", "OpenAITextAdapter", "SourceEditingEnhanced", "Alignment",
        "Autoformat", "AutoImage", "AutoLink", "Autosave", "BalloonToolbar", "BlockQuote",
        "BlockToolbar", "Bold", "Bookmark", "CKBox", "CKBoxImageEdit", "CloudServices",
        "Code", "CodeBlock", "Emoji", "Essentials", "FindAndReplace", "FontBackgroundColor",
        "FontColor", "FontFamily", "FontSize", "Fullscreen", "GeneralHtmlSupport",
        "Heading", "Highlight", "HorizontalLine", "ImageBlock", "ImageCaption",
        "ImageEditing", "ImageInline", "ImageInsert", "ImageInsertViaUrl", "ImageResize",
        "ImageStyle", "ImageTextAlternative", "ImageToolbar", "ImageUpload", "ImageUtils",
        "Indent", "IndentBlock", "Italic", "Link", "LinkImage", "List", "ListProperties",
        "MediaEmbed", "Mention", "PageBreak", "Paragraph", "ExportPdf", "ExportWord",
        "ImportWord", "PasteFromMarkdownExperimental", "PasteFromOffice", "PictureEditing",
        "PlainTableOutput", "RemoveFormat", "ShowBlocks", "SourceEditing", "SpecialCharacters",
        "SpecialCharactersArrows", "SpecialCharactersCurrency", "SpecialCharactersEssentials",
        "SpecialCharactersLatin", "SpecialCharactersMathematical", "SpecialCharactersText",
        "Strikethrough", "Subscript", "Superscript", "Table", "TableCaption",
        "TableCellProperties", "TableColumnResize", "TableLayout", "TableProperties",
        "TableToolbar", "TextTransformation", "TodoList", "Underline", "Typing"
    ],
    "balloonToolbar": ["aiCommands", "aiAssistant", "bold", "italic", "|", "link", "insertImage", "|", "bulletedList", "numberedList", "emoji"],
    "blockToolbar": ["aiCommands", "aiAssistant", "fontSize", "fontColor", "fontBackgroundColor", "|", "bold", "italic", "|", "link", "insertImage", "insertTable", "|", "bulletedList", "numberedList"],
    "ckbox": {
        "defaultUploadCategories": ["ae691d16-621b-4b2f-ada9-88367736e98b"],
        "view": {"openLastView": True},
    },
}
