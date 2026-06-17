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
            image_caption: this.info.text,   // Instagram caption (image-only, full text)
            thread: this.info.thread_text,
        };
        this.igImageUrl = '';   // set once the IG step-1 image push makes it public
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

        // Instagram has its own image-only, two-step (push image → publish) flow.
        if (i.platform === 'instagram') { this.renderInstagram(); return; }

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
            <label class="check hidden" id="pub-embed-row" title="${i.embed_url}">
                <input type="checkbox" id="pub-embed"> Add link preview card
                <span class="hint" id="pub-embed-host"></span>
            </label>
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
        if (i.embed_url) {
            const embed = document.getElementById('pub-embed');
            embed.checked = true;   // opt-out: a card is the nicer post when a link exists
            document.getElementById('pub-embed-host').textContent =
                '→ ' + this.linkHost(i.embed_url);
            embed.addEventListener('change', () => this.validate());
        }
        for (const r of modal.querySelectorAll('input[name="pub-img-src"]')) {
            r.addEventListener('change', () => this.validate());
        }

        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        document.getElementById('pub-go').addEventListener('click', () => this.send());
        this.validate();
    },

    // ====================================================================================
    // Instagram is a special case: image-only, and the image must be PUBLIC before the
    // API call (IG fetches it server-side). So it's an explicit two-step flow — (1) push
    // the grabbed card to the site repo, (2) create the post — each with its own button
    // and feedback. It must also be the LAST platform you publish to (the post URL only
    // exists after publishing).
    renderInstagram() {
        const i = this.info;
        const modal = document.getElementById('modal');
        // A reopened popup whose image is already committed+pushed skips straight to
        // step 2 — no redundant re-push. The public URL comes back from prepare_post.
        const pushed = !!i.ig_image_pushed;
        this.igImageUrl = pushed ? (i.ig_public_url || '') : '';

        const canPush = i.image_exists && i.ig_repo_found;
        const repoWarn = i.ig_repo_found ? '' :
            `<p class="warn">Can't find the martingamsby.com checkout above the posts
             folder — the image push (step 1) won't work until that's fixed.</p>`;

        modal.innerHTML = `
        <h3>Publish to Instagram — ${this.hl.toUpperCase()}</h3>
        <p class="hint">Instagram is image-only and should be your <b>last</b> publish
           step. Use the <b>Square</b> sizing on the card before grabbing.</p>
        ${repoWarn}
        <div class="pub-cols">
          <div class="pub-controls">
            <label class="ig-field">Caption
              <textarea id="pub-text" rows="7"></textarea>
            </label>
            <div class="pub-meta"><span id="pub-count"></span></div>
            <ol class="ig-steps">
              <li class="ig-step">
                <div class="ig-step-head">
                  <b>1 · Push image to the site</b>
                  <button id="ig-push" ${canPush ? '' : 'disabled'}>${pushed ? 'Re-push image' : 'Push image'}</button>
                </div>
                <div class="ig-step-status" id="ig-push-status">${pushed
                    ? '<span class="ig-ok">✓ Already pushed — re-push only if you changed the card.</span>'
                    : (i.image_exists
                        ? 'Ready to push the grabbed card so Instagram can fetch it.'
                        : '<span class="warn">No grabbed card yet — Square + Grab it first.</span>')}</div>
              </li>
              <li class="ig-step">
                <div class="ig-step-head">
                  <b>2 · Publish to Instagram</b>
                  <button id="ig-go" class="primary" disabled>Publish</button>
                </div>
                <div class="ig-step-status" id="ig-go-status">${pushed ? 'Image is public — ready to publish.' : 'Push the image first.'}</div>
              </li>
            </ol>
            <p class="warn hidden" id="pub-warn"></p>
            <div class="modal-buttons"><button id="pub-cancel">Cancel</button></div>
          </div>
          <div class="pub-preview">
            <div class="pv-label">Preview — what you'll post</div>
            <div id="pub-preview-body"></div>
          </div>
        </div>`;

        const textarea = document.getElementById('pub-text');
        textarea.value = this.drafts.image_caption;
        textarea.addEventListener('input', () => {
            this.drafts.image_caption = textarea.value;
            this.igValidate();
        });
        const pushBtn = document.getElementById('ig-push');
        if (pushBtn) { pushBtn.addEventListener('click', () => this.pushIgImage()); }
        document.getElementById('ig-go').addEventListener('click', () => this.sendInstagram());
        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        this.igValidate();
    },

    // Caption length + step-2 gating (image pushed AND caption fits + non-empty).
    igValidate() {
        const i = this.info;
        const text = document.getElementById('pub-text').value;
        const count = document.getElementById('pub-count');
        count.textContent = `${text.length} / ${i.max_length}`;
        count.classList.toggle('over', text.length > i.max_length);
        document.getElementById('ig-go').disabled =
            !(this.igImageUrl && text.length > 0 && text.length <= i.max_length);
        this.renderIgPreview(text);
    },

    renderIgPreview(text) {
        const i = this.info;
        const host = document.getElementById('pub-preview-body');
        host.className = '';
        host.innerHTML = this.postCard({
            body: text, image: i.image_exists ? i.image_data_url : null,
            missing: !i.image_exists, count: text.length, over: text.length > i.max_length });
    },

    // Step 1: stage + git-push the grabbed JPEG; stream the per-step log into the card.
    async pushIgImage() {
        const btn = document.getElementById('ig-push');
        const status = document.getElementById('ig-push-status');
        btn.disabled = true;
        status.innerHTML = '<span class="ig-busy">Pushing image to the site repo…</span>';

        let result;
        try {
            result = await API.publish_instagram_image(this.hl);
        } catch (e) {
            result = { ok: false, log: [],
                       error: 'Image push failed: ' + (e && e.message ? e.message : e) };
        }

        const lines = (result.log || [])
            .map(l => `<div class="ig-log-line">✓ ${this.escapeHtml(l)}</div>`).join('');
        if (result.ok) {
            this.igImageUrl = result.public_url;
            status.innerHTML = lines +
                `<div class="ig-log-line ok">Public URL: ${this.escapeHtml(result.public_url)}</div>`;
            document.getElementById('ig-go-status').textContent =
                'Image is public — ready to publish.';
            btn.textContent = 'Re-push image';
        } else {
            status.innerHTML = lines +
                `<div class="ig-log-line err">✗ ${this.escapeHtml(result.error || 'Push failed.')}</div>`;
        }
        btn.disabled = false;
        this.igValidate();
    },

    // Step 2: create the IG post from the now-public image URL + caption.
    async sendInstagram() {
        const go = document.getElementById('ig-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = 'Publishing…';

        let result;
        try {
            result = await API.publish(this.hl, 'instagram', 'image',
                document.getElementById('pub-text').value, { image_url: this.igImageUrl });
        } catch (e) {
            result = { ok: false, error: 'Publish failed: ' + (e && e.message ? e.message : e) };
        }

        if (result.ok) {
            await App.refresh(this.hl);
            const modal = document.getElementById('modal');
            modal.innerHTML = `
            <h3>Published to Instagram ✓</h3>
            <p><a href="${result.url}">${result.url}</a></p>
            <p class="hint">The Instagram link is saved into the article — commit + push
               the post so the site carries it too.</p>
            <div class="modal-buttons"><button id="pub-cancel">Close</button></div>`;
            document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        } else {
            warn.textContent = result.error;
            warn.classList.remove('hidden');
            go.textContent = 'Publish';
            this.igValidate();
        }
    },

    mode() {
        return document.querySelector('input[name="pub-mode"]:checked').value;
    },

    // The host part of a URL, for a compact link-card label ("→ youtube.com").
    linkHost(url) {
        try { return new URL(url).hostname.replace(/^www\./, ''); }
        catch (e) { return url; }
    },

    // The link-card embed applies to single posts and the first thread post (not image
    // mode, where the image owns the embed slot). On only when a URL exists + checked.
    embedAvailable(mode) {
        return !!this.info.embed_url && (mode === 'text' || mode === 'thread');
    },
    embedEnabled(mode) {
        const el = document.getElementById('pub-embed');
        return this.embedAvailable(mode) && el && el.checked;
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

        const embedRow = document.getElementById('pub-embed-row');
        if (embedRow) embedRow.classList.toggle('hidden', !this.embedAvailable(mode));

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

    // A mock link-preview card for the right-hand preview ("" when no embed is on).
    embedCardHtml(mode) {
        if (!this.embedEnabled(mode)) return '';
        const url = this.info.embed_url;
        const video = /youtu\.?be/.test(url);
        return `<div class="pv-embed">${video ? '▶ ' : '🔗 '}
            <b>${this.escapeHtml(this.linkHost(url))}</b>
            <span>${this.escapeHtml(url)}</span></div>`;
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
            // The link card (if any) rides the first post, and only without an image.
            host.innerHTML = segs.length
                ? segs.map((s, idx) => this.postCard({
                    body: s, count: s.length, over: s.length > i.max_length,
                    image: (idx === 0 && imgData) ? imgData : null,
                    missing: idx === 0 && this.threadImage() && !imgData })
                    + (idx === 0 && !imgData ? this.embedCardHtml(mode) : '')).join('')
                : '<div class="pv-empty">Add some text to preview the thread.</div>';
            return;
        }

        host.className = '';
        host.innerHTML = this.postCard({
            body: text, count: text.length, over: text.length > i.max_length })
            + this.embedCardHtml(mode);
    },

    // ====================================================================================
    async send() {
        const go = document.getElementById('pub-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = 'Publishing…';

        const mode = this.mode();
        const options = {};
        if (mode === 'thread') {
            options.number = this.threadNumber();
            options.image = this.threadImage() ? this.threadImageSource() : 'none';
        }
        if (this.embedAvailable(mode)) options.embed = this.embedEnabled(mode);
        const opts = Object.keys(options).length ? options : null;

        // The bridge rejects this promise if Python raises (e.g. a platform 403).
        // Catch it so the popup recovers instead of hanging on "Publishing…".
        let result;
        try {
            result = await API.publish(this.hl, this.info.platform, mode,
                                       document.getElementById('pub-text').value, opts);
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
