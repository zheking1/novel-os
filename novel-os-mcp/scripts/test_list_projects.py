import requests
s = requests.Session()
s.post('http://127.0.0.1:8790/api/login', json={'username':'admin','password':'${NAS_SSH_PASSWORD}'})
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'project.list','arguments':{'workspace':'default'}})
print(r.text)
