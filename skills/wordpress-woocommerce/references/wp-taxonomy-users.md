# WordPress REST API — Taxonomies, Users, Search, Settings

Source: official WordPress.org REST API Handbook (https://developer.wordpress.org/rest-api/reference/). Every fact below was fetched and read directly from the official page cited in each section on **2026-08-28**. Where a detail could not be confirmed on the official page, it is explicitly marked `NOT VERIFIED — could not confirm from official docs` rather than inferred. Namespace for all routes below is `wp/v2` unless noted otherwise.

---

## Categories
**Base route:** `/wp/v2/categories`
**Official doc:** https://developer.wordpress.org/rest-api/reference/categories/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/categories` | List all categories |
| POST | `/wp/v2/categories` | Create a new category |
| GET | `/wp/v2/categories/<id>` | Retrieve a specific category |
| POST | `/wp/v2/categories/<id>` | Update a category |
| DELETE | `/wp/v2/categories/<id>` | Delete a category |

**Key list/retrieve parameters:**
- `context` — `view` (default), `embed`, `edit`
- `page` — default `1`
- `per_page` — default `10`
- `search` — filter by matching string
- `exclude` / `include` — ID filters
- `order` — `asc` (default) / `desc`
- `orderby` — default `name`; also `id`, `include`, `slug`, `include_slugs`, `term_group`, `description`, `count`
- `hide_empty` — exclude terms with no posts
- `parent` — filter by parent term ID
- `post` — filter by assigned post
- `slug` — filter by specific slug(s)

Schema fields: `id` (read-only), `count` (read-only), `description`, `link` (read-only URI), `name`, `slug`, `taxonomy` (read-only, always `category`), `parent`, `meta`.

**Key create/update body fields:**
- `name` — required on creation
- `description`, `slug`, `parent`, `meta` — optional

**Delete behavior:** Categories are terms, and per the official doc "terms do not support trashing" — the `force` parameter must be set to `true`, and deletion is permanent (no trash/restore step, unlike posts).

**Gotchas:**
- `taxonomy` is read-only and always returns `category` for this endpoint.
- Deleting a category does not delete the posts assigned to it; per WordPress's general taxonomy behavior a post losing its only category is commonly reassigned to the default category — the Categories reference page itself does not spell out post-reassignment behavior, so treat that specific mechanic as `NOT VERIFIED — could not confirm from official docs` beyond the general "terms don't trash, must force-delete" statement it does make.

---

## Tags
**Base route:** `/wp/v2/tags`
**Official doc:** https://developer.wordpress.org/rest-api/reference/tags/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/tags` | Retrieve a collection of tags |
| POST | `/wp/v2/tags` | Create a new tag |
| GET | `/wp/v2/tags/<id>` | Retrieve a specific tag record |
| POST | `/wp/v2/tags/<id>` | Update an existing tag |
| DELETE | `/wp/v2/tags/<id>` | Delete a tag |

**Key list/retrieve parameters:**
- `context` — `view` (default), `embed`, `edit`
- `page` — default `1`
- `per_page` — default `10`
- `search` — filter by matching string
- `exclude` / `include` — ID filters
- `offset` — offset the result set by a number of items
- `order` — `asc` (default) / `desc`
- `orderby` — default `name`; also `id`, `slug`, `count`, etc.
- `hide_empty` — exclude terms with no assigned posts
- `post` — limit results to terms assigned to a specific post
- `slug` — limit results to specific slug(s)

Schema fields: `id` (read-only), `count` (read-only), `description` (writable), `link` (read-only URI), `name` (writable), `slug` (writable), `taxonomy` (read-only, always `post_tag`), `meta` (writable).

**Key create/update body fields:**
- `name` — required on creation
- `description`, `slug`, `meta` — optional

**Delete behavior:** Same as categories — tags are terms and "do not support trashing"; `force=true` is required and deletion is permanent.

**Gotchas:**
- Unlike categories, tags have **no `parent` field** — tags are a flat (non-hierarchical) taxonomy, categories are hierarchical.
- `taxonomy` is always `post_tag` for this endpoint (read-only).

---

## Taxonomies
**Base route:** `/wp/v2/taxonomies`
**Official doc:** https://developer.wordpress.org/rest-api/reference/taxonomies/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/taxonomies` | Retrieve all registered taxonomies (or filtered by post type) |
| GET | `/wp/v2/taxonomies/<taxonomy>` | Retrieve a specific taxonomy by its slug identifier |

**Key list/retrieve parameters:**
- `context` — `view` (default), `embed`, `edit`
- `type` — filters results to taxonomies associated with a particular post type (list endpoint only)
- `taxonomy` — the alphanumeric identifier for a specific taxonomy (path parameter, required for the single-taxonomy endpoint)

**Key create/update body fields:** None — this is a **read-only, informational** resource. There is no POST/PUT/DELETE method; taxonomies are registered in PHP (`register_taxonomy()`), not via the REST API.

**Delete behavior:** Not applicable — no delete method exists for this endpoint.

**Gotchas:**
- All schema fields (`name`, `slug`, `description`, `types`, `hierarchical`, `rest_base`, `rest_namespace`, `capabilities`, `labels`, `visibility`, `show_cloud`) are read-only.
- `rest_base` is the value used to build the taxonomy's own REST route (see "Custom Taxonomies" below) — e.g. for `category` the `rest_base` is `categories`, for `post_tag` it is `tags`.
- `capabilities`, `labels`, `visibility`, and `show_cloud` are only present in the `edit` context.
- This is the meta-resource an agent should query first to discover what taxonomy REST routes actually exist on a given site (built-in and custom) before assuming a route name.

---

## Users
**Base route:** `/wp/v2/users`
**Official doc:** https://developer.wordpress.org/rest-api/reference/users/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/users` | List users |
| POST | `/wp/v2/users` | Create a user |
| GET | `/wp/v2/users/<id>` | Retrieve a specific user |
| POST | `/wp/v2/users/<id>` | Update a specific user |
| DELETE | `/wp/v2/users/<id>` | Delete a specific user |
| GET | `/wp/v2/users/me` | Retrieve the current (authenticated) user |
| POST | `/wp/v2/users/me` | Update the current user |
| DELETE | `/wp/v2/users/me` | Delete the current user |

**Key list/retrieve parameters:**
- `context` — `view` (default), `embed`, `edit`
- `page` — default `1`
- `per_page` — default `10`
- `search`, `exclude`, `include`, `offset`
- `order` — `asc` (default) / `desc`
- `orderby` — default `name`; also `id`, `include`, `registered_date`, `slug`, `include_slugs`, `email`, `url`
- `slug` — limit to specific slug(s)
- `roles` — limit to users with specific role(s)
- `capabilities` — limit to users with specific capabilities
- `who` — limit to authors of the site (value: `authors`)
- `has_published_posts` — limit to users who have published posts

**Schema fields:**
- Read-only: `id`, `link`, `registered_date`, `capabilities`, `extra_capabilities`, `avatar_urls`
- Editable: `username`, `name`, `first_name`, `last_name`, `email`, `url`, `description`, `locale`, `nickname`, `slug`, `roles`, `password`, `meta`

**Key create/update body fields:**
- Required on creation: `username`, `email`, `password`
- Optional: all other editable schema fields above
- `password` is never included in responses — write-only.
- `locale` accepts an empty string or a locale like `en_US`.

**Delete behavior:** Requires **both** `force=true` and `reassign=<user_id>` — `reassign` transfers the deleted user's posts/content to the specified user ID. There is no trash step for users.

**Gotchas:**
- `password` is accepted in create/update request bodies but is stripped from every response — never rely on reading it back.
- `/wp/v2/users/me` is a convenience alias for the authenticated user's own record and supports the same GET/POST/DELETE operations as `/wp/v2/users/<id>`.
- Listing users without sufficient permissions typically only surfaces users who have authored content (public `view`/`embed` context is limited); use the `who=authors` parameter deliberately when you specifically want post authors.

---

## Search Results
**Base route:** `/wp/v2/search`
**Official doc:** https://developer.wordpress.org/rest-api/reference/search-results/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/search` | Site-wide search across the object types/subtypes below |

**Key list/retrieve parameters:**
- `context` — `view` (default) or `embed` (no `edit` context for this endpoint)
- `page` — default `1`
- `per_page` — default `10`
- `search` — the query string to match
- `type` — object type filter; default `post`; accepts `post`, `term`, `post-format`
- `subtype` — object subtype filter; default `any`; accepts `post`, `page`, `category`, `post_tag`
- `exclude` / `include` — ID filters

Schema fields (all read-only, present in both `view` and `embed`): `id` (integer or string), `title` (string), `url` (URI), `type` (`post` / `term` / `post-format`), `subtype` (`post` / `page` / `category` / `post_tag`).

**Key create/update body fields:** None — GET-only, read-only resource.

**Delete behavior:** Not applicable.

**Gotchas:**
- There is no `edit` context on this endpoint — it never exposes editor-only fields.
- `subtype=any` (the default) searches across all registered subtypes for the given `type`; narrow with an explicit `subtype` (e.g. `post`, `page`) to avoid mixing posts, pages, categories, and tags in one result set.
- The `_fields` / `_filter` query mechanism can be used generically across REST endpoints (including this one) to trim the response to specific fields.

---

## Settings
**Base route:** `/wp/v2/settings`
**Official doc:** https://developer.wordpress.org/rest-api/reference/settings/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/settings` | Retrieve site settings |
| POST | `/wp/v2/settings` | Update site settings |

**Key list/retrieve parameters:** No arguments are required for the GET request; the generic `context` parameter pattern applies (this resource itself only documents a single-object read, not a filterable collection).

**Key create/update body fields (schema):**
- `title` — site title
- `description` — site tagline
- `url` — site URL
- `email` — admin notification address
- `timezone` — city in the site's timezone
- `date_format` / `time_format`
- `start_of_week` — integer day number
- `language` — WordPress locale code
- `use_smilies` — boolean, convert emoticons to graphics
- `default_category` — integer, default post category ID
- `default_post_format`
- `posts_per_page` — integer
- `show_on_front` — what the front page displays
- `page_on_front` — page ID shown on the front page
- `page_for_posts` — page ID shown for the latest posts
- `default_ping_status` — `open` / `closed`
- `default_comment_status` — `open` / `closed`
- `site_logo` — integer (attachment ID)
- `site_icon` — integer (attachment ID)

**Delete behavior:** Not applicable — settings are a singleton resource, no delete method.

**Gotchas:**
- The official reference page does not document which capability is required to read vs. write Settings, nor which fields are gated for unauthenticated requests — this is `NOT VERIFIED — could not confirm from official docs`. In practice, writing to this endpoint requires an authenticated request with the `manage_options` capability, but that specific capability name is **not stated on the Settings reference page itself**, so treat it as general WordPress knowledge, not something confirmed from this official page.
- This is a singleton object (not a collection) — there are no `id`, `page`, or `per_page` semantics.

---

## Application Passwords
**Base route:** `/wp/v2/users/<user_id>/application-passwords`
**Official doc:** https://developer.wordpress.org/rest-api/reference/application-passwords/

| Method | Route | Description |
|---|---|---|
| GET | `/wp/v2/users/<user_id>/application-passwords` | List all application passwords for a user |
| POST | `/wp/v2/users/<user_id>/application-passwords` | Create a new application password |
| GET | `/wp/v2/users/<user_id>/application-passwords/<uuid>` | Retrieve a specific application password record |
| POST | `/wp/v2/users/<user_id>/application-passwords/<uuid>` | Update a specific application password (name/app_id only) |
| DELETE | `/wp/v2/users/<user_id>/application-passwords/<uuid>` | Delete a specific application password |
| DELETE | `/wp/v2/users/<user_id>/application-passwords` | Delete all application passwords for the user |
| GET | `/wp/v2/users/<user_id>/application-passwords/introspect` | Retrieve info about the application password currently authenticating the request |

**Key list/retrieve parameters:**
- `context` — `view` (default), `embed`, `edit`

**Key create/update body fields:**
- `name` — required on creation; the human-readable label for the application password
- `app_id` — optional; a UUID (v5 recommended, URL/DNS namespace) the calling application supplies to uniquely identify itself
- On update, only `name` and `app_id` are accepted — the password value itself cannot be changed via update, only regenerated by creating a new one.

Schema fields: `uuid` (read-only, unique identifier), `app_id` (writable), `name` (writable), `password` (read-only, **edit context only**, "only available after adding an application"), `created` (read-only, GMT datetime), `last_used` (read-only, datetime or null), `last_ip` (read-only, IP address or null).

**Delete behavior:** Deleting a specific record via `DELETE /wp/v2/users/<user_id>/application-passwords/<uuid>` removes that credential immediately (no trash step documented). A bulk `DELETE /wp/v2/users/<user_id>/application-passwords` removes all application passwords for that user.

**Gotchas:**
- `password` is exposed **only once**, in the response to the `POST` create request (and generally in the `edit` context) — it cannot be retrieved again afterward via GET; if lost, the application password must be deleted and re-created.
- The `introspect` route is a special sub-resource that reports on the credential the current request is authenticated with, not an arbitrary UUID lookup.
- The official reference page for this resource does not itself state an HTTPS requirement or any other security precondition — do not assert an HTTPS requirement as sourced from this page. Treat "application passwords require HTTPS" as `NOT VERIFIED — could not confirm from official docs` (this reference page only covers the schema/routes, not deployment/security requirements).

---

## Custom Taxonomies

Per the official `/wp/v2/taxonomies` reference, every taxonomy registered with `register_taxonomy()` and `show_in_rest: true` is automatically exposed as its own REST resource, following the same request/response shape documented above for Categories and Tags:

- The taxonomy's route is built from its `rest_namespace` (default `wp/v2`) and `rest_base` (defaults to the taxonomy's `slug`, but can be overridden at registration) — e.g. a custom taxonomy with `rest_base: 'portfolio-tags'` becomes reachable at `/wp/v2/portfolio-tags`.
- To discover what custom taxonomies (and their REST bases) exist on a given site, query `GET /wp/v2/taxonomies` (optionally filtered with `?type=<post_type>`) rather than guessing the route name — the `rest_base` field in that response is the authoritative route segment to use.
- A custom taxonomy's generated collection/single-item routes support the same `context`, `page`, `per_page`, `search`, `exclude`, `include`, `order`, `orderby`, `hide_empty`, `parent` (if `hierarchical: true`), `post`, and `slug` list parameters, and the same create/update/delete semantics (terms don't trash — `force=true` required to delete) as Categories/Tags.
- Whether a custom taxonomy behaves like Categories (hierarchical, has `parent`) or like Tags (flat, no `parent`) depends on the `hierarchical` argument passed to `register_taxonomy()`, which is reported back on the `/wp/v2/taxonomies/<taxonomy>` schema.
