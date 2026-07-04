f = open('/app/index.html', 'rb')
raw = f.read()

idx = raw.find(b'<option value="world"')
if idx != -1:
    print('First world option at:', idx)
    print('Context:', raw[idx:idx+60].decode('utf-8', errors='replace'))
else:
    print('No world option found')

idx2 = raw.find(b'data-i18n="option.world"')
if idx2 != -1:
    print('data-i18n world at:', idx2)
    print('Context:', raw[idx2-20:idx2+40].decode('utf-8', errors='replace'))
else:
    print('No data-i18n world found')