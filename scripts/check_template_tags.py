from pathlib import Path
p=Path('templates/atencion/registro.html')
s=p.read_text(encoding='utf-8')
lines=s.splitlines()
for i,l in enumerate(lines, start=1):
    if '{% if' in l or '{% endif' in l or '{% for' in l or '{% endfor' in l or '{% block' in l or '{% endblock' in l or '{% else' in l:
        print(f"{i:04}: {l}")
# Counts
print('\nCounts:')
print('if', s.count('{% if'))
print('endif', s.count('{% endif'))
print('for', s.count('{% for'))
print('endfor', s.count('{% endfor'))
print('block', s.count('{% block'))
print('endblock', s.count('{% endblock'))
