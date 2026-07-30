from app.database import SessionLocal
from app import models, auth

db = SessionLocal()
users = db.query(models.Utilisateur).all()
print(f"Total users: {len(users)}")
for u in users:
    h = u.mot_de_passe_hash[:30] if u.mot_de_passe_hash else "None"
    print(f"  [{u.role.value}] {u.email} | hash: {h}... | premiere: {u.premiere_connexion}")

test_cases = [
    ("admin@sienv.ci", "admin123"),
    ("resp.env@ageroute.ci", "env123"),
    ("expert.hse@ageroute.ci", "expert123"),
    ("spec.env@ageroute.ci", "spec123"),
    ("spec.par@ageroute.ci", "spec123"),
]

print()
print("=== Password verification ===")
for email, pwd in test_cases:
    u = db.query(models.Utilisateur).filter_by(email=email).first()
    if u:
        ok = auth.verifier_mot_de_passe(pwd, u.mot_de_passe_hash)
        result = "OK" if ok else "FAIL"
        print(f"  {email} / {pwd} => {result}")
    else:
        print(f"  {email} => USER NOT FOUND")

db.close()
