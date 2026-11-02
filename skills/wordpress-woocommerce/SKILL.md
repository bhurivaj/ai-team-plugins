---
name: wordpress-woocommerce
description: >-
  Official-docs-verified reference for the WordPress core REST API (wp/v2) and the WooCommerce REST API (wc/v3)
  — every resource an agent can read, create, update, or delete on the project's WordPress site, including posts,
  pages, media, comments, users, categories/tags, custom taxonomies, templates, menus, widgets, themes/plugins,
  plus full WooCommerce management (products, variations, orders, refunds, coupons, customers, shipping, tax,
  webhooks, reports, settings). Use this whenever an agent needs to call a WordPress or WooCommerce endpoint —
  through an MCP connector or directly over HTTPS — especially for anything the MCP tool surface doesn't cover
  (WooCommerce writes, comments, users, revisions, menus, widgets). Site domain, MCP connector name/alias, and
  credential locations are project-specific — always read from the project's CLAUDE.md, never hardcoded here.
  Every API fact is sourced from developer.wordpress.org and developer.woocommerce.com, never guessed.
user-invocable: false
---

# WordPress + WooCommerce REST API Reference

Knowledge base for any agent that reads, creates, updates, or deletes data on a WordPress + WooCommerce site via REST. Built for one reason: **never guess an endpoint, parameter, or delete behavior.** Every fact in the six `references/*.md` files was pulled directly from the official WordPress.org REST API Handbook and the official WooCommerce REST API docs (developer.woocommerce.com) on **2026-08-28**, not from memory.

This skill is domain-agnostic by design — it documents the WordPress/WooCommerce REST API surface itself, not any one site. **Site-specific facts (which domain, which MCP connector/alias, where credentials live, which business rules apply to media/content) are never hardcoded here — always resolve them from the current project's `CLAUDE.md` first.** If a task involves the live site and `CLAUDE.md` doesn't answer a needed detail (e.g. the exact domain or connector alias), ask before guessing rather than reusing a value seen in an example elsewhere in this skill.

## Source policy — read this first

1. **Check `CLAUDE.md` first for anything site-specific**: the domain, which MCP connector (if any) is wired up and its site alias, where credentials/secrets are stored, and any business-specific content rules (e.g. a rule that certain media bypasses the WP media library). Treat any domain or alias appearing in this skill's own examples as illustrative only, never as this project's actual value.
2. **Check the reference files below before calling anything.** They already cite the exact official URL for every resource.
3. **If a reference file marks something `NOT VERIFIED`**, that means the official page itself didn't state it — do not fill the gap from memory. Either test against the live site with a safe read-only call first, or fetch the cited official URL yourself before writing/deleting.
4. **If you need a resource not covered here** (WordPress and WooCommerce both add things over time), fetch the live reference index first — `https://developer.wordpress.org/rest-api/reference/` for WP core, `https://developer.woocommerce.com/docs/apis/rest-api/v3/` for WooCommerce — read the actual page, then act. Don't infer a route by pattern-matching similar resources.
5. **Re-verify before trusting this skill blindly** if you know WordPress or WooCommerce has shipped a new major version since 2026-08-28 (see the version note near the bottom) — REST resources are generally stable across core versions, but newer features (e.g. WordPress 7.0's Abilities API / AI Client) may add routes not yet catalogued here.

## Default to firing the API, not just planning around it

When a task is to actually create/update/publish content on the live site, the end state is a real API call (through the MCP connector or direct REST) that lands on the site itself — not just a draft left inside an adjacent planning/campaign tool (e.g. a content calendar or social-scheduling MCP) that never syncs to WordPress. If a project uses both a planning tool and a live-site connector, check `CLAUDE.md` for how the two relate, and default to also (or instead) firing the real API call when the goal is publishing, not just planning.

## Two ways to call these APIs

**A. Through an MCP connector, when the project has one wired up (preferred when available).** Check `CLAUDE.md` for whether this project has a WordPress MCP connector configured (name, config file, site alias) — e.g. some projects wire up `claudeus-wp-mcp` (see its config and secrets paths as documented in that project's `CLAUDE.md`). Such a connector wraps a subset of the WordPress REST API as namespaced tools, typically covering posts/pages/blocks, media, taxonomy, settings, search, health, templates, theme, global styles, and patterns (namespaces vary by connector — discover the live tool list rather than assuming). Use any provided endpoint-discovery tool (e.g. `claudeus_wp_discover_endpoints`) to confirm what's live on the actual site before assuming a tool call will work. **The reference files below tell you exactly what request each namespaced tool is really making** — same base route, same parameters, same delete semantics — so you know what to expect even though you're calling through an MCP wrapper.

**B. Direct HTTPS calls (`curl`/`WebFetch`) when the MCP tool surface doesn't cover it, or no MCP connector exists.** MCP connectors typically do **not** expose: comments, users, post revisions, menus/navigation, widgets, plugin/theme listing beyond basic theme tools, or **any WooCommerce write operation** (creating/updating/deleting products, orders, refunds, coupons, customers, shipping zones, tax rates, webhooks, settings) — confirm the actual gaps for this project's connector rather than assuming this list is exhaustive. For all of that, call the REST API directly against the project's real domain (from `CLAUDE.md`):
- WordPress core: `https://<site-domain>/wp-json/wp/v2/<route>`
- WooCommerce: `https://<site-domain>/wp-json/wc/v3/<route>`

Auth for direct calls: WP Application Passwords (Basic Auth, `username:app-password`) for `wp/v2`; Consumer Key/Secret (Basic Auth over HTTPS) for `wc/v3`. Full detail — including the OAuth 1.0a fallback and the query-string workaround for servers that strip the `Authorization` header — is in [`references/woo-store-config-auth.md`](references/woo-store-config-auth.md), Part 2. Credentials themselves (actual keys/passwords) live in the project's secrets, never in this skill — check `CLAUDE.md` for where they're tracked (e.g. a `.secret/` path or a `docs/reference-ids.md`-style index, if this project has one).

## Reference files

Load only the file(s) relevant to the current task — don't read all six preemptively.

| File | Covers | Namespace |
|---|---|---|
| [references/wp-content.md](references/wp-content.md) | Posts, Pages, Post Revisions, Post Types, Post Statuses, Media, Comments, Custom Post Types | `wp/v2` |
| [references/wp-taxonomy-users.md](references/wp-taxonomy-users.md) | Categories, Tags, Custom Taxonomies, Users, Search, Settings, Application Passwords | `wp/v2` |
| [references/wp-site-editor.md](references/wp-site-editor.md) | Plugins, Themes, Templates, Template Parts, Global Styles, Navigation/Menus (block + classic), Widgets, Sidebars, Block Types/Patterns | `wp/v2` |
| [references/woo-catalog.md](references/woo-catalog.md) | Products, Variations, Attributes, Attribute Terms, Categories, Tags, Shipping Classes, Reviews | `wc/v3` |
| [references/woo-orders-customers.md](references/woo-orders-customers.md) | Orders, Order Notes, Refunds, Coupons, Customers | `wc/v3` |
| [references/woo-store-config-auth.md](references/woo-store-config-auth.md) | Reports, Tax Rates/Classes, Shipping Zones/Methods/Locations, Payment Gateways, Webhooks, Settings, System Status, Data — **plus authentication for both APIs and WordPress core version grounding** | `wc/v3` + auth |

Each resource section in every file follows the same shape: base route, official doc URL, method/route table, key parameters, delete behavior, and gotchas — so once you know the shape, skimming is fast.

## Quick reference — what supports what

| Area | Read | Create | Update | Delete | Delete semantics |
|---|---|---|---|---|---|
| Posts, Pages, Comments, Media | ✅ | ✅ | ✅ (via `POST`, not PUT/PATCH) | ✅ | Trash by default; `force=true` bypasses Trash permanently |
| Post Revisions | ✅ | — (auto-created) | — | ✅ | **Always permanent** — `force=true` is required, revisions have no Trash state |
| Post Types, Post Statuses | ✅ | — | — | — | Read-only (registered in PHP) |
| Categories, Tags, Custom Taxonomies | ✅ | ✅ | ✅ | ✅ | Terms don't support trashing — `force=true` required |
| Users | ✅ | ✅ | ✅ | ✅ | Deleting a user **requires `reassign`** (target user ID for their content) |
| Templates, Template Parts, Global Styles, Navigation | ✅ | ✅ (varies) | ✅ | varies | See `wp-site-editor.md` — several of these are FSE-theme-only and some lack documented DELETE routes; check before assuming |
| WooCommerce Products, Variations | ✅ | ✅ | ✅ | ✅ | Products alone support Trash (`force=false` default); everything else in the catalog requires `force=true` (no trash) |
| WooCommerce Attributes/Terms/Categories/Tags/Shipping Classes/Reviews | ✅ | ✅ | ✅ | ✅ | No trash — `force=true` required |
| WooCommerce Orders, Refunds, Coupons, Customers | ✅ | ✅ | ✅ | ✅ | See `woo-orders-customers.md` for status-transition and refund side-effect details |
| WooCommerce Tax/Shipping/Webhooks | ✅ | ✅ | ✅ | ✅ | No trash — `force=true` required; **deleting a tax class cascades and deletes its rates** |
| WooCommerce Reports, System Status, Data (countries/currencies) | ✅ | — | — | — | Read-only |
| WooCommerce Payment Gateways, Shipping Methods (types) | ✅ | — | ✅ (gateways only) | — | Provided by code/plugins, not created or deleted via API |
| WooCommerce Settings/Setting Options | ✅ | — | ✅ (`value` only) | — | Read-only metadata, writable `value` |
| WooCommerce System Status Tools | ✅ | — | ✅ (executes the tool) | — | **Destructive** — always require an explicit `confirm: true`, never call blindly (e.g. `clear_sessions`, `reset_roles`) |

## Critical rules

1. **Never fabricate a route, parameter, or field name.** This skill exists because that's exactly the failure mode it prevents — every one of the ~1,900 lines across the six reference files was pulled from a live official page, not recalled from training data.
2. **Check delete semantics before every DELETE.** "Trash by default, `force=true` for permanent" is the WordPress core pattern (posts/pages/comments/media) but **not** the WooCommerce pattern — WooCommerce resources other than Products have no trash at all, so `force=true` is required just to delete them, and it's still permanent. Get this backwards and you either fail silently (post lands in Trash when you meant to purge it) or permanently destroy something you meant to soft-delete.
3. **`title`/`content`/`excerpt`/similar fields are objects, not strings**, with `rendered` (always) and `raw` (only in `context=edit`, with edit permission). Write to `.raw`, read `.rendered` for display, per `wp-content.md`.
4. **Confirm before destructive or store-wide actions**: WooCommerce System Status Tools, tax class deletion (cascades to rates), webhook deletion, bulk user/customer deletion. These affect live store state — flag to a human before executing, don't just proceed because the API call is available.
5. **Check `CLAUDE.md` for media/content routing overrides before uploading.** Some sites intentionally bypass `/wp/v2/media` or an MCP media-upload tool for certain asset types (e.g. routing processed images through a CDN/blob store instead), documented as a project-specific rule, not a WordPress default. See the Gotchas note in `wp-content.md` → Media for the shape such a rule takes, but get the actual rule (if any) from this project's `CLAUDE.md`.
6. **When acting on a custom post type**, don't guess its REST route from its admin-visible name — call `GET /wp/v2/types` (or `GET /wp/v2/types/<slug>`) to confirm the real `rest_base`, which can differ from the type's slug (see `wp-content.md` → Custom Post Types).

## Authentication (summary — full detail in `woo-store-config-auth.md` Part 2)

- **WordPress core (`wp/v2`):** Application Passwords, a core feature since WP 5.6. Generate under wp-admin → Users → Profile → Application Passwords. Authenticate with HTTP Basic Auth: `username:application-password`. Available by default only over HTTPS.
- **WooCommerce (`wc/v3`):** Consumer Key + Consumer Secret, generated under WooCommerce → Settings → Advanced → REST API with a Read / Write / Read-Write permission level tied to a WordPress user. Basic Auth over HTTPS is the standard method for any site served over HTTPS (OAuth 1.0a is only required for plain-HTTP deployments — check `CLAUDE.md` / the live domain to confirm this project's site is HTTPS, which is the norm). A query-string fallback (`?consumer_key=...&consumer_secret=...`) exists for hosts that strip the `Authorization` header.
- Both auth methods inherit the underlying WordPress user's **role capabilities** — an Application Password or API key doesn't grant anything the user account couldn't already do via wp-admin.

## WordPress version note

As of the verification date (2026-08-28), **WordPress 7.0 "Armstrong" (released May 20, 2026)** and **7.1 (released August 19, 2026)** are both confirmed real, current releases per the official wordpress.org releases archive — the "version 7 onward" framing for this skill is grounded, not assumed. The `wp/v2` REST namespace has been stable and additive across major versions; no official versioning-guarantee document was found, so treat that stability as observed practice, not a documented contract. WordPress 7.0 introduced an **Abilities API** and an **AI Client in Core** — these may eventually expose their own REST routes; none were found in this pass, so re-check `developer.wordpress.org/rest-api/reference/` if a task involves either feature.

## Maintenance

If any reference file's facts seem stale (a route 404s, a field name doesn't match a live response), don't patch around it silently — re-fetch the cited official URL, update the specific section, and note the new verification date. Full re-verification is warranted after a new WordPress or WooCommerce major version ships.
