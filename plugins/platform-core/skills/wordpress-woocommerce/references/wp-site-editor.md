# WordPress REST API — Site Editor, Menus, Widgets, Plugins & Themes

Source: official WordPress.org REST API Handbook, https://developer.wordpress.org/rest-api/reference/. Every
route, parameter, and behavior below was fetched and read directly from the cited page on **2026-08-28**. Where
the official docs did not state a fact (permissions, delete semantics, undocumented sub-routes, etc.), this file
says so explicitly rather than guessing. All routes are relative to a site's REST root, e.g.
`https://<site-domain>/wp-json/wp/v2/...` (get `<site-domain>` from the project's `CLAUDE.md`).

**Full Site Editing (FSE) vs. classic themes — quick map:**

| Resource | Requires block-based (FSE) theme? |
|---|---|
| Templates, Template Parts, Global Styles, Navigation (`/wp/v2/navigation`) | Yes — these are core to the Site Editor and are the modern replacement for theme template files / `theme.json` / block-based nav. The official docs for these pages did not explicitly restate the FSE requirement (noted as a gap below), but their purpose (managing `wp_template`, `wp_template_part`, `wp_global_styles`, `wp_navigation` post types) is FSE-specific per WordPress core documentation elsewhere. |
| Nav Menus, Menu Items, Menu Locations (`/wp/v2/menus`, `/menu-items`, `/menu-locations`) | No — these manage the **classic**, taxonomy-based `nav_menu` system (Appearance → Menus) and work on both classic and block themes. Distinct from the `/wp/v2/navigation` post type. |
| Widgets, Widget Types, Sidebars | Classic widgets/sidebars system (Appearance → Widgets). Block themes generally replace sidebars with template parts, but the endpoints themselves are not documented as FSE-gated. |
| Plugins, Themes, Block Types, Block Renderer, Block Patterns, Block Pattern Categories, Pattern Directory Items, Block Directory Items | Theme-model agnostic. |

If the project's site runs a block/site editor theme (check `CLAUDE.md` or query the active theme), Templates, Template Parts, Global Styles, and Navigation are the routes most relevant to structural/appearance changes; a classic theme instead relies on the Nav Menus and Widgets/Sidebars routes above.

---

## Plugins
**Base route:** `/wp/v2/plugins`
**Official doc:** https://developer.wordpress.org/rest-api/reference/plugins/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/plugins` | Retrieve a collection of plugin records |
| POST | `/wp/v2/plugins` | Create (install/activate) a plugin |
| GET | `/wp/v2/plugins/<plugin>` | Retrieve a specific plugin |
| POST | `/wp/v2/plugins/<plugin>` | Update a plugin (e.g. change status) |
| DELETE | `/wp/v2/plugins/<plugin>` | Delete a plugin |

**Key list/retrieve parameters:** `context` (`view`, `embed`, `edit`; default `view`); `search` (limit results to a matching string); `status` (filter by activation status); `plugin` (required identifier on the single-item route).
**Key create/update body fields:** `slug` (required on create — WordPress.org plugin directory slug); `status` (`inactive` or `active`, default `inactive` on create).
**Delete behavior:** `DELETE /wp/v2/plugins/<plugin>` is supported. The official page does not document the specific consequences (e.g. whether it also removes files) beyond the route existing.
**Gotchas:** Docs do not state required capabilities/permissions explicitly (in practice this requires `activate_plugins`/`install_plugins`-class capabilities, but that is not spelled out on this page — NOT VERIFIED beyond the route list itself). Most schema fields are read-only.

---

## Themes
**Base route:** `/wp/v2/themes`
**Official doc:** https://developer.wordpress.org/rest-api/reference/themes/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/themes` | Retrieve a collection of theme records |
| GET | `/wp/v2/themes/<stylesheet>` | Retrieve a specific theme by its stylesheet identifier |

**Key list/retrieve parameters:** `status` (filter by `inactive`/`active`); `stylesheet` (uniquely identifies the theme, required on single-item route).
**Key create/update body fields:** None — no POST/PUT/DELETE methods are documented for this resource.
**Delete behavior:** Not applicable — no DELETE method is documented.
**Gotchas:** Read-only endpoint. Schema includes `is_block_theme` (boolean) — useful for an agent to confirm at runtime whether a site is running a block-based (FSE) theme before attempting Template/Template Part/Global Styles/Navigation operations. Also includes `stylesheet`, `template`, `theme_supports`, `requires_php`, `requires_wp`.

---

## Templates
**Base route:** `/wp/v2/templates`
**Official doc:** https://developer.wordpress.org/rest-api/reference/wp_templates/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/templates` | Retrieve a collection of `wp_template` records |
| POST | `/wp/v2/templates` | Create a new template |
| GET | `/wp/v2/templates/<id>` | Retrieve a single template |
| POST | `/wp/v2/templates/<id>` | Update an existing template |
| DELETE | `/wp/v2/templates/<id>` | Remove a template |

**Key list/retrieve parameters:** `context` (`view`/`embed`/`edit`, default `view`); `wp_id` (filter by underlying post ID); `area` (filter by template area); `post_type` (filter templates applicable to a post type).
**Key create/update body fields:** `slug` (required on create — unique slug identifying the template); `theme`; `type`; `content`; `title`; `description`; `status` (`publish`/`future`/`draft`/`pending`/`private`, default `publish`); `author`.
**Delete behavior:** `DELETE /wp/v2/templates/<id>`, with `id` required and `force` (boolean) to bypass trash and force deletion.
**Gotchas:** Read-only schema fields include `id`, `source`, `origin`, `wp_id`, `has_theme_file`, `modified`, `is_custom` — useful for distinguishing a theme-file-backed template from a user-customized one. The official page does **not** explicitly state this endpoint only works on block-based/FSE themes, nor does it document required capabilities — NOT VERIFIED beyond what's listed.

---

## Template Parts
**Base route:** `/wp/v2/template-parts`
**Official doc:** https://developer.wordpress.org/rest-api/reference/wp_template_parts/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/template-parts` | Retrieve a collection of `wp_template_part` records |
| POST | `/wp/v2/template-parts` | Create a new template part |
| GET | `/wp/v2/template-parts/<id>` | Retrieve a single template part |
| POST | `/wp/v2/template-parts/<id>` | Update an existing template part |
| DELETE | `/wp/v2/template-parts/<id>` | Remove a template part |

**Key list/retrieve parameters:** `context`; `wp_id`; `area` (filter by template part area, e.g. header/footer); `post_type`.
**Key create/update body fields:** `slug` (required on create); `theme`; `type`; `content`; `title`; `description`; `status` (same enum as Templates, default `publish`); `author`; `area` ("Where the template part is intended for use").
**Delete behavior:** `DELETE /wp/v2/template-parts/<id>` — `id` required, `force` (boolean) to bypass trash.
**Gotchas:** Same shape/fields as Templates. Official page does not state FSE-only requirement or capability requirements explicitly — NOT VERIFIED beyond route/field list.

---

## Global Styles
**Base route:** `/wp/v2/global-styles/<id>` (numeric post ID, not a slug)
**Official doc:** https://developer.wordpress.org/rest-api/reference/wp_global_styles/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/global-styles/<id>` | Retrieve a specific `global_styles` record |
| POST | `/wp/v2/global-styles/<id>` | Update a global styles configuration |

**Key list/retrieve parameters:** `id` (required — described in the docs as "The id of a template").
**Key create/update body fields:** `styles` (object); `settings` (object); `title` (object/string — title of the global styles variation).
**Delete behavior:** NOT VERIFIED — the official page does not document a DELETE method for this resource at all.
**Gotchas:** This is the only major site-editor resource with **no documented list route** — it is accessed strictly by numeric ID. The official page does **not** document how a client is supposed to discover that ID (e.g. via a theme endpoint `_links` relation or an `edit-site` context) — confirmed absent by a direct re-check of the page. It also does not document a `/wp/v2/global-styles/themes/<stylesheet>` or `.../variations` sub-route — if such routes exist in current WordPress core, they are **NOT VERIFIED from this official reference page** and should not be assumed available. Required capabilities are not documented.

---

## Navigation (block-based, `wp_navigation` post type)
**Base route:** `/wp/v2/navigation`
**Official doc:** https://developer.wordpress.org/rest-api/reference/wp_navigations/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/navigation` | Retrieve a collection of navigations |
| POST | `/wp/v2/navigation` | Create a new navigation record |
| GET | `/wp/v2/navigation/<id>` | Retrieve a specific navigation record |
| POST | `/wp/v2/navigation/<id>` | Update an existing navigation |
| DELETE | `/wp/v2/navigation/<id>` | Remove a navigation record |

**Key list/retrieve parameters:** `context`; `page` (default 1); `per_page` (default 10); `search`, `search_columns`; `after`, `before`, `modified_after`, `modified_before`; `include`, `exclude`, `offset`; `orderby` (default `date`), `order` (default `desc`); `slug`; `status` (default `publish`); plus, on the single-item route, `id` (required) and `password` (for password-protected content).
**Key create/update body fields:** `date`, `date_gmt`, `slug`, `status` (`publish`/`future`/`draft`/`pending`/`private`), `password`, `title`, `content`, `template`.
**Delete behavior:** `DELETE /wp/v2/navigation/<id>` — `id` required, `force` optional (bypasses trash when true).
**Gotchas:** This is the **block-editor/FSE "Navigation" post type**, distinct from the classic `nav_menus`/`menu-items` endpoints below. The official page does not explicitly document the relationship/migration between the two systems, nor required capabilities — NOT VERIFIED beyond the route and field list. A `content` field holding serialized navigation-link block markup is the mechanism for defining the actual menu structure (analogous to post content), per the schema shape returned.

---

## Block Types
**Base route:** `/wp/v2/block-types`
**Official doc:** https://developer.wordpress.org/rest-api/reference/block-types/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/block-types` | Retrieve a collection of registered block type records |
| GET | `/wp/v2/block-types/<namespace>` | Retrieve block types filtered by namespace |
| GET | `/wp/v2/block-types/<namespace>/<name>` | Retrieve a single block type by namespace and name |

**Key list/retrieve parameters:** `context` (`view`/`embed`/`edit`, default `view`); `namespace` (required on the namespace-filtered route); `name` (required on the single block-type route).
**Key create/update body fields:** None — entirely read-only, no POST/PATCH/DELETE.
**Delete behavior:** Not applicable.
**Gotchas:** Schema exposes `api_version`, `title`, `name`, `description`, `icon`, `attributes`, `provides_context`, `uses_context`, `selectors`, `supports`, `category`, `is_dynamic`, script/style handles, `variations`, `keywords`, `example`, and parent/ancestor relationships. Several fields are marked deprecated in favor of newer "handles"-based equivalents per the schema.

---

## Block Renderer
**Base route:** `/wp/v2/block-renderer/<name>`
**Official doc:** https://developer.wordpress.org/rest-api/reference/rendered-blocks/

| Method | Route | Description |
|---|---|---|
| POST | `/wp/v2/block-renderer/<name>` | Render a block server-side and return its HTML |

**Key list/retrieve parameters:** Not applicable — no GET/list route is documented; this is a POST-only render action keyed by `name` (the registered block name, passed in the URL).
**Key create/update body fields:** `context` (default `view`; also accepts `edit` — the rendered `rendered` field is only present in `edit` context per the schema); `attributes` (object — block-specific attribute values); `post_id` (integer — optional post context for rendering).
**Delete behavior:** Not applicable.
**Gotchas:** Response is an object whose `rendered` field contains the HTML output. Docs do not specify required capabilities, error codes, or rate limits — NOT VERIFIED beyond the route/argument list.

---

## Block Patterns
**Base route:** `/wp/v2/block-patterns/patterns`
**Official doc:** https://developer.wordpress.org/rest-api/reference/block-patterns/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/block-patterns/patterns` | Retrieve locally-registered block pattern records |

**Key list/retrieve parameters:** None — the official docs state explicitly "There are no arguments for this endpoint" (aside from the universal `_fields`/`_filter` mechanisms).
**Key create/update body fields:** Not applicable — read-only, no POST/PUT/DELETE.
**Delete behavior:** Not applicable.
**Gotchas:** Returns locally-registered patterns only (core/plugin/theme-registered), with `source` values `core`, `plugin`, `theme`, `pattern-directory/core`, `pattern-directory/theme`, `pattern-directory/featured`. For the *remote* WordPress.org pattern directory, use Pattern Directory Items below instead.

---

## Block Pattern Categories
**Base route:** `/wp/v2/block-patterns/categories`
**Official doc:** https://developer.wordpress.org/rest-api/reference/block-pattern-categories/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/block-patterns/categories` | Retrieve locally-registered block pattern category records |

**Key list/retrieve parameters:** None documented ("There are no arguments for this endpoint").
**Key create/update body fields:** Not applicable — read-only.
**Delete behavior:** Not applicable.
**Gotchas:** Schema is just `name`, `label`, `description`, all read-only.

---

## Pattern Directory Items
**Base route:** `/wp/v2/pattern-directory/patterns`
**Official doc:** https://developer.wordpress.org/rest-api/reference/pattern-directory-items/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/pattern-directory/patterns` | Retrieve a collection of patterns from the **remote** WordPress.org pattern directory |

**Key list/retrieve parameters:** `context` (default `view`); `page` (default 1); `per_page` (default 100); `search`; `category` (filter by category ID); `keyword` (filter by keyword ID); `slug`; `offset`; `order` (`asc`/`desc`, default `desc`); `orderby` (`author`, `date`, `id`, `include`, `modified`, `parent`, `relevance`, `slug`, `include_slugs`, `title`, `favorite_count`; default `date`).
**Key create/update body fields:** Not applicable — read-only.
**Delete behavior:** Not applicable.
**Gotchas:** Distinct from "Block Patterns" above — this proxies WordPress.org's remote directory rather than locally-registered patterns. Response fields: `id`, `title`, `content`, `categories`, `keywords`, `description`, `viewport_width`, `block_types`.

---

## Block Directory Items
**Base route:** `/wp/v2/block-directory/search`
**Official doc:** https://developer.wordpress.org/rest-api/reference/block-directory-items/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/block-directory/search` | Search the remote WordPress.org block-plugin directory |

**Key list/retrieve parameters:** `term` (**required** — search string); `page` (default 1); `per_page` (default 10); `context` (accepts `view` only, default `view`).
**Key create/update body fields:** Not applicable — read-only.
**Delete behavior:** Not applicable.
**Gotchas:** `term` is mandatory — omitting it is a client error. Returns installable block-plugins (not patterns): `name`, `title`, `description`, `id`, `rating`, `rating_count`, `active_installs`, `author_block_rating`, `author_block_count`, `author`, `icon`, `last_updated`, `humanized_updated`.

---

## Widgets
**Base route:** `/wp/v2/widgets`
**Official doc:** https://developer.wordpress.org/rest-api/reference/widgets/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/widgets` | Retrieve a collection of widget records |
| POST | `/wp/v2/widgets` | Create a new widget |
| GET | `/wp/v2/widgets/<id>` | Retrieve a specific widget |
| POST | `/wp/v2/widgets/<id>` | Update an existing widget |
| DELETE | `/wp/v2/widgets/<id>` | Remove or deactivate a widget |

**Key list/retrieve parameters:** `context` (default `view`); `sidebar` (return widgets belonging to a given sidebar).
**Key create/update body fields:** `id`; `id_base` (widget type — corresponds to the `id` in Widget Types); `sidebar` (defaults to `wp_inactive_widgets` on create if omitted); `instance` (widget configuration settings, where supported); `form_data` (URL-encoded form data from the widget admin form — write-only, used to update widgets that don't support `instance`).
**Delete behavior:** `DELETE /wp/v2/widgets/<id>` — docs note a `force` parameter distinguishes permanent removal from moving the widget to the inactive-widgets sidebar.
**Gotchas:** Official page does not document required capabilities, nor whether block-based ("Widgets" screen with block widgets) vs. classic text-widget instances behave differently at the API level — NOT VERIFIED beyond what's listed. `form_data` write-only field is a notable gotcha for widgets that use the classic form-based settings UI rather than structured `instance` data.

---

## Widget Types
**Base route:** `/wp/v2/widget-types`
**Official doc:** https://developer.wordpress.org/rest-api/reference/widget-types/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/widget-types` | Retrieve a collection of registered widget type records |
| GET | `/wp/v2/widget-types/<id>` | Retrieve a specific widget type |

**Key list/retrieve parameters:** `context` (default `view`); `id` (required on single-item route).
**Key create/update body fields:** Not applicable — read-only.
**Delete behavior:** Not applicable.
**Gotchas:** Schema: `id` (unique slug, read-only), `name` (read-only), `description`, `is_multi` (whether the widget supports multiple instances, read-only), `classname` (read-only). The official page as fetched did **not** document an `encode_rendered`/render sub-route for widget types — NOT VERIFIED.

---

## Sidebars
**Base route:** `/wp/v2/sidebars`
**Official doc:** https://developer.wordpress.org/rest-api/reference/sidebars/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/sidebars` | Retrieve a collection of sidebar records |
| GET | `/wp/v2/sidebars/<id>` | Retrieve a specific sidebar |
| POST | `/wp/v2/sidebars/<id>` | Update a sidebar's widget assignment |

**Key list/retrieve parameters:** `context` (default `view`).
**Key create/update body fields:** `widgets` (array — nested widgets to assign to the sidebar).
**Delete behavior:** NOT VERIFIED — no DELETE method is documented for this resource (sidebars are theme-registered, not user-created, which is consistent with there being no delete route).
**Gotchas:** Schema fields `id`, `name`, `description`, `class`, `before_widget`, `after_widget`, `before_title`, `after_title`, `status` (`active`/`inactive`), `widgets` are all documented as read-only, yet the `widgets` field is also the documented POST body field for reassigning widgets — treat the POST route as the one write path into an otherwise read-only-looking resource. Official page does not document capabilities/permissions.

---

## Nav Menus (classic, taxonomy-based)
**Base route:** `/wp/v2/menus`
**Official doc:** https://developer.wordpress.org/rest-api/reference/nav_menus/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/menus` | Retrieve a collection of `nav_menu` terms |
| POST | `/wp/v2/menus` | Create a new navigation menu |
| GET | `/wp/v2/menus/<id>` | Retrieve a specific `nav_menu` |
| POST | `/wp/v2/menus/<id>` | Update an existing menu |
| DELETE | `/wp/v2/menus/<id>` | Remove a menu |

**Key list/retrieve parameters:** `context`; `page`, `per_page`; `search`; `exclude`, `include`, `offset`; `order` (`asc`/`desc`), `orderby` (`id`, `name`, `slug`, `count`, etc.); `hide_empty`; `post`; `slug`.
**Key create/update body fields:** `name` (required — HTML title for the menu); `description`; `slug`; `locations` (array — menu location assignments); `auto_add` (boolean — whether to automatically add top-level pages to this menu); `meta`.
**Delete behavior:** `DELETE /wp/v2/menus/<id>` requires `force=true` — the docs state "terms do not support trashing," i.e. there is no soft-delete/trash state for menus.
**Gotchas:** This is a **taxonomy-term-backed** resource (the `nav_menu` taxonomy), not a post type — that's why delete requires `force=true` unconditionally. Explicitly distinct from the block-editor `/wp/v2/navigation` post type covered above. No capabilities documented.

---

## Menu Items (classic)
**Base route:** `/wp/v2/menu-items`
**Official doc:** https://developer.wordpress.org/rest-api/reference/nav_menu_items/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/menu-items` | Retrieve a collection of `nav_menu_item` records |
| POST | `/wp/v2/menu-items` | Create a new menu item |
| GET | `/wp/v2/menu-items/<id>` | Retrieve a specific menu item |
| POST | `/wp/v2/menu-items/<id>` | Update an existing menu item |
| DELETE | `/wp/v2/menu-items/<id>` | Remove a menu item |

**Key list/retrieve parameters:** `menus` (filter to items assigned to given `nav_menu` term(s)); `menus_exclude`; `menu_order`; `context`; `page`, `per_page`, `offset`; `search`, `search_columns`; `orderby` (default `menu_order`), `order`.
**Key create/update body fields:** `title`; `type` (`taxonomy`/`post_type`/`post_type_archive`/`custom`, default `custom`); `status` (`publish`/`future`/`draft`/`pending`/`private`, default `publish`); `url`; `attr_title`; `description`; `object`, `object_id` (the referenced taxonomy/post/etc.); `parent`; `target`; `classes` (array); `xfn` (array); `menu_order` (default `1`); `menus` (assigned `nav_menu` term); `meta`. Read-only: `id`, `type_label`, `invalid`.
**Delete behavior:** `DELETE /wp/v2/menu-items/<id>` — `id` required, `force` (boolean) to bypass trash and permanently delete.
**Gotchas:** `parent` is the DB ID of this item's parent menu item (for nesting/sub-menus), not a taxonomy parent. `invalid` (read-only) flags items whose referenced `object`/`object_id` (e.g. a deleted post or category) no longer exists — worth checking after bulk content deletions. `type_label` is read-only even though `type` itself is writable.

---

## Menu Locations
**Base route:** `/wp/v2/menu-locations`
**Official doc:** https://developer.wordpress.org/rest-api/reference/menu-locations/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/menu-locations` | Retrieve a collection of theme-registered menu location records |
| GET | `/wp/v2/menu-locations/<location>` | Retrieve a specific menu location |

**Key list/retrieve parameters:** `context` (default `view`); `location` (alphanumeric identifier, required on single-item route).
**Key create/update body fields:** Not applicable — every schema field (`name`, `description`, `menu`) is documented as read-only; there is no POST/PUT.
**Delete behavior:** Not applicable — no DELETE method.
**Gotchas:** Fully read-only. `menu` (integer) is the ID of the `nav_menu` currently assigned to that location — to *change* the assignment, update the `locations` array on the corresponding menu via the Nav Menus (`/wp/v2/menus/<id>`) endpoint above, not this one. Menu locations themselves are defined by the active theme's `register_nav_menu()` calls, not created via the API.

---

## Summary of gaps ("NOT VERIFIED")

The official REST API Handbook pages fetched above frequently omit: required user capabilities/permissions for write operations (nearly every resource), explicit DELETE support/behavior for Themes, Global Styles, Block Types, Block Renderer, Block Patterns, Block Pattern Categories, Pattern Directory Items, Block Directory Items, and Menu Locations (all read-only or lacking a documented delete route), and — notably — how a client is meant to discover the numeric Global Styles post ID, or whether a `/wp/v2/global-styles/themes/<stylesheet>` sub-route exists (a direct re-check of that page confirms it is **not** documented there). Treat any of those specifics as unconfirmed until verified against a live site's actual `OPTIONS` response or the WP core source, rather than assumed from this file.
