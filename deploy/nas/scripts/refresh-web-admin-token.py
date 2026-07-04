#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_USERS = ROOT / "data" / "web" / "users.json"
MCP_URL = "http://novel-os-mcp:8787/mcp"


def load_env() -> dict[str, str]:
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key] = value.strip().strip("'\"")
    return env


def run_psql(sql: str, env: dict[str, str]) -> None:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "--username",
        env["POSTGRES_USER"],
        "--dbname",
        env["POSTGRES_DB"],
        "--set",
        "ON_ERROR_STOP=1",
        "--quiet",
        "--command",
        sql,
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    env = load_env()
    token = "nos_" + secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    sql = f"""
INSERT INTO users (username, display_name, status)
VALUES ('admin', 'Default Admin', 'active')
ON CONFLICT (username) DO UPDATE SET status = 'active';

INSERT INTO api_tokens (user_id, name, token_hash, scopes, expires_at)
SELECT id, 'web-console-admin', '{token_hash}', ARRAY['admin','read','write']::TEXT[], NULL
FROM users
WHERE username = 'admin';
"""
    run_psql(sql, env)

    users = json.loads(WEB_USERS.read_text(encoding="utf-8"))
    if "admin" in users:
        username = "admin"
    elif users:
        username = next(iter(users))
    else:
        raise SystemExit("No Web users found in data/web/users.json")
    users[username]["mcp_url"] = MCP_URL
    users[username]["mcp_token"] = token
    WEB_USERS.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated Web account '{username}' with a fresh admin MCP token.")


if __name__ == "__main__":
    main()
