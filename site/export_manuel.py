"""Génère /manuel/ (sommaire + chapitres imbriqués) depuis Notion, via notion_to_word.

Chaîne : Notion (API) -> .docx (notion_to_word/manuel)
         -> HTML (pandoc) -> pages du site (gabarits SITE_ROOT/templates/manuel-*.html).

Arborescence : le référencement DP-XXX est invariable.
  Chaque chiffre significatif = un niveau
  → /manuel/dp-100/dp-110/index.html, etc.

Fiches DP-XXX/X ou DP-XXX/XX (ex. DP-100/1, DP-311_1) : registre actualité,
mises de côté dans /manuel/_aside/ (hors sommaire et menu).

Usage :
    python site/export_manuel.py [--limit N] [--reuse]

IMPORTANT : lancer APRÈS SITE_ROOT/build_assets.py (qui recrée dist/site).
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SITE_ROOT = Path(__file__).resolve().parent
TEMPLATES = SITE_ROOT / "templates"
SITE = SITE_ROOT / "dist" / "site"
MANUEL_DIR = SITE / "manuel"
ASIDE_DIR = MANUEL_DIR / "_aside"

# DP-311, DP-100 — manuel
_RE_MANUEL = re.compile(r"^DP-(\d+)$", re.I)
# DP-100/1, DP-100/12, DP-311_1 (slash sanitizé en _) — actualité
_RE_ACTUALITE = re.compile(r"^DP-(\d+)[/ _](\d+)$", re.I)


def ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def load_config() -> dict[str, Any]:
    cfg_path = SITE_ROOT / "config.json"
    return json.loads(cfg_path.read_text(encoding="utf-8-sig"))


def extract_ref_from_stem(stem: str) -> str:
    """stem = 'AAAAMMJJhhmmss - {Référence} - {Titre}' → référence."""
    parts = (stem or "").split(" - ")
    if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 14:
        return parts[1].strip()
    return ""


def normalize_ref(ref: str) -> str:
    """Unifie DP-100/1 et DP-100_1 → DP-100/1 pour affichage."""
    ref = (ref or "").strip()
    m = _RE_ACTUALITE.match(ref.replace("_", "/"))
    if m:
        return f"DP-{m.group(1)}/{m.group(2)}"
    m = _RE_MANUEL.match(ref)
    if m:
        return f"DP-{m.group(1)}"
    return ref


def is_actualite_ref(ref: str) -> bool:
    """DP-XXX/X ou DP-XXX/XX (slash ou underscore)."""
    return bool(_RE_ACTUALITE.match((ref or "").strip().replace("_", "/")))


def manuel_digits(ref: str) -> str | None:
    """DP-311 → '311' ; sinon None."""
    m = _RE_MANUEL.match((ref or "").strip())
    if not m:
        return None
    return m.group(1)


def pad_digits(digits: str, width: int = 3) -> str:
    d = (digits or "").lstrip("0") or "0"
    if d == "0":
        return "0" * width
    return d.ljust(width, "0") if len(d) <= width else d


def parent_digits(digits: str) -> str | None:
    """Parent Dewey-like : 311→310, 310→300, 300→000, 000→None."""
    d = (digits or "").rstrip("0")
    if not d:
        return None
    parent_sig = d[:-1]
    if not parent_sig:
        return "000"
    width = max(3, len(digits))
    return parent_sig.ljust(width, "0")


def ancestor_chain(digits: str) -> list[str]:
    """['000','300','310','311'] pour 311."""
    chain: list[str] = []
    cur: str | None = pad_digits(digits)
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = parent_digits(cur)
    chain.reverse()
    return chain


def segment_for(digits: str) -> str:
    return f"dp-{digits.lower()}"


def path_segments_for(digits: str) -> list[str]:
    """Segments d'URL sous /manuel/ : dp-100/dp-110."""
    return [segment_for(d) for d in ancestor_chain(digits)]


def rel_between(from_segs: list[str], to_segs: list[str]) -> str:
    """Lien relatif d'une page (dans from_segs/) vers to_segs/."""
    i = 0
    while i < len(from_segs) and i < len(to_segs) and from_segs[i] == to_segs[i]:
        i += 1
    up = "../" * (len(from_segs) - i)
    down = "/".join(to_segs[i:])
    if down:
        return f"{up}{down}/"
    return up or "./"


def asset_prefix(depth: int) -> str:
    """depth = nb de segments sous manuel/ (ex. dp-100/dp-110 → 2)."""
    return "../" * (depth + 1)


def run_notion_export(pipeline_dir: Path, database_url: str, out_dir: Path, limit: int | None) -> None:
    venv_python = pipeline_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        raise SystemExit(
            f"Python introuvable dans le venv du pipeline : {venv_python}\n"
            "Vérifie SITE_ROOT/config.json -> manuel.pipeline_dir."
        )
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(venv_python),
        "-m",
        "manuel",
        "--database",
        database_url,
        "--format",
        "docx",
        "--out",
        str(out_dir),
    ]
    if limit:
        cmd += ["--limit", str(limit)]

    print(f"> Export Notion -> docx ({pipeline_dir.name})…")
    proc = subprocess.run(
        cmd,
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise SystemExit("Échec de l'export Notion (voir ci-dessus).")


def load_manifest_entries(out_dir: Path) -> list[dict[str, Any]]:
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifeste introuvable : {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("entries") or {}
    return [e for e in entries.values() if e.get("registre") == "manuel"]


def docx_to_html(docx_path: Path) -> str:
    if shutil.which("pandoc") is None:
        raise SystemExit("pandoc introuvable sur le PATH. Installe pandoc puis relance.")
    proc = subprocess.run(
        ["pandoc", str(docx_path), "-f", "docx", "-t", "html", "--wrap=none"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise SystemExit(f"pandoc a échoué sur {docx_path.name} :\n{proc.stderr}")
    return proc.stdout


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def strip_title_paragraph(html: str, title: str) -> str:
    m = re.match(r"^\s*<p>(.*?)</p>\s*", html, flags=re.DOTALL)
    if not m:
        return html
    text = re.sub(r"<[^>]+>", "", m.group(1))
    if _normalize_ws(text).casefold() == _normalize_ws(title or "").casefold():
        return html[m.end() :]
    return html


def sort_key_ref(ref: str) -> tuple:
    """Tri alphanumérique sur la référence normalisée."""
    parts = re.split(r"(\d+)", (ref or "").strip())
    key: list = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.casefold()))
    return tuple(key)


def effective_parent(digits: str, by_digits: dict[str, dict[str, Any]]) -> str | None:
    """Parent le plus proche présent dans le jeu (saute les maillons manquants)."""
    p = parent_digits(digits)
    while p is not None and p not in by_digits:
        p = parent_digits(p)
    return p


def build_nav_tree_html(
    chapters: list[dict[str, Any]],
    *,
    from_segs: list[str] | None,
    current_digits: str | None = None,
    skip_root: bool = False,
) -> str:
    """Menu arborescent (ul imbriqués) ; liens relatifs depuis from_segs (None = sommaire)."""
    by_digits = {ch["digits"]: ch for ch in chapters}
    children: dict[str | None, list[dict[str, Any]]] = {}
    for ch in chapters:
        p = effective_parent(ch["digits"], by_digits)
        children.setdefault(p, []).append(ch)
    for kids in children.values():
        kids.sort(key=lambda c: sort_key_ref(c["ref"]))

    def href_for(ch: dict[str, Any]) -> str:
        if from_segs is None:
            return "./" + "/".join(ch["segments"]) + "/"
        return rel_between(from_segs, ch["segments"])

    def render(parent: str | None) -> str:
        kids = children.get(parent) or []
        if not kids:
            return ""
        lines = ["<ul>"]
        for ch in kids:
            active = ch["digits"] == current_digits
            cls = ' class="is-current"' if active else ""
            lines.append(
                f"<li{cls}>"
                f'<a href="{href_for(ch)}">'
                f'<span class="nav-title">{ch["title_esc"]}</span>'
                f"</a>"
            )
            nested = render(ch["digits"])
            if nested:
                lines.append(nested)
            lines.append("</li>")
        lines.append("</ul>")
        return "\n".join(lines)

    roots = children.get(None) or []
    if skip_root and len(roots) == 1:
        return render(roots[0]["digits"])
    return render(None)


def build_breadcrumb_html(chapter: dict[str, Any], by_digits: dict[str, dict[str, Any]]) -> str:
    prefix = asset_prefix(len(chapter["segments"]))
    bits = [
        '<span>Éditions Particulières</span>',
        '<span class="sep">›</span>',
        f'<a href="{prefix}index.html">Droit public et administratif</a>',
        '<span class="sep">›</span>',
        f'<a href="{prefix}bibliotheque/">Bibliothèque universitaire</a>',
        '<span class="sep">›</span>',
        f'<a href="{rel_between(chapter["segments"], [])}">Manuel</a>',
    ]
    for dig in chapter["ancestors"]:
        ch = by_digits.get(dig)
        if not ch:
            continue
        if dig == chapter["digits"]:
            bits.append('<span class="sep">›</span>')
            bits.append(f'<strong>{ch["title_esc"]}</strong>')
        else:
            href = rel_between(chapter["segments"], ch["segments"])
            bits.append('<span class="sep">›</span>')
            bits.append(f'<a href="{href}">{ch["title_esc"]}</a>')
    return "\n    ".join(bits)


def render_chapter_link(
    chapter: dict[str, Any] | None,
    *,
    kind: str,
    from_segs: list[str],
) -> str:
    if chapter is None:
        return ""
    label = "Chapitre précédent" if kind == "prev" else "Chapitre suivant"
    css = "manuel-chapternav-prev" if kind == "prev" else "manuel-chapternav-next"
    href = rel_between(from_segs, chapter["segments"])
    return (
        f'    <a class="{css}" href="{href}">'
        f'<span>{label}</span>{chapter["title_esc"]}</a>'
    )


def write_aside_readme(aside_chapters: list[dict[str, Any]]) -> None:
    ASIDE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fiches mises de cote — registre actualite",
        "",
        "Hors arborescence du manuel ; destinees a un autre registre de ressources.",
        "",
    ]
    for ch in aside_chapters:
        lines.append(f"- {ch['title']} → `{ch['slug']}/`")
    (ASIDE_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Limite le nombre de pages (test).")
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="Réutilise flipcards_site_export sans rappeler Notion.",
    )
    args = parser.parse_args()

    if not SITE.exists():
        raise SystemExit("SITE_ROOT/dist/site introuvable — lance d'abord : python site/build_assets.py")

    cfg = load_config()
    manuel_cfg = cfg.get("manuel") or {}
    database_url = (manuel_cfg.get("notion_database_url") or "").strip()
    pipeline_dir = Path((manuel_cfg.get("pipeline_dir") or "").strip())
    if not database_url or not pipeline_dir:
        raise SystemExit("SITE_ROOT/config.json -> manuel.notion_database_url / manuel.pipeline_dir manquants.")
    if not pipeline_dir.exists():
        raise SystemExit(f"Dossier pipeline introuvable : {pipeline_dir}")

    export_dir = pipeline_dir / "flipcards_site_export"
    if args.reuse:
        if not (export_dir / "manifest.json").exists():
            raise SystemExit(f"--reuse : manifeste introuvable dans {export_dir}")
        print(f"> Réutilisation de l'export existant : {export_dir}")
    else:
        run_notion_export(pipeline_dir, database_url, export_dir, args.limit)

    entries = load_manifest_entries(export_dir)
    if not entries:
        raise SystemExit("Aucune page 'manuel' exportée — vérifie la base Notion / le token.")

    print(f"> {len(entries)} page(s) — classification manuel / actualité…")
    chapters: list[dict[str, Any]] = []
    aside: list[dict[str, Any]] = []
    skipped: list[str] = []

    for entry in entries:
        title = entry.get("title") or "Sans titre"
        stem = entry.get("stem") or title
        raw_ref = extract_ref_from_stem(stem)
        # Si stem sans horodatage, tente la ref depuis le début du stem
        if not raw_ref and stem.upper().startswith("DP-"):
            raw_ref = stem.split(" - ")[0].strip()
        ref = normalize_ref(raw_ref) if raw_ref else ""

        docx_path = export_dir / entry["relpath"]
        if not docx_path.exists():
            skipped.append(f"fichier manquant : {entry.get('relpath')}")
            continue
        html = docx_to_html(docx_path)
        html = strip_title_paragraph(html, title)

        if is_actualite_ref(raw_ref or ref):
            # slug stable pour _aside
            safe = re.sub(r"[^a-zA-Z0-9]+", "-", (raw_ref or ref).lower()).strip("-")
            aside.append(
                {
                    "title": title,
                    "title_esc": html_mod.escape(title),
                    "ref": normalize_ref(raw_ref or ref),
                    "ref_esc": html_mod.escape(normalize_ref(raw_ref or ref)),
                    "slug": safe or "fiche",
                    "body": html,
                }
            )
            continue

        digits = manuel_digits(ref)
        if not digits:
            skipped.append(f"réf. hors schéma DP-XXX : {raw_ref!r} ({title})")
            continue

        digits = pad_digits(digits)
        segs = path_segments_for(digits)
        chapters.append(
            {
                "title": title,
                "title_esc": html_mod.escape(title),
                "ref": f"DP-{digits}",
                "ref_esc": html_mod.escape(f"DP-{digits}"),
                "digits": digits,
                "ancestors": ancestor_chain(digits),
                "segments": segs,
                "depth": len(segs),
                "body": html,
            }
        )

    chapters.sort(key=lambda c: sort_key_ref(c["ref"]))
    by_digits = {c["digits"]: c for c in chapters}

    # Avertir si un parent manquant dans la chaîne
    for ch in chapters:
        p = parent_digits(ch["digits"])
        if p and p not in by_digits and p != "000":
            print(f"! Parent manquant pour {ch['ref']} (attendu DP-{p})")

    if MANUEL_DIR.exists():
        shutil.rmtree(MANUEL_DIR)
    MANUEL_DIR.mkdir(parents=True, exist_ok=True)

    page_tpl = (TEMPLATES / "manuel-page.html").read_text(encoding="utf-8")
    for i, ch in enumerate(chapters):
        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i + 1 < len(chapters) else None
        prefix = asset_prefix(ch["depth"])
        nav = build_nav_tree_html(chapters, from_segs=ch["segments"], current_digits=ch["digits"])
        crumb = build_breadcrumb_html(ch, by_digits)
        page = (
            page_tpl            .replace("{{TITLE}}", ch["title_esc"])
            .replace("{{CRUMB_TRAIL}}", crumb)
            .replace("{{BODY}}", ch["body"])
            .replace("{{ASSET_PREFIX}}", prefix)
            .replace("{{NAV_TREE}}", nav)
            .replace("{{TOC_HREF}}", rel_between(ch["segments"], []))
            .replace("{{PREV_LINK}}", render_chapter_link(prev_ch, kind="prev", from_segs=ch["segments"]))
            .replace("{{NEXT_LINK}}", render_chapter_link(next_ch, kind="next", from_segs=ch["segments"]))
        )
        chapter_dir = MANUEL_DIR.joinpath(*ch["segments"])
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (chapter_dir / "index.html").write_text(page, encoding="utf-8")

    # Actualité → _aside (hors navigation)
    if aside:
        ASIDE_DIR.mkdir(parents=True, exist_ok=True)
        aside_tpl = page_tpl  # même gabarit, nav vide
        for ch in aside:
            prefix = asset_prefix(2)  # manuel/_aside/slug/
            page = (
                aside_tpl                .replace("{{TITLE}}", ch["title_esc"])
                .replace(
                    "{{CRUMB_TRAIL}}",
                    '<span>Éditions Particulières</span>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <a href="{prefix}index.html">Droit public et administratif</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <a href="{prefix}bibliotheque/">Bibliothèque universitaire</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <a href="../">Manuel</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <strong>{ch["title_esc"]}</strong>',
                )
                .replace("{{BODY}}", ch["body"])
                .replace("{{ASSET_PREFIX}}", prefix)
                .replace("{{NAV_TREE}}", "")
                .replace("{{TOC_HREF}}", "../")
                .replace("{{PREV_LINK}}", "")
                .replace("{{NEXT_LINK}}", "")
            )
            d = ASIDE_DIR / ch["slug"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(page, encoding="utf-8")
        write_aside_readme(aside)

    sommaire_tpl = (TEMPLATES / "manuel-sommaire.html").read_text(encoding="utf-8")
    nav_sommaire = build_nav_tree_html(chapters, from_segs=None, skip_root=True)
    sommaire = (
        sommaire_tpl.replace("{{NAV_TREE}}", nav_sommaire)
        .replace("{{CHAPTER_COUNT}}", str(len(chapters)))
        .replace("{{ASIDE_NOTE}}", "")
    )
    (MANUEL_DIR / "index.html").write_text(sommaire, encoding="utf-8")

    # CSS / nav à jour même si build_assets n'a pas été relancé
    for asset in ("site.css", "site-nav.js"):
        src = TEMPLATES / asset
        if src.exists():
            shutil.copy2(src, SITE / asset)

    print(f"OK : {len(chapters)} chapitre(s) manuel → {MANUEL_DIR}")
    if aside:
        print(f"   {len(aside)} fiche(s) actualité → {ASIDE_DIR}")
    if skipped:
        print(f"   {len(skipped)} ignorée(s) :")
        for s in skipped[:12]:
            print(f"     - {s}")
    print("N'oublie pas de synchroniser SITE_ROOT/dist/site/ vers SITE_ROOT/host-repo/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
