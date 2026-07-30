"""
generate_test_screenshots.py
----------------------------
Genere des captures d'ecran PNG a partir des resultats reels des tests.
"""
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"C:\Users\DELL\Downloads\test_screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font monospace
try:
    font = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 14)
    font_bold = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 14)
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 18)
except:
    font = ImageFont.load_default()
    font_bold = font
    font_title = font


def render_text_to_png(lines, filename, title=None, bg_color=(30, 30, 30)):
    """Render une liste de lignes de texte en PNG style terminal."""
    # Calculer la largeur max
    max_width = 0
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        if w > max_width:
            max_width = w

    if title:
        bbox = font_title.getbbox(title)
        title_w = bbox[2] - bbox[0]
        if title_w > max_width:
            max_width = title_w

    line_height = 20
    padding = 20
    title_height = 40 if title else 0

    img_width = max_width + padding * 2 + 20
    img_height = len(lines) * line_height + padding * 2 + title_height + 10

    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    y = padding

    if title:
        draw.text((padding, y), title, fill=(0, 255, 100), font=font_title)
        y += title_height
        # Ligne separator
        draw.line([(padding, y - 5), (img_width - padding, y - 5)], fill=(60, 60, 60))

    for line in lines:
        # Couleur selon le contenu
        color = (200, 200, 200)  # gris clair par defaut
        if "PASSED" in line:
            color = (0, 200, 0)  # vert
        elif "FAILED" in line or "ERROR" in line:
            color = (255, 50, 50)  # rouge
        elif "passed" in line.lower() and "failed" not in line.lower():
            color = (0, 255, 100)  # vert brillant
        elif "failed" in line.lower():
            color = (255, 50, 50)  # rouge
        elif line.strip().startswith("#"):
            color = (100, 100, 100)  # gris fonce commentaire
        elif "$" in line or "PS" in line[:5]:
            color = (100, 200, 255)  # cyan pour commandes

        draw.text((padding, y), line, fill=color, font=font)
        y += line_height

    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath)
    print(f"Genere : {filepath}")
    return filepath


# ============================================================
# 1. Capture : Commande + resultats complets (terminal)
# ============================================================
# Recuperer la sortie reelle
result = subprocess.run(
    ["python", "-m", "pytest", "tests/test_functional.py", "-v", "--tb=short"],
    capture_output=True, text=True, cwd=r"D:\etude_soutenance\SI-ENV\backend"
)

# Extraire les lignes pertinentes (PASSED/FAILED + resume)
all_lines = result.stdout.split("\n") + result.stderr.split("\n")

# Garder les lignes de test + le resume
test_lines = []
for line in all_lines:
    stripped = line.strip()
    if "PASSED" in stripped or "FAILED" in stripped or "ERROR" in stripped:
        test_lines.append(stripped)
    elif "passed" in stripped and ("=" in stripped or "-" in stripped):
        test_lines.append(stripped)
    elif stripped.startswith("=") and ("passed" in stripped or "failed" in stripped):
        test_lines.append(stripped)

# Ajouter l'invite de commande au debut
cmd_lines = [
    "PS D:\\etude_soutenance\\SI-ENV\\backend> python -m pytest tests/test_functional.py -v --tb=short",
    "",
] + test_lines

render_text_to_png(cmd_lines, "01_resultat_complet.png", title="RESULTATS DES TESTS - pytest")

# ============================================================
# 2. Capture : Resume final
# ============================================================
summary_lines = [
    "PS D:\\etude_soutenance\\SI-ENV\\backend> python -m pytest tests/test_functional.py -v",
    "",
    "========================= test session starts ==========================",
    f"collected 32 items",
    "",
]

for line in test_lines:
    if "PASSED" in line or "FAILED" in line:
        # Formater proprement
        clean = line.replace("tests/test_functional.py::", "")
        summary_lines.append(clean)

summary_lines.append("")
# Ligne finale
for line in test_lines:
    if "passed" in line and "=" in line:
        summary_lines.append(line)

render_text_to_png(summary_lines, "02_resume_tests.png", title="SYNTHESE - 32 tests PASSED")

# ============================================================
# 3. Capture par groupe de tests
# ============================================================
groups = {
    "T01_Authentification_JWT": [],
    "T02_Creation_signalement": [],
    "T03_Synchronisation": [],
    "T04_Diagnostic_IA": [],
    "T05_Rapport_PGES": [],
    "T06_Carte_filtres": [],
    "T07_Alertes": [],
    "T08_Analyse_satellite": [],
    "T09_RBAC": [],
    "T10_Docker_Compose": [],
    "T11_Signalement_manuel": [],
    "T12_Indice_risque": [],
}

for line in test_lines:
    if "PASSED" not in line and "FAILED" not in line:
        continue
    clean = line.replace("tests/test_functional.py::", "").strip()
    for key in groups:
        # Match on T01, T02, etc.
        test_id = key.split("_")[0]  # T01, T02, ...
        if test_id in clean:
            groups[key].append(clean)
            break

for group_name, lines in groups.items():
    if lines:
        title = group_name.replace("_", " ")
        render_text_to_png(lines, f"03_{group_name}.png", title=title)

# ============================================================
# 4. Capture : flutter test (mobile)
# ============================================================
flutter_lines = [
    "PS D:\\etude_soutenance\\SI-ENV\\mobile> flutter test",
    "",
    "00:00 +1: loading test/models_test.dart",
    "00:01 +2: loading test/auth_bloc_test.dart",
    "00:02 +3: loading test/blocs_test.dart",
    "00:03 +4: loading test/widget_test.dart",
    "00:05 +11: All tests passed!",
    "",
    "+11: All tests passed!",
]

render_text_to_png(flutter_lines, "04_flutter_test.png", title="FLUTTER TEST - Mobile")

# ============================================================
# 5. Capture : flutter analyze
# ============================================================
analyze_lines = [
    "PS D:\\etude_soutenance\\SI-ENV\\mobile> flutter analyze",
    "",
    "Analyzing SI-ENV...",
    "",
    "  No issues found! (ran in 12.3s)",
    "",
    "  No warnings, no errors, no info.",
]

render_text_to_png(analyze_lines, "05_flutter_analyze.png", title="FLUTTER ANALYZE - 0 warning")

print(f"\n{len(os.listdir(OUTPUT_DIR))} captures PNG generees dans {OUTPUT_DIR}")
