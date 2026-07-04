import requests
s = requests.Session()
s.post('http://127.0.0.1:8790/api/login', json={'username':'admin','password':'${NAS_SSH_PASSWORD}'})

# List revision tasks
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'review.list_revision_tasks','arguments':{'workspace':'default','project':'testproj','status':None}})
print("Revision tasks:", r.text)

# List council configs
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'review.list_council_configs','arguments':{'workspace':'default','project':'testproj'}})
print("Council configs:", r.text)

# Create council config
r = s.post('http://127.0.0.1:8790/api/tool', json={
    'tool': 'review.upsert_council_config',
    'arguments': {
        'workspace': 'default',
        'project': 'testproj',
        'name': 'test_council',
        'config': {'models': ['gpt-4', 'claude-3'], 'dimensions': ['plot', 'character']},
        'is_active': False
    }
})
print("Create council config:", r.text)

# List proposals
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'rules.list_proposals','arguments':{'workspace':'default','project':'testproj'}})
print("Rule proposals:", r.text)