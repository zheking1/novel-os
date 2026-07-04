f = open('/app/index.html', 'rb')
raw = f.read()

zh_start = raw.find(b'zh: {')
if zh_start != -1:
    idx = raw.find(b'"option.world"', zh_start)
    if idx != -1:
        print('option.world found at:', idx)
        print('Context:', raw[idx:idx+40].decode('utf-8', errors='replace'))
    else:
        print('option.world not found in zh block')
    
    idx2 = raw.find(b'"option.character"', zh_start)
    if idx2 != -1:
        print('option.character found at:', idx2)
        print('Context:', raw[idx2:idx2+50].decode('utf-8', errors='replace'))
else:
    print('zh block not found')