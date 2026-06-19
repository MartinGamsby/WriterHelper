// App boot + shared state. Pull-based: after any mutation we re-fetch the
// article state and re-render (no push notifications from Python needed).
"use strict";

const App = {
    state: { fr: null, en: null },

    // ====================================================================================
    debounce(fn, ms) {
        let t = null;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), ms);
        };
    },

    // Update an input's value unless the user is typing in it right now.
    setValue(id, value) {
        const el = document.getElementById(id);
        if (el && document.activeElement !== el) { el.value = value; }
    },

    toast(message) {
        const el = document.getElementById('toast');
        el.textContent = message;
        el.classList.remove('hidden');
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => el.classList.add('hidden'), 4000);
    },

    // A small yes/no dialog reusing the publish modal-overlay. Resolves true on
    // confirm, false on cancel / overlay-click / Escape. `body` is trusted HTML
    // (callers pass static markup, never user input).
    confirm({ title, body, confirmLabel = 'OK', cancelLabel = 'Cancel', danger = false }) {
        return new Promise((resolve) => {
            const overlay = document.getElementById('modal-overlay');
            const modal = document.getElementById('modal');
            let settled = false;
            const finish = (val) => {
                if (settled) { return; }
                settled = true;
                overlay.removeEventListener('click', onOverlay);
                document.removeEventListener('keydown', onKey);
                modal.classList.remove('modal-narrow');
                overlay.classList.add('hidden');
                resolve(val);
            };
            const onOverlay = (e) => { if (e.target.id === 'modal-overlay') { finish(false); } };
            const onKey = (e) => { if (e.key === 'Escape') { finish(false); } };

            modal.classList.add('modal-narrow');
            modal.innerHTML = `
                <h3>${title}</h3>
                ${body}
                <div class="modal-buttons">
                    <button id="confirm-ok" class="${danger ? 'danger' : 'primary'}">${confirmLabel}</button>
                    <button id="confirm-cancel">${cancelLabel}</button>
                </div>`;
            overlay.classList.remove('hidden');
            document.getElementById('confirm-ok').addEventListener('click', () => finish(true));
            document.getElementById('confirm-cancel').addEventListener('click', () => finish(false));
            overlay.addEventListener('click', onOverlay);
            document.addEventListener('keydown', onKey);
        });
    },

    // ====================================================================================
    async refresh(hl) {
        const s = await API.get_state(hl);
        this.state[hl] = s;
        Editor.apply(hl, s);
        Meta.apply(hl, s);
    },

    async refreshAll() {
        await Promise.all([this.refresh('fr'), this.refresh('en')]);
    },

    async setField(hl, field, value) {
        await API.set_field(hl, field, value);
        await this.refresh(hl);
    },

    async setLink(hl, name, url) {
        await API.set_link(hl, name, url);
        await this.refresh(hl);
    },

    // ====================================================================================
    boot() {
        for (const hl of ['fr', 'en']) {
            Meta.build(hl);
            Editor.build(hl);
        }

        // FR/EN column visibility toggles
        for (const hl of ['fr', 'en']) {
            document.getElementById(`cb-${hl}`).addEventListener('change', (e) => {
                document.getElementById(`meta-${hl}`).classList.toggle('hidden', !e.target.checked);
                document.getElementById(`content-${hl}`).classList.toggle('hidden', !e.target.checked);
            });
        }

        // Clock (fr-CA, like the QML footer)
        const clock = document.getElementById('clock');
        setInterval(() => {
            clock.textContent = new Date().toLocaleString('fr-CA');
        }, 1000);

        // Never let a stray file-drop navigate the webview away from the app:
        // swallow drops everywhere except inside an image drop-zone (Meta wires those).
        for (const ev of ['dragover', 'drop']) {
            window.addEventListener(ev, (e) => {
                if (!e.target.closest('.img-drop')) { e.preventDefault(); }
            });
        }

        // Close the modal on overlay click (outside the dialog)
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') { Publish.close(); }
        });

        this.refreshAll();
    },
};

window.addEventListener('DOMContentLoaded', () => App.boot());
