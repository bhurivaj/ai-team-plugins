"""HMAC-signed tokens (login cookie, auth-flow cookie). Stdlib only."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json

FRESH_AUTH_S = 600  # a security-room change needs an Entra sign-in this recent


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _mac(body: str, secret: bytes) -> bytes:
    return hmac.new(secret, body.encode(), hashlib.sha256).digest()


def sign(payload: dict, secret: bytes, ttl_s: int, now: float) -> str:
    body = _b64(json.dumps({**payload, "exp": now + ttl_s}, separators=(",", ":")).encode())
    return body + "." + _b64(_mac(body, secret))


def verify(token: str, secret: bytes, now: float) -> dict | None:
    try:
        body, mac = token.split(".")
        if not hmac.compare_digest(_unb64(mac), _mac(body, secret)):
            return None
        data = json.loads(_unb64(body))
        if not isinstance(data, dict) or not now < data["exp"]:
            return None
        return data
    except Exception:  # any malformed input -> None, never raise
        return None
