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
                    "description": "Test project for context preview"
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
        print("Web Console - Context Preview Test Results")
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


def test_prepare_chapter_context(suite, result):
    data = suite.call_tool("workflow.prepare_chapter_context", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "chapter_no": 1,
        "purpose": "draft",
        "pov_mode": "omniscient",
        "focus": [],
        "budget": {"total_tokens": 8000}
    })
    if data.get("ok") and data.get("result"):
        pack = data["result"]
        required_fields = ["id", "chapter_no", "purpose", "sections", "warnings", "retrieval_audit"]
        missing = [f for f in required_fields if f not in pack]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        sections_count = len(pack.get("sections", []))
        warnings_count = len(pack.get("warnings", []))
        result["message"] = f"Generated pack: {sections_count} sections, {warnings_count} warnings"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_list_context_packs(suite, result):
    data = suite.call_tool("context.list_packs", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "limit": 10
    })
    if data.get("ok") and isinstance(data.get("result"), list):
        packs = data["result"]
        result["message"] = f"Listed {len(packs)} context packs"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_get_context_pack(suite, result):
    # First list to get an ID
    list_data = suite.call_tool("context.list_packs", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "limit": 1
    })
    if not list_data.get("ok") or not isinstance(list_data.get("result"), list) or len(list_data["result"]) == 0:
        raise Exception("No context packs available")
    
    pack_id = list_data["result"][0].get("id")
    data = suite.call_tool("context.get_pack", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "context_pack_id": pack_id
    })
    if data.get("ok") and data.get("result"):
        pack = data["result"]
        if pack.get("id") != pack_id:
            raise Exception(f"Unexpected pack_id: {pack.get('id')}")
        result["message"] = f"Got pack: {pack['id']}, chapter: {pack.get('chapter_no')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_validate_context_pack(suite, result):
    data = suite.call_tool("workflow.validate_context_pack", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "chapter_no": 1
    })
    if data.get("ok") and data.get("result"):
        validation = data["result"]
        required_fields = ["ok", "issues"]
        missing = [f for f in required_fields if f not in validation]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        issues_count = len(validation.get("issues", []))
        result["message"] = f"Validation: {validation.get('ok')}, {issues_count} issues"
    else:
        raise Exception(f"Unexpected response: {data}")


def main():
    print("=" * 70)
    print("Web Console - Context Preview Test")
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
        ("1. Prepare Chapter Context", test_prepare_chapter_context),
        ("2. List Context Packs", test_list_context_packs),
        ("3. Get Context Pack", test_get_context_pack),
        ("4. Validate Context Pack", test_validate_context_pack),
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