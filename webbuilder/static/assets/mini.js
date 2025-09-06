// !function (e, t) {
//     "object" == typeof exports && typeof module < "u" ? t(exports) : "function" == typeof define && define.amd ? define(["exports"], t) : t((e = typeof globalThis < "u" ? globalThis : e || self).GrapesJsStudioSDK = {})
// }(this, (function (e) {
//     "use strict";
//
//     function t(e) {
//         return e && e.__esModule && Object.prototype.hasOwnProperty.call(e, "default") ? e.default : e
//     }
//
//     var n, r = {exports: {}}, o = {}, i = {exports: {}}, a = {};
//
// }));

!function (e, t) {
    "object" == typeof exports && typeof module < "u" ? t(exports) : "function" == typeof define && define.amd ? define(["exports"], t) : t((e = typeof globalThis < "u" ? globalThis : e || self).GrapesJsStudioSDK = {})
}(this, async(function (e) {
    "use strict";

    try {
        // Mengimpor file myModule.js
        const response = await fetch('');
        const scriptText = await response.text();

        // Mengeksekusi kode JavaScript yang diimpor
        eval(scriptText);

    } catch (err) {
        console.error('Error loading module:', err);
    }
}));
/**
 * pangil file nya disini
 * 1. react.production.min.js
 * 2. react-jsx-runtime.production.min.js
 * 3. scheduler.production.min.js
 * 4. react-dom.production.min.js
 * 5. use-sync-external-store-shim.production.min.js
 * 6. classnames.min.js
 */

