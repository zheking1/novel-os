import requests
s = requests.Session()
s.post('http://127.0.0.1:8790/api/login', json={'username':'admin','password':'${NAS_SSH_PASSWORD}'})

r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'project.list','arguments':{'workspace':'default'}})
print("List projects:", r.text)

r = s.post('http://127.0.0.1:8790/api/tool', json={
    'tool': 'project.create',
    'arguments': {
        'workspace': 'default',
        'slug': 'testproj',
        'title': 'Test Project'
    }
})
print("Create project:", r.text)

r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'project.list','arguments':{'workspace':'default'}})
print("List after create:", r.text)
