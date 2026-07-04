"""
全局设定系统综合测试脚本

测试内容：
1. MCP 服务健康检查
2. 全局设定工具列表验证
3. 分类管理功能测试
4. 设定项目 CRUD 测试
5. BM25 检索功能测试
6. 题材规范化功能测试
"""

import json
import sys
import time
from typing import Any

import requests


MCP_BASE_URL = "http://${NAS_HOST}:8787/mcp"
WORKSPACE = "2fa7fe16-c1f0-414f-9589-7837be6663b6"
TEST_TIMEOUT = 30


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration = 0.0
        self.data: Any = None


class TestSuite:
    def __init__(self):
        self.results: list[TestResult] = []
        self.session = requests.Session()
        self.session_id = None

    def _mcp_request(self, tool: str, arguments: dict | None = None) -> dict:
        """发送 MCP 请求"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": arguments or {}
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = self.session.post(
            MCP_BASE_URL,
            json=payload,
            headers=headers,
            timeout=TEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def run_test(self, name: str, test_func) -> TestResult:
        """运行单个测试"""
        result = TestResult(name)
        start_time = time.time()
        
        try:
            test_func(result)
            result.passed = True
        except Exception as e:
            result.passed = False
            result.message = str(e)
        
        result.duration = time.time() - start_time
        self.results.append(result)
        return result

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 70)
        print("Test Results Summary")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        for i, result in enumerate(self.results, 1):
            status = "[PASS]" if result.passed else "[FAIL]"
            duration = f"{result.duration:.2f}s"
            print(f"[{i:2d}] {status}  {result.name}  ({duration})")
            if not result.passed and result.message:
                print(f"     Error: {result.message}")
        
        print("-" * 70)
        print(f"Total: {len(self.results)} tests, Passed: {passed}, Failed: {failed}")
        print(f"Total duration: {sum(r.duration for r in self.results):.2f}s")
        print("=" * 70)
        
        return failed == 0


def test_health_check(suite: TestSuite, result: TestResult):
    """测试 MCP 服务健康状态"""
    try:
        response = suite._mcp_request("admin.health")
        result.data = response
        if response.get("result") and response["result"].get("content"):
            content = response["result"]["content"][0]
            if content.get("type") == "text":
                health_data = json.loads(content["text"])
                if health_data.get("status") == "ok":
                    result.message = "服务健康，数据库连接正常"
                    return
        raise Exception("健康检查返回格式不正确")
    except requests.exceptions.ConnectionError:
        raise Exception(f"无法连接到 MCP 服务: {MCP_BASE_URL}")


def test_list_tools(suite: TestSuite, result: TestResult):
    """测试工具列表是否包含全局设定工具"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = suite.session.post(
        MCP_BASE_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TEST_TIMEOUT
    )
    response.raise_for_status()
    data = response.json()
    
    tools = data.get("result", {}).get("tools", [])
    tool_names = [t.get("name") for t in tools]
    
    setting_tools = [t for t in tool_names if t.startswith("setting.")]
    result.data = setting_tools
    
    expected_tools = [
        "setting.category.list",
        "setting.category.get",
        "setting.category.upsert",
        "setting.item.list",
        "setting.item.get",
        "setting.item.upsert",
        "setting.search",
        "setting.genre.list",
        "setting.genre.resolve",
    ]
    
    missing = [t for t in expected_tools if t not in tool_names]
    if missing:
        raise Exception(f"缺少工具: {missing}")
    
    result.message = f"找到 {len(setting_tools)} 个全局设定工具"


def test_category_list(suite: TestSuite, result: TestResult):
    """测试分类列表"""
    response = suite._mcp_request("setting.category.list", {"workspace": WORKSPACE})
    result.data = response
    
    if response.get("result") and response["result"].get("content"):
        content = response["result"]["content"][0]
        if content.get("type") == "text":
            categories = json.loads(content["text"])
            if isinstance(categories, list):
                result.message = f"获取到 {len(categories)} 个分类"
                return
    
    raise Exception("分类列表返回格式不正确")


def test_category_get(suite: TestSuite, result: TestResult):
    """测试获取分类详情"""
    response = suite._mcp_request("setting.category.list", {"workspace": WORKSPACE})
    
    if not response.get("result"):
        raise Exception("无法获取分类列表")
    
    content = response["result"]["content"][0]
    categories = json.loads(content["text"])
    
    if not categories:
        raise Exception("没有可用的分类")
    
    first_cat = categories[0]
    cat_id = first_cat.get("id")
    
    detail_response = suite._mcp_request(
        "setting.category.get",
        {"workspace": WORKSPACE, "category_id": cat_id}
    )
    result.data = detail_response
    
    if detail_response.get("result") and detail_response["result"].get("content"):
        content = detail_response["result"]["content"][0]
        if content.get("type") == "text":
            detail = json.loads(content["text"])
            if detail.get("id") == cat_id:
                result.message = f"成功获取分类详情: {detail.get('name', '')}"
                return
    
    raise Exception("分类详情返回格式不正确")


def test_item_list(suite: TestSuite, result: TestResult):
    """测试设定项目列表"""
    response = suite._mcp_request("setting.item.list", {"workspace": WORKSPACE})
    result.data = response
    
    if response.get("result") and response["result"].get("content"):
        content = response["result"]["content"][0]
        if content.get("type") == "text":
            items = json.loads(content["text"])
            if isinstance(items, list):
                result.message = f"获取到 {len(items)} 个设定项目"
                return
    
    raise Exception("设定项目列表返回格式不正确")


def test_bm25_search(suite: TestSuite, result: TestResult):
    """测试 BM25 检索功能"""
    response = suite._mcp_request(
        "setting.search",
        {
            "workspace": WORKSPACE,
            "query": "主角修炼",
            "limit": 5
        }
    )
    result.data = response
    
    if response.get("result") and response["result"].get("content"):
        content = response["result"]["content"][0]
        if content.get("type") == "text":
            results = json.loads(content["text"])
            if isinstance(results, list):
                result.message = f"BM25 搜索返回 {len(results)} 条结果"
                if results:
                    result.message += f"，最高分: {results[0].get('rank', 0):.2f}"
                return
    
    raise Exception("BM25 搜索返回格式不正确")


def test_genre_list(suite: TestSuite, result: TestResult):
    """测试题材列表"""
    response = suite._mcp_request("setting.genre.list", {})
    result.data = response
    
    if response.get("result") and response["result"].get("content"):
        content = response["result"]["content"][0]
        if content.get("type") == "text":
            genres = json.loads(content["text"])
            if isinstance(genres, list):
                result.message = f"获取到 {len(genres)} 个题材"
                return
    
    raise Exception("题材列表返回格式不正确")


def test_genre_resolve(suite: TestSuite, result: TestResult):
    """测试题材规范化"""
    test_cases = [
        ("东方玄幻", "玄幻"),
        ("都市异能", "都市"),
        ("修仙", "玄幻"),
        ("系统流", "系统"),
    ]
    
    results = []
    for input_genre, expected in test_cases:
        response = suite._mcp_request(
            "setting.genre.resolve",
            {"input": input_genre}
        )
        
        if response.get("result") and response["result"].get("content"):
            content = response["result"]["content"][0]
            if content.get("type") == "text":
                resolved = json.loads(content["text"])
                if isinstance(resolved, list) and len(resolved) > 0:
                    results.append({
                        "input": input_genre,
                        "expected": expected,
                        "matched": resolved[0].get("canonical_genre", ""),
                        "confidence": resolved[0].get("confidence", 0)
                    })
    
    result.data = results
    
    if len(results) == len(test_cases):
        result.message = f"成功解析 {len(results)}/{len(test_cases)} 个题材"
        return
    
    raise Exception("题材规范化测试失败")


def test_item_upsert(suite: TestSuite, result: TestResult):
    """测试创建设定项目"""
    test_item = {
        "workspace": WORKSPACE,
        "item_code": "test_item_001",
        "category_ids": [],
        "level": "knowledge",
        "core_summary": "测试用设定项目，用于验证 CRUD 功能",
        "keywords": ["测试", "验证"],
        "intent_synonyms": ["测试设定", "验证项目"],
        "detailed_expansion": "这是一个用于测试的设定项目，包含完整的字段定义。",
        "ai_instruction": "这是给 AI 的指令说明",
        "poison_points": ["不要在正式内容中使用"],
        "is_global": True,
        "platforms": ["通用"],
        "source_type": "manual"
    }
    
    response = suite._mcp_request("setting.item.upsert", test_item)
    result.data = response
    
    if response.get("result") and response["result"].get("content"):
        content = response["result"]["content"][0]
        if content.get("type") == "text":
            item = json.loads(content["text"])
            if item.get("item_code") == "test_item_001":
                result.message = f"成功创建设定项目，ID: {item.get('id', '')}"
                return
    
    raise Exception("创建设定项目失败")


def test_item_get(suite: TestSuite, result: TestResult):
    """测试获取设定项目详情"""
    list_response = suite._mcp_request("setting.item.list", {"workspace": WORKSPACE})
    
    if not list_response.get("result"):
        raise Exception("无法获取设定项目列表")
    
    content = list_response["result"]["content"][0]
    items = json.loads(content["text"])
    
    test_items = [i for i in items if i.get("item_code") == "test_item_001"]
    if not test_items:
        raise Exception("找不到测试项目")
    
    item_id = test_items[0]["id"]
    
    detail_response = suite._mcp_request(
        "setting.item.get",
        {"workspace": WORKSPACE, "item_id": item_id}
    )
    result.data = detail_response
    
    if detail_response.get("result") and detail_response["result"].get("content"):
        content = detail_response["result"]["content"][0]
        if content.get("type") == "text":
            detail = json.loads(content["text"])
            if detail.get("id") == item_id:
                result.message = f"成功获取设定项目详情: {detail.get('item_code', '')}"
                return
    
    raise Exception("获取设定项目详情失败")


def test_item_delete(suite: TestSuite, result: TestResult):
    """测试删除设定项目"""
    list_response = suite._mcp_request("setting.item.list", {"workspace": WORKSPACE})
    
    if not list_response.get("result"):
        raise Exception("无法获取设定项目列表")
    
    content = list_response["result"]["content"][0]
    items = json.loads(content["text"])
    
    test_items = [i for i in items if i.get("item_code") == "test_item_001"]
    if not test_items:
        result.message = "测试项目已不存在，跳过删除测试"
        return
    
    item_id = test_items[0]["id"]
    
    delete_response = suite._mcp_request(
        "setting.item.delete",
        {"workspace": WORKSPACE, "item_id": item_id}
    )
    result.data = delete_response
    
    if delete_response.get("result") and delete_response["result"].get("content"):
        content = delete_response["result"]["content"][0]
        if content.get("type") == "text":
            result_data = json.loads(content["text"])
            if result_data.get("success") or result_data.get("deleted"):
                result.message = f"成功删除设定项目，ID: {item_id}"
                return
    
    raise Exception("删除设定项目失败")


def main():
    print("=" * 70)
    print("Global Settings System - Comprehensive Test")
    print("=" * 70)
    print(f"MCP URL: {MCP_BASE_URL}")
    print(f"Workspace: {WORKSPACE}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    
    suite = TestSuite()
    
    tests = [
        ("1. MCP 服务健康检查", test_health_check),
        ("2. 全局设定工具列表验证", test_list_tools),
        ("3. 分类列表功能", test_category_list),
        ("4. 分类详情功能", test_category_get),
        ("5. 设定项目列表功能", test_item_list),
        ("6. BM25 检索功能", test_bm25_search),
        ("7. 题材列表功能", test_genre_list),
        ("8. 题材规范化功能", test_genre_resolve),
        ("9. 创建设定项目", test_item_upsert),
        ("10. 获取设定项目详情", test_item_get),
        ("11. 删除设定项目", test_item_delete),
    ]
    
    for name, test_func in tests:
        print(f"\nRunning test: {name} ...", end=" ", flush=True)
        result = suite.run_test(name, lambda r, f=test_func, s=suite: f(s, r))
        if result.passed:
            print("PASS")
            if result.message:
                print(f"   {result.message}")
        else:
            print("FAIL")
            print(f"   Error: {result.message}")
    
    success = suite.print_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
