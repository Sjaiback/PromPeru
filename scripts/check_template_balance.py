from pathlib import Path
p=Path('templates/atencion/registro.html')
s=p.read_text(encoding='utf-8')
lines=s.splitlines()
count=0
for i,l in enumerate(lines, start=1):
    inc=l.count('{% if')
    dec=l.count('{% endif')
    count += inc - dec
    if inc or dec:
        print(f"{i:04}: +{inc} -{dec} -> balance={count} | {l}")
if count!=0:
    print('\nFinal balance',count)
else:
    print('\nAll if/endif balanced')
