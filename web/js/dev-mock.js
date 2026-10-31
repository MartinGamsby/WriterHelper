// Dev harness: fake window.pywebview so the UI runs in a plain browser
// (no Python). Loaded ONLY by dev.html, never by index.html.
"use strict";

(function () {
    // Tiny mutable per-language store so facet/draft toggles persist across the
    // pull-based refresh (facets are pair-shared, so writes mirror to the twin).
    const ALL_FACETS = ['dev', 'physics', 'fiction', 'music', 'ideas'];
    const store = {
        fr: { facets: [], draft: false, tags: "Gamsblurb,Demo" },
        en: { facets: [], draft: false, tags: "Gamsblurb,Demo" },
    };

    // A stand-in vocabulary so the tag picker is exercisable in the browser harness.
    const SUGGEST = {
        fr: { matching: ['Développement Logiciel', 'Programmation', 'Code'],
              popular: ['Santé', 'Fiction', 'Motivation', 'Science', 'Apprentissage'] },
        en: { matching: ['Software Development', 'Programming', 'Code'],
              popular: ['Health', 'Fiction', 'Motivation', 'Science', 'Learning'] },
    };
    const PAIR = { Health: 'Santé', Santé: 'Health', Programming: 'Programmation',
        Programmation: 'Programming', Code: 'Code', Fiction: 'Fiction',
        Motivation: 'Motivation', Science: 'Science', Learning: 'Apprentissage',
        Apprentissage: 'Learning' };

    // Tracks whether the IG image has been "pushed" this session, so reopening the
    // popup demonstrates skipping step 1 (mirrors site_push.image_status on the backend).
    const igPushed = { fr: false, en: false };
    const igUrl = (hl) => "https://raw.githubusercontent.com/MartinGamsby/"
        + `martingamsby.com/main/public/assets/ig/my-demo-article.${hl}.jpg`;

    // A stand-in square "grabbed card" so the Instagram preview + step 1 are exercisable.
    const SAMPLE_IMG = "data:image/svg+xml," + encodeURIComponent(
        "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='600'>"
        + "<rect width='600' height='600' fill='#2e6b3e'/>"
        + "<text x='50%' y='50%' fill='#ade6b9' font-size='44' font-family='sans-serif' "
        + "text-anchor='middle'>Demo card</text></svg>");

    // Platform table (mirrors platforms.PLATFORMS). Everything but Bluesky goes through
    // the browser hook by default.
    const META = {
        x: { label: 'X / Twitter', slot: 'X/Twitter', max: 280, thread: true },
        bluesky: { label: 'Bluesky', slot: 'Bluesky', max: 300, thread: true },
        facebook: { label: 'Facebook', slot: 'Facebook', max: 63206 },
        instagram: { label: 'Instagram', slot: 'Instagram', max: 2200, media: 'image' },
        linkedin: { label: 'LinkedIn', slot: 'LinkedIn', max: 3000 },
        threads: { label: 'Threads', slot: 'Threads', max: 500, thread: true },
        pinterest: { label: 'Pinterest', slot: 'Pinterest', max: 500, media: 'image' },
        tiktok: { label: 'TikTok', slot: 'TikTok', max: 2200, media: 'image' },
        medium: { label: 'Medium', slot: 'Medium', max: 100000 },
    };
    // Link slots + fake browser jobs (a pending job "completes" after a few polls, as if
    // Claude in Chrome had posted it and run `browser_jobs.py done`).
    const links = { fr: {}, en: {} };
    const jobs = {};

    const sample = (hl) => ({
        hl,
        title: hl === 'fr' ? "Mon article de démo" : "My demo article",
        content: "A paragraph of demo content.\n\nAnother **bold** one.",
        date: "2026-06-11",
        tags: store[hl].tags,
        excerpt_image: "",
        excerpt_image_local: "",
        posts_folder: "C:/demo/_posts",
        website_url: "https://example.com/",
        slug: "my-demo-article",
        post_url: "https://example.com/2026-06-11-my-demo-article/",
        translation_key: "2026-06-11-my-demo-article",
        facets: store[hl].facets.slice(),
        all_facets: ALL_FACETS,
        draft: store[hl].draft,
        green: true,
        black: true,
        title_color: "#ade6b9",
        length_short: "Short",
        links: [
            ...(hl === 'fr' ? [{ name: "Medium", url: links[hl].Medium || "",
                                 publish: "medium", via: "browser" }] : []),
            ...['x', 'linkedin', 'facebook', 'instagram', 'bluesky', 'threads',
                'pinterest', 'tiktok']
                .filter(k => hl === 'en' || k !== 'linkedin')
                .map(k => ({ name: META[k].slot, url: links[hl][META[k].slot] || "",
                             publish: k, via: k === 'bluesky' ? "" : "browser" })),
            { name: "Source", url: "", publish: "" },
        ],
        content_md: "---\nlayout: post\ntitle: demo\n---\ndemo",
        content_md_separators: "<h3 align='center' style='color: #ade6b9'>My demo article</h3><p>A paragraph of demo content.</p>",
        content_md_separators_br: "<h3>My demo article:</h3><p>A paragraph of demo content.<br /></p>",
        content_short: "<h3><strong>My demo article</strong></h3><br />\n#demo",
        watermark: hl === 'en' ? "MartinGamsby.com/en" : "MartinGamsby.com/fr",
    });

    window.pywebview = {
        api: {
            get_state: async (hl) => sample(hl),
            set_field: async (hl, field, value) => {
                if (field === 'facets' || field === 'draft') {   // pair-shared
                    store.fr[field] = value;
                    store.en[field] = value;
                }
                return true;
            },
            set_link: async () => true,
            tag_suggestions: async (hl) => {
                const applied = new Set(store[hl].tags.split(',').map(t => t.trim()));
                const drop = (list) => list.filter(t => !applied.has(t));
                const matching = drop(SUGGEST[hl].matching);
                const mset = new Set(matching);
                return { matching, popular: drop(SUGGEST[hl].popular).filter(t => !mset.has(t)) };
            },
            toggle_tag: async (hl, label) => {
                // Toggle on both sides (pairing) using the demo PAIR map.
                const other = hl === 'fr' ? 'en' : 'fr';
                const otherLabel = PAIR[label] || label;
                const toggle = (h, lbl) => {
                    const tags = store[h].tags.split(',').map(t => t.trim()).filter(Boolean);
                    const i = tags.indexOf(lbl);
                    if (i >= 0) { tags.splice(i, 1); } else { tags.push(lbl); }
                    store[h].tags = tags.join(',');
                };
                toggle(hl, label);
                toggle(other, otherLabel);
                return store[hl].tags;
            },
            new_article: async () => true,
            new_both_articles: async () => true,
            open_article: async () => true,
            open_image: async () => true,
            open_prev_article: async () => true,
            open_next_article: async () => true,
            translate: async () => true,
            clear_link: async (hl, platform) => {
                delete links[hl][META[platform].slot];
                return true;
            },
            open_url: async (url) => { console.log('open_url', url); return true; },
            save_capture: async (hl, page) => `richTextArea_demo_${hl}${page}.jpg`,
            prepare_post: async (hl, platform) => {
                const meta = META[platform] || { label: platform, max: 280 };
                // ?ig=api in the URL exercises the Graph-API two-step Instagram panel.
                const igApi = /[?&]ig=api/.test(location.search);
                const isIg = platform === 'instagram' && igApi;
                const supportsThread = !!meta.thread;
                const mediaKind = meta.media || 'any';
                const transport = (platform === 'bluesky' || isIg) ? 'api' : 'browser';
                const pending = Object.values(jobs).find(j => j.hl === hl
                    && j.platform === platform && j.status === 'pending') || null;
                return {
                    platform,
                    label: meta.label,
                    max_length: meta.max,
                    existing_url: links[hl][meta.slot] || "",
                    transport,
                    via: transport === 'browser' ? 'browser' : '',
                    compose_url: '',
                    pending_job: pending,
                    hook_command: /[?&]hook=1/.test(location.search)
                        ? 'claude --chrome "/chrome-post {id}"' : '',
                    text: "My demo article:\nA paragraph of demo content.\nAnother bold one.",
                    text_length: 63,
                    fits: true,
                    suggested_mode: mediaKind === 'image' ? 'image' : 'text',
                    supports_thread: supportsThread,
                    media: mediaKind,
                    separator: "---",
                    thread_text: "My demo article:\nA paragraph of demo content.\n---\nAnother bold one.",
                    thread_count: 2,
                    author: `MartinGamsby.com/${hl}`,
                    title: "My demo article",
                    image_file: `richTextArea_demo_${hl}1.jpg`,
                    // Fake both a grabbed card and an article header image so every mode
                    // (image source picker, thread first-post image, IG push) is
                    // exercisable in the browser harness.
                    image_exists: true,
                    image_data_url: SAMPLE_IMG,
                    article_image_exists: true,
                    article_image_data_url: SAMPLE_IMG,
                    facets_ok: store[hl].facets.length > 0,
                    embed_url: platform === 'bluesky'
                        ? "https://www.youtube.com/watch?v=dQw4w9WgXcQ" : "",
                    ig_repo_found: true,
                    ig_image_dest: `my-demo-article.${hl}.jpg`,
                    ig_image_pushed: isIg && igPushed[hl],
                    ig_public_url: (isIg && igPushed[hl]) ? igUrl(hl) : "",
                    ig_repo_image_data_url: (isIg && igPushed[hl]) ? SAMPLE_IMG : "",
                };
            },
            publish: async (hl, platform, mode, message, options) => {
                const meta = META[platform];
                const igApi = /[?&]ig=api/.test(location.search);
                if (platform === 'bluesky' || (platform === 'instagram' && igApi)) {
                    const url = platform === 'instagram'
                        ? "https://www.instagram.com/p/DEMO123/"
                        : "https://bsky.app/profile/demo/post/123";
                    links[hl][meta.slot] = url;
                    return { ok: true, url, error: "" };
                }
                const id = `20261031-120000-${platform}-${hl}-demo`;
                const posts = mode === 'thread'
                    ? message.split(/^\s*-{3,}\s*$/m).map(s => s.trim()).filter(Boolean)
                    : [message];
                jobs[id] = { id, status: 'pending', platform, hl, label: meta.label,
                    mode, posts, image: (options && options.image && options.image !== 'none')
                        ? `C:/demo/richTextArea_demo_${hl}1.jpg` : '',
                    account: platform === 'x' ? (hl === 'en' ? 'Martin_Gamsby' : 'MartinGamsby') : '',
                    url: '', error: '', polls: 0 };
                console.log('queued browser job', jobs[id]);
                const hook = /[?&]hook=1/.test(location.search)
                    ? { ran: true, command: `claude --chrome "/chrome-post ${id}"`, error: '' }
                    : { ran: false, command: '', error: '' };
                return { ok: true, queued: true, url: '', job: jobs[id], hook, error: '' };
            },
            browser_job: async (hl, id) => {
                const j = jobs[id];
                if (j && j.status === 'pending' && ++j.polls >= 2) {
                    if (/[?&]fail=1/.test(location.search)) {
                        j.status = 'failed';
                        j.error = 'Chrome is signed in as a different account.';
                    } else {
                        j.status = 'applied';
                        j.url = `https://example.com/${j.platform}/post/DEMO`;
                        links[hl][META[j.platform].slot] = j.url;
                    }
                }
                return j || null;
            },
            cancel_browser_job: async (id) => {
                if (jobs[id] && jobs[id].status === 'pending') jobs[id].status = 'cancelled';
                return true;
            },
            run_browser_hook: async (id) => ({ ran: true,
                command: `claude --chrome "/chrome-post ${id}"`, error: '' }),
            publish_instagram_image: async (hl) => {
                igPushed[hl] = true;   // a later prepare_post now reports it as pushed
                return {
                    ok: true,
                    public_url: igUrl(hl),
                    log: [`Copied image -> public/assets/ig/my-demo-article.${hl}.jpg`,
                          `Committed: IG image: my-demo-article (${hl})`,
                          "Pushed to origin — image is now public"],
                    error: "",
                };
            },
        },
    };
})();
