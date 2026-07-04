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
                    "description": "Test project for model cost"
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
        print("Web Console - Model & Cost Test Results")
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


def test_model_profile_create(suite, result):
    data = suite.call_tool("model.profile.upsert", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "profile_key": "test_model_draft",
        "display_name": "GPT-4 Draft Model",
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview",
        "tier": "standard",
        "task_types": ["draft", "outline"],
        "cost_config": {"input_per_1k": 0.01, "output_per_1k": 0.03, "currency": "USD"},
        "status": "active"
    })
    if data.get("ok") and data.get("result"):
        profile = data["result"]
        required_fields = ["profile_key", "model_name", "tier", "status"]
        missing = [f for f in required_fields if f not in profile]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        result["message"] = f"Created model profile: {profile['profile_key']}, tier: {profile['tier']}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_model_profile_list(suite, result):
    data = suite.call_tool("model.profile.list", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "tier": "standard",
        "status": "active"
    })
    if data.get("ok") and isinstance(data.get("result"), list):
        profiles = data["result"]
        if len(profiles) == 0:
            raise Exception("Expected at least 1 profile, got 0")
        result["message"] = f"Listed {len(profiles)} model profiles"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_model_profile_get(suite, result):
    # model.profile.get tool not implemented, use list and filter
    data = suite.call_tool("model.profile.list", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "status": "active"
    })
    if data.get("ok") and isinstance(data.get("result"), list):
        profiles = data["result"]
        profile = next((p for p in profiles if p.get("profile_key") == "test_model_draft"), None)
        if not profile:
            raise Exception("Profile test_model_draft not found")
        result["message"] = f"Got model profile: {profile['profile_key']}, model: {profile.get('model_name')}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_cost_report(suite, result):
    data = suite.call_tool("cost.report", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "group_by": "model"
    })
    if data.get("ok") and data.get("result"):
        report = data["result"]
        required_fields = ["project_id", "group_by", "summary", "groups"]
        missing = [f for f in required_fields if f not in report]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        groups_count = len(report.get("groups", []))
        summary = report.get("summary", {})
        total_cost = float(summary.get("total_cost", 0) or 0)
        result["message"] = f"Cost report: {groups_count} groups, total: ${total_cost:.4f}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_model_usage_record(suite, result):
    data = suite.call_tool("cost.record_usage", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "task_type": "draft",
        "profile_key": "test_model_draft",
        "input_tokens": 1000,
        "output_tokens": 500,
        "latency_ms": 1500,
        "success": True
    })
    if data.get("ok") and data.get("result"):
        record = data["result"]
        required_fields = ["profile_key", "task_type", "input_tokens", "output_tokens"]
        missing = [f for f in required_fields if f not in record]
        if missing:
            raise Exception(f"Missing fields: {missing}")
        result["message"] = f"Created usage record: {record['profile_key']}, tokens: {record['input_tokens']}/{record['output_tokens']}"
    else:
        raise Exception(f"Unexpected response: {data}")


def test_model_profile_archive(suite, result):
    data = suite.call_tool("model.profile.archive", {
        "workspace": WORKSPACE,
        "project": suite.project_slug,
        "profile_key": "test_model_draft",
        "reason": "Test cleanup"
    })
    if data.get("ok"):
        result["message"] = "Archived model profile successfully"
    else:
        raise Exception(f"Unexpected response: {data}")


def main():
    print("=" * 70)
    print("Web Console - Model & Cost Test")
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
        ("1. Create Model Profile", test_model_profile_create),
        ("2. List Model Profiles", test_model_profile_list),
        ("3. Get Model Profile", test_model_profile_get),
        ("4. Create Usage Record", test_model_usage_record),
        ("5. Cost Report", test_cost_report),
        ("6. Archive Model Profile", test_model_profile_archive),
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