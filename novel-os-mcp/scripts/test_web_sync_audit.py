import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.novel_os_mcp.main import mcp
from src.novel_os_mcp.db import Database
from src.novel_os_mcp.config import get_settings

settings = get_settings()

async def test_sync_tools():
    print("=== Testing Sync & Audit Tools ===\n")
    
    db = Database(settings)
    await db.connect()
    
    try:
        cursor = await db._conn.fetch("SELECT id, slug FROM workspaces LIMIT 1")
        if not cursor:
            print("❌ No workspace found")
            return False
        workspace = cursor[0]["slug"]
        print(f"Found workspace: {workspace}")
        
        cursor = await db._conn.fetch("SELECT id, slug FROM projects LIMIT 1")
        if not cursor:
            print("❌ No project found")
            return False
        project = cursor[0]["slug"]
        print(f"Found project: {project}\n")
        
        results = []
        
        print("1. Testing sync.list_conflicts...")
        try:
            conflicts = await mcp.call_tool(
                "sync.list_conflicts",
                {"workspace": workspace, "project": project}
            )
            print(f"   ✅ OK - Found {len(conflicts)} conflicts")
            results.append(("sync.list_conflicts", True))
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append(("sync.list_conflicts", False))
        
        print("\n2. Testing sync.export_project_pack...")
        try:
            pack = await mcp.call_tool(
                "sync.export_project_pack",
                {"workspace": workspace, "project": project, "include_bindings": True}
            )
            print(f"   ✅ OK - Pack exported with keys: {list(pack.keys())}")
            if "bindings" in pack:
                print(f"   - Bindings count: {len(pack['bindings'])}")
            results.append(("sync.export_project_pack", True))
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append(("sync.export_project_pack", False))
        
        print("\n3. Testing workflow.list_audit_logs...")
        try:
            logs = await mcp.call_tool(
                "workflow.list_audit_logs",
                {"workspace": workspace, "project": project, "limit": 10}
            )
            print(f"   ✅ OK - Found {len(logs)} audit logs")
            if logs:
                print(f"   - First log action: {logs[0].get('action')}")
            results.append(("workflow.list_audit_logs", True))
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append(("workflow.list_audit_logs", False))
        
        print("\n4. Testing workflow.list_audit_logs with filters...")
        try:
            logs = await mcp.call_tool(
                "workflow.list_audit_logs",
                {"workspace": workspace, "project": project, "action": "create", "limit": 5}
            )
            print(f"   ✅ OK - Found {len(logs)} filtered audit logs")
            results.append(("workflow.list_audit_logs (filtered)", True))
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append(("workflow.list_audit_logs (filtered)", False))
        
        print("\n" + "="*50)
        passed = sum(1 for _, ok in results if ok)
        total = len(results)
        print(f"Results: {passed}/{total} PASS")
        
        return passed == total
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_sync_tools())
    sys.exit(0 if success else 1)