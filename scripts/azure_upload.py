#!/usr/bin/env python3
"""
Upload a local directory of files to an Azure Blob Storage container, mirroring
relative paths 1:1 (per CLAUDE.md's medias/<container-kind>/<path> -> <container>
blob <path> convention).

Reads auth from .secret/ms_azure_credentials.json (SAS token, connection string,
or account key - whichever is populated). Never prints the credential itself.

Usage:
    python3 azure_upload.py <local_dir> <container> <blob_prefix>

Example:
    python3 azure_upload.py medias/images/OPP-20241000105 ci-images OPP-20241000105

Prints a JSON object {"uploaded": [{"filename": ..., "url": ...}, ...], "errors": [...]}
to stdout. Never echoes credential values.
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import client_config

CRED_PATH = client_config.path(client_config.load(), "azure", "credentials")


def load_credentials():
    with open(CRED_PATH, "r") as f:
        return json.load(f)


def parse_connection_string(cs):
    parts = dict(p.split("=", 1) for p in cs.split(";") if "=" in p)
    return parts.get("AccountName"), parts.get("AccountKey"), parts.get("EndpointSuffix", "core.windows.net")


def sign_shared_key(method, account_name, account_key, url_path, query_params, headers, content_length):
    """Build the Authorization header for Azure Shared Key Lite/Full (Blob service)."""
    key = base64.b64decode(account_key)

    def canon_headers():
        ms_headers = {k.lower(): v for k, v in headers.items() if k.lower().startswith("x-ms-")}
        lines = []
        for k in sorted(ms_headers):
            lines.append(f"{k}:{ms_headers[k]}")
        return "\n".join(lines)

    def canon_resource():
        # url_path must already be the percent-encoded path actually used in the request
        res = f"/{account_name}{url_path}"
        if query_params:
            for k in sorted(query_params):
                res += f"\n{k}:{query_params[k]}"
        return res

    content_encoding = headers.get("Content-Encoding", "")
    content_language = headers.get("Content-Language", "")
    content_type = headers.get("Content-Type", "")
    content_md5 = headers.get("Content-MD5", "")
    # Date field in the signature string is empty when x-ms-date is used instead
    # of a literal Date header (this request never sends a literal Date header).
    date = ""
    if_modified_since = headers.get("If-Modified-Since", "")
    if_match = headers.get("If-Match", "")
    if_none_match = headers.get("If-None-Match", "")
    if_unmodified_since = headers.get("If-Unmodified-Since", "")
    ms_range = headers.get("Range", "")

    string_to_sign = "\n".join([
        method,
        content_encoding,
        content_language,
        str(content_length) if content_length else "",
        content_md5,
        content_type,
        date,
        if_modified_since,
        if_match,
        if_none_match,
        if_unmodified_since,
        ms_range,
        canon_headers(),
        canon_resource(),
    ])

    signature = base64.b64encode(hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).digest()).decode()
    return f"SharedKey {account_name}:{signature}"


def encode_path_segment(seg):
    # percent-encode each path segment, preserving "/" separators
    return urllib.parse.quote(seg, safe="")


def upload_blob(endpoint, account_name, account_key, sas_token, container, blob_path, local_file):
    encoded_blob_path = "/".join(encode_path_segment(p) for p in blob_path.split("/"))
    url_path = f"/{container}/{encoded_blob_path}"
    url = f"{endpoint}{url_path}"

    with open(local_file, "rb") as f:
        data = f.read()

    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    ext = os.path.splitext(local_file)[1].lower()
    content_type = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp",
    }.get(ext, "application/octet-stream")

    headers = {
        "x-ms-blob-type": "BlockBlob",
        "x-ms-version": "2021-08-06",
        "x-ms-date": date_str,
        "Content-Type": content_type,
        "Content-Length": str(len(data)),
    }

    if sas_token:
        full_url = url + ("?" if "?" not in url else "&") + sas_token.lstrip("?")
    else:
        full_url = url
        # Pass the FULL header set (not just x-ms-*) - sign_shared_key needs
        # Content-Type/Content-Length/etc. too; it does its own x-ms-* filtering
        # internally for CanonicalizedHeaders. Pre-filtering here previously
        # caused Content-Type to always be signed as empty while the real
        # request sent "image/jpeg" etc., silently breaking every signature.
        auth = sign_shared_key("PUT", account_name, account_key, url_path, {}, headers, len(data))
        headers["Authorization"] = auth

    req = urllib.request.Request(full_url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{e.code} {e.reason}: {body}") from None
    return f"{endpoint}{url_path}"


def ensure_public_access(endpoint, account_name, account_key, sas_token, container):
    """Best-effort: set container-level public blob read access if not already set."""
    if sas_token:
        return  # SAS tokens typically can't change container ACLs; skip silently
    url_path = f"/{container}"
    query = {"restype": "container", "comp": "acl"}
    query_str = "&".join(f"{k}={v}" for k, v in sorted(query.items()))
    full_url = f"{endpoint}{url_path}?{query_str}"
    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    headers = {
        "x-ms-blob-public-access": "blob",
        "x-ms-version": "2021-08-06",
        "x-ms-date": date_str,
    }
    auth = sign_shared_key("PUT", account_name, account_key, url_path, query, headers, 0)
    headers["Authorization"] = auth
    headers["Content-Length"] = "0"
    req = urllib.request.Request(full_url, data=b"", method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except Exception:
        pass  # non-fatal; container may already be configured, or SAS/key lacks ACL rights


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"error": "usage: azure_upload.py <local_dir> <container> <blob_prefix>"}))
        sys.exit(1)

    local_dir, container, blob_prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    creds = load_credentials()

    sas_token = creds.get("sasToken") or None
    conn_str = creds.get("connectionString") or None
    account_name = creds.get("accountName") or None
    account_key = creds.get("accountKey") or None
    endpoint = creds.get("blobEndpoint") or None

    # Prefer connectionString when present - it's the most recently/explicitly
    # provided credential, and may carry a newer key than stale accountName/accountKey
    # fields sitting alongside it in the same file.
    if conn_str:
        cs_account_name, cs_account_key, suffix = parse_connection_string(conn_str)
        if cs_account_name and cs_account_key:
            account_name, account_key = cs_account_name, cs_account_key
            if not endpoint:
                endpoint = f"https://{account_name}.blob.{suffix}"

    if not endpoint and account_name:
        endpoint = f"https://{account_name}.blob.core.windows.net"

    if not endpoint:
        print(json.dumps({"error": "could not resolve blob endpoint from credentials"}))
        sys.exit(1)

    if not sas_token and not account_key:
        print(json.dumps({"error": "no usable auth method found (sasToken/accountKey/connectionString all empty)"}))
        sys.exit(1)

    if account_key and not account_name:
        print(json.dumps({"error": "accountKey present but accountName missing"}))
        sys.exit(1)

    if account_key:
        ensure_public_access(endpoint, account_name, account_key, sas_token, container)

    uploaded, errors = [], []
    for fname in sorted(os.listdir(local_dir)):
        fpath = os.path.join(local_dir, fname)
        if not os.path.isfile(fpath) or fname.startswith("."):
            continue
        blob_path = f"{blob_prefix}/{fname}"
        try:
            url = upload_blob(endpoint, account_name, account_key, sas_token, container, blob_path, fpath)
            uploaded.append({"filename": fname, "url": url})
        except Exception as e:
            errors.append({"filename": fname, "error": str(e)})

    print(json.dumps({"uploaded": uploaded, "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
