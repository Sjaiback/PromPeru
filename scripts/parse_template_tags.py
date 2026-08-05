from pathlib import Path
s=Path('templates/atencion/registro.html').read_text(encoding='utf-8')
idx=0
tags=[]
while True:
    start=s.find('{%',idx)
    if start==-1: break
    end=s.find('%}',start)
    if end==-1:
        print('Unclosed tag at',start)
        break
    content=s[start+2:end].strip()
    # compute line number
    line=s.count('\n',0,start)+1
    tags.append((line,content))
    idx=end+2
for line,content in tags:
    if content.startswith('if') or content.startswith('endif') or content.startswith('for') or content.startswith('endfor') or content.startswith('else') or content.startswith('block') or content.startswith('endblock'):
        print(f"{line:04}: {{% {content} %}}")
# balance if/endif
balance=0
for line,content in tags:
    if content.startswith('if'):
        balance+=1
    elif content.startswith('endif'):
        balance-=1
    elif content.startswith('else'):
        pass
print('\nFinal if balance:',balance)
