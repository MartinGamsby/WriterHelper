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
            <div class="img-input-row">
                <input id="img-${hl}" data-field="excerpt_image" placeholder="path · URL · or drop/Browse a file">
                <button type="button" id="img-browse-${hl}" class="img-browse">Browse…</button>
            </div>
            <div id="img-drop-${hl}" class="img-drop">
                <img id="img-preview-${hl}" class="img-preview hidden" alt="">
                <span class="img-drop-hint">Drop an image here — it gets self-hosted (webp)</span>
            </div>
        </div>
        <div class="setting">
            <div class="setting-name">Links</div>
            <div class="links-grid" id="links-${hl}"></div>
        </div>
        <div class="setting">
            <div class="setting-name">Tags</div>
            <input id="tags-${hl}" data-field="tags">
            <div class="tag-suggest" id="tag-suggest-${hl}"></div>
        </div>
        <div class="setting" id="facet-setting-${hl}">
            <div class="setting-name">Facets <span class="req" title="At least one is required">*</span></div>
            <div class="facets-grid" id="facets-${hl}"></div>
            <div class="facet-hint">Pick at least one facet — it sets which “door” the post appears under.</div>
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

        this.wireImage(hl);

        // Facets and draft are shared across the FR/EN pair: persist, then refresh
        // BOTH columns so the twin reflects the change. Delegated so it survives the
        // checkboxes being (re)rendered from the backend facet list in apply().
        document.getElementById(`facets-${hl}`).addEventListener('change', (e) => {
            if (!e.target.matches('[data-facet]')) { return; }
            const facets = [...document.querySelectorAll(`#facets-${hl} [data-facet]:checked`)]
                .map(c => c.dataset.facet);
            refreshBoth(() => API.set_field(hl, 'facets', facets));
        });
        document.getElementById(`draft-${hl}`).addEventListener('change', (e) =>
            refreshBoth(() => API.set_field(hl, 'draft', e.target.checked)));

        // Tag picker: clicking a suggestion chip toggles that tag on the article.
        // Pairing onto the twin happens in set_tags, so refresh BOTH columns. Delegated
        // so it survives the chips being re-rendered from tag_suggestions in apply().
        document.getElementById(`tag-suggest-${hl}`).addEventListener('click', (e) => {
            const chip = e.target.closest('.tag-chip');
            if (!chip) { return; }
            refreshBoth(() => API.toggle_tag(hl, chip.dataset.tag));
        });
    },

    // ====================================================================================
    // Drop-zone + Browse for the excerpt image. Both ends hand the image to the
    // backend as a data: URL, which routes through set_excerpt_img → the site's
    // localize hook → self-hosted webp (header + 160² thumb). No new backend mode:
    // Browse reads the file in Python (open_image); drop reads it here and reuses
    // the generic set_field('excerpt_image', …).
    wireImage(hl) {
        const browse = document.getElementById(`img-browse-${hl}`);
        browse.addEventListener('click', async () => {
            const ok = await API.open_image(hl);
            if (ok) { await App.refresh(hl); App.toast('Image self-hosted'); }
        });

        const zone = document.getElementById(`img-drop-${hl}`);
        const stop = (e) => { e.preventDefault(); e.stopPropagation(); };
        for (const ev of ['dragenter', 'dragover']) {
            zone.addEventListener(ev, (e) => { stop(e); zone.classList.add('drag-over'); });
        }
        for (const ev of ['dragleave', 'dragend']) {
            zone.addEventListener(ev, (e) => { stop(e); zone.classList.remove('drag-over'); });
        }
        zone.addEventListener('drop', (e) => {
            stop(e);
            zone.classList.remove('drag-over');
            const file = [...((e.dataTransfer && e.dataTransfer.files) || [])]
                .find(f => f.type.startsWith('image/'));
            if (!file) { return; }
            const reader = new FileReader();
            reader.onload = async () => {
                App.toast('Self-hosting image…');
                await App.setField(hl, 'excerpt_image', reader.result);
                App.toast('Image self-hosted');
            };
            reader.readAsDataURL(file);
        });
    },

    // ====================================================================================
    apply(hl, s) {
        App.setValue(`img-${hl}`, s.excerpt_image);
        App.setValue(`tags-${hl}`, s.tags);
        this.renderTagSuggestions(hl);

        this.renderFacets(hl, s.all_facets || [], s.facets || []);
        const draft = document.getElementById(`draft-${hl}`);
        if (draft) { draft.checked = !!s.draft; }

        const preview = document.getElementById(`img-preview-${hl}`);
        preview.classList.toggle('hidden', !s.excerpt_image_local);
        if (s.excerpt_image_local) { preview.src = s.excerpt_image_local; }

        this.applyLinks(hl, s.links);
    },

    // ====================================================================================
    // Tag picker chips. `matching` (tags that co-occur with this article's facets) is
    // shown first, then `popular` (overall frequency); the two are disjoint and exclude
    // tags already on the article (the backend handles both). Clicking a chip toggles
    // the tag — wired once, delegated, in wire(). Fire-and-forget: the backend index is
    // cached, and a failure (e.g. mid-boot) just leaves the chips empty.
    async renderTagSuggestions(hl) {
        const box = document.getElementById(`tag-suggest-${hl}`);
        if (!box) { return; }
        let sug;
        try { sug = await API.tag_suggestions(hl); }
        catch (e) { return; }
        const esc = (s) => String(s).replace(/[&<>"]/g,
            c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
        const row = (label, tags) => (tags && tags.length)
            ? `<div class="tag-row"><span class="tag-row-label">${label}</span>`
              + tags.map(t =>
                  `<button type="button" class="tag-chip" data-tag="${esc(t)}">${esc(t)}</button>`
              ).join('')
              + `</div>`
            : '';
        box.innerHTML = row('Matching', sug.matching) + row('Popular', sug.popular);
    },

    // ====================================================================================
    // Render the facet checkboxes from the backend's facet list (serializers.FACETS,
    // kept in lock-step with martingamsby.com's content.config.ts enum) so the choices
    // can never drift from the site. At least one facet is required: flag the section
    // when none is selected.
    renderFacets(hl, all, selected) {
        const grid = document.getElementById(`facets-${hl}`);
        const want = all.join(',');
        if (grid.dataset.built !== want) {          // (re)build only when the list changes
            grid.innerHTML = all.map(f =>
                `<label><input type="checkbox" data-facet="${f}"> ${f}</label>`).join('');
            grid.dataset.built = want;
        }
        for (const cb of grid.querySelectorAll('[data-facet]')) {
            cb.checked = selected.includes(cb.dataset.facet);
        }
        document.getElementById(`facet-setting-${hl}`)
            .classList.toggle('required-missing', selected.length === 0);
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
