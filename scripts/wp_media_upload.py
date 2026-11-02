#!/usr/bin/env python3
"""
Upload a single local image file to the WordPress media library (wp/v2/media) via a raw
binary POST + Content-Disposition header, using Basic Auth credentials from
.secret/claudeus-wp-mcp/wp-sites.json (same credentials as wp_rest.py).

This is deliberately narrow: per .claude/rules/knowledge-content-improvement-workflow.md
Phase C step 4, portfolio/blog images normally bypass the media library entirely (they live
on Azure Blob Storage / SharePoint) -- this script exists only for the one-file-per-post
featured-image exception, never for bulk content images.

Usage:
    python3 wp_media_upload.py <local_file> [--alt "<alt text>"] [--filename "<ascii-name.jpg>"]

Content-Disposition headers must be Latin-1, so a non-ASCII local filename (e.g. Thai) will
raise UnicodeEncodeError unless --filename supplies an ASCII-safe name to send instead (the
local file itself is read as-is; only the header/remote filename changes).

Prints the created attachment's JSON response to stdout (id, source_url, media_details, ...).
Never logs the credential itself.
"""
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

import client_config


def load_credentials():
    return client_config.wp_site(client_config.load())


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: wp_media_upload.py <local_file> [--alt '<alt text>']"}))
        sys.exit(1)

    local_file = sys.argv[1]
    alt_text = None
    filename_override = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--alt" and i + 1 < len(args):
            alt_text = args[i + 1]
            i += 2
        elif args[i] == "--filename" and i + 1 < len(args):
            filename_override = args[i + 1]
            i += 2
        else:
            i += 1

    if not os.path.isfile(local_file):
        print(json.dumps({"error": f"not a file: {local_file}"}))
        sys.exit(1)

    filename = filename_override or os.path.basename(local_file)
    try:
        filename.encode("latin-1")
    except UnicodeEncodeError:
        print(json.dumps({"error": "filename is not Latin-1 safe; pass --filename with an ASCII-safe name"}))
        sys.exit(1)
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    site = load_credentials()
    base_url = site["URL"].rstrip("/")
    auth = base64.b64encode(f"{site['USER']}:{site['PASS']}".encode()).decode()

    with open(local_file, "rb") as f:
        data = f.read()

    url = f"{base_url}/wp-json/wp/v2/media"
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": mime_type,
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"{e.code} {e.reason}", "body": e.read().decode(errors="replace")[:2000]}))
        sys.exit(1)

    if alt_text is not None:
        media_id = result["id"]
        patch_body = json.dumps({"alt_text": alt_text}).encode()
        patch_req = urllib.request.Request(
            f"{base_url}/wp-json/wp/v2/media/{media_id}",
            data=patch_body,
            method="POST",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(patch_req) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(json.dumps({"error": f"{e.code} {e.reason}", "body": e.read().decode(errors="replace")[:2000]}))
            sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
