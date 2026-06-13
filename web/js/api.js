// Thin promise wrapper over window.pywebview.api.
// Usage: await API.get_state('fr')
"use strict";

const pywebviewReady = new Promise((resolve) => {
    if (window.pywebview) { resolve(); }
    else { window.addEventListener('pywebviewready', resolve); }
});

const API = new Proxy({}, {
    get: (_, name) => (...args) =>
        pywebviewReady.then(() => window.pywebview.api[name](...args)),
});

// Route every external link through the OS browser (the webview window
// must never navigate away from the app).
document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="http"]');
    if (a) {
        e.preventDefault();
        API.open_url(a.href);
    }
});
