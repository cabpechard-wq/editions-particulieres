"""Génère /membre/ (+ forgot/reset/compte) et auth.js depuis les templates API."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
SITE = SITE_ROOT / "dist" / "site"
MEMBRE = SITE / "membre"
TEMPLATES = SITE_ROOT / "templates"


def auth_api_url(cfg: dict) -> str:
    auth = cfg.get("auth") or {}
    url = (auth.get("api_url") or "").strip().rstrip("/")
    if not url:
        # Placeholder jusqu’au déploiement Worker
        url = "https://flipcards-auth.EXAMPLE.workers.dev"
    return url


def inject_auth(js_or_html: str, api: str) -> str:
    return js_or_html.replace("__AUTH_API__", api)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    cfg = json.loads((SITE_ROOT / "config.json").read_text(encoding="utf-8-sig"))
    api = auth_api_url(cfg)

    SITE.mkdir(parents=True, exist_ok=True)
    auth_js = inject_auth(
        (TEMPLATES / "auth.js").read_text(encoding="utf-8"),
        api,
    )
    write(SITE / "auth.js", auth_js)
    for asset in ("site.css", "site-nav.js"):
        shutil.copy2(TEMPLATES / asset, SITE / asset)

    pages = [
        ("membre.html", MEMBRE / "index.html"),
        ("membre-forgot.html", MEMBRE / "forgot" / "index.html"),
        ("membre-reset.html", MEMBRE / "reset" / "index.html"),
        ("membre-compte.html", MEMBRE / "compte" / "index.html"),
    ]
    for src_name, dst in pages:
        html = inject_auth((TEMPLATES / src_name).read_text(encoding="utf-8"), api)
        write(dst, html)

    write(MEMBRE / "robots.txt", "User-agent: *\nDisallow: /\n")

    base = (cfg.get("hosting") or {}).get("base_url") or (
        "https://cabpechard-wq.github.io/editions-particulieres"
    )
    cfg.setdefault("sotion", {})
    cfg["sotion"]["site_url"] = f"{base.rstrip('/')}/membre/"
    cfg["sotion"]["provider"] = "cloudflare-worker"
    cfg["sotion"]["notes"] = (
        "Auth via Cloudflare Worker + KV + Resend. "
        "Front: /membre/ login, forgot, reset, compte."
    )
    cfg.setdefault("auth", {})
    cfg["auth"]["api_url"] = api
    cfg["auth"]["min_password_length"] = 4
    (SITE_ROOT / "config.json").write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Membre pages : {MEMBRE}")
    print(f"auth.js API : {api}")
    if "EXAMPLE" in api:
        print("ATTENTION : configure auth.api_url après wrangler deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
