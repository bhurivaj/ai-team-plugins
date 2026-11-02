# WooCommerce REST API — Orders, Coupons & Customers

Source: official WooCommerce developer documentation at `https://developer.woocommerce.com/docs/apis/rest-api/v3/` (the current official home for WooCommerce REST API v3 docs; the legacy `woocommerce.github.io/woocommerce-rest-api-docs/` mirror was not needed — every resource in scope has a live page on `developer.woocommerce.com`). All facts below were fetched from the exact URLs cited per section. Verified: 2026-08-28.

All routes use namespace **`wc/v3`**, mounted at `/wp-json/wc/v3/...` on the store (i.e. `https://<site-domain>/wp-json/wc/v3/...` — get `<site-domain>` from the project's `CLAUDE.md`). Authentication (Basic Auth with consumer key/secret over HTTPS, or OAuth1.0a over HTTP) is documented separately at `https://developer.woocommerce.com/docs/apis/rest-api/authentication/` and is out of scope for this file.

---

## Orders
**Base route:** `/wc/v3/orders`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/orders/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/orders` | Create an order |
| GET | `/wc/v3/orders/<id>` | Retrieve an order |
| GET | `/wc/v3/orders` | List all orders |
| PUT | `/wc/v3/orders/<id>` | Update an order |
| DELETE | `/wc/v3/orders/<id>` | Delete an order |
| POST | `/wc/v3/orders/batch` | Batch create/update/delete orders (default limit 100 objects per request) |

**Key list/retrieve parameters:**
- `context` (string) — `view` or `edit`, default `view`
- `page` (integer, default `1`), `per_page` (integer, default `10`)
- `search` (string) — filter by text match
- `status` (array, default `any`) — one or more of: `pending`, `processing`, `on-hold`, `completed`, `cancelled`, `refunded`, `failed`, `trash`
- `customer` (integer) — filter by customer ID
- `product` (integer) — filter by product ID
- `dp` (integer, default `2`) — number of decimal points to use in each resource
- `order` (string, default `desc`) — `asc`/`desc`
- `orderby` (string, default `date`) — `date`, `modified`, `id`, `include`, `title`, `slug`

**Key create/update body fields:**
- `parent_id` (integer), `status` (string; same enum as above), `currency` (string, ISO code, default `USD`), `customer_id` (integer, default `0` — "User ID who owns the order. 0 for guests."), `customer_note` (string)
- `payment_method`, `payment_method_title`, `transaction_id`
- `set_paid` (boolean, default `false`, **WRITE-ONLY**) — quoted from the doc: "Define if the order is paid. It will set the status to processing and reduce stock items."
- `billing` object: `first_name`, `last_name`, `company`, `address_1`, `address_2`, `city`, `state`, `postcode`, `country`, `email`, `phone`
- `shipping` object: `first_name`, `last_name`, `company`, `address_1`, `address_2`, `city`, `state`, `postcode`, `country` (no email/phone)
- `line_items` array — each item: `product_id`, `variation_id`, `quantity`, `tax_class`, `subtotal`, `total`, `meta_data` (writable); `name`, `sku`, `price`, `subtotal_tax`, `total_tax`, `taxes`, `parent_name` are READ-ONLY
- `shipping_lines` array: `method_id`, `method_title`, `total` (writable); `total_tax`, `taxes` READ-ONLY
- `fee_lines` array: `name`, `tax_class`, `tax_status` (`taxable` or `none`), `total` (writable); `total_tax`, `taxes` READ-ONLY
- `coupon_lines` array: `code` (writable); `discount`, `discount_tax` READ-ONLY
- `meta_data` array: `key`, `value` (writable); `id` READ-ONLY
- READ-ONLY response fields: `id`, `number`, `order_key`, `created_via`, `version`, `date_created`/`date_created_gmt`, `date_modified`/`date_modified_gmt`, `date_paid`/`date_paid_gmt`, `date_completed`/`date_completed_gmt`, `discount_total`, `discount_tax`, `shipping_total`, `shipping_tax`, `cart_tax`, `total_tax`, `total`, `prices_include_tax`, `customer_ip_address`, `customer_user_agent`, `cart_hash`, `tax_lines` (with `rate_code`, `rate_id`, `label`, `compound`, `tax_total`, `shipping_tax_total`, `meta_data`), `refunds` (`id`, `reason`, `total`)

**Delete behavior:** `force` (boolean) query parameter — `force=true` permanently deletes the order; default (`false`) moves it to trash rather than permanently deleting.

**Gotchas:**
- Guest vs. registered-customer orders are distinguished purely by `customer_id`: `0` = guest, quoted verbatim: "User ID who owns the order. 0 for guests. Default is `0`."
- `set_paid` is write-only and side-effecting: setting it transitions status to `processing` and reduces stock — it is not just a flag, it triggers stock/status mutation server-side.
- The official v3 page does **not** document the specific behavioral rules for every status transition (e.g. exact stock/inventory effects of moving to `cancelled` vs `refunded` vs `failed`) — NOT VERIFIED beyond what's stated for `set_paid`. Do not assume additional automatic stock behavior on other status changes without testing against the live store.
- `line_items`, `shipping_lines`, `fee_lines`, `coupon_lines`, and `meta_data` are all arrays of sub-objects with their own writable vs. read-only field split — sending read-only sub-fields on create/update is harmless but has no effect.
- A batch endpoint exists (`/wc/v3/orders/batch`) capped at 100 objects per call for combined create/update/delete operations.

---

## Order Notes
**Base route:** `/wc/v3/orders/<order_id>/notes`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/order-notes/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/orders/<order_id>/notes` | Create an order note |
| GET | `/wc/v3/orders/<order_id>/notes/<note_id>` | Retrieve an order note |
| GET | `/wc/v3/orders/<order_id>/notes` | List all order notes |
| DELETE | `/wc/v3/orders/<order_id>/notes/<note_id>` | Delete an order note |

**Key list/retrieve parameters:**
- `context` (string) — `view` or `edit`, default `view` (retrieve + list)
- `type` (string, list only, default `any`) — `any`, `customer`, or `internal`

**Key create/update body fields:**
- `note` (string) — **MANDATORY**, the note content
- `customer_note` (boolean, default `false`) — "If true, the note will be shown to customers and they will be notified. If false, the note will be for admin reference only."
- `added_by_user` (boolean, default `false`) — "If true, this note will be attributed to the current user. If false, the note will be attributed to the system."
- READ-ONLY: `id`, `author`, `date_created`, `date_created_gmt`

**Delete behavior:** No trash concept — `force` is required to be `true` on delete, quoted from the doc: "Required to be `true`, as resource does not support trashing." There is **no update/PUT endpoint** for order notes — they can only be created, retrieved, listed, and deleted.

**Gotchas:**
- Order notes are always scoped under a parent order (`<order_id>` in the path) — there is no top-level `/wc/v3/notes` collection.
- Since there's no update endpoint, "editing" a note in practice means deleting and recreating it.
- `type=customer` vs `type=internal` on list lets you filter customer-visible notes from admin-only notes.

---

## Order Refunds
**Base route:** `/wc/v3/orders/<order_id>/refunds`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/order-refunds/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/orders/<order_id>/refunds` | Create a refund |
| GET | `/wc/v3/orders/<order_id>/refunds/<refund_id>` | Retrieve a refund |
| GET | `/wc/v3/orders/<order_id>/refunds` | List all refunds for an order |
| DELETE | `/wc/v3/orders/<order_id>/refunds/<refund_id>` | Delete a refund |
| POST | `/wc/v3/orders/<order_id>/refunds/preview` | Preview a refund without creating it (WooCommerce 11.1+) |

**Key list/retrieve parameters:**
- List: `context`, `page`, `per_page`, `search`, `after`, `before`, `exclude`, `include`, `orderby`, `order`, `dp`
- Retrieve: `dp` (decimal points in response)

**Key create/update body fields:**
- `amount` (string) — total refund amount; optional, and takes precedence over the sum of line-item totals if supplied
- `reason` (string) — reason for the refund
- `line_items` (array) — items being refunded, each with `id`, `refund_total`, `refund_tax`
- `api_refund` (boolean, default `true`) — whether to use the payment gateway's API to process the refund
- `api_restock` (boolean, default `true`) — whether to restock the refunded items
- `compute_totals` (boolean, default `false`, WooCommerce 11.1+) — have the server compute per-line refund amounts
- READ-ONLY: `id`, `date_created`, `date_created_gmt`, `refunded_payment`, `subtotal_tax`, `total_tax`, `sku`, `price`

**Delete behavior:** `force=true` is required on delete — the doc states the resource "doesn't support trashing," same pattern as order notes.

**Gotchas / refund side effects:** Per the official page, refund creation is explicitly tied to two independent toggles: `api_refund` (default `true`) triggers the actual payment-gateway refund call, and `api_restock` (default `true`) returns refunded quantities to stock. The doc's own wording ("automatically handle restocking and payment processing based on `api_refund` and `api_restock` flags") confirms refund creation **can** adjust stock automatically (via `api_restock`) — but the page does not spell out precisely how/when the parent order's `total`/`status` fields are recalculated beyond the read-only `refunds` array shown on the Orders resource. Treat exact order-total recalculation timing as **NOT VERIFIED — could not confirm precise mechanics from official docs**; rely on re-fetching the order after refund creation rather than assuming client-side math. The new `preview` sub-endpoint (11.1+) lets you compute a refund breakdown by product/shipping/fee before committing.

---

## Coupons
**Base route:** `/wc/v3/coupons`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/coupons/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/coupons` | Create a coupon |
| GET | `/wc/v3/coupons/<id>` | Retrieve a coupon |
| GET | `/wc/v3/coupons` | List all coupons |
| PUT | `/wc/v3/coupons/<id>` | Update a coupon |
| DELETE | `/wc/v3/coupons/<id>` | Delete a coupon |
| POST | `/wc/v3/coupons/batch` | Batch create/update/delete coupons (up to 100 objects per request) |

**Key list/retrieve parameters:**
- `context`, `page`, `per_page`, `search`, `after`, `before`, `modified_after`, `modified_before`, `dates_are_gmt`, `exclude`, `include`, `offset`, `order`, `orderby`, `code` (filter by exact coupon code)

**Key create/update body fields:**
- `code` (string) — **mandatory**, the coupon identifier
- `discount_type` (string, default `fixed_cart`) — enum values verbatim: `percent`, `fixed_cart`, `fixed_product`
- `amount` (string) — numeric discount value
- `individual_use` (boolean, default `false`) — prevents combining with other coupons
- `exclude_sale_items` (boolean, default `false`) — won't apply to sale-priced items
- `minimum_amount` / `maximum_amount` (string) — cart spend thresholds
- `product_ids` / `excluded_product_ids` (array) — product-level restrictions
- `usage_limit` (integer) — total redemption cap
- `usage_limit_per_user` (integer) — per-customer redemption cap
- `limit_usage_to_x_items` (integer) — max number of cart items the coupon can apply to
- `free_shipping` (boolean, default `false`)
- `date_expires` (string) — expiration date/timestamp
- `email_restrictions` (array) — allowed customer emails
- `used_by` (array, READ-ONLY) — user IDs/emails that have redeemed the coupon

**Delete behavior:** `force` (boolean) — `true` for permanent deletion; not explicitly confirmed on this page whether default is trash (NOT VERIFIED beyond what was returned in the fetch — the summarized page content stated only "Set `true` for permanent deletion" without repeating the trash-default wording seen on Orders/Customers; treat coupons as following the same trash-by-default / `force=true`-for-permanent pattern used elsewhere in `wc/v3`, but confirm empirically before relying on it).

**Gotchas:**
- `discount_type` only accepts the three listed enum values — Thai marketing agents building promo codes should map "percent off", "fixed amount off cart", "fixed amount off product" to `percent` / `fixed_cart` / `fixed_product` respectively.
- Batch endpoint capped at 100 objects, same as Orders and Customers.

---

## Customers
**Base route:** `/wc/v3/customers`
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/customers/

| Method | Route | Description |
|---|---|---|
| POST | `/wc/v3/customers` | Create a customer |
| GET | `/wc/v3/customers/<id>` | Retrieve a customer |
| GET | `/wc/v3/customers` | List all customers |
| PUT | `/wc/v3/customers/<id>` | Update a customer |
| DELETE | `/wc/v3/customers/<id>` | Delete a customer |
| POST | `/wc/v3/customers/batch` | Batch create/update/delete customers (max 100 objects) |
| GET | `/wc/v3/customers/<id>/downloads` | Get a customer's download permissions (sub-resource, GET only — see Customer Downloads below) |

**Key list/retrieve parameters:**
- `context` (`view`/`edit`, default `view`), `page` (default `1`), `per_page` (default `10`)
- `search` (string), `exclude` (array), `include` (array), `offset` (integer)
- `order` (default `asc`), `orderby` (default `name`; also `id`, `include`, `registered_date`)
- `email` (string) — filter by email address
- `role` (string, default `customer`) — `all`, `administrator`, `editor`, `author`, `contributor`, `subscriber`, `customer`, `shop_manager`

**Key create/update body fields:**
- `email` (string) — required for creation
- `first_name`, `last_name` (string)
- `username` (string) — login identifier
- `password` (string, WRITE-ONLY)
- `billing` object: `first_name`, `last_name`, `company`, `address_1`, `address_2`, `city`, `state`, `postcode`, `country`, `email`, `phone`
- `shipping` object: `first_name`, `last_name`, `company`, `address_1`, `address_2`, `city`, `state`, `postcode`, `country`
- `is_paying_customer` (boolean, READ-ONLY)
- `meta_data` (array): `id` (READ-ONLY), `key`, `value`

**Delete behavior:** `force=true` is **required** — quoted pattern from the doc: this resource "doesn't support soft-deletion." Also accepts `reassign` (integer, optional) — a user ID to reassign the deleted customer's posts/content to.

**Gotchas:**
- Unlike Orders, Customer deletion has no trash option at all — `force=true` is mandatory, not optional, and `reassign` lets you preserve authored content (e.g. reviews) under another user ID instead of orphaning it.
- `role` list filter defaults to `customer`, so listing without overriding `role` will not surface shop managers/admins.
- Guest WooCommerce orders are **not** WooCommerce "customers" in this resource — they only exist as `customer_id: 0` on the Orders resource; there is no customer record to fetch/update/delete for a guest checkout.

---

## Customer Downloads
**Base route:** `/wc/v3/customers/<id>/downloads` (documented as a sub-resource of Customers, not a standalone top-level resource)
**Official doc:** https://developer.woocommerce.com/docs/apis/rest-api/v3/customers/ (the v3 REST API index at https://developer.woocommerce.com/docs/apis/rest-api/v3/ lists Orders, Order Notes, Order Refunds, Order Actions, Coupons, Customers, Products and related product sub-resources as distinct pages; it does **not** list a separate "Customer Downloads" page — the downloads endpoint appears only inline on the Customers page)

| Method | Route | Description |
|---|---|---|
| GET | `/wc/v3/customers/<id>/downloads` | Retrieve a customer's available download permissions (e.g. for downloadable/digital products they've purchased) |

**Key list/retrieve parameters:** NOT VERIFIED — could not confirm from official docs beyond the base `GET /wc/v3/customers/<id>/downloads` route and an example request (`curl https://example.com/wp-json/wc/v3/customers/26/downloads -u consumer_key:consumer_secret`) returning download URL data.

**Key create/update body fields:** Not applicable — this endpoint is documented as read-only (GET only). No POST/PUT/DELETE method is documented for customer downloads.

**Delete behavior:** Not applicable / NOT VERIFIED — no delete method is documented for this endpoint.

**Gotchas:**
- This endpoint only matters when the store sells downloadable products; a business selling physical goods/services (check `CLAUDE.md` for this project's business type) is unlikely to need it, but it's included here for completeness.
- Because it's a sub-resource of Customers rather than an independent documented resource, do not expect a `/wc/v3/downloads` top-level collection — always scope the request under a specific customer ID.

---

## Cross-resource notes for agent implementers

- **Namespace:** All routes above use `wc/v3` exclusively, per the task requirement — do not fall back to `wc/v2` or `wc/v1` routes even though those legacy versions are still documented (v2: `/docs/apis/rest-api/v2/...`, v1: `/docs/apis/rest-api/v1/...`); v3 is current WooCommerce's actively recommended version.
- **Deletion pattern:** Orders and (implicitly) Coupons default to trash unless `force=true`; Order Notes, Order Refunds, and Customers require `force=true` unconditionally because they don't support trashing at all. Always pass `force=true` explicitly only when permanent deletion is actually intended.
- **Batch operations:** Orders, Coupons, and Customers each expose a `/batch` endpoint capped at 100 objects per request for combined create/update/delete calls; Order Notes and Order Refunds do not have documented batch endpoints.
- **Guest vs. customer records:** `customer_id: 0` on an Order means a guest checkout — there is no corresponding row in the Customers resource for that purchase. Do not assume every order has a fetchable customer record.
