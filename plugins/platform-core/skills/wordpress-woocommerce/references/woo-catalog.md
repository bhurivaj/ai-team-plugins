# WooCommerce REST API — Product Catalog

This file documents the WooCommerce REST API endpoints used for reading, creating, updating, and
deleting catalog data (products, variations, attributes, terms, categories, tags, shipping
classes, and reviews) on a WooCommerce store, via the REST API namespace `wc/v3`.

**Official source(s) used:**

- Index: https://developer.woocommerce.com/docs/apis/rest-api/
- Products: https://developer.woocommerce.com/docs/apis/rest-api/v3/products/
- Product Variations: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-variations/
- Product Attributes: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-attributes/
- Product Attribute Terms: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-attribute-terms/
- Product Categories: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-categories/
- Product Tags: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-tags/
- Product Shipping Classes: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-shipping-classes/
- Product Reviews: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-reviews/

**Date verified:** 2026-08-28
**REST API version:** `v3` (namespace `wc/v3`) — confirmed as the current version on the official
index page; requires WooCommerce 3.5+ and WordPress 4.4+. All routes below are prefixed
`/wp-json/wc/v3/`.

All pages above are live on `developer.woocommerce.com`, the current official home for WooCommerce
REST API docs (docs previously lived on `woocommerce.github.io` / `woocommerce.com/document` and
have moved here). No page returned a 404 or a "moved" notice during verification.

---

## Products

**Base route:** `/wc/v3/products`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/products/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products` | Create a new product (simple, grouped, external, or variable) |
| GET | `/wc/v3/products/<id>` | Retrieve a specific product by ID |
| GET | `/wc/v3/products` | List all products, with filtering/sorting |
| POST | `/wc/v3/products/<product_id>/duplicate` | Duplicate an existing product (new product created with `draft` status, SKU suffixed to avoid conflicts) |
| PUT | `/wc/v3/products/<id>` | Update an existing product |
| DELETE | `/wc/v3/products/<id>` | Delete a product |
| POST | `/wc/v3/products/batch` | Batch create/update/delete (default limit 100 objects total) |

**Key list/retrieve parameters:**
`context` (view/edit, default view), `page` (default 1), `per_page` (default 10), `search`,
`search_fields` (name, sku, global_unique_id, description, short_description), `after`, `before`,
`modified_after`, `modified_before`, `dates_are_gmt`, `exclude`, `include`, `offset`, `order`
(asc/desc, default desc), `orderby` (date, modified, id, include, title, slug, price, popularity,
rating, menu_order), `parent`, `parent_exclude`, `slug`, `status` (draft/pending/private/publish/any),
`include_status`, `exclude_status`, `type` (simple/grouped/external/variable), `include_types`,
`exclude_types`, `sku`, `featured`, `category`, `tag`, `shipping_class`, `attribute`,
`attribute_term`, `tax_class` (standard/reduced-rate/zero-rate), `on_sale`, `min_price`, `max_price`,
`stock_status` (instock/outofstock/onbackorder), `virtual`, `downloadable`, `image_size`.

**Key create/update body fields:**
`name`, `slug`, `type` (default `simple`), `status` (default `publish`), `featured` (default
false), `catalog_visibility` (visible/catalog/search/hidden, default visible), `description`,
`short_description`, `regular_price`, `sale_price`, `date_on_sale_from(_gmt)`,
`date_on_sale_to(_gmt)`, `sku`, `global_unique_id` (GTIN/UPC/EAN/ISBN), `virtual` (default false),
`downloadable` (default false), `downloads` (array of `id`/`name`/`file`), `download_limit`
(default -1 = unlimited), `download_expiry` (default -1 = never), `external_url`, `button_text`
(for `external` type), `tax_status` (taxable/shipping/none, default taxable), `tax_class`,
`manage_stock` (default false), `stock_quantity`, `stock_status` (default instock), `backorders`
(no/notify/yes, default no), `weight`, `dimensions` (`length`/`width`/`height`), `shipping_class`
(slug), `reviews_allowed` (default true), `upsell_ids`, `cross_sell_ids`, `parent_id`,
`grouped_products`, `categories` (array of `{id}`), `tags` (array of `{id}`), `brands` (array,
`id` required for write), `purchase_note`, `menu_order`, `images` (array — reference existing
Media Library `id` or upload via `src` URL, plus `name`/`alt`), `attributes` (array of
`id`/`name`/`position`/`visible`/`variation`/`options`), `default_attributes` (array of
`id`/`name`/`option`), `meta_data` (array of `key`/`value`).

Read-only fields (never send): `id`, `permalink`, `date_created(_gmt)`, `date_modified(_gmt)`,
`price`, `price_html`, `on_sale`, `purchasable`, `total_sales`, `backorders_allowed`,
`backordered`, `shipping_required`, `shipping_taxable`, `shipping_class_id`, `average_rating`,
`rating_count`, `related_ids`, `variations` (variation product IDs).

**Delete behavior:** `force` parameter (boolean). Per the official doc, `force=true` performs
permanent deletion; `force=false` (the default) moves the product to trash. Products **do**
support trashing, unlike most other catalog taxonomies documented below.

**Gotchas:**
- Price fields (`regular_price`, `sale_price`, `price`) are **strings**, not numbers — e.g. send
  `"1500.00"`, not `1500.00`.
- For **variable** products, `price` and `purchasable` are empty/false until child variations are
  created via the separate Product Variations endpoint — variations are NOT created by nesting
  them in the product's `variations` field (that field is read-only, listing only IDs).
- On an `attributes` entry, set `"variation": true` to make that attribute usable as a variation
  selector; `"visible"` only controls display on the storefront product page.
- Duplicating a product sets its status to `draft` and appends a suffix to the SKU to avoid
  collisions.
- Batch operations (`/products/batch`) are capped at 100 objects total across `create` + `update`
  + `delete` combined, by default.

---

## Product Variations

**Base route:** `/wc/v3/products/<product_id>/variations`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-variations/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/<product_id>/variations` | Create a variation under a variable parent product |
| GET | `/wc/v3/products/<product_id>/variations/<id>` | Retrieve a specific variation |
| GET | `/wc/v3/products/<product_id>/variations` | List all variations for a parent product |
| PUT | `/wc/v3/products/<product_id>/variations/<id>` | Update an existing variation |
| DELETE | `/wc/v3/products/<product_id>/variations/<id>` | Delete a variation |
| POST | `/wc/v3/products/<product_id>/variations/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context`, `page` (default 1), `per_page` (default 10), `offset`, `search`, `status` (or `any`),
`include_status`, `exclude_status` (comma-separated, take precedence), `sku`, `tax_class`,
`stock_status`, `on_sale`, `min_price`, `max_price`, `virtual`, `downloadable`, `parent`,
`parent_exclude`, `after`, `before`, `dates_are_gmt` (default false), `include`, `exclude`, `slug`,
`order` (default desc), `orderby` (date, modified, id, include, title, slug), `image_size`.

**Key create/update body fields:**
`regular_price`, `sale_price`, `date_on_sale_from(_gmt)`, `date_on_sale_to(_gmt)`,
`manage_stock` (boolean **or** the string `"parent"`, meaning "delegate stock control to the
parent product"; default false), `stock_quantity`, `stock_status`, `backorders` (default `no`),
`virtual` (default false), `downloadable` (default false), `downloads`, `download_limit` (default
-1), `download_expiry` (default -1), `tax_status` (default taxable), `tax_class`, `shipping_class`
(slug), `weight`, `dimensions`, `sku`, `global_unique_id`, `image` (single object: `id`, `src`,
`name`, `alt`), `gallery_image_ids` (array, separate from the single featured `image`),
`attributes` (array of `id`/`name`/`option` — **`option` is the attribute term's name/label, not
its numeric ID**), `status` (default publish), `menu_order`, `meta_data`.

Minimal create example given in the docs:
```json
{
  "regular_price": "9.00",
  "attributes": [{ "id": 6, "option": "Black" }]
}
```

Read-only fields: `price`, `on_sale`, `purchasable`, `backorders_allowed`, `backordered`,
`shipping_class_id`, meta_data `id`.

**Delete behavior:** `force=true` is **required**. The doc explicitly states variations "do not
support trashing" — there is no soft-delete; omitting `force=true` will not permanently remove
the variation.

**Gotchas:**
- Every variation write requires a valid parent `<product_id>` (a `variable`-type product) in the
  route.
- `attributes[].option` must match the attribute **term name**, not the term ID — this differs
  from the parent product's `attributes[].options` array (list of term names) and from Attribute
  Terms' own numeric `id`.
- `manage_stock` can be the literal string `"parent"` in addition to boolean true/false.
- Batch endpoint capped at 100 objects (create+update+delete combined) by default.
- Price fields are strings, same as Products.

---

## Product Attributes

**Base route:** `/wc/v3/products/attributes`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-attributes/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/attributes` | Create a new global product attribute |
| GET | `/wc/v3/products/attributes/<id>` | Retrieve a specific attribute |
| GET | `/wc/v3/products/attributes` | List all product attributes |
| PUT | `/wc/v3/products/attributes/<id>` | Update an attribute |
| DELETE | `/wc/v3/products/attributes/<id>` | Delete an attribute (**also deletes all its terms**) |
| POST | `/wc/v3/products/attributes/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context` (view/edit, default view) — the list endpoint doc only documents this parameter.

**Key create/update body fields:**
`name` (string, **mandatory**), `slug` (alphanumeric, unique within the taxonomy type), `type`
(currently only `select` is supported by default), `order_by` (default sort of terms:
`menu_order`, `name`, `name_num`, or `id`), `has_archives` (boolean, default false).

Read-only: `id`.

**Delete behavior:** `force=true` is required — "resource does not support trashing." Deleting an
attribute **cascades and removes all terms belonging to it**.

**Gotchas:**
- Deleting an attribute is destructive to its entire term list — confirm before calling.
- Batch capped at 100 objects by default.
- Only `select`-type attributes are documented as supported by default.

---

## Product Attribute Terms

**Base route:** `/wc/v3/products/attributes/<attribute_id>/terms`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-attribute-terms/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/attributes/<attribute_id>/terms` | Create a new term under an attribute |
| GET | `/wc/v3/products/attributes/<attribute_id>/terms/<id>` | Retrieve a specific term |
| GET | `/wc/v3/products/attributes/<attribute_id>/terms` | List all terms for an attribute |
| PUT | `/wc/v3/products/attributes/<attribute_id>/terms/<id>` | Update a term |
| DELETE | `/wc/v3/products/attributes/<attribute_id>/terms/<id>` | Delete a term |
| POST | `/wc/v3/products/attributes/<attribute_id>/terms/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context` (view/edit, default view), `page` (default 1), `per_page` (default 10), `search`,
`exclude`, `include`, `order` (default asc), `orderby` (id, include, name, slug, term_group,
description, count — default name), `hide_empty` (default false), `parent`, `product`, `slug`.

**Key create/update body fields:**
`name` (string, **mandatory** on create), `slug` (auto-generated from `name` if omitted),
`description`, `menu_order`.

Read-only: `id`, `count` (number of published products using the term).

**Delete behavior:** `force=true` is required — "resource does not support trashing"; deletion is
permanent only.

**Gotchas:**
- The `<attribute_id>` path segment is required in every route — terms are always scoped to a
  parent attribute.
- `count` only reflects *published* products.
- Batch capped at 100 objects by default.

---

## Product Categories

**Base route:** `/wc/v3/products/categories`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-categories/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/categories` | Create a new category |
| GET | `/wc/v3/products/categories/<id>` | Retrieve a specific category |
| GET | `/wc/v3/products/categories` | List all categories |
| PUT | `/wc/v3/products/categories/<id>` | Update a category |
| DELETE | `/wc/v3/products/categories/<id>` | Delete a category |
| POST | `/wc/v3/products/categories/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context`, `page`, `per_page`, `search`, `exclude`, `include`, `order`, `orderby`, `hide_empty`,
`parent`, `product`, `slug`.

**Key create/update body fields:**
`name` (string, **mandatory**), `slug`, `parent` (integer, parent category ID), `description`
(HTML accepted), `display` (default/products/subcategories/both), `image` (object: `id`, `src`,
`name`, `alt`; timestamps read-only), `menu_order`.

Read-only: `id`, `count` (published product count).

**Delete behavior:** `force=true` required — "resource does not support trashing"; permanent
deletion only.

**Gotchas:**
- `name` is mandatory on create.
- No soft-delete/trash — deletion cannot be undone via the API.
- Batch capped at 100 objects by default.

---

## Product Tags

**Base route:** `/wc/v3/products/tags`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-tags/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/tags` | Create a new product tag |
| GET | `/wc/v3/products/tags/<id>` | Retrieve a specific tag |
| GET | `/wc/v3/products/tags` | List all product tags |
| PUT | `/wc/v3/products/tags/<id>` | Update a tag |
| DELETE | `/wc/v3/products/tags/<id>` | Delete a tag |
| POST | `/wc/v3/products/tags/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context` (default view), `page` (default 1), `per_page` (default 10), `search`, `exclude`,
`include`, `offset`, `order` (default asc), `orderby` (id, include, name, slug, term_group,
description, count — default name), `hide_empty` (default false), `product`, `slug`.

**Key create/update body fields:**
`name` (string, **required** on create), `slug` (auto-generated if omitted), `description` (HTML
accepted).

Read-only: `id`, `count`.

**Delete behavior:** `force=true` required — "resource does not support trashing"; permanent only.

**Gotchas:**
- All CRUD requires authentication via `consumer_key`/`consumer_secret`.
- Batch capped at 100 objects by default.

---

## Product Shipping Classes

**Base route:** `/wc/v3/products/shipping_classes`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-shipping-classes/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/shipping_classes` | Create a new shipping class |
| GET | `/wc/v3/products/shipping_classes/<id>` | Retrieve a specific shipping class |
| GET | `/wc/v3/products/shipping_classes` | List all shipping classes |
| PUT | `/wc/v3/products/shipping_classes/<id>` | Update a shipping class |
| DELETE | `/wc/v3/products/shipping_classes/<id>` | Delete a shipping class |
| POST | `/wc/v3/products/shipping_classes/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context`, `page`, `per_page`, `search`, `exclude`, `include`, `offset`, `order`, `orderby`,
`hide_empty`, `product`, `slug`.

**Key create/update body fields:**
`name` (string, **mandatory**), `slug` (auto-generated from name, can be overridden),
`description` (HTML accepted).

Read-only: `id`, `count` (published product count).

**Delete behavior:** `force=true` required — "resource does not support trashing"; permanent
deletion only.

**Gotchas:**
- `name` mandatory on create.
- No soft-delete.
- Batch capped at 100 objects by default.
- A product references its shipping class by `shipping_class` (slug) on the Products/Variations
  resources; `shipping_class_id` on those resources is read-only.

---

## Product Reviews

**Base route:** `/wc/v3/products/reviews`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/product-reviews/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/products/reviews` | Create a new product review |
| GET | `/wc/v3/products/reviews/<id>` | Retrieve a specific review |
| GET | `/wc/v3/products/reviews` | List all product reviews |
| PUT | `/wc/v3/products/reviews/<id>` | Update a review |
| DELETE | `/wc/v3/products/reviews/<id>` | Delete a review |
| POST | `/wc/v3/products/reviews/batch` | Batch create/update/delete (default limit 100) |

**Key list/retrieve parameters:**
`context` (default view), `page` (default 1), `per_page` (default 10), `search`, `after`,
`before`, `dates_are_gmt` (default false), `exclude`, `include`, `offset`, `order` (default desc),
`orderby` (date, date_gmt, id, slug, include, product — default date_gmt), `reviewer` (array of
user IDs), `reviewer_exclude`, `reviewer_email` (array), `product` (array of product IDs),
`status` (all, hold, approved, spam, trash — default approved).

**Key create/update body fields:**
`product_id` (integer, **required** on create), `review` (string, review text/content —
plain text on create, may render as HTML in list responses), `reviewer` (string, name),
`reviewer_email` (string), `rating` (integer, 0–5), `status` (approved, hold, spam, unspam, trash,
untrash — default approved).

Read-only: `id`, `date_created(_gmt)`, `verified` (boolean — whether the reviewer actually
purchased the product).

**Delete behavior:** `force=true` required — "resource does not support trashing", i.e. even
though `status` includes `trash`/`untrash` values for moderation, the DELETE endpoint itself only
supports permanent removal via `force=true`. The `status` value is ignored on delete. Response
includes `deleted: true` and a `previous` object holding the deleted review's data.

**Gotchas:**
- `verified` is read-only and purely informational (was it a verified-purchase reviewer).
- `status` has both moderation states (hold/spam/approved) and trash-oriented values
  (trash/untrash) usable via PUT for moderation, but the dedicated DELETE endpoint always requires
  `force=true` for actual removal.
- Batch capped at 100 objects by default.

---

## Cross-cutting notes (apply to all resources above)

- **Authentication:** REST API v3 uses Consumer Key/Secret (`consumer_key` / `consumer_secret`),
  either as query params (HTTP only) or as HTTP Basic Auth (HTTPS) — per the official Getting
  Started / Authentication section of the docs index.
- **Batch endpoints** (`/batch` on every resource above) accept a JSON body with `create`,
  `update`, and `delete` arrays and are limited to 100 objects total per request by default.
- **Trashing support differs by resource:** Products support `force=false` (trash, default) vs.
  `force=true` (permanent). Every other resource documented here — Variations, Attributes,
  Attribute Terms, Categories, Tags, Shipping Classes, and Reviews — explicitly "does not support
  trashing" and requires `force=true` to delete at all.
- **Price and numeric-looking fields are strings** (`regular_price`, `sale_price`, `price`,
  `weight`, dimension values) on Products and Variations — always send/parse as strings, not JSON
  numbers.
- **Pretty permalinks** (Settings > Permalinks) must be enabled on the WordPress site for the
  REST API to function, per the official docs index page.

All eight resources in scope were successfully verified from live pages under
`developer.woocommerce.com/docs/apis/rest-api/v3/` — none required fallback to the
`woocommerce.github.io` mirror, and no facts in this file are unverified.
