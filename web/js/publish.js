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
        this.drafts = {
            text: this.info.text,
            image: this.info.title,
            thread: this.info.thread_text,
        };
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

        if (!i.facets_ok) {
            modal.innerHTML = `
            <h3>Publish to ${i.label} — ${this.hl.toUpperCase()}</h3>
            <p class="warn">This article has no facet.</p>
            <p>Pick at least one facet (it sets which “door” the post appears under on
               the site) before publishing.</p>
            <div class="modal-buttons"><button id="pub-cancel">Close</button></div>`;
            document.getElementById('pub-cancel').addEventListener('click', () => this.close());
            return;
        }

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
            <label class="check"><input type="radio" name="pub-mode" value="thread"> Thread</label>
            <label class="check"><input type="radio" name="pub-mode" value="image"> Title + image</label>
            <span class="hint">${i.fits
                ? 'fits as text'
                : `too long for one post (${i.text_length}/${i.max_length}) — thread suggested`}</span>
        </div>
        <textarea id="pub-text" rows="8"></textarea>
        <div id="pub-thread-controls" class="thread-controls hidden">
            <label class="check"><input type="checkbox" id="pub-number" checked> Number posts (1/n)</label>
            <label class="check"><input type="checkbox" id="pub-thread-img"
                ${i.image_exists ? '' : 'disabled'}> Attach card image to first post${
                i.image_exists ? '' : ' (Grab first)'}</label>
            <div class="hint">Edit the split: separate posts with a line containing only <code>${i.separator}</code>.</div>
            <div id="pub-segs" class="pub-segs"></div>
        </div>
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

        for (const id of ['pub-number', 'pub-thread-img']) {
            document.getElementById(id).addEventListener('change', () => this.validate());
        }

        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        document.getElementById('pub-go').addEventListener('click', () => this.send());
        this.validate();
    },

    mode() {
        return document.querySelector('input[name="pub-mode"]:checked').value;
    },

    // Split the edited thread blob back into segments (mirrors thread_split.py).
    segments(text) {
        return text.split(/^\s*-{3,}\s*$/m).map(s => s.trim()).filter(Boolean);
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
        const threadCtl = document.getElementById('pub-thread-controls');

        threadCtl.classList.toggle('hidden', mode !== 'thread');
        count.classList.toggle('hidden', mode === 'thread');
        img.classList.toggle('hidden', mode !== 'image');

        if (mode === 'thread') {
            note.textContent = '';
            this.validateThread(text, go);
            return;
        }

        count.textContent = `${text.length} / ${i.max_length}`;
        const over = text.length > i.max_length;
        count.classList.toggle('over', over);

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

    // Per-segment counts, accounting for the projected " (i/n)" counter when numbering
    // is on. Publish is blocked if any segment is over the limit or there are none.
    validateThread(text, go) {
        const i = this.info;
        const segs = this.segments(text);
        const n = segs.length;
        const number = document.getElementById('pub-number').checked;
        const segsEl = document.getElementById('pub-segs');
        let anyOver = false;

        const parts = segs.map((s, idx) => {
            const extra = (number && n > 1) ? ` (${idx + 1}/${n})`.length : 0;
            const len = s.length + extra;
            const over = len > i.max_length;
            anyOver = anyOver || over;
            return `<span class="seg${over ? ' over' : ''}">#${idx + 1} ${len}/${i.max_length}</span>`;
        });
        segsEl.innerHTML = n ? `<b>${n} post${n > 1 ? 's' : ''}:</b> ${parts.join(' · ')}`
                             : '<span class="over">no posts — add some text</span>';
        go.disabled = anyOver || n === 0;
    },

    // ====================================================================================
    async send() {
        const go = document.getElementById('pub-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = 'Publishing…';

        const mode = this.mode();
        const options = mode === 'thread' ? {
            number: document.getElementById('pub-number').checked,
            image: document.getElementById('pub-thread-img').checked,
        } : null;
        const result = await API.publish(this.hl, this.info.platform, mode,
                                         document.getElementById('pub-text').value, options);
        if (result.ok) {
            await App.refresh(this.hl);
            const modal = document.getElementById('modal');
            const extra = (result.urls && result.urls.length > 1)
                ? `<p>${result.urls.length} posts in the thread; link points to the first.</p>` : '';
            modal.innerHTML = `
            <h3>Published to ${this.info.label} ✓</h3>
            <p><a href="${result.url}">${result.url}</a></p>
            ${extra}
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
