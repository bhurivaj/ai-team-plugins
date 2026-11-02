---
name: asset-upload
description: Upload images/files for the current company to Azure Blob Storage and SharePoint with the shared scripts — staging folder, container and site from company.json, path conventions, and the auth gotchas. Use whenever an image or asset must be uploaded, re-uploaded, or its public URL found.
---

# Asset Upload (Azure Blob + SharePoint)

## Before you start
1. Read the company project's `company.json`: `prefix`, `azure.containers`, and the SharePoint site of the department you are working for (e.g. `marketing.sharepoint_site`; each department section names its own site). Run every command **from the company project root** — the scripts find `company.json` by walking up from the current directory and stop with an error otherwise.
2. Read the project's CLAUDE.md for its folder conventions (which SharePoint library path and which blob prefix each content type uses). This skill is the mechanics; the paths are the company's.
3. Never read or print `.secret/`.

## Default: upload to both
Unless the project's rules name an exception for that asset type, every upload goes to **both** destinations, under the same folder/slug in each:

```bash
python3 .claude/scripts/azure_upload.py <local_dir> <company.json azure.containers.images> "<blob_prefix>"
python3 .claude/scripts/sharepoint_upload.py <local_dir> "<department SharePoint site from company.json>" "<library/relative/path>"
```

- Both scripts upload a **whole directory**: stage only the files you mean to upload, under their final names, in a local folder under `medias/` (local `medias/images/<path>` mirrors blob `<path>` in the images container).
- **Embed the Azure CDN URL** in content; the SharePoint copy is the archive. A WordPress featured image / og:image is the exception — it must be a media-library attachment (`.claude/scripts/wp_media_upload.py <file> --alt "<alt>"`).
- Only touch this company's containers (its `prefix`, e.g. `ci-*` / `cm-*`). The storage account is shared between companies.

## Gotchas
- **Non-ASCII/space blob names:** the script percent-encodes the path and signs the encoded form. If you ever sign a request by hand, sign exactly the encoded path you send.
- **New container = private.** Anonymous reads 404 until blob-level public access is set; `azure_upload.py` ensures it, a hand-made container won't have it.
- **Soft delete is on (~7 days).** Undeleting a container does not restore its blobs; each blob needs its own undelete.
- **SharePoint token rotates on every `get_access_token()` call.** In your own Python, fetch it once per process and retry once on a 401 before concluding the credential is dead. `graph_get(token, path)` takes the token first and a path relative to the Graph root (`drives/{id}/root:/<path>:/children`).
- **First SharePoint run for a company** may need a device-code sign-in (the script prints the code); that's an interactive step for the user.

## Verify
The scripts print JSON with each file's URL and any errors. Fetch one Azure URL anonymously (`curl -sI`) and expect 200; report every error line, never just "uploaded".
