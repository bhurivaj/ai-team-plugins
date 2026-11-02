# WordPress REST API — Content Resources (Posts, Pages, Media, Comments)

Source: official WordPress.org REST API Handbook (https://developer.wordpress.org/rest-api/reference/) and, where the Handbook's reference tables omit detail present only in the generated PHP schema, the official WordPress Code Reference (https://developer.wordpress.org/reference/classes/). All facts below were verified against the live pages on **2026-08-28**. All routes are under the `wp/v2` namespace, i.e. `https://<site-domain>/wp-json/wp/v2/...` (get `<site-domain>` from the project's `CLAUDE.md`).

---

## Posts

**Base route:** `/wp/v2/posts`
**Official doc:** https://developer.wordpress.org/rest-api/reference/posts/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/posts | List posts |
| POST | /wp/v2/posts | Create a post |
| GET | /wp/v2/posts/<id> | Retrieve a post |
| POST | /wp/v2/posts/<id> | Update a post |
| DELETE | /wp/v2/posts/<id> | Delete a post |

Note: the official docs show **POST** (not PUT/PATCH) as the update method for `/wp/v2/posts/<id>`.

**Key list/retrieve parameters:**

| Name | Type | Default | What it does |
|---|---|---|---|
| `context` | string | `view` | Scope of the request; determines which fields appear in the response. One of `view`, `embed`, `edit` |
| `page` | integer | `1` | Current page of the collection |
| `per_page` | integer | `10` | Max items to return |
| `search` | string | — | Limit results to those matching a string |
| `slug` | array | — | Limit to posts with one or more specific slugs |
| `status` | array | `publish` | Limit to posts with one or more specific statuses |
| `author` | array | — | Limit to posts by specific author IDs |
| `categories` | array | — | Limit to posts with specific category term IDs |
| `tags` | array | — | Limit to posts with specific tag term IDs |
| `orderby` | string | `date` | Sort attribute: `author`, `date`, `id`, `include`, `modified`, `parent`, `relevance`, `slug`, `include_slugs`, `title` |
| `order` | string | `desc` | `asc` or `desc` |
| `before` / `after` | string | — | Limit to posts published before/after an ISO8601 date |
| `sticky` | boolean | — | Limit to sticky posts |

`_fields` and `_embed` are not resource-specific — they are global query parameters documented on the "Global Parameters" page (see Gotchas below) and work on this endpoint like any other.

**Key create/update body fields:**

| Field | Type | Notes |
|---|---|---|
| `title` | object | "The title for the post" |
| `content` | object | "The content for the post" |
| `excerpt` | object | "The excerpt for the post" |
| `status` | string | One of `publish`, `future`, `draft`, `pending`, `private` |
| `featured_media` | integer | ID of the featured media attachment |
| `categories` | array | Term IDs in the `category` taxonomy |
| `tags` | array | Term IDs in the `post_tag` taxonomy |
| `slug` | string | Alphanumeric identifier unique to the post type |
| `date` / `date_gmt` | string/null | Publish date, site time / GMT |
| `comment_status` | string | `open` or `closed` |
| `ping_status` | string | `open` or `closed` |
| `format` | string | `standard`, `aside`, `chat`, `gallery`, `link`, `image`, `quote`, `status`, `video`, `audio` |
| `sticky` | boolean | Whether to treat the post as sticky |
| `password` | string | Password to protect content/excerpt (writable in `edit` context only) |
| `author` | integer | Author user ID |
| `meta` | object | Custom meta fields |
| `template` | string | Theme file used to display the post |

**Delete behavior:** `DELETE /wp/v2/posts/<id>` — the `force` parameter controls this: "Whether to bypass Trash and force deletion." Without `force=true`, the post is moved to Trash (status becomes `trash`); with `force=true`, it is permanently deleted, bypassing Trash. The reference page does not name a specific required capability for this endpoint. The general Authentication doc states only that "the current user must have the appropriate capability to perform the action being performed" — under WordPress's standard capability model this is `delete_posts` (own posts) / `delete_others_posts` (others' posts), but that specific capability name is **NOT VERIFIED** against the Posts reference page itself — it does not state it explicitly.

**Gotchas:**

- **`title`, `content`, `excerpt` are objects, not strings.** The Posts reference table lists them only as `"JSON data type: object"` with no sub-property breakdown. The actual sub-schema (confirmed via the official WordPress Code Reference for `WP_REST_Posts_Controller::get_item_schema()`) is:
  - `raw` — string, context `edit` only, writable. The unprocessed content as stored in the database. This is the field you should send/read when editing.
  - `rendered` — string, context `view`/`edit`/`embed` (content.rendered is `view`/`edit` only, no `embed`), **read-only**. The HTML-rendered version for display.
  - Practical effect: when you `GET` a post without `context=edit` (i.e. the default `view` context, or as an unauthenticated caller), you will only receive `title.rendered` / `content.rendered` / `excerpt.rendered` — there is no `.raw` in the response. To retrieve or write the raw/source content, you must request `context=edit` **and** be authenticated as a user with edit permission on that post; otherwise the API will not return the `raw` key.
- Update method is `POST`, not `PUT`/`PATCH` — sending PUT/PATCH per REST convention will not work against this API as documented.
- Default `status` filter for list requests is `publish` — draft/pending/private posts will not appear in a plain `GET /wp/v2/posts` call unless you pass `status` explicitly (and are authenticated with permission to see them).
- `_embed` must be added as a query string flag (`?_embed`) to pull in linked resources (author, featured media, terms) inline via `_embedded`; without it you only get `_links` (hrefs) and must make follow-up requests.
- `context=edit` generally requires authentication with edit capability on the resource — anonymous/unauthenticated requests are treated as user ID 0 and will not receive edit-only fields.
- **On a block/site-editor theme (check via `.claude/scripts/wp_rest.py GET wp/v2/themes --query status=active` → `is_block_theme: true`, or CLAUDE.md), `content.raw` must be Gutenberg block markup, not plain HTML.** Plain `<h2>`/`<ol><li>` tags with no block wrapper will still display on the front end (WP falls back to `wpautop` on unrecognized content), but they render *differently* than a content-planning tool's own preview (e.g. Flowtone's Tiptap-based editor) because they're missing the block comments and canonical classnames the theme's block styles (colors/fonts from `theme.json`/DESIGN.md) target. If content originates as a different document model (Tiptap/ProseMirror JSON, Markdown, etc.), convert each node to its WP block equivalent before writing `content`, not just to equivalent-looking HTML:
  - paragraph → `<!-- wp:paragraph -->\n<p>...</p>\n<!-- /wp:paragraph -->`
  - heading (level N) → `<!-- wp:heading -->\n<h`N` class="wp-block-heading">...</h`N`>\n<!-- /wp:heading -->` (add `{"level":N}` inside the opening comment for N ≠ 2)
  - ordered/unordered list → `<!-- wp:list {"ordered":true} -->\n<ol class="wp-block-list"><li>...</li></ol>\n<!-- /wp:list -->` (drop `{"ordered":true}` and use `<ul>` for unordered)
  - Verify by reading back `content.rendered` after creating/updating the post — it should show the same `wp-block-*` classed elements, confirming WP parsed the blocks rather than falling back to raw HTML.

---

## Pages

**Base route:** `/wp/v2/pages`
**Official doc:** https://developer.wordpress.org/rest-api/reference/pages/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/pages | List pages |
| POST | /wp/v2/pages | Create a page |
| GET | /wp/v2/pages/<id> | Retrieve a page |
| POST | /wp/v2/pages/<id> | Update a page |
| DELETE | /wp/v2/pages/<id> | Delete a page |

**Key list/retrieve parameters:**

| Name | Type | Default | What it does |
|---|---|---|---|
| `context` | string | `view` | `view`, `embed`, or `edit` |
| `page` | integer | `1` | Current page of the collection |
| `per_page` | integer | `10` | Max items to return |
| `search` | string | — | Limit results to those matching a string |
| `slug` | string | — | Limit to pages with a specific slug |
| `status` | string | `publish` | Limit to pages with a specific status |
| `author` | integer | — | Limit to pages by a specific author |
| `parent` | integer | — | Limit to children of a particular parent page ID |
| `menu_order` | integer | — | Limit to pages with a specific `menu_order` value |
| `orderby` | string | `date` | `author`, `date`, `id`, `include`, `modified`, `parent`, `relevance`, `slug`, `include_slugs`, `title`, `menu_order` |
| `order` | string | `desc` | `asc` or `desc` |

**Key create/update body fields:**

| Field | Type | Notes |
|---|---|---|
| `title` | object | Same rendered/raw shape as posts |
| `content` | object | Same rendered/raw shape as posts |
| `excerpt` | object | Same rendered/raw shape as posts |
| `status` | string | `publish`, `future`, `draft`, `pending`, `private` |
| `featured_media` | integer | Featured image attachment ID |
| `parent` | integer | Parent page ID (pages are hierarchical) |
| `menu_order` | integer | Order relative to sibling pages |
| `template` | string | Theme template file for the page |
| `slug` | string | Alphanumeric identifier |
| `date` | string/null | Publish date, site timezone |
| `comment_status` | string | `open` or `closed` |

**Delete behavior:** Same as Posts — `DELETE /wp/v2/pages/<id>` takes a `force` parameter: "Whether to bypass Trash and force deletion" when set to `true`. Without it, the page is trashed; with it, permanently deleted. Capability requirement not spelled out on this reference page (standard WP model: `delete_pages`/`delete_others_pages` — **NOT VERIFIED** against this specific page).

**Gotchas:**

- Pages are hierarchical (`parent`/`menu_order` exist; posts do not have these). Category/tag taxonomies from Posts do not apply to Pages by default.
- Same rendered-vs-raw object shape and update-via-POST caveats as Posts apply here (see Posts Gotchas above) — the Pages reference page schema is likewise generated from the same underlying controller pattern.

---

## Post Revisions

**Base route:** `/wp/v2/posts/<parent>/revisions`
**Official doc:** https://developer.wordpress.org/rest-api/reference/post-revisions/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/posts/<parent>/revisions | List revisions of a post |
| GET | /wp/v2/posts/<parent>/revisions/<id> | Retrieve a specific revision |
| DELETE | /wp/v2/posts/<parent>/revisions/<id> | Delete a specific revision |

Revisions are nested under their parent post; there is no standalone `/wp/v2/revisions` collection in this reference. (Pages, having their own hierarchical post type, expose revisions the same way under `/wp/v2/pages/<parent>/revisions`, by the same controller pattern — not independently re-verified on a separate page, but consistent with the documented pattern.)

**Key list/retrieve parameters:** `parent` (required — ID of the parent post), `context` (default `view`; `view`/`embed`/`edit`), `page`, `per_page`, `search`, `exclude`, `include`, `offset`, `order` (default `desc`), `orderby` (default `date`).

**Key create/update body fields:** Revisions are read-only snapshots — there is no create or update endpoint for revisions in the official reference (only List, Retrieve, Delete).

**Delete behavior:** `DELETE /wp/v2/posts/<parent>/revisions/<id>` — the `force` argument is documented as: **"Required to be true, as revisions do not support trashing."** This is a direct quote from the official reference. In other words, unlike posts/pages/comments, revisions have no Trash state at all — deletion is always permanent and `force=true` must be explicitly passed or the request will not succeed as a no-op-to-trash the way posts do.

**Gotchas:**

- You cannot delete a revision without `force=true` — omitting it is not "trash it," it simply is not the documented behavior for this endpoint (per the quote above).
- No POST/create or update route exists for revisions — WordPress creates them automatically when a post/page is saved; agents should not attempt to `POST` a new revision directly.

---

## Post Types

**Base route:** `/wp/v2/types`
**Official doc:** https://developer.wordpress.org/rest-api/reference/post-types/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/types | List all registered (REST-visible) post types |
| GET | /wp/v2/types/<type> | Retrieve a specific post type by its slug |

This resource is read-only in the official reference — no POST/PUT/DELETE routes are documented (registering post types is a PHP/plugin-side operation, not a REST write operation).

**Key list/retrieve parameters:** `context` (default `view`; `view`/`embed`/`edit`); `type` (required path parameter on the single-item route — the post type slug, e.g. `post`, `page`, `attachment`).

**Schema fields returned (useful for a marketing agent to discover what's available):**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Human-readable post type title |
| `slug` | string | Alphanumeric identifier (e.g. `post`, `page`) |
| `description` | string | Human-readable description |
| `hierarchical` | boolean | Whether the type supports parent/child (like Pages) |
| `viewable` | boolean | Whether the type can be viewed on the front end |
| `labels` | object | Context-specific human-readable labels |
| `supports` | object | Features supported (e.g. `title`, `editor`, `thumbnail`) |
| `has_archive` | string/boolean | Archive slug, or `false` if none |
| `taxonomies` | array | Taxonomies associated with this post type |
| `rest_base` | string | The REST route base for this post type (see Custom Post Types section below) |
| `rest_namespace` | string | REST namespace for this post type (normally `wp/v2`) |
| `capabilities` | object | All capabilities used by the post type |
| `visibility` | object | Visibility settings |

**Gotchas:**

- Use `rest_base` from this endpoint, not the type's `slug`, to build the correct collection route — they can differ (see Custom Post Types below).
- Only post types registered with `show_in_rest: true` will appear here.

---

## Post Statuses

**Base route:** `/wp/v2/statuses`
**Official doc:** https://developer.wordpress.org/rest-api/reference/post-statuses/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/statuses | List all registered post statuses |
| GET | /wp/v2/statuses/<status> | Retrieve a specific status by its slug |

Read-only resource — no write routes documented.

**Key list/retrieve parameters:** `context` (default `view`; `view`/`embed`/`edit`); `status` (required path parameter on the single-item route — the status slug).

**Schema fields returned:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | "The title for the status" |
| `slug` | string | Alphanumeric identifier for the status |
| `public` | boolean | Whether posts of this status show on the front end |
| `queryable` | boolean | Whether posts of this status are publicly queryable |
| `private` | boolean | Whether posts of this status should be private |
| `protected` | boolean | Whether posts of this status should be protected |
| `show_in_list` | boolean | Whether to include in the edit listing for the post type |
| `date_floating` | boolean | Whether posts of this status may have floating publish dates |

**Standard status slugs:** The official reference page does **not** enumerate the standard status slugs (`publish`, `future`, `draft`, `pending`, `private`, `trash`) in prose — this list is only inferable from the `status` enum shown on the Posts schema (`publish`, `future`, `draft`, `pending`, `private` are the ones listed as writable values there). `trash` appears as a status a post moves into on non-forced delete but is not listed among the writable `status` enum values on the Posts create/update schema. **NOT VERIFIED**: a definitive enumerated list of all standard status slugs together with their `public`/`private`/`protected` flags was not found on the Post Statuses reference page itself — agents needing the full authoritative list should call `GET /wp/v2/statuses` against the live site.

---

## Media

**Base route:** `/wp/v2/media`
**Official doc:** https://developer.wordpress.org/rest-api/reference/media/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/media | List media items |
| POST | /wp/v2/media | Create (upload) a media item |
| GET | /wp/v2/media/<id> | Retrieve a media item |
| POST | /wp/v2/media/<id> | Update a media item |
| DELETE | /wp/v2/media/<id> | Delete a media item |

**Key list/retrieve parameters:**

| Name | Type | Default | What it does |
|---|---|---|---|
| `context` | string | `view` | `view`, `embed`, `edit` |
| `page` | integer | `1` | Current page of the collection |
| `per_page` | integer | `10` | Max items to return |
| `search` | string | — | Limit results to those matching a string |
| `slug` | string | — | Limit to specific slug(s) |
| `status` | string | `inherit` | Limit to media with an assigned status (default status for attachments is `inherit`, not `publish`) |
| `media_type` | string | — | `image`, `video`, `text`, `application`, `audio` |
| `mime_type` | string | — | Limit to a specific MIME type, e.g. `image/jpeg` |
| `parent` | integer | — | Limit to attachments of a specific parent post ID |
| `orderby` | string | `date` | `author`, `date`, `id`, `include`, `modified`, `parent`, `relevance`, `slug`, `include_slugs`, `title` |
| `order` | string | `desc` | `asc` or `desc` |

**Key create/update body fields:**

| Field | Notes |
|---|---|
| `title` | Object, rendered/raw shape |
| `alt_text` | "Alternative text to display when attachment is not displayed" |
| `caption` | The attachment caption (object, rendered/raw) |
| `description` | The attachment description (object, rendered/raw) |
| `post` | "The ID for the associated post of the attachment" — links the media item to a parent post |
| `status` | Attachment status |
| `slug`, `date`, `date_gmt`, `author`, `comment_status`, `ping_status`, `meta`, `template` | Same general shape as Posts |

**Create note:** The official reference page's schema/body-field listing does **not** spell out the required upload headers (`Content-Disposition: attachment; filename="..."` and `Content-Type: <mime>`) or that the file itself is sent as the raw binary POST body rather than as one of the named JSON fields above — this is standard WP REST media-upload behavior but was **NOT VERIFIED as explicit prose** on this specific reference page during this check. If uploading raw binary directly to `/wp/v2/media` rather than through an MCP wrapper, agents should test against a real WordPress instance or consult a supplementary source for the header requirements.

**Delete behavior:** `DELETE /wp/v2/media/<id>` — same documented `force` parameter as Posts/Pages: "Whether to bypass Trash and force deletion." The reference page does **not** state that media items are exempt from Trash or must always be force-deleted; this common claim about media (that attachments can't be trashed) is **NOT VERIFIED** from the official Media reference page or a corresponding Code Reference page for this project — do not assume `force=true` is mandatory for media without testing against the live site.

**Gotchas:**

- Default list `status` is `inherit`, not `publish` — different from Posts/Pages, because attachments "inherit" their published state from their parent post in the WP data model.
- **Check the project's `CLAUDE.md` for a media-routing override before uploading.** Some projects have a convention that certain asset types (e.g. processed portfolio photos) must bypass `/wp/v2/media` (and any MCP media-upload tool) entirely and instead go to an external store (CDN/blob storage), with only the resulting URL referenced in post content. Absent such a documented rule, use this endpoint normally for cases where the media library genuinely needs the asset (e.g. a featured image required by the theme).
- `alt_text`, `caption`, `description`, `title` follow the same rendered/raw object pattern as post `title`/`content`/`excerpt` — write via the raw field in `edit` context.
- `post` (not `parent`) is the field name that associates a media item with the post/page it belongs to.

---

## Comments

**Base route:** `/wp/v2/comments`
**Official doc:** https://developer.wordpress.org/rest-api/reference/comments/

| Method | Route | Description |
|---|---|---|
| GET | /wp/v2/comments | List comments |
| POST | /wp/v2/comments | Create a comment |
| GET | /wp/v2/comments/<id> | Retrieve a comment |
| POST | /wp/v2/comments/<id> | Update a comment |
| DELETE | /wp/v2/comments/<id> | Delete a comment |

**Key list/retrieve parameters:**

| Name | Type | Default | What it does |
|---|---|---|---|
| `context` | string | `view` | `view`, `embed`, `edit` |
| `page` | integer | `1` | Current page of the collection |
| `per_page` | integer | `10` | Max items to return |
| `search` | string | — | Limit results matching a string |
| `status` | string | `approve` | "Limit result set to comments assigned a specific status. Requires authorization." |
| `post` | integer | — | Limit to comments on specific post ID(s) |
| `author` | integer | — | "Limit result set to comments assigned to specific user IDs. Requires authorization." |
| `author_email` | string | — | Limit to comments from a specific author email. Requires authorization |
| `parent` | integer | — | Limit to comments with a specific parent comment ID |
| `orderby` | string | `date_gmt` | `date`, `date_gmt`, `id`, `include`, `post`, `parent`, `type` |
| `order` | string | `desc` | `asc` or `desc` |
| `password` | string | — | Password for the parent post, if it's password protected |

**Key create/update body fields:**

| Field | Notes |
|---|---|
| `author` | User ID, if the author is a registered user |
| `author_name` | Display name for the comment author |
| `author_email` | Email of the comment author |
| `author_url` | URL of the comment author |
| `content` | The comment content (object, rendered/raw shape as with posts) |
| `post` | ID of the associated post |
| `parent` | ID of the parent comment (for threaded replies) |
| `status` | Comment status (e.g. `approve`, `hold`, `spam`, `trash` — exact enum not itemized on this reference page) |
| `date` / `date_gmt` | Publish date |
| `meta` | Meta fields |

**Delete behavior:** `DELETE /wp/v2/comments/<id>` — arguments are `id`, `force` ("Whether to bypass Trash and force deletion"), and `password` (for a password-protected parent post). Per the official reference: **"The `force` parameter controls whether deletion moves the comment to trash or permanently removes it immediately."** Same trash-by-default / force-for-permanent pattern as Posts and Pages.

**Gotchas:**

- Default `status` filter is `approve` — pending/spam/trash comments won't appear in a plain list call unless `status` is explicitly requested (and the caller is authorized).
- Several list filters (`status`, `author`, `author_email`) are explicitly marked "Requires authorization" in the docs — anonymous requests will get a permission error or be ignored for these, not silently return unfiltered/all results.
- `content` again follows the object `{rendered, raw}` shape — same caveat as Posts applies (raw only in `edit` context with proper auth).

---

## Custom Post Types

**Official docs consulted:**
- https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-rest-api-support-for-custom-content-types/
- https://developer.wordpress.org/rest-api/reference/post-types/ (for discovering registered types, see above)

Custom post types are not exposed via REST by default. A post type is registered in PHP via `register_post_type()`; to give it a REST route, the registration arguments must include:

| Argument | Purpose |
|---|---|
| `show_in_rest` | Must be set to `true`. Per the official docs: setting this to `true` "will add a route in the `wp/v2` namespace." Without it, the post type has no REST presence at all. |
| `rest_base` | Optional. Customizes the URL segment. If omitted, it defaults to the post type's registered name/slug. Official example: setting `rest_base` to `books` produces `wp-json/wp/v2/books` instead of the default `wp-json/wp/v2/book`. |
| `rest_namespace` | Optional. Defaults to `wp/v2`. |
| `rest_controller_class` | Optional. The PHP class handling REST requests for this type, must extend `WP_REST_Controller`. Defaults to `WP_REST_Posts_Controller`. A custom controller class typically means the type's behavior may diverge from the standard Posts-like CRUD/schema conventions documented above. |

**Route formation:** the resulting collection route follows the pattern `/{rest_namespace}/{rest_base}` — normally `/wp/v2/{rest_base}`. Once registered this way, the type gets the standard collection/single-item verbs (GET list, POST create, GET/POST/DELETE by ID) via the default `WP_REST_Posts_Controller`, i.e. it behaves like Posts/Pages above (title/content/excerpt as rendered/raw objects, `status` field, trash-by-default delete with `force` to bypass, etc.), unless a custom controller changes that.

**Official example (from the docs):**

```php
add_action( 'init', 'my_book_cpt' );
function my_book_cpt() {
    $args = array(
        'public'       => true,
        'show_in_rest' => true,
        'label'        => 'Books',
    );
    register_post_type( 'book', $args );
}
```

This produces `GET /wp/v2/books` (rest_base defaults to the post type name `book`... — note the docs' own example calls out that an explicit `rest_base` of `books` is needed to get the plural route `wp/v2/books`; without it, the default route uses the singular type name, e.g. `wp/v2/book`).

**Working with any project's custom post types:** a custom post type must have `show_in_rest: true` (and ideally an explicit `rest_base`) before any agent can read/write it through `/wp/v2/<rest_base>`. Use `GET /wp/v2/types` (see Post Types section above) to confirm a custom type's exact `rest_base` and `rest_namespace` before constructing calls to it — do not assume the route matches the type's internal slug. Check `CLAUDE.md` for whether this project has registered any custom post types worth knowing about upfront.

**Gotchas:**

- A post type existing in WP admin does **not** mean it's REST-accessible — always check `show_in_rest` (indirectly, by calling `GET /wp/v2/types` and seeing if it's listed, or by testing the assumed route).
- The route's `rest_base` may differ from the post type slug — always confirm via `GET /wp/v2/types/<slug>` rather than guessing pluralization.
- If a custom `rest_controller_class` is used instead of the default `WP_REST_Posts_Controller`, none of the standard Posts-like schema/behavior documented above (rendered/raw objects, trash-by-default delete, etc.) is guaranteed — that would need to be separately verified against whatever custom controller is deployed.
