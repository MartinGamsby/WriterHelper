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
            { name: "X/Twitter", url: "", publish: "x" },
            { name: "Facebook", url: "", publish: "facebook" },
            { name: "Instagram", url: "", publish: "instagram" },
            { name: "Bluesky", url: "", publish: "bluesky" },
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
            clear_link: async () => true,
            open_url: async (url) => { console.log('open_url', url); return true; },
            save_capture: async (hl, page) => `richTextArea_demo_${hl}${page}.jpg`,
            prepare_post: async (hl, platform) => {
                const meta = ({
                    x: { label: 'X / Twitter', max: 280 },
                    bluesky: { label: 'Bluesky', max: 300 },
                    facebook: { label: 'Facebook', max: 63206 },
                    instagram: { label: 'Instagram', max: 2200 },
                })[platform] || { label: platform, max: 280 };
                const isIg = platform === 'instagram';
                return {
                    platform,
                    label: meta.label,
                    max_length: meta.max,
                    existing_url: "",
                    text: "My demo article:\nA paragraph of demo content.\nAnother bold one.",
                    text_length: 63,
                    fits: true,
                    suggested_mode: "text",
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
            publish: async (hl, platform) => ({
                ok: true,
                url: platform === 'instagram'
                    ? "https://www.instagram.com/p/DEMO123/"
                    : "https://bsky.app/profile/demo/post/123",
                error: "",
            }),
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
