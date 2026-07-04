from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
import urllib.error
import urllib.request
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Try to import bcrypt, fallback to pure python if not available
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# Database configuration from environment
DB_HOST = os.environ.get("POSTGRES_HOST", "postgres")
DB_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
DB_NAME = os.environ.get("POSTGRES_DB", "novel_os")
DB_USER = os.environ.get("POSTGRES_USER", "novel_os")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

DEFAULT_MCP_URL = os.environ.get("NOVEL_OS_MCP_URL", "http://novel-os-mcp:8787/mcp")
# Service token for Web backend to call MCP (set in .env)
MCP_SERVICE_TOKEN = os.environ.get("NOVEL_OS_MCP_SERVICE_TOKEN", "")
HOST = os.environ.get("NOVEL_OS_WEB_HOST", "0.0.0.0")
PORT = int(os.environ.get("NOVEL_OS_WEB_PORT", "8790"))
DATA_DIR = Path(os.environ.get("NOVEL_OS_WEB_DATA_DIR", "/app/data"))
SECRET_FILE = DATA_DIR / "session.secret"
INDEX = Path(__file__).with_name("index.html")
SESSION_COOKIE = "novel_os_web_session"
SESSION_TTL_SECONDS = int(os.environ.get("NOVEL_OS_WEB_SESSION_TTL_SECONDS", str(7 * 24 * 3600)))


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def parse_mcp_response(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    data_lines = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
    if data_lines:
        return json.loads("\n".join(data_lines))
    raise RuntimeError(f"Unrecognized MCP response: {text[:300]}")


def session_secret() -> bytes:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SECRET_FILE.exists():
        return SECRET_FILE.read_bytes()
    secret = secrets.token_bytes(32)
    SECRET_FILE.write_bytes(secret)
    return secret


# Local storage for MCP settings (not in database)
MCP_SETTINGS_FILE = DATA_DIR / "mcp_settings.json"

def load_mcp_settings() -> dict[str, Any]:
    """Load MCP settings from local file."""
    if not MCP_SETTINGS_FILE.exists():
        return {}
    return json.loads(MCP_SETTINGS_FILE.read_text(encoding="utf-8"))


def save_mcp_settings(settings: dict[str, Any]) -> None:
    """Save MCP settings to local file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MCP_SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(MCP_SETTINGS_FILE)


def get_user_mcp_settings(username: str) -> dict[str, Any]:
    """Get MCP settings for a user."""
    settings = load_mcp_settings()
    return settings.get(username, {})


def set_user_mcp_settings(username: str, mcp_url: str | None = None, mcp_token: str | None = None) -> None:
    """Set MCP settings for a user."""
    settings = load_mcp_settings()
    if username not in settings:
        settings[username] = {}
    if mcp_url is not None:
        settings[username]["mcp_url"] = mcp_url
    if mcp_token is not None:
        settings[username]["mcp_token"] = mcp_token
    save_mcp_settings(settings)


def hash_password(password: str) -> str:
    """Hash password using bcrypt-compatible format (using pbkdf2 for consistency)."""
    salt_bytes = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    return "pbkdf2_sha256$200000$%s$%s" % (
        base64.urlsafe_b64encode(salt_bytes).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        method, rounds, salt, digest = stored.split("$", 3)
        if method != "pbkdf2_sha256" or rounds != "200000":
            return False
        expected = hash_password(password, salt).split("$", 3)[3]
        return hmac.compare_digest(expected, digest)
    except Exception:
        return False


def sign_session(username: str) -> str:
    payload = {"username": username, "exp": int(time.time()) + SESSION_TTL_SECONDS}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    sig = hmac.new(session_secret(), raw.encode("ascii"), hashlib.sha256).hexdigest()
    return raw + "." + sig


def verify_session(value: str | None) -> str | None:
    if not value or "." not in value:
        return None
    raw, sig = value.rsplit(".", 1)
    expected = hmac.new(session_secret(), raw.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    username = payload.get("username")
    return username if isinstance(username, str) else None


class McpClient:
    def __init__(self, url: str, token: str | None):
        self.url = url
        self.token = token
        self.session_id: str | None = None

    def post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["X-Novel-OS-Token"] = self.token
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sid = resp.headers.get("mcp-session-id")
                if sid:
                    self.session_id = sid
                return parse_mcp_response(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MCP HTTP {exc.code}: {detail}") from exc

    def initialize(self) -> None:
        response = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "novel-os-web", "version": "0.2.0"},
                },
            }
        )
        if response and response.get("error"):
            raise RuntimeError(str(response["error"]))
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if not self.session_id:
            self.initialize()
        response = self.post(
            {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if response is None:
            return None
        if response.get("error"):
            raise RuntimeError(str(response["error"]))
        result = response.get("result")
        if isinstance(result, dict) and "content" in result:
            return decode_tool_content(result["content"])
        return result


def decode_tool_content(content: Any) -> Any:
    if not isinstance(content, list) or not content:
        return content
    first = content[0]
    if isinstance(first, dict) and first.get("type") == "text":
        text = first.get("text", "")
        if text.strip().startswith("Error calling tool"):
            raise RuntimeError(text.strip())
        try:
            value = json.loads(text)
            if isinstance(value, str) and value.strip().startswith("Error calling tool"):
                raise RuntimeError(value.strip())
            if isinstance(value, str) and value.strip().startswith(("{", "[")):
                return json.loads(value)
            return value
        except json.JSONDecodeError:
            return text
    return content


class Handler(BaseHTTPRequestHandler):
    server_version = "NovelOSWeb/0.2"

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, status: int, payload: dict[str, Any], cookie_header: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie_header:
            self.send_header("Set-Cookie", cookie_header)
        self.end_headers()
        self.wfile.write(body)

    def cookie_username(self) -> str | None:
        header = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(header)
        morsel = jar.get(SESSION_COOKIE)
        return verify_session(morsel.value if morsel else None)

    def get_user_from_db(self, username: str) -> dict[str, Any] | None:
        """Get user from PostgreSQL database."""
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT username, nickname as display_name, status, password_hash, 
                       role, is_active, created_at
                       FROM users WHERE username = %s AND status = 'active'""",
                    (username,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"DB error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def create_user_in_db(self, username: str, password_hash: str, **kwargs) -> bool:
        """Create or update user in database."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO users (username, display_name, email, status, password_hash)
                       VALUES (%s, %s, %s, 'active', %s)
                       ON CONFLICT (username) DO UPDATE SET
                           display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                           email = COALESCE(EXCLUDED.email, users.email),
                           password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
                           updated_at = NOW()
                       RETURNING id""",
                    (username, kwargs.get('display_name', username), 
                     kwargs.get('email'), password_hash)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"DB error creating user: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_user_in_db(self, username: str, **fields) -> bool:
        """Update user fields in database."""
        if not fields:
            return True
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Build dynamic update query
                set_parts = []
                values = []
                for key, value in fields.items():
                    set_parts.append(f"{key} = %s")
                    values.append(value)
                values.append(username)
                
                query = f"""UPDATE users SET {', '.join(set_parts)}, updated_at = NOW() 
                           WHERE username = %s"""
                cur.execute(query, values)
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"DB error updating user: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def check_users_exist(self) -> bool:
        """Check if any users exist in database."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
                count = cur.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"DB error checking users: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def current_user(self) -> tuple[str, dict[str, Any]] | None:
        username = self.cookie_username()
        if not username:
            return None
        user = self.get_user_from_db(username)
        if not user:
            return None
        # Merge with local MCP settings
        mcp_settings = get_user_mcp_settings(username)
        user["mcp_url"] = mcp_settings.get("mcp_url")
        user["mcp_token"] = mcp_settings.get("mcp_token")
        return username, user

    def do_GET(self) -> None:
        # Static file serving
        if self.path.startswith(("/js/", "/css/")):
            self.serve_static()
            return
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "default_mcp_url": DEFAULT_MCP_URL})
            return
        if self.path == "/api/me":
            current = self.current_user()
            current_user_data = current[1] if current else {}
            self.send_json(
                200,
                {
                    "setup_required": not self.check_users_exist(),
                    "authenticated": current is not None,
                    "username": current[0] if current else None,
                    "default_mcp_url": DEFAULT_MCP_URL,
                    "mcp_url": current_user_data.get("mcp_url") if current else None,
                    "has_mcp_token": bool(current_user_data.get("mcp_token")) if current else False,
                },
            )
            return
        body = INDEX.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/setup":
                self.handle_setup()
                return
            if self.path == "/api/login":
                self.handle_login()
                return
            if self.path == "/api/logout":
                expired = f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
                self.send_json(200, {"ok": True}, expired)
                return
            if self.path == "/api/account":
                self.handle_account()
                return
            if self.path == "/api/tool":
                self.handle_tool()
                return
            self.send_json(404, {"ok": False, "error": "not found"})
        except Exception as exc:
            self.send_json(400, {"ok": False, "error": str(exc)})

    def handle_setup(self) -> None:
        if self.check_users_exist():
            self.send_json(403, {"ok": False, "error": "setup already completed"})
            return
        payload = self.read_json()
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        token = str(payload.get("token") or "").strip()
        if not username or not password or not token:
            self.send_json(400, {"ok": False, "error": "username, password, and token are required"})
            return
        
        # Create user in database (only auth info)
        password_hash = hash_password(password)
        if not self.create_user_in_db(username, password_hash):
            self.send_json(500, {"ok": False, "error": "failed to create user"})
            return
        
        # Save MCP settings locally
        set_user_mcp_settings(username, payload.get("mcp_url") or DEFAULT_MCP_URL, token)
        
        self.send_login(username)

    def handle_login(self) -> None:
        payload = self.read_json()
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        
        user = self.get_user_from_db(username)
        if not user:
            # Auto-create user with default password if not exists
            # This handles migration from old local users.json to PostgreSQL
            if self.create_user_in_db(username, hash_password("123456")):
                user = self.get_user_from_db(username)
            if not user:
                self.send_json(401, {"ok": False, "error": "invalid username or password"})
                return
        
        # Check password - support both bcrypt (from auth.py) and pbkdf2 (from old server)
        stored_hash = str(user.get("password_hash") or "")
        if not self._verify_password_any(password, stored_hash):
            self.send_json(401, {"ok": False, "error": "invalid username or password"})
            return
        self.send_login(username)

    def _verify_password_any(self, password: str, stored: str) -> bool:
        """Verify password supporting both pbkdf2 (legacy) and bcrypt (new) formats."""
        if not stored:
            return False
        # Try pbkdf2 format (legacy)
        if stored.startswith("pbkdf2_sha256$"):
            return verify_password(password, stored)
        # Try bcrypt format (starts with $2b$)
        if stored.startswith("$2b$") and HAS_BCRYPT:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored.encode("ascii"))
            except Exception:
                return False
        return False

    def send_login(self, username: str) -> None:
        cookie_header = f"{SESSION_COOKIE}={sign_session(username)}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL_SECONDS}"
        self.send_json(200, {"ok": True, "username": username}, cookie_header)

    def handle_account(self) -> None:
        current = self.current_user()
        if current is None:
            self.send_json(401, {"ok": False, "error": "login required"})
            return
        username, user = current
        payload = self.read_json()
        
        # Handle password change
        old_password = payload.get("old_password")
        new_password = payload.get("new_password")
        if old_password is not None and new_password is not None:
            if not verify_password(str(old_password), str(user.get("password_hash") or "")):
                self.send_json(403, {"ok": False, "error": "current password is incorrect"})
                return
            new_hash = hash_password(str(new_password))
            if self.update_user_in_db(username, password_hash=new_hash):
                self.send_json(200, {"ok": True, "message": "Password changed successfully"})
            else:
                self.send_json(500, {"ok": False, "error": "failed to update password"})
            return
        
        # Handle MCP settings update (stored locally, not in database)
        mcp_url = str(payload.get("mcp_url") or "").strip()
        mcp_token = str(payload.get("mcp_token") or "").strip()
        if mcp_url or mcp_token:
            set_user_mcp_settings(username, mcp_url or None, mcp_token or None)
            # Get updated settings
            updated_settings = get_user_mcp_settings(username)
            self.send_json(200, {
                "ok": True, 
                "mcp_url": updated_settings.get("mcp_url"), 
                "has_mcp_token": bool(updated_settings.get("mcp_token"))
            })
        else:
            self.send_json(200, {"ok": True, "mcp_url": user.get("mcp_url"), 
                                "has_mcp_token": bool(user.get("mcp_token"))})

    def handle_tool(self) -> None:
        current = self.current_user()
        if current is None:
            self.send_json(401, {"ok": False, "error": "login required"})
            return
        _username, user = current
        payload = self.read_json()
        tool = payload["tool"]
        arguments = payload.get("arguments") or {}
        url = payload.get("mcp_url") or user.get("mcp_url") or DEFAULT_MCP_URL
        # Use service token if available, otherwise fall back to user's token
        token = MCP_SERVICE_TOKEN or user.get("mcp_token")
        if not token:
            self.send_json(500, {"ok": False, "error": "No MCP token available. Please configure MCP_SERVICE_TOKEN in .env"})
            return
        result = McpClient(url, token).call_tool(tool, arguments)
        self.send_json(200, {"ok": True, "result": result})

    def serve_static(self) -> None:
        path = self.path.lstrip("/")
        filepath = Path(os.environ.get("NOVEL_OS_WEB_ROOT", Path(__file__).parent)) / path
        filepath = filepath.resolve()
        if not str(filepath).startswith(str(Path(__file__).parent.resolve())):
            self.send_json(403, {"error": "forbidden"})
            return
        if filepath.exists() and filepath.is_file():
            body = filepath.read_bytes()
            self.send_response(200)
            if path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
            elif path.endswith(".css"):
                self.send_header("Content-Type", "text/css; charset=utf-8")
            else:
                self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(fmt % args)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"novel-os-web listening on {HOST}:{PORT}")
    httpd.serve_forever()
