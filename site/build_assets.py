"""Génère démo publique (N cartes) + pack membres (HTML complet + gate mot de passe)."""

from __future__ import annotations

import hashlib
import random
import secrets
import shutil
import sys
from pathlib import Path

_SITE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SITE_DIR))

from _repo import SITE_ROOT, REPO_ROOT  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))

from flipcards.cli import load_matrice  # noqa: E402
from flipcards.generator import DEFAULT_PAGE_TITLE, FlipcardGenerator, sanitize_filename  # noqa: E402

DIST = SITE_ROOT / "dist"
DEMO_DIR = DIST / "demo"
MEMBERS_DIR = DIST / "members"


def _resolve_matrice() -> Path:
    try:
        from packages.ep_core.paths import resolve_path

        path = resolve_path("matrices_flipcards") / "flipcards_matrice.csv"
        if path.exists():
            return path
    except Exception:
        pass
    return REPO_ROOT / "flipcards" / "matrices" / "flipcards_matrice.csv"


def _flipcards_output_dir() -> Path:
    try:
        from packages.ep_core.paths import resolve_path

        return resolve_path("flipcards_output")
    except Exception:
        return REPO_ROOT / "output"


MATRICE = _resolve_matrice()
_OUTPUT = _flipcards_output_dir()
SOURCE_HTML = _OUTPUT / "20260804182655 - GADA.html"
FALLBACK_HTML = REPO_ROOT / "GADA-2026.html"
ALT_FALLBACK = _OUTPUT / "GADA 2026 FC.html"

# Démo publique (8 cartes) : Blanco, Prince Napoléon, Benjamin conservés ;
# les 5 autres privilégient des arrêts plus récents (répartition ★ maintenue).
DEMO_TITLES = [
    "TC, 1873, Blanco",
    "CE, 1875, Prince Napoléon",
    "CE, 1933, Benjamin",
    "CE, 2016, Czabaj",
    "CE, 2022, SNC Grasse-vacances",
    "CE, 2022, Asso. Les Amis de la Terre Fr.",
    "CE, 2021, Collectif des maires anti-pesticides",
    "CE, 2020, Fédé. CFDT des finances",
]


GATE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Accès abonnés — Flipcards</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<style>
  :root {
    --ink:#e8ebe6; --muted:#8b969e; --accent:#c4a35a; --bg:#0e1419;
    --card:#162028; --border:rgba(232,235,230,.12);
  }
  * { box-sizing: border-box; }
  body { margin:0; min-height:100vh; display:grid; place-items:center;
    font-family: "DM Sans", system-ui, sans-serif;
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse 80% 50% at 50% -10%, #1c2a35 0%, transparent 55%),
      radial-gradient(ellipse 40% 30% at 100% 80%, #1a2420 0%, transparent 45%);
    color: var(--ink); padding: 1.5rem; }
  .box { width:min(420px,100%); background:var(--card); border:1px solid var(--border); border-radius:2px; padding:1.75rem; }
  h1 { font-family: "Cormorant Garamond", "Times New Roman", serif; font-size:1.55rem; font-weight:600; margin:0 0 .35rem; }
  p { margin:0 0 1rem; color:var(--muted); font-size:.95rem; line-height:1.45; }
  label { display:block; font-size:.8rem; font-weight:600; margin-bottom:.35rem; }
  input { width:100%; padding:.7rem .8rem; border:1px solid var(--border); border-radius:2px; font-size:1rem;
    background:var(--bg); color:var(--ink); }
  button { margin-top:.9rem; width:100%; border:0; border-radius:2px; padding:.75rem 1rem; background:var(--accent); color:var(--bg);
    font-family:inherit; font-weight:600; cursor:pointer; }
  button:hover { filter:brightness(1.08); }
  .err { color:#f87171; font-size:.85rem; min-height:1.2em; margin-top:.5rem; }
  .links { margin-top:1.1rem; font-size:.9rem; line-height:1.6; }
  .links a { color:var(--accent); }
</style>
</head>
<body>
  <form class="box" id="gate" autocomplete="off">
    <h1>Accès abonnés</h1>
    <p>Flipcards complètes — réservées aux abonnés. Parcours normal : <a href="../membre/">connexion email + mot de passe</a>. Ci-dessous : accès admin (mdp partagé).</p>
    <label for="pw">Mot de passe admin</label>
    <input id="pw" name="pw" type="password" required autofocus>
    <button type="submit">Ouvrir les flipcards</button>
    <div class="err" id="err"></div>
    <div class="links">
      Pas encore abonné ?<br>
      <a href="../demo/">Essayer la démo (gratuit)</a><br>
      <a href="../checkout/">S’abonner</a><br>
      <a href="../membre/">Connexion membre (email + mdp)</a>
    </div>
  </form>
<script>
const HASH = __HASH__;
async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2,"0")).join("");
}
const form = document.getElementById("gate");
const err = document.getElementById("err");
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  err.textContent = "";
  const pw = document.getElementById("pw").value;
  const h = await sha256(pw);
  if (h !== HASH) { err.textContent = "Mot de passe incorrect."; return; }
  sessionStorage.setItem("flipcards_ok", "1");
  location.replace("./app.html");
});
</script>
</body>
</html>
"""

APP_GUARD = """<script>
(function(){
  var API = __AUTH_API_JSON__;
  var token = sessionStorage.getItem("flipcards_token") || localStorage.getItem("flipcards_token") || "";
  function deny() {
    sessionStorage.removeItem("flipcards_ok");
    location.replace("../membre/");
  }
  if (!token || !API || API.indexOf("EXAMPLE") !== -1) {
    // Fallback admin: ancien flag session uniquement si API pas encore déployée
    if (sessionStorage.getItem("flipcards_ok") === "1" && (!API || API.indexOf("EXAMPLE") !== -1)) {
      return;
    }
    if (!token) { deny(); return; }
  }
  fetch(API.replace(/\\/$/, "") + "/api/me", {
    headers: { Authorization: "Bearer " + token }
  }).then(function(r){
    if (!r.ok) throw new Error("nope");
    sessionStorage.setItem("flipcards_ok", "1");
  }).catch(function(){ deny(); });
})();
</script>
"""

def ensure_password(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    pw = secrets.token_urlsafe(9)
    path.write_text(pw + "\n", encoding="utf-8")
    return pw


def select_demo_rows(all_rows: list[dict[str, str]], titles: list[str]) -> list[dict[str, str]]:
    """Sélectionne les lignes démo par titre exact (Nom / title)."""
    by_title: dict[str, dict[str, str]] = {}
    for row in all_rows:
        for key in ("Nom", "title", "Titre de la décision"):
            t = (row.get(key) or "").strip()
            if t and t not in by_title:
                by_title[t] = row
    selected: list[dict[str, str]] = []
    missing: list[str] = []
    for title in titles:
        row = by_title.get(title)
        if not row:
            # tolère espaces doubles / variantes légères
            needle = " ".join(title.split())
            row = next(
                (
                    r
                    for t, r in by_title.items()
                    if " ".join(t.split()) == needle
                ),
                None,
            )
        if row:
            selected.append(row)
        else:
            missing.append(title)
    if missing:
        raise SystemExit("Titres démo introuvables dans la matrice : " + ", ".join(missing))
    return selected


def select_aside_rows(
    all_rows: list[dict[str, str]],
    exclude_titles: list[str],
    n: int = 15,
    *,
    seed: int = 42,
) -> list[dict[str, str]]:
    """Pool de N fiches hors lot d'étude pour « 3 au hasard » (sélection stable au build)."""
    exclude = {" ".join(t.split()) for t in exclude_titles}
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in all_rows:
        title = (row.get("Nom") or row.get("title") or "").strip()
        key = " ".join(title.split())
        if not key or key in exclude or key in seen:
            continue
        seen.add(key)
        candidates.append(row)
    if len(candidates) < n:
        raise SystemExit(
            f"Pas assez de fiches hors démo pour l'aside ({len(candidates)} < {n})"
        )
    rng = random.Random(seed)
    rng.shuffle(candidates)
    return candidates[:n]


def build_demo(limit: int = 8) -> Path:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = load_matrice(MATRICE)
    rows = select_demo_rows(all_rows, DEMO_TITLES)
    if limit and len(rows) > limit:
        rows = rows[:limit]
    aside = select_aside_rows(all_rows, DEMO_TITLES, n=15)
    gen = FlipcardGenerator()
    out = DEMO_DIR / "index.html"
    title = f"Démo — {sanitize_filename(DEFAULT_PAGE_TITLE)}"
    # Toutes les puces thème/notion ; celles absentes de la démo sont grisées
    # « 3 au hasard » : 15 fiches hors lot démo (tirage client parmi ce pool)
    gen.convert_many_html(
        rows,
        out,
        title=title,
        classifier_rows=all_rows,
        aside_rows=aside,
    )
    (DEMO_DIR / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    return out


def build_members(password: str, auth_api: str = "") -> Path:
    import json as _json

    MEMBERS_DIR.mkdir(parents=True, exist_ok=True)
    app = MEMBERS_DIR / "app.html"

    # Régénère depuis la matrice (filtre Importance inclus) ; sinon HTML déjà généré
    rows = load_matrice(MATRICE) if MATRICE.exists() else []
    if rows:
        gen = FlipcardGenerator()
        title = sanitize_filename(DEFAULT_PAGE_TITLE)
        gen.convert_many_html(rows, app, title=title)
        raw = app.read_text(encoding="utf-8")
    else:
        src = SOURCE_HTML if SOURCE_HTML.exists() else (
            FALLBACK_HTML if FALLBACK_HTML.exists() else ALT_FALLBACK
        )
        if not src.exists():
            raise SystemExit(
                f"HTML GADA introuvable ({SOURCE_HTML} / {FALLBACK_HTML}) "
                "et matrice absente"
            )
        raw = src.read_text(encoding="utf-8")

    if "importance_level" not in raw and "chip-importance" not in raw:
        # Force la version output avec Importance si le HTML source est obsolète
        if SOURCE_HTML.exists():
            raw = SOURCE_HTML.read_text(encoding="utf-8")

    api = (auth_api or "").strip() or "https://flipcards-auth.EXAMPLE.workers.dev"
    guard = APP_GUARD.replace("__AUTH_API_JSON__", _json.dumps(api))

    if "<head>" in raw:
        raw = raw.replace("<head>", "<head>\n" + guard, 1)
    else:
        raw = guard + raw
    app.write_text(raw, encoding="utf-8")

    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    gate = GATE_HTML.replace("__HASH__", json_dumps(digest))
    (MEMBERS_DIR / "index.html").write_text(gate, encoding="utf-8")
    (MEMBERS_DIR / "robots.txt").write_text(
        "User-agent: *\nDisallow: /\n", encoding="utf-8"
    )
    return MEMBERS_DIR / "index.html"


def json_dumps(s: str) -> str:
    import json

    return json.dumps(s)


def update_config(password: str) -> None:
    import json

    cfg_path = SITE_ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() else {}
    cfg["members_password"] = password
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    pw_path = SITE_ROOT / ".members_password"
    password = ensure_password(pw_path)
    demo = build_demo(8)

    import json

    cfg_path = SITE_ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() else {}
    auth_api = ((cfg.get("auth") or {}).get("api_url") or "").strip()

    members = build_members(password, auth_api=auth_api)
    update_config(password)
    # site root for Netlify: dist/site with demo + members
    site = DIST / "site"
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)
    shutil.copytree(DEMO_DIR, site / "demo")
    shutil.copytree(MEMBERS_DIR, site / "flipcards")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() else {}
    ls = cfg.get("lemonsqueezy") or {}
    stripe = cfg.get("stripe") or {}
    monthly = (
        ls.get("monthly_checkout_url")
        or stripe.get("monthly_payment_link")
        or ""
    )
    yearly = (
        ls.get("yearly_checkout_url")
        or stripe.get("yearly_payment_link")
        or ""
    )
    checkout_tpl = (SITE_ROOT / "templates" / "checkout.html").read_text(encoding="utf-8")
    checkout_tpl = (
        checkout_tpl.replace('monthly: ""', f"monthly: {json.dumps(monthly)}")
        .replace('yearly: ""', f"yearly: {json.dumps(yearly)}")
    )
    checkout_dst = site / "checkout"
    checkout_dst.mkdir(parents=True, exist_ok=True)
    (checkout_dst / "index.html").write_text(checkout_tpl, encoding="utf-8")

    base = (cfg.get("hosting") or {}).get("base_url") or ""

    # Page post-paiement (success URL Stripe)
    merci_tpl = (SITE_ROOT / "templates" / "merci.html").read_text(encoding="utf-8")
    merci_dst = site / "merci"
    merci_dst.mkdir(parents=True, exist_ok=True)
    (merci_dst / "index.html").write_text(merci_tpl, encoding="utf-8")
    cfg["merci_url"] = (
        f"{base.rstrip('/')}/merci/?session_id={{CHECKOUT_SESSION_ID}}"
        if base
        else "https://www.editions-particulieres.fr/merci/?session_id={CHECKOUT_SESSION_ID}"
    )

    # URL checkout dans config
    if base:
        cfg["checkout_url"] = f"{base.rstrip('/')}/checkout/"
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    home_tpl = (SITE_ROOT / "templates" / "home.html").read_text(encoding="utf-8")
    (site / "index.html").write_text(home_tpl, encoding="utf-8")
    for asset in ("site.css", "site-nav.js"):
        shutil.copy2(SITE_ROOT / "templates" / asset, site / asset)

    # Hubs intermédiaires Accueil → Bibliothèque / Amphithéâtre / TD
    for hub in ("bibliotheque", "ressources", "exercices"):
        hub_tpl = (SITE_ROOT / "templates" / f"{hub}.html").read_text(encoding="utf-8")
        hub_dir = site / hub
        hub_dir.mkdir(parents=True, exist_ok=True)
        (hub_dir / "index.html").write_text(hub_tpl, encoding="utf-8")

    # Pages légales obligatoires
    from build_legal import build_legal_page

    legal_tpl = (SITE_ROOT / "templates" / "legal-page.html").read_text(encoding="utf-8")
    legal_pages = (
        ("mentions-legales", "mentions-legales.md", "Mentions légales", "Mentions légales"),
        ("cgv", "cgv.md", "Conditions générales de vente (CGV)", "CGV"),
    )
    for slug, md_name, title, crumb in legal_pages:
        dst = site / slug
        dst.mkdir(parents=True, exist_ok=True)
        page = build_legal_page(
            SITE_ROOT / "legal" / md_name,
            legal_tpl,
            title=title,
            crumb=crumb,
        )
        (dst / "index.html").write_text(page, encoding="utf-8")

    (site / "_headers").write_text(
        """/flipcards/*
  X-Robots-Tag: noindex, nofollow
  Cache-Control: no-store
""",
        encoding="utf-8",
    )
    (site / "robots.txt").write_text(
        "User-agent: *\nDisallow: /flipcards/\nAllow: /demo/\n",
        encoding="utf-8",
    )
    custom_domain = ((cfg.get("hosting") or {}).get("custom_domain") or "").strip()
    if custom_domain:
        (site / "CNAME").write_text(f"{custom_domain}\n", encoding="utf-8")
    print(f"Démo : {demo}")
    print(f"Membres gate : {members}")
    print(f"Site Netlify : {site}")
    print(f"Mot de passe membres : {password}")
    print("(stocké dans SITE_ROOT/.members_password — ne pas committer)")

    # /membre/ + auth.js après rmtree(site)
    sys.path.insert(0, str(SITE_ROOT))
    from build_membre_gate import main as build_membre_main

    build_membre_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
