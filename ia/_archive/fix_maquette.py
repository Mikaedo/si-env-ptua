# -*- coding: utf-8 -*-
p = r'C:\Users\DELL\CascadeProjects\si-env-maquettes\design_pro.html'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer le bloc IA pour ajouter le selecteur de criticite manuel apres
old_block = '<p style="margin-top:4px"><span class="chip orange">Criticité modérée</span></p>\n</div>\n\n<button class="btn btn-primary">'

new_block = '<p style="margin-top:4px"><span class="chip orange">Criticité modérée</span></p>\n</div>\n\n<div class="input-group" style="margin-top:12px">\n<label class="input-label">Niveau de criticité (évaluation agent)</label>\n<select class="input"><option>Faible</option><option>Modéré</option><option>Élevé</option></select>\n</div>\n\n<button class="btn btn-primary">'

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - Selecteur criticite manuel ajoute apres diagnostic IA')
else:
    print('ERR - bloc non trouve')
    # Debug
    idx = content.find('Criticité modérée')
    if idx >= 0:
        print(f'Trouve "Criticite" a index {idx}')
        print(repr(content[idx:idx+200]))
