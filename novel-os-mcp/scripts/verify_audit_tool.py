#!/usr/bin/env python
import sys
sys.path.insert(0, '/app/src')
from novel_os_mcp.main import mcp

# Check all attributes
attrs = [a for a in dir(mcp) if not a.startswith('__')]
print(f'FastMCP attributes: {attrs}')

# Try to find tools
for attr in attrs:
    val = getattr(mcp, attr, None)
    if val and hasattr(val, '__iter__') and not isinstance(val, str):
        try:
            items = list(val)
            if items and isinstance(items[0], str):
                print(f'{attr}: {items[:5]}...')
        except:
            pass

# Direct check - just import and see if the function exists
try:
    from novel_os_mcp.main import workflow_list_audit_logs
    print('OK: workflow_list_audit_logs function exists')
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)