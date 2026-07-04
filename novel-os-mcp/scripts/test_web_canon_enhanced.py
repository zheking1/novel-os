import json
import sys
import time

import requests


WEB_BASE_URL = "http://127.0.0.1:8790"
USERNAME = "admin"
PASSWORD = "${NAS_SSH_PASSWORD}"
WORKSPACE = "default"
PROJECT = "default"


class WebTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.project_slug = None

    def login(self):
        response = self.session.post(
            f"{WEB_BASE_URL}/api/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Login failed: {data}")
        print(f"Logged in as {USERNAME}")

    def ensure_project(self):
        response = self.session.post(
            f"{WEB_BASE_URL}/api/tool",
            json={"tool": "project.list", "arguments": {"workspace": WORKSPACE}},
            timeout=10
        )
        data = response.json()
        if data.get("ok") and isinstance(data.get("result"), list) and len(data["result"]) > 0:
            self.project_slug = data["result"][0].get("slug")
            print(f"Found project: {self.project_slug}")
            return
        
        response = self.session.post(
            f"{WEB_BASE_URL}/api/tool",
            json={
                "tool": "project.create",
                "arguments": {
                    "workspace": WORKSPACE,
                    "slug": PROJECT,
                    "title": "Test Project",
                    "description": "Test project for canon docs"
                }
            },
            timeout=10
        )
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Failed to create project: {data}")
        self.project_slug = PROJECT
        print(f"Created project: {self.project_slug}")

    def call_tool(self, tool_name, arguments=None):
        response = self.session.post(
            f"{WEB_BASE_URL}/api/tool",
            json={"tool": tool_name, "arguments": arguments or {}},
            timeout=30
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise Exception(f"HTTP {response.status_code}: {error_detail}")
        return response.json()

    def run_test(self, name, test_func):
        result = {"name": name, "passed": False, "message": "", "duration": 0}
        start_time = time.time()
        
        try:
            test_func(result)
            result["passed"] = True
        except Exception as e:
            result["passed"] = False
            result["message"] = str(e)
        
        result["duration"] = time.time() - start_time
        self.results.append(result)
        return result

    def print_results(self):
        print("\n" + "=" * 70)
        print("Web Console - Canon Docs Enhancement Test Results")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"])
        
        for i, result in enumerate(self.results, 1):
            status = "[PASS]" if result["passed"] else "[FAIL]"
            duration = f"{result['duration']:.2f}s"
            print(f"[{i:2d}] {status}  {result['name']}  ({duration})")
            if not result["passed"] and result["message"]:
                print(f"     Error: {result['message']}")
        
        print("-" * 70)
        print(f"Total: {len(self.results)} tests, Passed: {passed}, Failed: {failed}")
        print(f"Total duration: {sum(r['duration'] for r in self.results):.2f}s")
        print("=" * 70)
        
        return failed == 0


def test_canon_create(suite, result):
    data = suite.call_tool("canon.doc.upsert", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "doc_type": "world",
        "key": "test_world_001",
        "title": "Test World Setting",
        "content": "This is a test world setting document for testing.",
        "status": "active",
        "review_status": "approved",
        "source_type": "manual",
        "change_reason": "Initial creation"
    })
    if data.get("ok") and data.get("result"):
        result["message"] = f"Created canon doc: {data['result'].get('key')}, version: {data['result'].get('version')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_get(suite, result):
    data = suite.call_tool("canon.doc.get", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "key": "test_world_001"
    })
    if data.get("ok") and data.get("result"):
        doc = data["result"]
        required_fields = ["key", "title", "doc_type", "status", "review_status", "source_type", "version"]
        missing = [f for f in required_fields if f not in doc]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        result["message"] = f"Got doc: {doc['key']}, v{doc['version']}, review: {doc.get('review_status')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_update(suite, result):
    data = suite.call_tool("canon.doc.upsert", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "doc_type": "world",
        "key": "test_world_001",
        "title": "Test World Setting - Updated",
        "content": "Updated content for testing version history.",
        "status": "active",
        "review_status": "approved",
        "source_type": "manual",
        "change_reason": "Test update for version history"
    })
    if data.get("ok") and data.get("result"):
        new_version = data["result"].get("version", 0)
        if new_version < 2:
            raise Exception(f"Version should be >= 2, got {new_version}")
        result["message"] = f"Updated doc, version: {new_version}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_list(suite, result):
    data = suite.call_tool("canon.doc.list", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "doc_types": ["world"],
        "statuses": ["active"]
    })
    if data.get("ok") and isinstance(data.get("result"), list):
        items = data["result"]
        if len(items) == 0:
            raise Exception("Expected at least 1 doc, got 0")
        result["message"] = f"Listed {len(items)} docs"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_history(suite, result):
    data = suite.call_tool("canon.doc.history", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "key": "test_world_001"
    })
    if data.get("ok") and isinstance(data.get("result"), list):
        history = data["result"]
        if len(history) < 2:
            raise Exception(f"Expected at least 2 versions, got {len(history)}")
        result["message"] = f"History has {len(history)} versions"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_restore(suite, result):
    data = suite.call_tool("canon.doc.restore", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "key": "test_world_001",
        "version": 1,
        "reason": "Test restore"
    })
    if data.get("ok") and data.get("result"):
        result["message"] = f"Restored to version 1, new version: {data['result'].get('version')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_canon_archive(suite, result):
    data = suite.call_tool("canon.doc.archive", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "key": "test_world_001",
        "reason": "Test cleanup"
    })
    if data.get("ok"):
        result["message"] = "Archived successfully"
    else:
        raise Exception(f"Unexpected response: {data}")


def main():
    print("=" * 70)
    print("Web Console - Canon Docs Enhancement Test")
    print("=" * 70)
    print(f"Web URL: {WEB_BASE_URL}")
    print(f"User: {USERNAME}")
    print(f"Workspace: {WORKSPACE}")
    
    suite = WebTestSuite()
    
    try:
        suite.login()
        suite.ensure_project()
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1
    
    tests = [
        ("1. Create Canon Doc", test_canon_create),
        ("2. Get Canon Doc (with enhanced fields)", test_canon_get),
        ("3. Update Canon Doc (version increment)", test_canon_update),
        ("4. List Canon Docs (with filters)", test_canon_list),
        ("5. Canon Doc History", test_canon_history),
        ("6. Canon Doc Restore", test_canon_restore),
        ("7. Canon Doc Archive", test_canon_archive),
    ]
    
    for name, test_func in tests:
        print(f"\nRunning test: {name} ...", end=" ", flush=True)
        result = suite.run_test(name, lambda r, f=test_func, s=suite: f(s, r))
        if result["passed"]:
            print("PASS")
            if result["message"]:
                print(f"   {result['message']}")
        else:
            print("FAIL")
            print(f"   Error: {result['message']}")
    
    success = suite.print_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
