"""
验证全局设定系统

测试 GlobalSettingsService 和 MCP 工具的功能
"""

import asyncio
import sys

# 添加 src 到路径
sys.path.insert(0, "src")

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.global_settings import GlobalSettingsService


async def verify_tables(db: Database) -> dict:
    """验证表是否正确创建"""
    tables = [
        "setting_categories",
        "setting_field_definitions",
        "setting_items",
        "genre_canonical",
        "setting_category_relations",
    ]
    
    results = {}
    for table in tables:
        try:
            row = await db.fetchrow(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            )
            results[table] = row["exists"]
        except Exception as e:
            results[table] = str(e)
    
    return results


async def verify_seed_data(db: Database) -> dict:
    """验证种子数据"""
    results = {}
    
    # 检查标准分类
    try:
        row = await db.fetchrow(
            "SELECT COUNT(*) FROM setting_categories WHERE is_standard = TRUE"
        )
        results["standard_categories"] = row["count"]
    except Exception as e:
        results["standard_categories"] = str(e)
    
    # 检查题材规范
    try:
        row = await db.fetchrow(
            "SELECT COUNT(*) FROM genre_canonical"
        )
        results["canonical_genres"] = row["count"]
    except Exception as e:
        results["canonical_genres"] = str(e)
    
    # 检查示例设定
    try:
        row = await db.fetchrow(
            "SELECT COUNT(*) FROM setting_items WHERE is_global = TRUE"
        )
        results["global_items"] = row["count"]
    except Exception as e:
        results["global_items"] = str(e)
    
    return results


async def verify_functions(db: Database) -> dict:
    """验证函数"""
    functions = [
        "fn_setting_items_bm25_search",
        "fn_genre_resolve",
        "fn_setting_items_csv_validate",
    ]
    
    results = {}
    for fn in functions:
        try:
            row = await db.fetchrow(
                f"""
                SELECT EXISTS (
                    SELECT FROM pg_proc 
                    WHERE proname = '{fn}'
                )
                """
            )
            results[fn] = row["exists"]
        except Exception as e:
            results[fn] = str(e)
    
    return results


async def test_bm25_search(service: GlobalSettingsService) -> dict:
    """测试 BM25 搜索"""
    try:
        results = await service.bm25_search(
            workspace_id="00000000-0000-0000-0000-000000000000",
            query="主角修炼",
            genre="玄幻",
            limit=5,
        )
        return {"status": "ok", "count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def test_genre_resolve(service: GlobalSettingsService) -> dict:
    """测试题材规范化"""
    try:
        results = await service.resolve_genre("东方玄幻")
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def test_list_genres(service: GlobalSettingsService) -> dict:
    """测试列出题材"""
    try:
        results = await service.list_genres()
        return {"status": "ok", "count": len(results)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def main():
    print("=" * 60)
    print("全局设定系统验证")
    print("=" * 60)
    
    settings = get_settings()
    db = Database(settings)
    service = GlobalSettingsService(db)
    
    await db.connect()
    
    # 1. 验证表
    print("\n[1] 验证表结构...")
    table_results = await verify_tables(db)
    for table, status in table_results.items():
        status_str = "✓" if status is True else f"✗ ({status})"
        print(f"  {table}: {status_str}")
    
    # 2. 验证种子数据
    print("\n[2] 验证种子数据...")
    seed_results = await verify_seed_data(db)
    print(f"  标准分类: {seed_results.get('standard_categories', 0)} 条")
    print(f"  Canonical Genre: {seed_results.get('canonical_genres', 0)} 条")
    print(f"  全局设定项: {seed_results.get('global_items', 0)} 条")
    
    # 3. 验证函数
    print("\n[3] 验证函数...")
    fn_results = await verify_functions(db)
    for fn, status in fn_results.items():
        status_str = "✓" if status is True else f"✗ ({status})"
        print(f"  {fn}: {status_str}")
    
    # 4. 测试 BM25 搜索
    print("\n[4] 测试 BM25 搜索...")
    search_results = await test_bm25_search(service)
    if search_results["status"] == "ok":
        print(f"  ✓ 搜索成功，返回 {search_results['count']} 条结果")
        if search_results["results"]:
            print(f"    示例: {search_results['results'][0].get('core_summary', '')[:50]}...")
    else:
        print(f"  ✗ 搜索失败: {search_results['message']}")
    
    # 5. 测试题材规范化
    print("\n[5] 测试题材规范化...")
    genre_results = await test_genre_resolve(service)
    if genre_results["status"] == "ok":
        print(f"  ✓ 规范化成功")
        for r in genre_results["results"]:
            print(f"    {r['canonical_genre']} ({r['match_type']}, 置信度: {r['confidence']})")
    else:
        print(f"  ✗ 规范化失败: {genre_results['message']}")
    
    # 6. 测试列出题材
    print("\n[6] 测试列出题材...")
    list_results = await test_list_genres(service)
    if list_results["status"] == "ok":
        print(f"  ✓ 列表成功，共 {list_results['count']} 个题材")
    else:
        print(f"  ✗ 列表失败: {list_results['message']}")
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())