// Content column: editors, counters, card surface, previews.
"use strict";

const Editor = {

    build(hl) {
        const col = document.getElementById(`content-${hl}`);
        col.innerHTML = `
        <div class="content-head">
            <span class="length-label" id="len-${hl}">Short</span>
            <h2>${hl} Article</h2>
            <span class="counter" id="count-${hl}"></span>
        </div>
        <div class="row">
            <input id="posts-${hl}" data-field="posts_folder" title="Posts folder" placeholder="Posts folder">
            <input id="site-${hl}" data-field="website_url" title="Website URL" placeholder="Website URL">
        </div>
        <input class="title-edit" id="title-${hl}" data-field="title" placeholder="Title">
        <div class="slug" id="slug-${hl}"></div>
        <div class="row">
            <label class="check"><input type="checkbox" id="dateov-${hl}"> Date override</label>
            <input id="date-${hl}" data-field="date" disabled>
        </div>
        <textarea class="content-edit" id="content-edit-${hl}" data-field="content"
                  placeholder="Write the content..."></textarea>
        <div class="row controls">
            <label>Font <input type="number" id="font-${hl}" value="14" min="4" max="64"></label>
            <label>Margin <input type="number" id="margin-${hl}" value="9" min="0" max="200" step="1"></label>
            <label class="check"><input type="checkbox" id="green-${hl}" checked> G</label>
            <label class="check"><input type="checkbox" id="black-${hl}" checked> B</label>
            <label>W <input type="number" id="w-${hl}" value="640" min="320" max="1280" step="32"></label>
            <label>H <input type="number" id="h-${hl}" value="906" min="32" max="12800" step="32"></label>
            <label class="check"><input type="checkbox" id="center-${hl}"> Center</label>
        </div>
        <div class="row buttons">
            <button id="grab-${hl}">Grab</button>
            <button id="adjust-${hl}">Adjust</button>
            <button id="square-${hl}">Square</button>
            <button id="portrait-${hl}">Portrait</button>
            <button id="landscape-${hl}">Landscape</button>
            <button id="r54-${hl}">500x400</button>
        </div>
        <div class="preview short-preview" id="short-${hl}"></div>
        <div class="card-frame" id="card-${hl}">
            <div class="card-inner">
                <div class="card-scroll">
                    <div class="card-content" id="card-content-${hl}"></div>
                </div>
                <div class="card-watermark" id="wm-${hl}"></div>
                <div class="card-page hidden" id="page-${hl}">1</div>
            </div>
        </div>
        <div class="preview br-preview" id="br-${hl}"></div>
        <pre class="preview md-preview" id="md-${hl}"></pre>`;

        this.wire(hl);
    },

    // ====================================================================================
    wire(hl) {
        // Debounced auto-save for every data-field input in this column
        for (const input of document.querySelectorAll(`#content-${hl} [data-field]`)) {
            const save = App.debounce(() => {
                App.setField(hl, input.dataset.field, input.value);
            }, 600);
            input.addEventListener('input', () => {
                if (input.dataset.field === 'content') { this.updateCounter(hl); }
                save();
            });
            input.addEventListener('change', () =>
                App.setField(hl, input.dataset.field, input.value));
        }

        document.getElementById(`dateov-${hl}`).addEventListener('change', (e) => {
            document.getElementById(`date-${hl}`).disabled = !e.target.checked;
        });

        for (const name of ['green', 'black']) {
            document.getElementById(`${name}-${hl}`).addEventListener('change', (e) =>
                App.setField(hl, name, e.target.checked));
        }

        // Card geometry is purely local — restyle without a backend round-trip
        for (const id of [`font-${hl}`, `margin-${hl}`, `w-${hl}`, `h-${hl}`, `center-${hl}`]) {
            document.getElementById(id).addEventListener('change', () => this.restyleCard(hl));
        }

        document.getElementById(`grab-${hl}`).addEventListener('click', () => Capture.grab(hl));
        document.getElementById(`adjust-${hl}`).addEventListener('click', () => Capture.adjustHeight(hl));
        document.getElementById(`square-${hl}`).addEventListener('click', () => Capture.square(hl));
        document.getElementById(`portrait-${hl}`).addEventListener('click', () => Capture.portrait(hl));
        document.getElementById(`landscape-${hl}`).addEventListener('click', () => Capture.landscape(hl));
        document.getElementById(`r54-${hl}`).addEventListener('click', () => Capture.r500x400(hl));
    },

    // ====================================================================================
    apply(hl, s) {
        App.setValue(`title-${hl}`, s.title);
        App.setValue(`content-edit-${hl}`, s.content);
        App.setValue(`date-${hl}`, s.date);
        App.setValue(`posts-${hl}`, s.posts_folder);
        App.setValue(`site-${hl}`, s.website_url);
        document.getElementById(`green-${hl}`).checked = s.green;
        document.getElementById(`black-${hl}`).checked = s.black;
        document.getElementById(`slug-${hl}`).textContent = s.slug;
        document.getElementById(`len-${hl}`).textContent = s.length_short;
        document.getElementById(`short-${hl}`).innerHTML = s.content_short;
        document.getElementById(`card-content-${hl}`).innerHTML = s.content_md_separators;
        document.getElementById(`wm-${hl}`).textContent = s.watermark;
        document.getElementById(`br-${hl}`).innerHTML = s.content_md_separators_br;
        document.getElementById(`md-${hl}`).textContent = s.content_md;
        this.updateCounter(hl);
        this.restyleCard(hl);
    },

    // ====================================================================================
    updateCounter(hl) {
        const text = document.getElementById(`content-edit-${hl}`).value;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        document.getElementById(`count-${hl}`).textContent =
            `${text.length} characters, ${words} words`;
    },

    // ====================================================================================
    // Replicates the QML richTextArea colors: green -> #24475b bg / white text,
    // black -> black bg / white text, neither -> white bg / #000033 text.
    restyleCard(hl) {
        const s = App.state[hl] || { green: true, black: true };
        const frame = document.getElementById(`card-${hl}`);
        const inner = frame.querySelector('.card-inner');
        const content = document.getElementById(`card-content-${hl}`);
        const wm = document.getElementById(`wm-${hl}`);
        const page = document.getElementById(`page-${hl}`);

        frame.style.width = document.getElementById(`w-${hl}`).value + 'px';
        frame.style.height = document.getElementById(`h-${hl}`).value + 'px';
        inner.style.inset = document.getElementById(`margin-${hl}`).value + 'px';
        content.style.fontSize = document.getElementById(`font-${hl}`).value + 'pt';
        content.style.textAlign =
            document.getElementById(`center-${hl}`).checked ? 'center' : 'left';
        wm.style.fontSize = (document.getElementById(`font-${hl}`).value * 0.8) + 'pt';

        const bg = s.green ? '#24475b' : (s.black ? 'black' : 'white');
        frame.style.background = bg;
        content.style.color = (s.green || s.black) ? 'white' : '#000033';
        wm.style.color = s.green ? '#7a9295' : 'silver';
        page.style.color = s.green ? '#ade6b9' : (s.black ? '#000033' : 'white');

        Capture.layoutPages(hl);
    },
};
