import requests
s = requests.Session()
s.post('http://127.0.0.1:8790/api/login', json={'username':'admin','password':'${NAS_SSH_PASSWORD}'})

# List volumes
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'volume.list','arguments':{'workspace':'default','project':'testproj'}})
print("Volumes:", r.text)

# Create volume
r = s.post('http://127.0.0.1:8790/api/tool', json={
    'tool': 'volume.upsert',
    'arguments': {
        'workspace': 'default',
        'project': 'testproj',
        'volume_no': 1,
        'title': 'First Volume',
        'status': 'planned',
        'start_chapter_no': 1,
        'end_chapter_no': 50,
        'outline': 'Introduction to the story'
    }
})
print("Create volume:", r.text)

# List volumes again
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'volume.list','arguments':{'workspace':'default','project':'testproj'}})
print("Volumes after create:", r.text)

# Create plot thread
r = s.post('http://127.0.0.1:8790/api/tool', json={
    'tool': 'plot.thread.upsert',
    'arguments': {
        'workspace': 'default',
        'project': 'testproj',
        'key': 'main_plot',
        'title': 'Main Plot Line',
        'thread_type': 'main',
        'status': 'open',
        'importance': 'critical',
        'volume_no': 1
    }
})
print("Create thread:", r.text)

# List threads
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'plot.thread.list','arguments':{'workspace':'default','project':'testproj'}})
print("Threads:", r.text)

# Advance thread
r = s.post('http://127.0.0.1:8790/api/tool', json={
    'tool': 'plot.thread.advance',
    'arguments': {
        'workspace': 'default',
        'project': 'testproj',
        'key': 'main_plot',
        'chapter_no': 5,
        'progress_note': 'Main character introduced'
    }
})
print("Advance thread:", r.text)

# Check stalled
r = s.post('http://127.0.0.1:8790/api/tool', json={'tool':'plot.thread.check_stalled','arguments':{'workspace':'default','project':'testproj','current_chapter_no':100}})
print("Check stalled:", r.text)