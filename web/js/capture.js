// Card sizing helpers + html2canvas page-by-page capture.
// Output contract: JPEG named by article slug (richTextArea_<slug>_<hl><N>.jpg,
// N from 1) — the filename is built server-side in publishing.capture_filename, so
// a capture is tied to the article it was grabbed for. JPEG so it also serves as the
// Instagram asset.
"use strict";

const Capture = {

    els(hl) {
        const frame = document.getElementById(`card-${hl}`);
        return {
            frame,
            scroll: frame.querySelector('.card-scroll'),
            content: document.getElementById(`card-content-${hl}`),
            page: document.getElementById(`page-${hl}`),
            font: document.getElementById(`font-${hl}`),
            height: document.getElementById(`h-${hl}`),
        };
    },

    pageCount(hl) {
        const { scroll, content } = this.els(hl);
        return Math.max(1, Math.ceil(content.offsetHeight / scroll.clientHeight));
    },

    fitsOnePage(hl) {
        const { scroll, content } = this.els(hl);
        return content.offsetHeight <= scroll.clientHeight + 1;
    },

    // Center vertically when single page; show page number only when paginated.
    layoutPages(hl) {
        const { scroll, content, page } = this.els(hl);
        content.style.marginTop = '0px';
        const fits = this.fitsOnePage(hl);
        scroll.classList.toggle('centered', fits);
        page.classList.toggle('hidden', fits);
        page.textContent = '1';
    },

    // ====================================================================================
    async grab(hl) {
        const { frame, scroll, content, page } = this.els(hl);
        const pages = this.pageCount(hl);
        const viewH = scroll.clientHeight;

        let firstName = '';
        for (let p = 1; p <= pages; p++) {
            content.style.marginTop = `${-(p - 1) * viewH}px`;
            page.textContent = p;
            page.classList.toggle('hidden', pages === 1);
            // White background: JPEG has no alpha, so a null bg would render black.
            const canvas = await html2canvas(frame, { backgroundColor: '#ffffff', scale: 1 });
            const name = await API.save_capture(hl, p, canvas.toDataURL('image/jpeg', 0.92));
            if (p === 1) { firstName = name; }
        }
        this.layoutPages(hl);
        // Show the actual filename so it's clear WHICH article was grabbed.
        App.toast(`Saved ${pages} image${pages > 1 ? 's' : ''} → ${firstName}`);
    },

    // ====================================================================================
    // Sizing helpers, ported from QML (Adjust / Square / Portrait / Landscape / 500x400).
    setHeight(hl, value) {
        const { height } = this.els(hl);
        height.value = Math.min(Math.max(value, +height.min), +height.max);
        Editor.restyleCard(hl);
    },

    setFont(hl, value) {
        const { font } = this.els(hl);
        font.value = Math.min(Math.max(value, +font.min), +font.max);
        Editor.restyleCard(hl);
    },

    adjustHeight(hl) {
        const { height } = this.els(hl);
        const step = 32;
        while (this.fitsOnePage(hl) && +height.value > +height.min) {
            this.setHeight(hl, +height.value - step);
        }
        while (!this.fitsOnePage(hl) && +height.value < +height.max) {
            this.setHeight(hl, +height.value + step);
        }
        this.setHeight(hl, +height.value + step);
    },

    adjustFontSize(hl) {
        const { font } = this.els(hl);
        while (this.fitsOnePage(hl) && +font.value < +font.max) {
            this.setFont(hl, +font.value + 1);
        }
        while (!this.fitsOnePage(hl) && +font.value > +font.min) {
            this.setFont(hl, +font.value - 1);
        }
        const len = document.getElementById(`content-edit-${hl}`).value.length;
        if (len < 1000) { this.setFont(hl, +font.value - 1); }
        if (len < 300) { this.setFont(hl, +font.value - 1); }
    },

    cardWidth(hl) {
        return this.els(hl).frame.clientWidth;
    },

    square(hl) {
        this.setHeight(hl, this.cardWidth(hl));
        this.adjustFontSize(hl);
    },

    portrait(hl) {
        this.setHeight(hl, this.cardWidth(hl) * 5 / 4);
        this.adjustFontSize(hl);
    },

    landscape(hl) {
        this.setHeight(hl, this.cardWidth(hl) * 9 / 16);
        this.adjustFontSize(hl);
        const { font } = this.els(hl);
        if (document.getElementById(`content-edit-${hl}`).value.length < 300) {
            this.setFont(hl, +font.value - 1);
        }
    },

    r500x400(hl) {
        this.setHeight(hl, this.cardWidth(hl) * 4 / 5);
        this.adjustFontSize(hl);
    },
};
