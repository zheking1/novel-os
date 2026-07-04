import json
import sys
import time

import requests


WEB_BASE_URL = "http://127.0.0.1:8790"
USERNAME = "admin"
PASSWORD = "${NAS_SSH_PASSWORD}"
WORKSPACE = "default"


class WebTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.results = []

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
        print("Web Console Test Results")
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


def test_foreshadowing_list(suite, result):
    data = suite.call_tool("plot.list_foreshadowing", {"workspace": WORKSPACE, "project": WORKSPACE})
    if data.get("ok") and isinstance(data.get("result"), list):
        result["message"] = f"Got {len(data['result'])} foreshadowing items"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_foreshadowing_create(suite, result):
    data = suite.call_tool("plot.upsert_foreshadowing", {
        "workspace": WORKSPACE,
        "project": WORKSPACE,
        "key": "test_foreshadow_001",
        "title": "Test Foreshadow",
        "status": "planted",
        "importance": "medium"
    })
    if data.get("ok") and data.get("result"):
        result["message"] = f"Created foreshadowing: {data['result'].get('key')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_foreshadowing_overdue(suite, result):
    data = suite.call_tool("foreshadowing.check_overdue", {
        "workspace": WORKSPACE,
        "project": WORKSPACE,
        "current_chapter_no": 1
    })
    if data.get("ok"):
        result["message"] = f"Overdue check completed: {len(data.get('result', []))} items"
    else:
        raise Exception(f"Unexpected response: {data}")


def main():
    print("=" * 70)
    print("Web Console - Foreshadowing Kanban Test")
    print("=" * 70)
    print(f"Web URL: {WEB_BASE_URL}")
    print(f"User: {USERNAME}")
    
    suite = WebTestSuite()
    
    try:
        suite.login()
    except Exception as e:
        print(f"Login failed: {e}")
        return 1
    
    tests = [
        ("1. Foreshadowing List via Web API", test_foreshadowing_list),
        ("2. Foreshadowing Create via Web API", test_foreshadowing_create),
        ("3. Foreshadowing Overdue Check", test_foreshadowing_overdue),
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
