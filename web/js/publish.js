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
        this.stopPolling();   // publish-browser.js: stop watching a queued job
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

        // Already queued for Claude in Chrome and not reported back yet: show that job's
        // status (publish-browser.js) instead of a composer — the double-post guard.
        if (i.pending_job) { this.renderBrowserJob(i.pending_job, null); return; }

        // Instagram over the Graph API has its own two-step flow (publish-ig.js); over
        // the browser it's an ordinary image post in the composer below.
        if (i.platform === 'instagram' && i.transport === 'api') {
            this.renderInstagram(); return;
        }

        // A video-only platform can't be served — WriterHelper authors no video.
        if (i.media === 'video') { this.renderUnsupportedVideo(); return; }

        // Image-required platforms (Pinterest) offer only the Title + image mode.
        const imageOnly = i.media === 'image';

        modal.innerHTML = `
        <h3>Publish to ${i.label} — ${this.hl.toUpperCase()}</h3>
        <div class="pub-cols">
          <div class="pub-controls">
            <div class="mode-row">
                ${imageOnly ? '' : `<label class="check"><input type="radio" name="pub-mode" value="text"> Text post</label>`}
                ${(!imageOnly && i.supports_thread)
                    ? `<label class="check"><input type="radio" name="pub-mode" value="thread"> Thread</label>`
                    : ''}
                <label class="check"><input type="radio" name="pub-mode" value="image"> Title + image</label>
            </div>
            <span class="hint">${imageOnly
                ? `${i.label} requires an image — posts the title + image`
                : i.fits
                    ? 'fits as text'
                    : i.supports_thread
                        ? `too long for one post (${i.text_length}/${i.max_length}) — thread suggested`
                        : `too long for one post (${i.text_length}/${i.max_length}) — post as image`}</span>
            <textarea id="pub-text" rows="10"></textarea>
            <div id="pub-thread-controls" class="thread-controls hidden">
                <label class="check"><input type="checkbox" id="pub-number"> Number posts (1/n)</label>
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
            <div id="pub-image-controls" class="img-controls hidden">
                <div class="img-row">
                    <span class="hint">Image source:</span>
                    <label class="check"><input type="radio" name="pub-img-mode-src" value="grabbed"
                        ${i.image_exists ? 'checked' : 'disabled'}>
                        grabbed text card${i.image_exists ? '' : ' (Grab first)'}</label>
                    <label class="check"><input type="radio" name="pub-img-mode-src" value="article"
                        ${i.image_exists ? '' : (i.article_image_exists ? 'checked' : '')} ${i.article_image_exists ? '' : 'disabled'}>
                        article image${i.article_image_exists ? '' : ' (none)'}</label>
                </div>
            </div>
            <label class="check hidden" id="pub-embed-row" title="${i.embed_url}">
                <input type="checkbox" id="pub-embed"> Add link preview card
                <span class="hint" id="pub-embed-host"></span>
            </label>
            <div class="pub-meta"><span id="pub-count"></span></div>
            <p class="warn hidden" id="pub-warn"></p>
            ${this.browserNote()}
            <div class="modal-buttons">
                <button id="pub-go" class="primary">${this.goLabel()}</button>
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
        for (const r of modal.querySelectorAll(
                'input[name="pub-img-src"], input[name="pub-img-mode-src"]')) {
            r.addEventListener('change', () => this.validate());
        }

        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        document.getElementById('pub-go').addEventListener('click', () => this.send());
        this.validate();
    },

    // ====================================================================================
    // A platform that REQUIRES a video. WriterHelper authors text + branded
    // image cards, never video, so there's nothing valid to post — explain that instead of
    // showing a Publish button that can only fail.
    renderUnsupportedVideo() {
        const i = this.info;
        const modal = document.getElementById('modal');
        modal.innerHTML = `
        <h3>Publish to ${i.label} — ${this.hl.toUpperCase()}</h3>
        <p class="warn">${i.label} posts require a video.</p>
        <p>WriterHelper produces text and branded image cards, not video, so it can't
           publish to ${i.label} directly. Post there by hand, then paste the URL into the
           ${i.label} link field to keep the article's footer complete.</p>
        <div class="modal-buttons"><button id="pub-cancel">Close</button></div>`;
        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
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

    // Image-mode ("Title + image") source picker — same article-vs-grabbed choice as
    // a thread's first-post image, but the image is mandatory here.
    imageSource() {
        const el = document.querySelector('input[name="pub-img-mode-src"]:checked');
        return el ? el.value : 'none';
    },
    imageSourceData() {
        return this.imageSource() === 'article'
            ? this.info.article_image_data_url : this.info.image_data_url;
    },
    imageSourceExists() {
        return this.imageSource() === 'article' ? this.info.article_image_exists
            : this.imageSource() === 'grabbed' ? this.info.image_exists : false;
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
        document.getElementById('pub-image-controls').classList.toggle('hidden', mode !== 'image');
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
                go.disabled = over || !this.imageSourceExists();
            } else {
                go.disabled = over || text.length === 0;
            }
        }
        this.renderPreview(mode, text);
    },


    // ====================================================================================
    async send() {
        const go = document.getElementById('pub-go');
        const warn = document.getElementById('pub-warn');
        go.disabled = true;
        go.textContent = this.info.via === 'browser' ? 'Queueing…' : 'Publishing…';

        const mode = this.mode();
        const options = {};
        if (mode === 'thread') {
            options.number = this.threadNumber();
            options.image = this.threadImage() ? this.threadImageSource() : 'none';
        }
        if (mode === 'image') {
            options.image = this.imageSource();
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

        if (result.ok && result.queued) {
            this.renderBrowserJob(result.job, result.hook);   // Claude posts it, then reports
        } else if (result.ok) {
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
            go.textContent = this.goLabel();
            this.validate();
        }
    },
};
