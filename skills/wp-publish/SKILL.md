---
name: wp-publish
description: Publish or update approved content on the client's WordPress site through the shared REST scripts — Gutenberg block conversion, short romanized slugs, SEO-plugin fields (Yoast or AIOSEO from client.json), featured image/og:image, cache purge and post-publish verification. Use for any WordPress publish, update, or fix step.
---

# WordPress Publish

Only for content already approved (Flowtone item or exact text). Authored copy is drafted in Flowtone first; this skill is the mechanical publish step. Endpoint details: `marketing-core:wordpress-woocommerce`.

## Setup
- `client.json` → `domain`, `wordpress.seo_plugin`. The project's CLAUDE.md names its post types (e.g. a portfolio CPT), host cache, and any site-specific meta fields — read it.
- Calls: `python3 .claude/scripts/wp_rest.py <METHOD> <path> [--body '<json>'] [--query 'k=v']` from the project root. The body goes in `--body`, **not stdin** — a piped body is ignored and the POST returns the unchanged post, which looks exactly like success.
- Check the post type exists first: `wp_rest.py GET wp/v2/types`. Use its `rest_base`.

## Content
- Convert the body to **Gutenberg block markup**, not bare HTML: `<!-- wp:paragraph -->`, `<!-- wp:heading {"level":3} -->` (omit level for H2), `<!-- wp:list -->` + `<!-- wp:list-item -->`, `<!-- wp:image -->`. H1 is the theme's post title; body starts at H2.
- In-body images use the Azure CDN URL with descriptive alt text (see the project's alt-text standard). Don't upload body images to the media library.
- **Slug:** short English/romanized. WordPress silently truncates slugs at 200 bytes of their percent-encoded form, and Thai is 3 bytes/char, so a Thai slug gets cut mid-word with no error. Mirror the final slug back to the Flowtone item's `seo_slug`.
- Never put an internal project code in a public title or slug.

## SEO plugin (`client.json` → `wordpress.seo_plugin`)
- **yoast:** `meta._yoast_wpseo_title`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_focuskw` (REST-writable on `post`; check `OPTIONS` for other types). og:image comes from `featured_media`. Yoast's stored og:image is **one save behind**: POST twice, then purge cache, then verify `yoast_head_json.og_image`.
- **aioseo:** write SEO fields through AIOSEO's own endpoint as documented in the project's CLAUDE.md/memory; verify by reading them back.
- Meta description 120–160 characters, includes the primary keyword.

## Featured image
`featured_media` must be an attachment ID: upload the one cover with `.claude/scripts/wp_media_upload.py <file> --alt "<alt>"`, set `featured_media`, then (Yoast) save again.

## After every write
1. Purge the host cache if the project uses one (Catice: `PUT siteground-optimizer/v1/purge-cache`).
2. Re-fetch the post (`?context=edit`) and the public URL: title has no SEO suffix, body text appears once, og:image is right, slug is what you set.
3. Report the post ID, URL, and what you verified. Deletes: `wp_delete_post.py <id>` trashes by default; `--force` is permanent — only when explicitly asked.
