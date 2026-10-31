// Publish popup — the browser hook ([[browser-hook]]). A platform routed to Claude in
// Chrome isn't posted by WriterHelper: "Queue" writes a job, the /chrome-post skill
// posts it in the operator's signed-in Chrome and reports the URL back, and this panel
// polls the job until that URL is linked. Extends `Publish` (publish.js).
"use strict";

Object.assign(Publish, {
    pollTimer: null,

    // Composer extras for a browser-routed platform (empty for a native API one).
    goLabel() {
        return this.info.via === 'browser' ? 'Queue for Claude in Chrome' : 'Publish';
    },
    browserNote() {
        if (this.info.via !== 'browser') return '';
        return `<p class="hint chrome-note">🌐 <b>Claude in Chrome</b> posts this from your
            signed-in browser (<code>/chrome-post</code> in Claude Code). Nothing is sent
            until it runs; the link fills in when it reports back.</p>`;
    },

    stopPolling() {
        if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; }
    },

    // ====================================================================================
    // `hook` is publish()'s run_hook result ({ran, command, error}) right after queueing,
    // or null when reopening an already-pending job.
    renderBrowserJob(job, hook) {
        const i = this.info;
        const esc = (s) => this.escapeHtml(String(s || ''));
        const slash = `/chrome-post ${job.id}`;
        const n = job.posts.length;
        const what = `${n > 1 ? `A ${n}-post thread` : 'One post'}${job.image ? ' + image' : ''}`;

        let hookLine = '';
        if (hook && hook.ran) {
            hookLine = `<p class="ig-ok">✓ Started: <code>${esc(hook.command)}</code></p>`;
        } else if (hook && hook.error) {
            hookLine = `<p class="warn">Hook command failed: ${esc(hook.error)}</p>`;
        }
        const account = job.account
            ? `<p class="hint">Expected account: <b>${esc(job.account)}</b> — Claude stops if
               Chrome is signed in as someone else.</p>` : '';

        document.getElementById('modal').innerHTML = `
        <h3>Queued for Claude in Chrome — ${esc(i.label)} ${this.hl.toUpperCase()}</h3>
        <p>${what} waiting to be posted.</p>
        ${hookLine}
        <p class="hint">In Claude Code (Chrome extension connected), from the WriterHelper
           folder, run:</p>
        <div class="bj-cmd"><code id="bj-slash">${esc(slash)}</code>
            <button id="bj-copy">Copy</button></div>
        <p class="hint">…or just <code>/chrome-post</code> to post every queued job.</p>
        ${account}
        <div class="bj-status" id="bj-status"><span class="ig-busy">Waiting for Claude…</span></div>
        <div class="modal-buttons">
            ${i.hook_command ? '<button id="bj-hook">Run hook again</button>' : ''}
            <button id="bj-cancel" class="danger">Cancel job</button>
            <button id="pub-cancel">Close</button>
        </div>`;

        document.getElementById('bj-copy').addEventListener('click', () => this.copyText(slash));
        document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        document.getElementById('bj-cancel').addEventListener('click', async () => {
            this.stopPolling();
            await API.cancel_browser_job(job.id);
            this.open(this.hl, i.platform);        // back to the composer
        });
        const again = document.getElementById('bj-hook');
        if (again) {
            again.addEventListener('click', async () => {
                const r = await API.run_browser_hook(job.id);
                document.getElementById('bj-status').innerHTML = r.ran
                    ? `<span class="ig-ok">✓ Started: <code>${esc(r.command)}</code></span>`
                    : `<span class="warn">${esc(r.error || 'No hook command configured.')}</span>`;
            });
        }

        this.stopPolling();
        this.pollTimer = setInterval(() => this.pollJob(job.id), 3000);
    },

    async pollJob(jobId) {
        let job;
        try { job = await API.browser_job(this.hl, jobId); }
        catch (e) { return; }                       // transient; try again next tick
        const status = document.getElementById('bj-status');
        if (!job || !status) { this.stopPolling(); return; }
        if (job.status === 'pending') return;

        this.stopPolling();
        if (job.status === 'done' || job.status === 'applied') {
            await App.refresh(this.hl);
            const url = this.escapeHtml(job.url);
            document.getElementById('modal').innerHTML = `
            <h3>Posted to ${this.escapeHtml(job.label)} ✓</h3>
            <p><a href="${url}">${url}</a></p>
            <p class="hint">Claude in Chrome posted it; the link is saved into the article.</p>
            <div class="modal-buttons"><button id="pub-cancel">Close</button></div>`;
            document.getElementById('pub-cancel').addEventListener('click', () => this.close());
        } else if (job.status === 'failed') {
            status.innerHTML = `<span class="warn">✗ Claude couldn't post:
                ${this.escapeHtml(job.error || 'no reason given')}</span>`;
            const cancel = document.getElementById('bj-cancel');
            cancel.textContent = 'Edit & re-queue';
            cancel.classList.remove('danger');
        } else {                                    // cancelled elsewhere (CLI)
            this.open(this.hl, this.info.platform);
        }
    },

    async copyText(text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch (e) {                               // older WebView: select + copy
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
        }
        const btn = document.getElementById('bj-copy');
        if (btn) { btn.textContent = 'Copied ✓'; }
    },
});
