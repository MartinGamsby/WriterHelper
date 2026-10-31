// Publish popup — Instagram over the Graph API (transport "api"): image-only, and the
// image must be PUBLIC before the call, so it's an explicit two-step flow (push the
// card to the site repo, then publish). The default Instagram route is the browser
// hook, which uses the generic composer instead. Extends `Publish` (publish.js).
"use strict";

Object.assign(Publish, {
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

        // The image actually committed in the repo (what IG will fetch), shown so the
        // operator can confirm it's the one they want — or spot that it's stale.
        const repoImg = i.ig_repo_image_data_url;
        const sameAsCard = repoImg && repoImg === i.image_data_url;
        let repoCap, repoCls;
        if (!repoImg) { repoCap = repoCls = ''; }
        else if (pushed) { repoCls = 'ig-ok'; repoCap = '✓ In the repo now — exactly what Instagram will fetch.'; }
        else if (sameAsCard) { repoCls = 'warn'; repoCap = '⚠ Matches your card, but this commit isn’t pushed yet — push to make it public.'; }
        else { repoCls = 'warn'; repoCap = '⚠ Older image in the repo for this post — it differs from your current card; push to replace it.'; }
        const repoImgBlock = repoImg
            ? `<div class="ig-repo-img"><img src="${repoImg}" alt="image currently in the site repo">
                 <div class="ig-repo-cap ${repoCls}">${repoCap}</div></div>`
            : '';

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
                ${repoImgBlock}
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

});
