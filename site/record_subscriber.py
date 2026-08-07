"""Enregistre / met à jour un abonné dans SITE_ROOT/abonnes.json (GitHub)."""

from __future__ import annotations

import argparse
import json
import secrets
import string
import sys
from datetime import date
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
ABONNES = SITE_ROOT / "abonnes.json"

STATUTS = ("actif", "essai", "résilié", "impayé")
OFFRES = ("mensuel", "annuel", "test")


def load() -> dict[str, dict]:
    if not ABONNES.exists():
        return {}
    raw = json.loads(ABONNES.read_text(encoding="utf-8-sig"))
    if isinstance(raw, dict):
        return {str(k).strip().lower(): dict(v) for k, v in raw.items() if isinstance(v, dict)}
    raise SystemExit("abonnes.json doit être un objet { email: {...} }")


def save(data: dict[str, dict]) -> None:
    ordered = dict(sorted(data.items(), key=lambda kv: kv[0]))
    ABONNES.write_text(
        json.dumps(ordered, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def gen_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> int:
    p = argparse.ArgumentParser(description="Ajoute ou met à jour un abonné (GitHub JSON)")
    p.add_argument("--email", required=True)
    p.add_argument("--statut", default=None, choices=STATUTS)
    p.add_argument("--offre", default=None, choices=OFFRES)
    p.add_argument("--notes", default=None)
    p.add_argument(
        "--depuis",
        default="",
        help="Date ISO (défaut : aujourd’hui si nouvel e-mail)",
    )
    p.add_argument(
        "--password",
        default=None,
        help="Mot de passe clair (sinon généré si nouveau compte ou --set-password)",
    )
    p.add_argument(
        "--set-password",
        action="store_true",
        help="Ne change que le mot de passe (email doit exister)",
    )
    args = p.parse_args()

    email = args.email.strip().lower()
    if "@" not in email:
        raise SystemExit("e-mail invalide")

    data = load()
    prev = data.get(email)

    if args.set_password:
        if not prev:
            raise SystemExit(f"Abonné introuvable : {email} (crée-le sans --set-password)")
        new_pw = args.password if args.password is not None else gen_password()
        prev["password"] = new_pw
        data[email] = prev
        save(data)
        print(f"Mot de passe mis à jour : {email}")
        print(f"Nouveau mot de passe (à communiquer une fois) : {new_pw}")
        print(f"Fichier : {ABONNES}")
        print("Ensuite : python site/build_membre_gate.py  puis deploy host")
        return 0

    is_new = prev is None
    prev = prev or {}
    statut = args.statut or prev.get("statut") or "actif"
    offre = args.offre or prev.get("offre") or "mensuel"
    depuis = (args.depuis or prev.get("depuis") or date.today().isoformat()).strip()
    notes = (
        args.notes
        if args.notes is not None
        else (prev.get("notes") or "")
    )
    notes = str(notes).strip()

    if args.password is not None:
        password = args.password
        pw_generated = False
    elif is_new or not (prev.get("password") or "").strip():
        password = gen_password()
        pw_generated = True
    else:
        password = str(prev["password"])
        pw_generated = False

    data[email] = {
        "statut": statut,
        "offre": offre,
        "depuis": depuis,
        "password": password,
        "notes": notes,
    }
    save(data)
    print(f"Abonné enregistré : {email} / {statut} / {offre}")
    if pw_generated or args.password is not None:
        print(f"Mot de passe (à communiquer une fois) : {password}")
    print(f"Fichier : {ABONNES}")
    print("Ensuite : python site/build_membre_gate.py  puis deploy host")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
