#!/usr/bin/env python3
"""
Upload a local directory of files to a SharePoint document library via
Microsoft Graph, entirely within this process (no file content ever passes
through the model's context - that's the whole point: inlining base64 through
an LLM tool call costs on the order of millions of tokens per file, confirmed
empirically on 2026-09-20; a standalone script reading bytes off disk costs
nothing).

Auth: delegated OAuth2 device-code flow against the public, admin-consent-free
"Microsoft Graph Command Line Tools" first-party app (client_id
14d82eec-204b-4c2f-b7e8-296a70dab67e - the same one the bundled `msgraph`
skill CLI uses by default). No Azure AD app registration needed. First run
requires the user to open a URL and enter a code once; the resulting refresh
token is cached in .secret/msgraph_token_cache.json so subsequent runs are
silent until the refresh token itself expires (Microsoft default ~90 days of
inactivity).

Usage:
    python3 sharepoint_upload.py <local_dir> <site> <library_relative_path>

Example:
    python3 sharepoint_upload.py medias/images/OPP-20241000105 \\
        "catice.sharepoint.com:/sites/Marketing-Marketing-CI" \\
        "Asset_Library/Portfolios/OPP-20241000105"

Prints one JSON line to stdout: {"uploaded":[{"filename","webUrl"},...],"errors":[...]}
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph Command Line Tools (public, first-party)
SCOPES = "Sites.ReadWrite.All offline_access"
AUTHORITY = "https://login.microsoftonline.com/organizations"
GRAPH = "https://graph.microsoft.com/v1.0"

import client_config

CACHE_PATH = client_config.path(client_config.load(), "sharepoint", "token_cache")

CHUNK_UPLOAD_THRESHOLD = 4 * 1024 * 1024  # 4 MB - Graph's simple-upload limit


def _post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)
    os.chmod(CACHE_PATH, 0o600)


def _device_code_signin():
    resp = _post_form(f"{AUTHORITY}/oauth2/v2.0/devicecode",
                       {"client_id": CLIENT_ID, "scope": SCOPES})
    if "device_code" not in resp:
        raise RuntimeError(f"device code request failed: {resp}")
    print(resp["message"], file=sys.stderr)
    interval = resp.get("interval", 5)
    expires_in = resp.get("expires_in", 900)
    print(f"(code valid for {expires_in}s, polling every {interval}s)", file=sys.stderr)
    expires_at = time.time() + expires_in
    while time.time() < expires_at:
        time.sleep(interval)
        try:
            token_resp = _post_form(f"{AUTHORITY}/oauth2/v2.0/token", {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "client_id": CLIENT_ID,
                "device_code": resp["device_code"],
            })
        except (urllib.error.URLError, OSError) as e:
            # Transient network blip (e.g. connection reset) - the device code is
            # still valid until expires_at, so just retry on the next tick instead
            # of aborting a 15-minute wait over one dropped connection.
            print(f"transient network error while polling ({e}), retrying...", file=sys.stderr)
            continue
        if "access_token" in token_resp:
            return token_resp
        err = token_resp.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        raise RuntimeError(f"device code sign-in failed: {token_resp}")
    raise RuntimeError("device code expired before user completed sign-in")


def _refresh(refresh_token):
    return _post_form(f"{AUTHORITY}/oauth2/v2.0/token", {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": SCOPES,
    })


def get_access_token():
    cache = _load_cache()
    if cache.get("refresh_token"):
        token_resp = _refresh(cache["refresh_token"])
        if "access_token" in token_resp:
            cache.update(token_resp)
            _save_cache(cache)
            return token_resp["access_token"]
        print(f"cached refresh token no longer valid ({token_resp.get('error')}), re-authenticating...", file=sys.stderr)
    token_resp = _device_code_signin()
    _save_cache(token_resp)
    return token_resp["access_token"]


def graph_get(token, path):
    req = urllib.request.Request(f"{GRAPH}/{path.lstrip('/')}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_drive_id(token, site):
    site_info = graph_get(token, f"sites/{site}")
    site_id = site_info["id"]
    drives = graph_get(token, f"sites/{site_id}/drives")
    # Default document library is usually named "Documents" and is first, but
    # be explicit rather than assuming index 0.
    for d in drives.get("value", []):
        if d.get("name") in ("Documents", "Shared Documents"):
            return d["id"]
    if drives.get("value"):
        return drives["value"][0]["id"]
    raise RuntimeError(f"no drives found for site {site}")


CONTENT_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".pdf": "application/pdf",
}


def upload_file(token, drive_id, remote_path, local_file):
    size = os.path.getsize(local_file)
    ext = os.path.splitext(local_file)[1].lower()
    content_type = CONTENT_TYPES.get(ext, "application/octet-stream")
    encoded_path = "/".join(urllib.parse.quote(p, safe="") for p in remote_path.split("/"))

    if size <= CHUNK_UPLOAD_THRESHOLD:
        with open(local_file, "rb") as f:
            data = f.read()
        req = urllib.request.Request(
            f"{GRAPH}/drives/{drive_id}/root:/{encoded_path}:/content",
            data=data, method="PUT",
            headers={"Authorization": f"Bearer {token}", "Content-Type": content_type},
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
        return result.get("webUrl")

    # Resumable upload session for files over the simple-upload limit.
    session_req = urllib.request.Request(
        f"{GRAPH}/drives/{drive_id}/root:/{encoded_path}:/createUploadSession",
        data=json.dumps({"item": {"@microsoft.graph.conflictBehavior": "replace"}}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(session_req) as resp:
        session = json.loads(resp.read().decode())
    upload_url = session["uploadUrl"]

    chunk_size = 5 * 1024 * 1024  # must be a multiple of 320 KiB
    with open(local_file, "rb") as f:
        offset = 0
        result = None
        while offset < size:
            chunk = f.read(chunk_size)
            end = offset + len(chunk) - 1
            chunk_req = urllib.request.Request(
                upload_url, data=chunk, method="PUT",
                headers={"Content-Length": str(len(chunk)),
                         "Content-Range": f"bytes {offset}-{end}/{size}"},
            )
            with urllib.request.urlopen(chunk_req) as resp:
                body = resp.read().decode()
                if body:
                    result = json.loads(body)
            offset += len(chunk)
    return result.get("webUrl") if result else None


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"error": "usage: sharepoint_upload.py <local_dir> <site> <library_relative_path>"}))
        sys.exit(1)

    local_dir, site, remote_prefix = sys.argv[1], sys.argv[2], sys.argv[3].strip("/")
    token = get_access_token()
    drive_id = get_drive_id(token, site)

    uploaded, errors = [], []
    for fname in sorted(os.listdir(local_dir)):
        fpath = os.path.join(local_dir, fname)
        if not os.path.isfile(fpath) or fname.startswith("."):
            continue
        try:
            web_url = upload_file(token, drive_id, f"{remote_prefix}/{fname}", fpath)
            uploaded.append({"filename": fname, "webUrl": web_url})
        except urllib.error.HTTPError as e:
            errors.append({"filename": fname, "error": f"{e.code} {e.reason}: {e.read().decode(errors='replace')[:500]}"})
        except Exception as e:
            errors.append({"filename": fname, "error": str(e)})

    print(json.dumps({"uploaded": uploaded, "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
