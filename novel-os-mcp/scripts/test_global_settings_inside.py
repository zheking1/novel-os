import asyncio
import json
import sys
import time


sys.path.insert(0, "/app/src")

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.global_settings import GlobalSettingsService


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration = 0.0
        self.data = None


class TestSuite:
    def __init__(self):
        self.results = []
        self.db = None
        self.svc = None
        self.workspace = "2fa7fe16-c1f0-414f-9589-7837be6663b6"

    async def setup(self):
        settings = get_settings()
        self.db = Database(settings)
        self.svc = GlobalSettingsService(self.db)
        await self.db.connect()

    def run_test(self, name, test_func):
        result = TestResult(name)
        start_time = time.time()
        
        try:
            asyncio.get_event_loop().run_until_complete(test_func(self, result))
            result.passed = True
        except Exception as e:
            result.passed = False
            result.message = str(e)
        
        result.duration = time.time() - start_time
        self.results.append(result)
        return result

    def print_results(self):
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


async def test_db_connection(suite, result):
    row = await suite.db.fetchrow("SELECT 1 AS ok")
    if row and row["ok"] == 1:
        result.message = "Database connection OK"
    else:
        raise Exception("Database connection failed")


async def test_list_categories(suite, result):
    categories = await suite.svc.list_categories(suite.workspace)
    if isinstance(categories, list):
        result.message = f"Found {len(categories)} categories"
        result.data = categories
        if len(categories) == 0:
            raise Exception("No categories found")
    else:
        raise Exception("Invalid response format")


async def test_get_category(suite, result):
    categories = await suite.svc.list_categories(suite.workspace)
    if not categories:
        raise Exception("No categories available")
    
    first_cat = categories[0]
    cat_id = first_cat.get("id")
    
    detail = await suite.svc.get_category(suite.workspace, cat_id)
    if detail and detail.get("id") == cat_id:
        result.message = f"Got category detail: {detail.get('name', '')}"
        result.data = detail
    else:
        raise Exception("Failed to get category detail")


async def test_list_items(suite, result):
    items = await suite.svc.list_items(suite.workspace)
    if isinstance(items, list):
        result.message = f"Found {len(items)} items"
        result.data = items
    else:
        raise Exception("Invalid response format")


async def test_bm25_search(suite, result):
    results = await suite.svc.bm25_search(
        suite.workspace,
        "主角修炼",
        limit=5
    )
    if isinstance(results, list):
        result.message = f"BM25 search returned {len(results)} results"
        if results:
            result.message += f", top rank: {results[0].get('rank', 0):.2f}"
        result.data = results
    else:
        raise Exception("Invalid response format")

async def test_list_genres(suite, result):
    genres = await suite.svc.list_genres()
    if isinstance(genres, list):
        result.message = f"Found {len(genres)} genres"
        result.data = genres
        if len(genres) == 0:
            raise Exception("No genres found")
    else:
        raise Exception("Invalid response format")


async def test_resolve_genre(suite, result):
    test_cases = [
        ("东方玄幻", "玄幻"),
        ("都市异能", "都市"),
        ("修仙", "玄幻"),
    ]
    
    all_passed = True
    results_data = []
    
    for input_genre, expected in test_cases:
        resolved = await suite.svc.resolve_genre(input_genre)
        if isinstance(resolved, list) and len(resolved) > 0:
            results_data.append({
                "input": input_genre,
                "expected": expected,
                "matched": resolved[0].get("canonical_genre", ""),
                "confidence": resolved[0].get("confidence", 0)
            })
        else:
            all_passed = False
            results_data.append({
                "input": input_genre,
                "expected": expected,
                "matched": None,
                "error": "No result"
            })
    
    result.data = results_data
    
    if all_passed:
        result.message = f"Resolved {len(test_cases)} test genres successfully"
    else:
        raise Exception(f"Some genre resolutions failed")


async def test_upsert_item(suite, result):
    categories = await suite.svc.list_categories(suite.workspace)
    if not categories:
        raise Exception("No categories available")
    
    category_id = categories[0]["id"]
    
    row = await suite.db.fetchrow("SELECT id FROM users LIMIT 1")
    user_id = row["id"] if row else None
    
    if not user_id:
        result.message = "No users found, skipping upsert test"
        result.passed = True
        return
    
    item = await suite.svc.upsert_item(
        workspace_id=suite.workspace,
        category_id=category_id,
        username=user_id,
        item_code="test_item_api_001",
        level="knowledge",
        core_summary="Test item for API verification - 主角修炼升级体系",
        keywords=["测试", "验证", "主角", "修炼"],
        intent_synonyms=["测试设定", "验证项目", "主角升级"],
        detailed_expansion="This is a test item for API verification purposes. It describes the main character's cultivation system.",
        ai_instruction="This is AI instruction for test item",
        poison_points=["Do not use in production"],
        is_global=False,
        tags=["test", "verification"],
    )
    
    if item and item.get("item_code") == "test_item_api_001":
        result.message = f"Created item with ID: {item.get('id', '')}"
        result.data = item
    else:
        raise Exception("Failed to create item")


async def test_get_item(suite, result):
    items = await suite.svc.list_items(suite.workspace)
    
    if not items:
        raise Exception("No items found")
    
    item_id = items[0]["id"]
    detail = await suite.svc.get_item(suite.workspace, item_id)
    
    if detail and detail.get("id") == item_id:
        result.message = f"Got item detail: {detail.get('item_code', detail.get('id', ''))}"
        result.data = detail
    else:
        raise Exception("Failed to get item detail")


async def test_delete_item(suite, result):
    items = await suite.svc.list_items(suite.workspace)
    test_items = [i for i in items if i.get("item_code") == "test_item_api_001"]
    
    if not test_items:
        result.message = "No test item to delete, skipping"
        result.passed = True
        return
    
    item_id = test_items[0]["id"]
    deleted = await suite.svc.delete_item(suite.workspace, item_id)
    
    if deleted:
        result.message = f"Deleted item with ID: {item_id}"
    else:
        raise Exception("Failed to delete item")


async def test_verify_tables(suite, result):
    tables = [
        "setting_categories",
        "setting_field_definitions",
        "setting_items",
        "genre_canonical",
        "setting_category_relations",
    ]
    
    table_status = {}
    all_exist = True
    
    for table in tables:
        row = await suite.db.fetchrow(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
        )
        exists = row["exists"] if row else False
        table_status[table] = exists
        if not exists:
            all_exist = False
    
    result.data = table_status
    
    if all_exist:
        result.message = f"All {len(tables)} tables exist"
    else:
        missing = [t for t, e in table_status.items() if not e]
        raise Exception(f"Missing tables: {missing}")


async def test_seed_data(suite, result):
    checks = {
        "standard_categories": "SELECT COUNT(*) FROM setting_categories WHERE is_standard = TRUE",
        "canonical_genres": "SELECT COUNT(*) FROM genre_canonical",
        "global_items": "SELECT COUNT(*) FROM setting_items WHERE is_global = TRUE",
    }
    
    counts = {}
    for name, sql in checks.items():
        row = await suite.db.fetchrow(sql)
        counts[name] = row["count"] if row else 0
    
    result.data = counts
    
    if counts["standard_categories"] > 0 and counts["canonical_genres"] > 0:
        result.message = f"Seed data OK: {counts['standard_categories']} std cats, {counts['canonical_genres']} genres"
    else:
        raise Exception(f"Insufficient seed data: {counts}")


async def main():
    print("=" * 70)
    print("Global Settings System - Comprehensive Test")
    print("=" * 70)
    
    suite = TestSuite()
    await suite.setup()
    
    tests = [
        ("1. Database Connection", test_db_connection),
        ("2. Table Verification", test_verify_tables),
        ("3. Seed Data Check", test_seed_data),
        ("4. List Categories", test_list_categories),
        ("5. Get Category Detail", test_get_category),
        ("6. List Items", test_list_items),
        ("7. List Genres", test_list_genres),
        ("8. Resolve Genre", test_resolve_genre),
        ("9. Upsert Item", test_upsert_item),
        ("10. Get Item Detail", test_get_item),
        ("11. BM25 Search", test_bm25_search),
        ("12. Delete Item", test_delete_item),
    ]
    
    for name, test_func in tests:
        print(f"\nRunning test: {name} ...", end=" ", flush=True)
        result = TestResult(name)
        start_time = time.time()
        
        try:
            await test_func(suite, result)
            result.passed = True
        except Exception as e:
            result.passed = False
            result.message = str(e)
        
        result.duration = time.time() - start_time
        suite.results.append(result)
        
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
