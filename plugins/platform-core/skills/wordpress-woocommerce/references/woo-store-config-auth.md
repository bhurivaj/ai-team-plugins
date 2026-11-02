# WooCommerce Store Config & Reports + Authentication (WP core + WooCommerce)

Sources used (fetched and read directly, 2026-08-28):
- `https://developer.woocommerce.com/docs/apis/rest-api/` (official WooCommerce REST API home)
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/` (v3 index)
- `https://developer.woocommerce.com/docs/apis/rest-api/authentication/` (WooCommerce REST API authentication)
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/reports/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/taxes/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/tax-classes/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zones/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zone-locations/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zone-methods/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-methods/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/payment-gateways/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/webhooks/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/settings/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/setting-options/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/system-status/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/system-status-tools/`
- `https://developer.woocommerce.com/docs/apis/rest-api/v3/data/`
- `https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/`
- `https://developer.wordpress.org/rest-api/key-concepts/`
- `https://developer.wordpress.org/rest-api/`
- `https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/`
- `https://developer.wordpress.org/apis/security/user-roles-and-capabilities/` (referenced via search; general capability model)
- `https://wordpress.org/download/releases/`
- `https://wordpress.org/documentation/wordpress-version/version-7-0/`
- `https://wordpress.org/news/2026/05/wordpress-7-0-armstrong/`

The old `woocommerce.github.io/woocommerce-rest-api-docs/` GitHub Pages mirror was **not used** as a source — the current official home confirmed live is `developer.woocommerce.com/docs/apis/rest-api/` (v3 docs live under `.../rest-api/v3/`). A WooCommerce Developer Blog post title turned up in search — "WooCommerce REST API docs have a new home" (`developer.woocommerce.com/2026/05/08/new-woo-rest-api-docs/`) — confirming `developer.woocommerce.com` is the current, actively-maintained home as of 2026.

All base routes below are relative to a site's REST root, e.g. `https://example.com/wp-json/wc/v3/...` for WooCommerce, `https://example.com/wp-json/wp/v2/...` for WP core.

---

## Part 1 — WooCommerce Store Config & Reports (`wc/v3`)

### 1. Reports

- **Base route:** `GET /wp-json/wc/v3/reports`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/reports/`

| Method | Route | Description |
|---|---|---|
| GET | `/reports` | List all available report types (sales, top sellers, and totals reports for coupons, customers, orders, products, reviews, categories, tags, attributes) |
| GET | `/reports/sales` | Sales report: gross/net sales, order counts, items, taxes, shipping, refunds, discounts |
| GET | `/reports/top_sellers` | Top sellers report: products ranked by quantity sold in a period |
| GET | `/reports/coupons/totals` | Coupon counts grouped by discount type (percentage, fixed cart, fixed product) |
| GET | `/reports/customers/totals` | Customer counts split into paying vs. non-paying |
| GET | `/reports/orders/totals` | Order counts grouped by status (pending, processing, on-hold, completed, cancelled, refunded, failed) |
| GET | `/reports/products/totals` | Product counts grouped by type (simple, grouped, external/affiliate, variable) |
| GET | `/reports/reviews/totals` | Review counts grouped by star rating (1–5) |

**Key params (sales, top_sellers):**
- `period` — `week`, `month`, `last_month`, `year` (default: `today` for sales, `week` for top_sellers)
- `date_min` / `date_max` — `YYYY-MM-DD`
- `context` — `view` only

**Delete behavior:** N/A — all reports endpoints are read-only (GET only).

**Gotchas:**
- Per-period refunds in `totals` and the top-level `total_refunds` in the sales report "come from different queries" and may diverge when refunds straddle period boundaries.
- Totals reports (coupons/customers/orders/products/reviews) return a flat list of `{slug, name, total}` objects, not time-series data.

---

### 2. Tax Rates

- **Base route:** `/wp-json/wc/v3/taxes`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/taxes/`

| Method | Route | Description |
|---|---|---|
| POST | `/taxes` | Create a new tax rate |
| GET | `/taxes` | List all tax rates (filterable/paginated) |
| GET | `/taxes/<id>` | Retrieve a specific tax rate |
| PUT | `/taxes/<id>` | Update a tax rate |
| DELETE | `/taxes/<id>` | Delete a tax rate |
| POST | `/taxes/batch` | Batch create/update/delete (default limit ~100 objects) |

**Key params:** `context` (`view`/`edit`), `page`, `per_page`, `offset`, `order`, `orderby` (`id`, `order`, `priority`), `class` (filter by tax class). Key rate fields: `country` (ISO 3166), `state`, `postcodes`/`cities` (arrays), `rate`, `name`, `priority` ("only 1 matching rate per priority will be used"), `compound`, `shipping`, `class` (default `standard`).

**Delete behavior:** No trash — `force=true` is required to delete.

**Gotchas:** Singular `postcode`/`city` fields are deprecated in favor of the `postcodes`/`cities` arrays (WooCommerce 5.3+).

---

### 3. Tax Classes

- **Base route:** `/wp-json/wc/v3/taxes/classes`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/tax-classes/`

| Method | Route | Description |
|---|---|---|
| POST | `/taxes/classes` | Create a new tax class |
| GET | `/taxes/classes` | List all tax classes |
| DELETE | `/taxes/classes/<slug>` | Delete a tax class |

**Key params:** `slug` (read-only identifier), `name` (required).

**Delete behavior:** No trash — `force=true` required.

**Gotchas:** Deleting a tax class **cascades**: "this also will delete all tax rates from the selected class." Treat class deletion as destructive to associated rates.

---

### 4. Shipping Zones

- **Base route:** `/wp-json/wc/v3/shipping/zones`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zones/`

| Method | Route | Description |
|---|---|---|
| POST | `/shipping/zones` | Create a zone (requires `name`) |
| GET | `/shipping/zones` | List all zones |
| GET | `/shipping/zones/<id>` | Retrieve a specific zone |
| PUT | `/shipping/zones/<id>` | Update `name` / `order` |
| DELETE | `/shipping/zones/<id>` | Delete a zone |

**Key params:** `id` (read-only), `name` (required on create), `order` (determines zone matching priority).

**Delete behavior:** No trash — `force=true` required.

**Gotchas:** Zone ID `0` is the built-in "Rest of the World" default zone. Zone `order` affects which zone's methods are evaluated first for a given customer address.

---

### 5. Shipping Zone Locations

- **Base route:** `/wp-json/wc/v3/shipping/zones/<id>/locations`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zone-locations/`

| Method | Route | Description |
|---|---|---|
| GET | `/shipping/zones/<id>/locations` | List all locations assigned to a zone |
| PUT | `/shipping/zones/<id>/locations` | Replace/update the zone's locations (accepts an array — batch-style, not a single-location PUT) |

**Key params:** `code` (location code, e.g. country/state/postcode string), `type` — one of `postcode`, `state`, `country`, `continent` (default `country`).

**Delete behavior:** N/A — no dedicated DELETE; removal is done by PUT-ing a location list that omits the entry.

**Gotchas:** The zone `id` must exist in the URL path for every call. PUT expects `Content-Type: application/json` and an array payload (it fully replaces the location set, not a partial patch).

---

### 6. Shipping Zone Methods

- **Base route:** `/wp-json/wc/v3/shipping/zones/<zone_id>/methods`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-zone-methods/`

| Method | Route | Description |
|---|---|---|
| POST | `/shipping/zones/<zone_id>/methods` | Add a shipping method to a zone (requires `method_id`) |
| GET | `/shipping/zones/<zone_id>/methods` | List methods on a zone |
| GET | `/shipping/zones/<zone_id>/methods/<id>` | Retrieve a specific method instance |
| PUT | `/shipping/zones/<zone_id>/methods/<id>` | Update `order`, `enabled`, `settings` |
| DELETE | `/shipping/zones/<zone_id>/methods/<id>?force=true` | Remove a method from a zone |

**Key params:** `instance_id` (read-only), `method_id` (read-only after creation, mandatory on create — references a shipping method type, see §7), `enabled` (bool), `settings` (nested config object, per method type).

**Delete behavior:** No trash — `force=true` required.

**Gotchas:** `method_id` here refers to the shipping method *type* (e.g. `flat_rate`) registered in the store, distinct from the numeric `instance_id` of that method once attached to a zone.

---

### 7. Shipping Methods (available method types)

- **Base route:** `/wp-json/wc/v3/shipping_methods`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/shipping-methods/`

| Method | Route | Description |
|---|---|---|
| GET | `/shipping_methods` | List all shipping method types available in the store |
| GET | `/shipping_methods/<id>` | Retrieve a specific method type by ID |

**Key params:** All fields read-only: `id` (e.g. `flat_rate`), `title`, `description`.

**Built-in method types documented:**
- `flat_rate` — "Lets you charge a fixed rate for shipping."
- `free_shipping` — "Can be triggered with coupons and minimum spends"
- `local_pickup` — "Allow customers to pick up orders themselves"

**Delete behavior:** N/A — read-only endpoint (no create/update/delete).

**Gotchas:** This endpoint lists method *types* registered in the store (core + plugin-added), not the per-zone method instances — those are managed via §6.

---

### 8. Payment Gateways

- **Base route:** `/wp-json/wc/v3/payment_gateways`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/payment-gateways/`

| Method | Route | Description |
|---|---|---|
| GET | `/payment_gateways` | List all payment gateways |
| GET | `/payment_gateways/<id>` | Retrieve a specific gateway |
| PUT | `/payment_gateways/<id>` | Update a gateway |

**Key params:** Writable: `enabled`, `title`, `description`, `order`, `settings[].value` only. Read-only: `id`, `method_title`, `method_description`, `method_supports`, and all `settings[]` metadata (`type`, `label`, `description`, `default`, `tip`, `placeholder`) except `value`. `settings[].type` can be `text`, `email`, `number`, `color`, `password`, `textarea`, `select`, `multiselect`, `radio`, `image_width`, `checkbox`.

**Delete behavior:** N/A — no DELETE (gateways are provided by code/plugins, not created via API).

**Gotchas:** Results are **not paginated** — all gateways are always returned in one response.

---

### 9. Webhooks

- **Base route:** `/wp-json/wc/v3/webhooks`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/webhooks/`

| Method | Route | Description |
|---|---|---|
| POST | `/webhooks` | Create a webhook (requires `topic`, `delivery_url`) |
| GET | `/webhooks` | List webhooks |
| GET | `/webhooks/<id>` | Retrieve a webhook |
| PUT | `/webhooks/<id>` | Update a webhook |
| DELETE | `/webhooks/<id>` | Delete a webhook |
| POST | `/webhooks/batch` | Batch create/update/delete (max 100 items) |

**Key params:**
- `topic` (required) — resource + event, see below
- `delivery_url` (required)
- `name` (optional label)
- `secret` (optional — generates HMAC-SHA256 signature; defaults to an MD5 hash of the user ID if omitted)
- `status` — `active` (default), `paused`, `disabled`
- List filters: `page`, `per_page`, `search`, `status`, `orderby`, `order`, `include`, `exclude`, `after`, `before`, `offset`

**Valid `topic` values documented:**
- Coupons: `coupon.created`, `coupon.updated`, `coupon.deleted`
- Customers: `customer.created`, `customer.updated`, `customer.deleted`
- Orders: `order.created`, `order.updated`, `order.deleted`
- Products: `product.created`, `product.updated`, `product.deleted`
- Custom: `action.{hook_name}` format for arbitrary WordPress action hooks (e.g. `action.woocommerce_add_to_cart`)

**Delete behavior:** `force` boolean, default `false`; set `true` for permanent deletion.

**Gotchas:**
- Delivery is via `wp_remote_post()`, processed in the background via wp-cron — not instantaneous/synchronous.
- Custom headers sent on delivery: `X-WC-Webhook-Source`, `X-WC-Webhook-Topic`, `X-WC-Webhook-Resource`, `X-WC-Webhook-Event`, `X-WC-Webhook-Signature` (base64 HMAC-SHA256), `X-WC-Webhook-ID`, `X-WC-Webhook-Delivery-ID`.
- A webhook is **automatically disabled after 5 consecutive failed deliveries** (non-2xx responses) — must be manually re-enabled (status → `active`) via the API.
- Delivery logs (request/response, duration, status) are visible under WooCommerce > Status > Logs.

---

### 10. Settings & Settings Options

Distinct from WP core settings (`wp/v2/settings`) — this is WooCommerce-specific store configuration, structured as **groups** (§10a) containing **options** (§10b).

**10a. Settings (groups)**
- **Base route:** `/wp-json/wc/v3/settings`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/settings/`

| Method | Route | Description |
|---|---|---|
| GET | `/settings` | List all setting groups |

Read-only fields: `id`, `label`, `description`, `parent_id`, `sub_groups`. Primary groups documented: General, Products, Tax, Shipping, Checkout, Accounts, Emails, Integration, API. Email settings are nested sub-groups (New order, Cancelled order, Failed order, Order on-hold, Processing order, Completed order, Refunded order, Customer invoice, Customer note, Reset password, New account).

**Delete behavior:** N/A — read-only.

**10b. Setting Options**
- **Base route:** `/wp-json/wc/v3/settings/<group_id>`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/setting-options/`

| Method | Route | Description |
|---|---|---|
| GET | `/settings/<group_id>` | List all options in a group |
| GET | `/settings/<group_id>/<id>` | Retrieve a specific option |
| PUT | `/settings/<group_id>/<id>` | Update an option (only `value` is writable) |
| POST | `/settings/<group_id>/batch` | Batch update (~100 objects max), payload is an `update` array of `{id, value}` |

**Key params:** Read-only metadata: `id`, `label`, `description`, `default`, `type` (`text`, `email`, `number`, `color`, `password`, `textarea`, `select`, `multiselect`, `radio`, `image_width`, `checkbox`), `tip`, `placeholder`, `options` (choices for select/radio/multiselect), `group_id`. Only `value` can be changed.

**Delete behavior:** N/A — no DELETE.

**Gotchas:** Update requests need only `{"value": ...}` in the body — sending other fields is ignored/rejected since they're read-only.

---

### 11. System Status & System Status Tools

**11a. System Status**
- **Base route:** `GET /wp-json/wc/v3/system_status`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/system-status/`

Single read-only GET endpoint (no list/create/update/delete). Returns: **Environment** (PHP version, memory limits, cURL, remote connectivity tests), **Database** (WC DB version, table status, GeoIP DB path), **Active Plugins**, **Theme** (WC compatibility, outdated templates, parent theme), **Settings** (currency, SSL enforcement, REST API status, taxonomy mappings), **Security** (connection encryption, error visibility), **Pages** (Shop/Cart/Checkout/My Account status + shortcode checks).

**Key params:** None besides auth — no filtering/pagination.

**Delete behavior:** N/A.

**11b. System Status Tools**
- **Base route:** `/wp-json/wc/v3/system_status/tools`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/system-status-tools/`

| Method | Route | Description |
|---|---|---|
| GET | `/system_status/tools` | List all available maintenance tools |
| GET | `/system_status/tools/<id>` | Retrieve a specific tool |
| PUT | `/system_status/tools/<id>` | Run/execute the tool (requires `confirm: true`) |

**Key params:** `id` (read-only), `confirm` (bool, write-only, required to execute), `success` (bool, write-only response field), `message` (string, write-only response field).

**Example tool IDs documented:** `clear_transients`, `clear_expired_transients`, `delete_orphaned_variations`, `clear_expired_download_permissions`, `regenerate_product_lookup_tables`, `repair_coupons_lookup_table`, `reset_roles`, `clear_sessions`, `db_update_routine`.

**Delete behavior:** N/A.

**Gotchas:** Running a tool via PUT is a **destructive/stateful action** (e.g. `clear_sessions` wipes all customer sessions, `reset_roles` overwrites role definitions) — always require `confirm: true` deliberately, never call blindly.

---

### 12. Data (countries, currencies, continents)

- **Base route:** `GET /wp-json/wc/v3/data`
- **Official doc:** `https://developer.woocommerce.com/docs/apis/rest-api/v3/data/`

| Method | Route | Description |
|---|---|---|
| GET | `/data` | Index of available data resources (`slug`, `description`) |
| GET | `/data/continents` | List all continents |
| GET | `/data/continents/<location>` | Retrieve a continent (e.g. `/eu`, `/af`) — includes `code`, `name`, `countries[]` |
| GET | `/data/countries` | List all countries |
| GET | `/data/countries/<location>` | Retrieve a country (e.g. `/us`, `/br`) — includes `code` (ISO 3166 alpha-2), `name`, `states[]`, localized formatting (currency position, decimal separators, measurement units) |
| GET | `/data/currencies` | List all currencies |
| GET | `/data/currencies/<currency>` | Retrieve a currency (e.g. `/brl`) — `code` (ISO 4217), `name`, `symbol` |
| GET | `/data/currencies/current` | The store's currently configured currency |

**Key params:** Location/currency codes are lowercase in the path.

**Delete behavior:** N/A — fully read-only reference data.

**Gotchas:** None documented beyond standard read-only/`_links` behavior.

---

## Part 2 — Authentication

### WordPress core REST API (`wp/v2`)

Source: `https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/`, `https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/`, `https://developer.wordpress.org/rest-api/key-concepts/`.

**Application Passwords**
- Introduced as a **core WordPress feature in WordPress 5.6** (Nov 2020) — this is the minimum version; earlier sites needed the separate Application Passwords plugin.
- **How to generate:** wp-admin → Users → (edit) → **Profile → Application Passwords** section. Give it a name/description, click Add New. The generated password is shown once (24 characters, uppercase/lowercase/numbers, displayed chunked e.g. `abcd EFGH 1234` for readability, but works with or without the spaces) — over 142 bits of entropy.
- **Authenticating a request — Basic Auth header format:** credentials are `username:application-password`, sent as HTTP Basic Auth (RFC 7617).
  ```
  curl --user "USERNAME:PASSWORD" https://HOSTNAME/wp-json/wp/v2/users?context=edit
  ```
- **HTTPS requirement:** Application Passwords are available by default only on sites served over SSL/HTTPS. On non-HTTPS sites the feature is disabled unless a site admin explicitly re-enables it via the `wp_is_application_passwords_available` filter (a deliberate opt-in override, not recommended for production).
- **Per-user restriction:** Site admins can further restrict which users may use Application Passwords via the `wp_is_application_passwords_available_for_user` filter.
- **If deleted:** if the WordPress user tied to an application password is deleted, that password stops working.
- **Capability/permission model:** Application Passwords do not grant new capabilities — every REST request still runs through the same permission checks as if that user were logged in via the dashboard, evaluated against the user's **role capabilities**. Typical mappings used by REST controllers:
  - `edit_posts` — required to create/list-with-edit-context posts
  - `edit_others_posts` — core capability check used for editor-level access
  - `delete_posts` — required to delete posts
  - `manage_options` — required for site-settings-level actions (e.g. `wp/v2/settings`)
  - `edit_theme_options` — required to view/edit/delete templates
  - `edit_user` / `edit_users` — required to manage other users' data, including their Application Passwords
  Meta-capabilities like `edit_post` / `edit_user` are resolved to primitive capabilities via WordPress's `map_meta_cap()` and then checked with `current_user_can()` inside each endpoint's `permissions_check()` method. Fine-grained capability control specific to Application Passwords was noted as "planned for future versions" as of the core team's integration guide — NOT VERIFIED whether that has since shipped (not found in the sources fetched).
- **Cookie + nonce authentication (same-origin JS alternative):** For JavaScript running within wp-admin/the same origin as the site, the standard method is cookie authentication (the browser's existing logged-in session cookie) plus a nonce with action `wp_rest`, passed either as the `_wpnonce` query parameter or the `X-WP-Nonce` header. If no nonce is supplied, "the API will set the current user to 0, turning the request into an unauthenticated request" — i.e. the cookie alone is not sufficient; the nonce is mandatory to bind the request to the logged-in user and prevent CSRF. This method only works for requests made from within WordPress itself (not for external/server-to-server clients).
- **Other plugin-based methods documented (not core):** OAuth 1.0a Server plugin and JSON Web Tokens (JWT) plugins for external/remote applications; a Basic Authentication plugin exists but is explicitly documented as **for local development/testing only, not recommended for production** — Application Passwords are the recommended production method for Basic-Auth-style access.

### WooCommerce REST API (`wc/v3`)

Source: `https://developer.woocommerce.com/docs/apis/rest-api/authentication/`.

- **Generating keys:** WooCommerce > Settings > Advanced > **REST API** → "Add Key" → choose a description, the WordPress user the key acts as, and a **permission level**. This generates a **Consumer Key** and **Consumer Secret**. The key inherits the capabilities/role of the selected WordPress user. "If the WordPress user associated with an API key is deleted, the API key will cease to function."
- **Permission levels:** **Read**, **Write**, **Read/Write** — set per key at creation time.
- **Basic Auth over HTTPS (recommended):** Consumer Key as username, Consumer Secret as password.
  ```
  curl https://www.example.com/wp-json/wc/v3/orders -u consumer_key:consumer_secret
  ```
- **OAuth 1.0a over plain HTTP (required when not using HTTPS):** "one-legged" OAuth 1.0a signing is required for any request made over plain (non-SSL) HTTP, since Basic Auth credentials would otherwise travel in the clear. Required parameters: `oauth_consumer_key`, `oauth_timestamp`, `oauth_nonce`, `oauth_signature`, `oauth_signature_method`. Only **HMAC-SHA1 or HMAC-SHA256** are accepted as signature hash algorithms. The signature base string is built from the HTTP method, URL, and normalized parameters, then signed with the consumer secret + `&`. The `oauth_timestamp` must be a Unix timestamp; "the REST API will deny any requests that include a timestamp outside of a 15 minute window to prevent replay attacks."
- **Query-string fallback (for servers that strip/mishandle the Authorization header):** pass the keys as query parameters instead of a header:
  ```
  https://www.example.com/wp-json/wc/v3/orders?consumer_key=XXXX&consumer_secret=XXXX
  ```
  The official doc notes: "Occasionally some servers may not parse the Authorization header correctly (if you see a 'Consumer key is missing' error when authenticating over SSL, you have a server issue)" — the query-string method is the documented workaround for that specific failure mode.

**Practical note:** for any site served over HTTPS (check `CLAUDE.md` / the live domain — this is the norm), Basic Auth with Consumer Key/Secret (or the query-string fallback if the host strips Authorization headers) is the applicable method — OAuth 1.0a is only required for plain-HTTP deployments.

---

## Part 3 — WordPress core version grounding (as of 2026-08-28)

Source: `https://wordpress.org/download/releases/`, `https://wordpress.org/documentation/wordpress-version/version-7-0/`, `https://wordpress.org/news/2026/05/wordpress-7-0-armstrong/`.

- **Yes, WordPress 7.0 has been released.** The official releases archive lists **WordPress 7.0 "Armstrong"** as released **May 20, 2026**, confirmed by the official announcement at `wordpress.org/news/2026/05/wordpress-7-0-armstrong/`. Maintenance releases followed: 7.0.1 (Jul 9, 2026), 7.0.2 (Jul 17, 2026), 7.0.3 (Aug 6, 2026), 7.0.4 (Aug 12, 2026).
- **Current/latest major version:** the same official releases archive lists **WordPress 7.1** as released **August 19, 2026** — i.e., as of the verification date (2026-08-28), 7.1 is the current release line ("Only the most recent in the 7.1 series is safe to use and actively maintained," per the archive page). Web search results describing 7.1 as still "upcoming"/in Release Candidate are stale relative to the official releases page and should be disregarded in favor of the archive.
- **Does the `wp/v2` REST API namespace change between major core versions?** NOT VERIFIED — could not confirm from official docs. The REST API Handbook's Key Concepts and homepage pages fetched do not state a versioning/backward-compatibility policy for the `wp/v2` namespace, and no dedicated "REST API versioning" doc was found in this pass. Treat `wp/v2` as the long-standing stable namespace based on its continuous use since introduction, but do not assert stability as an officially documented guarantee without further sourcing.
- **REST-API-relevant features in WordPress 7.0** (per the official announcement): a new **AI Client in Core** ("lets WordPress communicate with generative AI models, while connections are easily managed from a single hub in the dashboard") paired with an **Abilities API** for workflow automation and creation tools, plus a client-side/JavaScript Abilities counterpart with a command palette. Also: server-level block/pattern registration via PHP, an extensible Site Editor (routing, route validation, new `wordpress/boot` package), per-block custom CSS, a dedicated Font Management page, and a modernized dashboard. NOT VERIFIED: whether the Abilities API or AI Client expose new dedicated `wp/v2` (or separate namespace) REST routes — the announcement describes the features at a product level; no dedicated API reference for these was fetched in this pass.
- **WordPress 7.1**, per the releases archive, is the current active line as of 2026-08-28; a search snippet (not an official doc fetched directly for this file) described planned 7.1 features as new Notes/collaboration UI, new blocks (Playlist, Table of Contents, Tabs), and an internal React 18 → 19 upgrade. This is flagged as sourced from search-result summaries, not a directly fetched official page — treat as lower-confidence context only, not a verified fact for this reference.
