import re, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = Document(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
NSB="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI="{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
corps=[]
for e in d.element.body.iterchildren():
    if e.tag==NSB+"p": corps.append(("p",Paragraph(e,d)))
    elif e.tag==NSB+"tbl": corps.append(("t",Table(e,d)))
debut=next(i for i,(g,el) in enumerate(corps) if g=="p" and el.style.name.startswith("Heading 1") and el.text.strip().lower().startswith("introduction g"))
fin=next(i for i,(g,el) in enumerate(corps) if g=="p" and el.style.name.startswith("Heading 1") and el.text.strip()=="Conclusion générale")
EMU=360000
print("=== figures du corps, avec leur hauteur ===")
tot=0
for i in range(debut,fin):
    g,el=corps[i]
    if g!="p": continue
    m=re.match(r"Figure ([\d.]+(?: bis)?)\s*:",el.text.strip())
    if not m: continue
    h=0
    for j in range(i-1,max(debut,i-3),-1):
        if corps[j][0]=="p" and corps[j][1]._element.findall(".//"+NSI):
            for sh in d.inline_shapes:
                pass
            h=1; break
    print(f"  Figure {m.group(1):<8} {el.text.strip()[7:70]}")
    tot+=1
print(f"\n{tot} figures dans le corps")
# Longueur de la conclusion generale
print("\n=== conclusion generale ===")
n=0
for i in range(fin+1,len(corps)):
    g,el=corps[i]
    if g=="p" and el.style.name.startswith("Heading 1"): break
    if g=="p" and el.text.strip(): n+=len(el.text.strip())
print(f"  {n} caracteres")
