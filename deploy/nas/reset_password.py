import json
import base64
import hashlib
import secrets

PASSWORD = "${NAS_SSH_PASSWORD}"

salt_bytes = secrets.token_bytes(16)
digest = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode("utf-8"), salt_bytes, 200_000)
password_hash = "pbkdf2_sha256$200000$%s$%s" % (
    base64.urlsafe_b64encode(salt_bytes).decode("ascii"),
    base64.urlsafe_b64encode(digest).decode("ascii"),
)

users = {
    "admin": {
        "password_hash": password_hash,
        "mcp_url": "http://novel-os-mcp:8787/mcp",
        "mcp_token": "nos_f7jlgRC9oCiwKfNVbifnaZD03BJhR8F766Q9-_oNGO8",
        "role": "admin",
        "enabled": True,
        "created_at": 1782215047,
    }
}

with open("/opt/novel-os/data/web/users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

print("✅ 密码重置成功")