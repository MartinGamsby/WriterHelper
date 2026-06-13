// Card sizing helpers + html2canvas page-by-page capture.
// Output contract (unchanged from QML): richTextArea_<hl><N>.png, N starting at 1.
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

        for (let p = 1; p <= pages; p++) {
            content.style.marginTop = `${-(p - 1) * viewH}px`;
            page.textContent = p;
            page.classList.toggle('hidden', pages === 1);
            const canvas = await html2canvas(frame, { backgroundColor: null, scale: 1 });
            await API.save_capture(hl, p, canvas.toDataURL('image/png'));
        }
        this.layoutPages(hl);
        App.toast(`Saved ${pages} image${pages > 1 ? 's' : ''} (richTextArea_${hl}1.png…)`);
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
