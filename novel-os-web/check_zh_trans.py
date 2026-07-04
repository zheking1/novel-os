f = open('/app/index.html', 'rb')
raw = f.read()

zh_start = raw.find(b'zh: {')
zh_end = raw.find(b'\n      }', zh_start)

if zh_start != -1 and zh_end != -1:
    zh_block = raw[zh_start:zh_end]
    print('ZH block length:', len(zh_block))
    print('First 200 bytes:')
    print(zh_block[:200].decode('utf-8', errors='replace'))
    print('...')
    print('Has Chinese chars:', b'\xe4\xb8\xad\xe6\x96\x87' in zh_block)
    print('Has "option.world":', b'"option.world"' in zh_block)
    print('Has "option.world":', b'\xe4\xb8\x96\xe7\x95\x8c\xe8\xa7\x82' in zh_block)
else:
    print('ZH block not found')