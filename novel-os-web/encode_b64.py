import base64

path = r'd:\Project\novels codex\novel-os-web\index.html'

with open(path, 'rb') as f:
    raw = f.read()

print('Original size:', len(raw))

encoded = base64.b64encode(raw).decode('ascii')

with open(path + '.b64', 'w', encoding='ascii') as f:
    f.write(encoded)

print('Base64 size:', len(encoded))
print('Done')