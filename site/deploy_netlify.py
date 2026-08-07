"""Déploie SITE_ROOT/dist/site vers Netlify (draft puis prod) et met à jour config.json."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _repo import REPO_ROOT as ROOT
SITE_ROOT = Path(__file__).resolve().parent
SITE = SITE_ROOT / "dist" / "site"
CFG = SITE_ROOT / "config.json"
NETLIFY_DIR = SITE_ROOT / ".netlify"


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess:
    print(">", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=str(SITE_ROOT),
        env=env or os.environ.copy(),
        text=True,
        capture_output=True,
    )


def ensure_netlify_cli() -> list[str]:
    if which("netlify"):
        return ["netlify"]
    # npx
    node_dir = ROOT / ".tools" / "node-v22.14.0-win-x64"
    npx = node_dir / "npx.cmd"
    if npx.exists():
        return [str(npx), "--yes", "netlify-cli@17"]
    if which("npx"):
        return ["npx", "--yes", "netlify-cli@17"]
    raise SystemExit("Node/npx introuvable pour Netlify CLI")


def main() -> int:
    if not SITE.exists():
        print("Lance d'abord : python site/build_assets.py", file=sys.stderr)
        return 1

    cfg = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    cli = ensure_netlify_cli()

    # Auth : NETLIFY_AUTH_TOKEN dans env ou .env
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(SITE_ROOT / ".env")
    token = (os.getenv("NETLIFY_AUTH_TOKEN") or "").strip()
    env = os.environ.copy()
    if token:
        env["NETLIFY_AUTH_TOKEN"] = token

    # Site name hint
    site_name = cfg.get("hosting", {}).get("site_name") or "flipcards-gada-members"

    # Deploy production (crée un site si besoin)
    args = cli + [
        "deploy",
        "--dir",
        str(SITE),
        "--prod",
        "--message",
        "flipcards SITE_ROOT v1",
    ]
    if token:
        # non-interactive create
        args += ["--site", site_name]
    else:
        # tenter deploy sans token → URL draft parfois possible? Non, auth requise.
        print(
            "NETLIFY_AUTH_TOKEN manquant.\n"
            "1) Crée un compte https://app.netlify.com\n"
            "2) User settings → Applications → New access token\n"
            "3) Ajoute NETLIFY_AUTH_TOKEN=... dans .env puis relance.\n"
            "Fallback : déploiement manuel du dossier SITE_ROOT/dist/site",
            file=sys.stderr,
        )
        # Écrit un script helper
        helper = SITE_ROOT / "deploy_manual.txt"
        helper.write_text(
            "Déployer le dossier SITE_ROOT/dist/site sur Netlify Drop :\n"
            "https://app.netlify.com/drop\n"
            "Puis reporter l'URL dans SITE_ROOT/config.json (demo_url, flipcards_url).\n",
            encoding="utf-8",
        )
        return 2

    proc = run(args, env=env)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        # Essai : créer le site puis redéployer
        create = run(
            cli
            + [
                "sites:create",
                "--name",
                site_name,
                "--account-slug",
                os.getenv("NETLIFY_ACCOUNT_SLUG", ""),
            ],
            env=env,
        )
        print(create.stdout)
        print(create.stderr, file=sys.stderr)
        proc = run(
            cli
            + [
                "deploy",
                "--dir",
                str(SITE),
                "--prod",
                "--site",
                site_name,
                "--message",
                "flipcards SITE_ROOT v1",
            ],
            env=env,
        )
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return proc.returncode

    # Extraire URL
    url = ""
    for line in (proc.stdout or "").splitlines():
        if "https://" in line and "netlify.app" in line:
            # Website URL / Unique deploy URL
            for part in line.split():
                if part.startswith("https://") and "netlify.app" in part:
                    url = part.strip()
    if not url:
        # lire .netlify/state.json
        state = NETLIFY_DIR / "state.json"
        if state.exists():
            st = json.loads(state.read_text(encoding="utf-8"))
            sid = st.get("siteId")
            print(f"siteId={sid}")

    if url:
        base = url.rstrip("/")
        cfg.setdefault("hosting", {})
        cfg["hosting"]["site_name"] = site_name
        cfg["hosting"]["base_url"] = base
        cfg["demo_url"] = f"{base}/demo/"
        cfg["flipcards_url"] = f"{base}/flipcards/"
        CFG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"demo_url={cfg['demo_url']}")
        print(f"flipcards_url={cfg['flipcards_url']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
