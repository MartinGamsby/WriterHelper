// Dev harness: fake window.pywebview so the UI runs in a plain browser
// (no Python). Loaded ONLY by dev.html, never by index.html.
"use strict";

(function () {
    const sample = (hl) => ({
        hl,
        title: hl === 'fr' ? "Mon article de démo" : "My demo article",
        content: "A paragraph of demo content.\n\nAnother **bold** one.",
        date: "2026-06-11",
        tags: "Gamsblurb,Demo",
        excerpt_image: "",
        excerpt_image_local: "",
        posts_folder: "C:/demo/_posts",
        website_url: "https://example.com/",
        slug: "my-demo-article",
        green: true,
        black: true,
        title_color: "#ade6b9",
        length_short: "Short",
        links: [
            { name: "X/Twitter", url: "", publish: "x" },
            { name: "Bluesky", url: "", publish: "bluesky" },
            { name: "Source", url: "", publish: "" },
        ],
        content_md: "---\nlayout: post\ntitle: demo\n---\ndemo",
        content_md_separators: "<h3 align='center' style='color: #ade6b9'>My demo article</h3><p>A paragraph of demo content.</p>",
        content_md_separators_br: "<h3>My demo article:</h3><p>A paragraph of demo content.<br /></p>",
        content_short: "<h3><strong>My demo article</strong></h3><br />\n#demo",
        watermark: hl === 'en' ? "linktr.ee/Gamsby" : "linktr.ee/MGamsby",
    });

    window.pywebview = {
        api: {
            get_state: async (hl) => sample(hl),
            set_field: async () => true,
            set_link: async () => true,
            new_article: async () => true,
            new_both_articles: async () => true,
            open_article: async () => true,
            open_prev_article: async () => true,
            open_next_article: async () => true,
            translate: async () => true,
            clear_link: async () => true,
            open_url: async (url) => { console.log('open_url', url); return true; },
            save_capture: async (hl, page) => `richTextArea_${hl}${page}.png`,
            prepare_post: async (hl, platform) => ({
                platform,
                label: platform === 'x' ? 'X / Twitter' : 'Bluesky',
                max_length: platform === 'x' ? 280 : 300,
                existing_url: "",
                text: "My demo article:\nA paragraph of demo content.\nAnother bold one.",
                text_length: 63,
                fits: true,
                suggested_mode: "text",
                title: "My demo article",
                image_file: `richTextArea_${hl}1.png`,
                image_exists: false,
                image_data_url: "",
            }),
            publish: async () => ({ ok: true, url: "https://bsky.app/profile/demo/post/123", error: "" }),
        },
    };
})();
