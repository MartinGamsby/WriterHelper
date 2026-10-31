// Publish popup — the right-hand "what you'll post" preview dock: approximate post
// cards (not platform-accurate). Extends `Publish` (publish.js).
"use strict";

Object.assign(Publish, {
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
            const exists = this.imageSourceExists();
            host.innerHTML = this.postCard({
                body: text, image: exists ? this.imageSourceData() : null,
                missing: !exists, count: text.length, over: text.length > i.max_length });
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

});
