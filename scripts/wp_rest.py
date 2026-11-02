#!/usr/bin/env python3
"""
Generic authenticated WordPress REST call, using Basic Auth credentials from
.secret/claudeus-wp-mcp/wp-sites.json. Exists because claudeus-wp-mcp is disabled in this
session and CLAUDE.md says to fall back to direct REST with the same credentials when the
MCP tool set is insufficient/unavailable (e.g. elementor_library requires auth to list/read,
and there's no MCP tool for it at all).

Usage:
    python3 wp_rest.py <METHOD> <path> [--body '<json>'] [--query 'k=v&k2=v2']

<path> is relative to /wp-json/, e.g. wp/v2/elementor_library or wp/v2/posts/5977.

Prints the raw JSON response body to stdout. Never logs the credential itself.
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
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: wp_rest.py <METHOD> <path> [--body '<json>'] [--query 'k=v']"}))
        sys.exit(1)

    method = sys.argv[1].upper()
    path = sys.argv[2].lstrip("/")
    body = None
    query = None
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--body" and i + 1 < len(args):
            body = args[i + 1]
            i += 2
        elif args[i] == "--query" and i + 1 < len(args):
            query = args[i + 1]
            i += 2
        else:
            i += 1

    site = load_credentials()
    base_url = site["URL"].rstrip("/")
    auth = base64.b64encode(f"{site['USER']}:{site['PASS']}".encode()).decode()

    url = f"{base_url}/wp-json/{path}"
    if query:
        url += f"?{query}"

    headers = {"Authorization": f"Basic {auth}"}
    data = None
    if body is not None:
        data = body.encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            print(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"{e.code} {e.reason}", "body": e.read().decode(errors="replace")[:2000]}))
        sys.exit(1)


if __name__ == "__main__":
    main()
