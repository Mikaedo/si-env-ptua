import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = Document(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
NSB = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
corps = []
for e in d.element.body.iterchildren():
    if e.tag == NSB+"p": corps.append(("p", Paragraph(e, d)))
    elif e.tag == NSB+"tbl": corps.append(("t", Table(e, d)))
for cible in ("Tableau 5.2 :", "Figure 5.2 bis"):
    for i,(g,el) in enumerate(corps):
        if i < 400: continue
        if g=="p" and el.text.strip().startswith(cible):
            print(f"--- autour de {cible} ---")
            for j in range(i-3, min(len(corps), i+5)):
                g2,e2 = corps[j]
                if g2=="t": desc=f"[TABLEAU {len(e2.rows)}x{len(e2.columns)}]"
                else:
                    img=len(e2._element.findall(".//"+NSI))
                    desc=f"{'[IMG] ' if img else ''}{e2.text.strip()[:50]!r}"
                print(f"  [{j}]{' <<<' if j==i else '   '} {desc}")
            print()
            break
