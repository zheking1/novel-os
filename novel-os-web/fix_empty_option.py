path = r'd:\Project\novels codex\novel-os-web\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

import re

def fix_empty_option(match):
    value = match.group(1)
    rest = match.group(2)
    text = match.group(3)
    
    if value == '':
        return f'<option value=""{rest}>{text}</option>'
    return match.group(0)

pattern = r'<option\s+value="([^"]*)"([^>]*)>([^<]*)</option>'
content = re.sub(pattern, fix_empty_option, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed empty options')