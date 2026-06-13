// Publish-confirmation popup: shows exactly what would be posted, lets the
// user pick text-vs-image mode and edit the message, and only posts on an
// explicit "Publish" click. Nothing is sent when the popup opens.
"use strict";

const Publish = {
    info: null,   // result of prepare_post
    hl: null,
    drafts: {},   // per-mode edited text, so switching modes keeps edits

    // ====================================================================================
    async open(hl, platform) {
        this.hl = hl;
        this.info = await API.prepare_post(hl, platform);
        this.drafts = { text: this.info.text, image: this.info.title };
        this.render();
    },

    close() {
        document.getElementById('modal-overlay').classList.add('hidden');
    },

    // ====================================================================================
    render() {
        const i = this.info;
        const modal = document.getElementById('modal');
        const overlay = document.getElementById('modal-overlay');
        overlay.classList.remove('hidden');

        if (i.existing_url) {
            modal.innerHTML = `
            <h3>Publish to ${i.label} — ${this.hl.toUpperCase()}</h3>
            <p class="warn">Already posted:</p>
            <p><a href="${i.existing_url}">${i.existing_url}</a></p>
            <p>Clear the link if you really want to post again.</p>
            <div class="modal-buttons">
                <button id="pub-clear" class="danger">Clear link (allow re-post)</button>
                <button id="pub-cancel">Close</button>
            </div>`;
            document.getElementById('pub-cancel').addEventListener('click', () => this.close());
            document.getElementById('pub-clear').addEventListener('click', async () => {
                await API.clear_link(this.hl, i.platform);
                await App.refresh(this.hl);
                this.open(this.hl, i.platform);
            });
            return;
        }

        modal.innerHTML = `
        <h3>Publish to ${i.label} — ${this.hl.toUpperCase()}</h3>
        <div class="mode-row">
            <label class="check"><input type="radio" name="pub-mode" value="text"> Text post</label>
            <label class="check"><input type="radio" name="pub-mode" value="image"> Title + image</label>
            <span class="hint">${i.fits
                ? 'fits as text'
                : `too long for a text post (${i.text_length}/${i.max_length}) — image suggested`}</span>
        </div>
        <textarea id="pub-text" rows="8"></textarea>
        <div class="pub-meta">
            <span id="pub-count"></span>
            <span id="pub-img-note"></span>
        </div>
        <img id="pub-img" class="pub-img hidden" alt="Captured card preview">
        <p class="warn hidden" id="pub-warn"></p>
        <div class="modal-buttons">
            <button id="pub-go" class="primary">Publish</button>
            <button id="pub-cancel">Cancel</button>
        </div>`;

        const radios = modal.querySelectorAll('input[name="pub-mode"]');
        const textarea = document.getElementById('pub-text');

        for (const r of radios) {
            r.checked = (r.value === i.suggested_mode);
            r.addEventListener('change', () => {
                textarea.value = this.drafts[this.mode()];
                this.validate();
            });
        }
        textarea.value = this.drafts[this.mode()];
        textarea.addEventListener('input', () => {
            this.drafts[this.mode()] = textarea.value;
            this.validate();
        });

        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        document.getElementById('pub-go').addEventListener('click', () => this.send());
        this.validate();
    },

    mode() {
        return document.querySelector('input[name="pub-mode"]:checked').value;
    },

    // ====================================================================================
    validate() {
        const i = this.info;
        const mode = this.mode();
        const text = document.getElementById('pub-text').value;
        const count = document.getElementById('pub-count');
        const img = document.getElementById('pub-img');
        const note = document.getElementById('pub-img-note');
        const go = document.getElementById('pub-go');

        count.textContent = `${text.length} / ${i.max_length}`;
        const over = text.length > i.max_length;
        count.classList.toggle('over', over);

        img.classList.toggle('hidden', mode !== 'image');
        if (mode === 'image') {
            if (i.image_exists) {
                img.src = i.image_data_url;
                note.textContent = `attaching ${i.image_file} (alt text = full article text)`;
                go.disabled = over;
            } else {
                img.classList.add('hidden');
                note.textContent = `${i.image_file} not found — use Grab first!`;
                go.disabled = true;
            }
        } else {
            note.textContent = '';
            go.disabled = over || text.length === 0;
        }
    },

    // ====================================================================================
    async send() {
        const go = document.getElementById('pub-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = 'Publishing…';

        const result = await API.publish(this.hl, this.info.platform, this.mode(),
                                         document.getElementById('pub-text').value);
        if (result.ok) {
            await App.refresh(this.hl);
            const modal = document.getElementById('modal');
            modal.innerHTML = `
            <h3>Published to ${this.info.label} ✓</h3>
            <p><a href="${result.url}">${result.url}</a></p>
            <div class="modal-buttons"><button id="pub-cancel">Close</button></div>`;
            document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        } else {
            warn.textContent = result.error;
            warn.classList.remove('hidden');
            go.textContent = 'Publish';
            this.validate();
        }
    },
};
