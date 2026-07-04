import requests
import json

session = requests.Session()

print("=== 测试登录 ===")
login_response = session.post('http://127.0.0.1:8790/api/login', json={'username': 'admin', 'password': '${NAS_SSH_PASSWORD}'})
print(f"登录状态: {login_response.status_code}")
print(f"登录响应: {login_response.text}")

print("\n=== 测试获取单个知识条目 ===")
item_response = session.post('http://127.0.0.1:8790/api/tool', json={'tool': 'knowledge.item.get', 'arguments': {'item_id': '88fb6167-13e0-4a95-b866-b2248c42ec0e'}})
print(f"状态: {item_response.status_code}")
result = item_response.json()
print(f"响应: {json.dumps(result, ensure_ascii=False)[:1000]}")