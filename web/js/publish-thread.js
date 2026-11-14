// Publish popup — Thread mode: the editable `---`-separated split, its per-segment
// readout, and the exact segments sent (mirrors thread_split.py). Extends `Publish`.
"use strict";

Object.assign(Publish, {
    // Split the edited thread blob back into segments (mirrors thread_split.py).
    segments(text) {
        return text.split(/^\s*-{3,}\s*$/m).map(s => s.trim()).filter(Boolean);
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
});
