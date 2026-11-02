"""Pure helpers for the Teams bot — no SDK imports, so they are unit-testable in CI."""
import json
import os
import tempfile
import threading


def parse_list(value):
    return {x.strip() for x in (value or "").split(",") if x.strip()}


def is_allowed(aad_object_id, allowlist):
    # Empty allowlist means nobody: Phase 0 is owner-only, never open by default.
    return bool(aad_object_id) and aad_object_id in allowlist


def base_conversation_id(conversation_id):
    # Channel threads look like "19:...@thread.tacv2;messageid=123"; the channel is the part before ";".
    return (conversation_id or "").split(";")[0]


def company_for(conversation_id, channel_map, default):
    return channel_map.get(base_conversation_id(conversation_id), default)


def split_message(text, limit=20000):
    """Split on paragraph boundaries so each Teams message stays under the size limit."""
    text = text or ""
    chunks, current = [], ""
    for para in text.split("\n\n"):
        while len(para) > limit:  # a single oversized paragraph is hard-cut
            if current:
                chunks.append(current)
                current = ""
            chunks.append(para[:limit])
            para = para[limit:]
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > limit:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current or not chunks:
        chunks.append(current)
    return chunks


class SessionStore:
    """Teams conversation id -> Claude session id, persisted as one JSON file."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()

    def _read(self):
        try:
            with open(self.path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get(self, conversation_id):
        return self._read().get(conversation_id)

    def set(self, conversation_id, session_id):
        with self._lock:
            data = self._read()
            data[conversation_id] = session_id
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path) or ".")
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
            os.replace(tmp, self.path)  # atomic: a crash never leaves a half-written file


def append_jsonl(path, record):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
