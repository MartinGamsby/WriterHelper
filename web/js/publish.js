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
        <div class="pub-cols">
          <div class="pub-controls">
            <div class="mode-row">
                <label class="check"><input type="radio" name="pub-mode" value="text"> Text post</label>
                <label class="check"><input type="radio" name="pub-mode" value="thread"> Thread</label>
                <label class="check"><input type="radio" name="pub-mode" value="image"> Title + image</label>
            </div>
            <span class="hint">${i.fits
                ? 'fits as text'
                : `too long for one post (${i.text_length}/${i.max_length}) — thread suggested`}</span>
            <textarea id="pub-text" rows="10"></textarea>
            <div id="pub-thread-controls" class="thread-controls hidden">
                <label class="check"><input type="checkbox" id="pub-number" checked> Number posts (1/n)</label>
                <div class="img-row">
                    <label class="check"><input type="checkbox" id="pub-thread-img"
                        ${(i.article_image_exists || i.image_exists) ? 'checked' : 'disabled'}>
                        Attach image to first post:</label>
                    <label class="check"><input type="radio" name="pub-img-src" value="article"
                        ${i.article_image_exists ? 'checked' : 'disabled'}>
                        article image${i.article_image_exists ? '' : ' (none)'}</label>
                    <label class="check"><input type="radio" name="pub-img-src" value="grabbed"
                        ${i.article_image_exists ? '' : 'checked'} ${i.image_exists ? '' : 'disabled'}>
                        grabbed text card${i.image_exists ? '' : ' (Grab first)'}</label>
                </div>
                <div class="hint">Edit the split: separate posts with a line containing only <code>${i.separator}</code>.</div>
                <div id="pub-segs" class="pub-segs"></div>
            </div>
            <div class="pub-meta"><span id="pub-count"></span></div>
            <p class="warn hidden" id="pub-warn"></p>
            <div class="modal-buttons">
                <button id="pub-go" class="primary">Publish</button>
                <button id="pub-cancel">Cancel</button>
            </div>
          </div>
          <div class="pub-preview">
            <div class="pv-label">Preview — what you'll post</div>
            <div id="pub-preview-body"></div>
          </div>
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
        for (const r of modal.querySelectorAll('input[name="pub-img-src"]')) {
            r.addEventListener('change', () => this.validate());
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

    threadNumber() { return document.getElementById('pub-number').checked; },
    threadImage()  { return document.getElementById('pub-thread-img').checked; },
    threadImageSource() {
        const el = document.querySelector('input[name="pub-img-src"]:checked');
        return el ? el.value : 'none';
    },
    // The data: URL for the currently-selected image source (for the preview card).
    threadImageData() {
        return this.threadImageSource() === 'article'
            ? this.info.article_image_data_url : this.info.image_data_url;
    },

    // ====================================================================================
    validate() {
        const i = this.info;
        const mode = this.mode();
        const text = document.getElementById('pub-text').value;
        const count = document.getElementById('pub-count');
        const go = document.getElementById('pub-go');
        const threadCtl = document.getElementById('pub-thread-controls');

        threadCtl.classList.toggle('hidden', mode !== 'thread');
        count.classList.toggle('hidden', mode === 'thread');

        if (mode === 'thread') {
            this.validateThread(text, go);
        } else {
            count.textContent = `${text.length} / ${i.max_length}`;
            const over = text.length > i.max_length;
            count.classList.toggle('over', over);
            if (mode === 'image') {
                go.disabled = over || !i.image_exists;
            } else {
                go.disabled = over || text.length === 0;
            }
        }
        this.renderPreview(mode, text);
    },

    // Per-segment counts, accounting for the projected " (i/n)" counter when numbering
    // is on. Publish is blocked if any segment is over the limit or there are none.
    validateThread(text, go) {
        const i = this.info;
        const segs = this.numberedSegments(text);
        const n = segs.length;
        const segsEl = document.getElementById('pub-segs');
        let anyOver = false;

        const parts = segs.map((s, idx) => {
            const over = s.length > i.max_length;
            anyOver = anyOver || over;
            return `<span class="seg${over ? ' over' : ''}">#${idx + 1} ${s.length}/${i.max_length}</span>`;
        });
        segsEl.innerHTML = n ? `<b>${n} post${n > 1 ? 's' : ''}:</b> ${parts.join(' · ')}`
                             : '<span class="over">no posts — add some text</span>';
        go.disabled = anyOver || n === 0;
    },

    // The segments exactly as they'll be sent: split + the projected " (i/n)" counter
    // appended when numbering is on (mirrors thread_split.number_segments).
    numberedSegments(text) {
        const segs = this.segments(text);
        const n = segs.length;
        if (!this.threadNumber() || n <= 1) return segs;
        return segs.map((s, idx) => `${s} (${idx + 1}/${n})`);
    },

    // ====================================================================================
    escapeHtml(s) {
        return s.replace(/[&<>"]/g, c => (
            { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    },

    // One rendered "post" card. `over`/`missing` flag problems; `image` is a data URL.
    postCard({ body, image, count, over, missing }) {
        const i = this.info;
        const media = image
            ? `<img class="pv-media" src="${image}" alt="">`
            : (missing ? `<div class="pv-media-missing">no image to attach — set an article image or “Grab” the card</div>` : '');
        const text = body ? `<div class="pv-body">${this.escapeHtml(body)}</div>` : '';
        const badge = (count !== undefined)
            ? `<div class="pv-foot${over ? ' over' : ''}">${count}/${i.max_length}</div>` : '';
        return `<div class="pv-post${over ? ' over' : ''}">
            <div class="pv-head">
                <div class="pv-avatar">M</div>
                <div class="pv-who"><b>Martin Gamsby</b><span>${i.author} · now</span></div>
            </div>
            ${text}${media}${badge}
        </div>`;
    },

    renderPreview(mode, text) {
        const i = this.info;
        const host = document.getElementById('pub-preview-body');

        if (mode === 'image') {
            host.className = '';
            host.innerHTML = this.postCard({
                body: text, image: i.image_exists ? i.image_data_url : null,
                missing: !i.image_exists, count: text.length, over: text.length > i.max_length });
            return;
        }

        if (mode === 'thread') {
            const segs = this.numberedSegments(text);
            const imgData = this.threadImage() ? this.threadImageData() : '';
            host.className = 'pv-thread';
            host.innerHTML = segs.length
                ? segs.map((s, idx) => this.postCard({
                    body: s, count: s.length, over: s.length > i.max_length,
                    image: (idx === 0 && imgData) ? imgData : null,
                    missing: idx === 0 && this.threadImage() && !imgData })).join('')
                : '<div class="pv-empty">Add some text to preview the thread.</div>';
            return;
        }

        host.className = '';
        host.innerHTML = this.postCard({
            body: text, count: text.length, over: text.length > i.max_length });
    },

    // ====================================================================================
    async send() {
        const go = document.getElementById('pub-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = 'Publishing…';

        const mode = this.mode();
        const options = mode === 'thread' ? {
            number: this.threadNumber(),
            image: this.threadImage() ? this.threadImageSource() : 'none',
        } : null;

        // The bridge rejects this promise if Python raises (e.g. a platform 403).
        // Catch it so the popup recovers instead of hanging on "Publishing…".
        let result;
        try {
            result = await API.publish(this.hl, this.info.platform, mode,
                                       document.getElementById('pub-text').value, options);
        } catch (e) {
            result = { ok: false, error: 'Publish failed: ' + (e && e.message ? e.message : e) };
        }

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
