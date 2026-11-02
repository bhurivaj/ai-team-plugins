---
name: flowtone-ops
description: Safe use of the client's Flowtone MCP connector (name in client.json → flowtone_connector) — per-tool parameter shapes, silent no-op writes, campaign_id drift, upsert wiping unmapped fields, body_json structure, variants and WordPress publishing behaviour. Use before any Flowtone create/update/variant/schedule call.
---

# Flowtone Ops

Connector: `client.json` → `flowtone_connector` (e.g. `flowtone-catice`, `flowtone-classmat`). Use only that one — other clients' connectors point at the same server.

## Before the first write in a session
Load the real schema: `ToolSearch("select:mcp__<connector>__<tool>")`. Tools disagree on shape and a wrong shape **returns 200 and writes nothing**:

| Tool | Shape |
| --- | --- |
| `create_content`, `create_campaign` | everything inside `request` |
| `update_content` / `update_campaign` | `content_id` / `campaign_id` top level, rest inside `request` |
| `upsert_content_variant` | every field top level — no `request` |

After every write, confirm the response echoes your value and `updated_at` moved.

## Content
- Write structured `body_json` — real `heading`, `bulletList`/`orderedList` > `listItem`, `image` nodes. The plain-text body field flattens headings/lists into paragraphs and zeroes the SEO/E-E-A-T structure checks. (A Workflow step that explicitly asks for the plain-text field overrides this.)
- Older drafts may already be flattened (`##`/`- ` inside `paragraph` nodes) — check before trusting `seo_score`.
- `update_content` is a true partial update for top-level fields.
- **Pass `campaign_id` explicitly on every `update_content`** and check it survived; Flowtone sometimes reassigns it.
- `seo_score` is an article scorer — meaningless (0) for social/notice posts.
- Copy Thai text from its source; never retype long Thai strings or Unicode-normalize them (NFKC turns ำ into ํา).

## Variants
- One variant per platform per item; two posts on one platform need two items.
- `upsert_content_variant` is **full-replace per field** (omitting `auto_comments` clears it) and can **null fields its schema doesn't list** (seen: `custom_fields`, `wordpress_post_type`). Read the item first; if the variant carries unlisted fields, don't call it — use the Flowtone UI or direct REST.
- `wordpress_post_type` takes the post type's **label** (`"Portfolio"`), not its `rest_base`.
- Without a `wordpress` variant, "Publish to WordPress" publishes a plain blog `post` using `seo_title` and `seo_slug`. Set the variant first; never press Publish twice (duplicates).

## Other
- `list_content` may ignore filter args — filter client-side.
- No MCP tool uploads into the Flowtone media library; files reach it by syncing from SharePoint or via the UI, then `attach_content_media`.
- `build_utm_link` only reads a campaign's existing UTM config (set in the UI); with none, build links by hand per the project's UTM doc.
- A LINE post's queue status `published` means handed off, not delivered — check the social account's `last_error` before calling it failed.
