import requests
import json

TOKEN = "nos_f7jlgRC9oCiwKfNVbifnaZD03BJhR8F766Q9-_oNGO8"
URL = "http://localhost:8787/mcp"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {TOKEN}"
}

payload = {
    "jsonrpc": "2.0",
    "method": "tool/invoke",
    "params": {
        "name": "knowledge.category.list",
        "arguments": {}
    },
    "id": 1
}

try:
    response = requests.post(URL, headers=headers, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")