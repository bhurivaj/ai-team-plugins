"""
Per-client config loader shared by every script in this folder.

The scripts live in marketing-core and are reached through a `.claude/scripts` symlink in each
client project, so they must never resolve paths relative to their own file. Instead they find
the client project by walking up from the current directory to the nearest `client.json`
(falling back to $CLAUDE_PROJECT_DIR), and resolve every secret path relative to that project.
"""
import json
import os

CONFIG_NAME = "client.json"


def project_root():
    d = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(d, CONFIG_NAME)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isfile(os.path.join(env, CONFIG_NAME)):
        return env
    raise SystemExit(f"error: no {CONFIG_NAME} found above {os.getcwd()} - run from inside a client project")


def load():
    root = project_root()
    with open(os.path.join(root, CONFIG_NAME)) as f:
        cfg = json.load(f)
    cfg["_root"] = root
    return cfg


def path(cfg, *keys):
    """Resolve a config path value (relative to the client project root unless absolute)."""
    v = cfg
    for k in keys:
        v = v[k]
    return os.path.normpath(os.path.join(cfg["_root"], os.path.expanduser(v)))


def wp_site(cfg):
    with open(path(cfg, "wordpress", "credentials")) as f:
        sites = json.load(f)
    alias = cfg["wordpress"]["site_alias"]
    if alias not in sites:
        raise SystemExit(f"error: site alias '{alias}' not in wordpress credentials file")
    return sites[alias]
