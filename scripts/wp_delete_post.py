#!/usr/bin/env python3
"""
Delete (trash by default, permanent with --force) a WordPress post/page/custom-post-type
item by ID via direct REST, using Basic Auth credentials from
.secret/claudeus-wp-mcp/wp-sites.json. Exists because claudeus-wp-mcp is disabled in this
session (.claude/settings.local.json -> disabledMcpjsonServers) and CLAUDE.md explicitly
says to fall back to direct REST with the same credentials when the MCP tool set is
insufficient/unavailable.

Usage:
    python3 wp_delete_post.py <post_id> [--type posts|pages|vework-portfolio|...] [--force]

Without --force, WordPress moves the item to Trash (recoverable). --force permanently deletes.
Prints one JSON line to stdout: {"id":..., "status": "trashed"|"deleted", "link": ...}
"""
import base64
import json
import sys
import urllib.error
import urllib.request

import client_config


def load_credentials():
    return client_config.wp_site(client_config.load())


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: wp_delete_post.py <post_id> [--type posts] [--force]"}))
        sys.exit(1)

    post_id = sys.argv[1]
    post_type = "posts"
    force = False
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            post_type = args[i + 1]
            i += 2
        elif args[i] == "--force":
            force = True
            i += 1
        else:
            i += 1

    site = load_credentials()
    base_url = site["URL"].rstrip("/")
    user = site["USER"]
    password = site["PASS"]

    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    url = f"{base_url}/wp-json/wp/v2/{post_type}/{post_id}"
    if force:
        url += "?force=true"

    req = urllib.request.Request(url, method="DELETE", headers={"Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"{e.code} {e.reason}", "body": e.read().decode(errors="replace")[:500]}))
        sys.exit(1)

    status = body.get("status")
    print(json.dumps({
        "id": body.get("id"),
        "status": "deleted" if force else "trashed",
        "wp_status": status,
        "link": body.get("link"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
