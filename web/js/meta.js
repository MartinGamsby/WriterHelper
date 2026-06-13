// Meta column: action buttons, excerpt image, link slots, tags.
"use strict";

const Meta = {

    build(hl) {
        const col = document.getElementById(`meta-${hl}`);
        col.innerHTML = `
        <div class="btn-grid">
            <button id="new-${hl}">New</button>
            <button id="translate-${hl}">Translate</button>
            <button id="open-${hl}">Open</button>
            <button id="v2-${hl}">Make V2</button>
            <button id="prev-${hl}">Open Prev</button>
            <button id="next-${hl}">Open Next</button>
            <button id="newboth-${hl}" class="wide">New both articles</button>
        </div>
        <div class="setting">
            <div class="setting-name">Image</div>
            <input id="img-${hl}" data-field="excerpt_image" placeholder="assets/images/...">
            <img id="img-preview-${hl}" class="img-preview hidden" alt="">
        </div>
        <div class="setting">
            <div class="setting-name">Links</div>
            <div class="links-grid" id="links-${hl}"></div>
        </div>
        <div class="setting">
            <div class="setting-name">Tags</div>
            <input id="tags-${hl}" data-field="tags">
        </div>
        <div class="setting">
            <div class="setting-name">Facets</div>
            <div class="facets-grid" id="facets-${hl}">
                ${['dev', 'physics', 'fiction', 'music', 'ideas'].map(f =>
                    `<label><input type="checkbox" data-facet="${f}"> ${f}</label>`).join('')}
            </div>
        </div>
        <div class="setting">
            <label class="draft-toggle"><input type="checkbox" id="draft-${hl}"> Draft</label>
        </div>`;

        this.wire(hl);
    },

    // ====================================================================================
    wire(hl) {
        const refreshBoth = async (fn) => { await fn(); await App.refreshAll(); };

        document.getElementById(`new-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.new_article(hl, false)));
        document.getElementById(`v2-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.new_article(hl, true)));
        document.getElementById(`newboth-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.new_both_articles(hl, false)));
        document.getElementById(`open-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.open_article(hl)));
        document.getElementById(`prev-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.open_prev_article(hl)));
        document.getElementById(`next-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.open_next_article(hl)));
        document.getElementById(`translate-${hl}`).addEventListener('click',
            () => refreshBoth(() => API.translate(hl)));

        for (const input of document.querySelectorAll(`#meta-${hl} [data-field]`)) {
            const save = App.debounce(() =>
                App.setField(hl, input.dataset.field, input.value), 600);
            input.addEventListener('input', save);
            input.addEventListener('change', () =>
                App.setField(hl, input.dataset.field, input.value));
        }

        // Facets and draft are shared across the FR/EN pair: persist, then refresh
        // BOTH columns so the twin reflects the change.
        for (const cb of document.querySelectorAll(`#facets-${hl} [data-facet]`)) {
            cb.addEventListener('change', () => {
                const facets = [...document.querySelectorAll(`#facets-${hl} [data-facet]:checked`)]
                    .map(c => c.dataset.facet);
                refreshBoth(() => API.set_field(hl, 'facets', facets));
            });
        }
        document.getElementById(`draft-${hl}`).addEventListener('change', (e) =>
            refreshBoth(() => API.set_field(hl, 'draft', e.target.checked)));
    },

    // ====================================================================================
    apply(hl, s) {
        App.setValue(`img-${hl}`, s.excerpt_image);
        App.setValue(`tags-${hl}`, s.tags);

        const facets = s.facets || [];
        for (const cb of document.querySelectorAll(`#facets-${hl} [data-facet]`)) {
            cb.checked = facets.includes(cb.dataset.facet);
        }
        const draft = document.getElementById(`draft-${hl}`);
        if (draft) { draft.checked = !!s.draft; }

        const preview = document.getElementById(`img-preview-${hl}`);
        preview.classList.toggle('hidden', !s.excerpt_image_local);
        if (s.excerpt_image_local) { preview.src = s.excerpt_image_local; }

        this.applyLinks(hl, s.links);
    },

    // ====================================================================================
    // One row per link slot. Slots with a platform adapter get a Publish button
    // that opens the confirmation popup; the rest are plain label + URL field.
    applyLinks(hl, links) {
        const grid = document.getElementById(`links-${hl}`);

        for (const slot of links) {
            const key = slot.name.replace(/[^a-zA-Z]/g, '');
            let row = grid.querySelector(`[data-slot="${key}"]`);
            if (!row) {
                row = document.createElement('div');
                row.className = 'link-row';
                row.dataset.slot = key;
                row.innerHTML = slot.publish
                    ? `<button class="publish-btn">${slot.name}</button><input>`
                    : `<span class="link-label">${slot.name}</span><input>`;
                const input = row.querySelector('input');
                const save = App.debounce(() =>
                    App.setLink(hl, slot.name, input.value), 600);
                input.addEventListener('input', save);
                input.addEventListener('change', () => App.setLink(hl, slot.name, input.value));
                if (slot.publish) {
                    row.querySelector('button').addEventListener('click',
                        () => Publish.open(hl, slot.publish));
                }
                grid.appendChild(row);
            }
            const input = row.querySelector('input');
            if (document.activeElement !== input) { input.value = slot.url; }
        }
    },
};
