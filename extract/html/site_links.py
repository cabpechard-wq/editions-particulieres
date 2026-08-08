"""Registre Notion ID → URL site + réécriture des liens + pieds relationnels."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from packages.ep_core.notion import NotionFetcher, page_title
from packages.ep_core.notion.ids import to_uuid

from extract.word.pages import page_reference

from .arrets_render import slugify as arret_slugify
from .arrets_render import title_from_page as arret_title
from .dictionnaire_render import slugify as dict_slugify
from .manuel_tree import manuel_digits, pad_digits, path_segments_for

_NOTION_LINK_RE = re.compile(
    r'<a\s+href="(https://(?:www\.|app\.)?notion\.(?:so|com)/[^"]+)"\s+rel="noopener">(.*?)</a>',
    re.I | re.S,
)

_KIND_CLASS = {
    "index": "dict-link",
    "manuel": "manuel-link",
    "arrets": "arret-link",
}

_RELATION_ALIASES: dict[str, frozenset[str]] = {
    "manuel": frozenset({"manuel", "cours"}),
    "index": frozenset({"index", "glossaire", "dictionnaire"}),
    "jurisprudence": frozenset({"jurisprudence", "arrêts", "arrets", "arrêt", "arret"}),
}

_LABELS = {
    "manuel": "Cours",
    "index": "Index",
    "jurisprudence": "Jurisprudence",
}


@dataclass(frozen=True)
class SiteTarget:
    kind: str
    path: str  # chemin depuis la racine site, sans slash initial (ex. dictionnaire/#x)
    title: str

    @property
    def css_class(self) -> str:
        return _KIND_CLASS.get(self.kind, "site-link")


class SiteLinkRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, SiteTarget] = {}

    def __len__(self) -> int:
        return len({id(t) for t in self._by_id.values()})

    def counts(self) -> dict[str, int]:
        seen: dict[str, set[int]] = {"index": set(), "manuel": set(), "arrets": set()}
        for t in self._by_id.values():
            if t.kind in seen:
                seen[t.kind].add(id(t))
        return {k: len(v) for k, v in seen.items()}

    def add(self, page_id: str, target: SiteTarget) -> None:
        pid = (page_id or "").strip().lower()
        if not pid:
            return
        self._by_id[pid] = target
        self._by_id[pid.replace("-", "")] = target

    def resolve(self, url_or_id: str) -> SiteTarget | None:
        try:
            pid = to_uuid(url_or_id).lower()
        except ValueError:
            return None
        return self._by_id.get(pid) or self._by_id.get(pid.replace("-", ""))

    def href(self, target: SiteTarget, *, prefix: str) -> str:
        base = prefix if prefix.endswith("/") else f"{prefix}/"
        return f"{base}{target.path}"


def _norm(name: str) -> str:
    return (name or "").strip().casefold()


def relation_ids(props: dict[str, Any], *canonical: str) -> list[str]:
    """IDs d'une relation Notion (aliases inclus : manuel/cours, etc.)."""
    wanted: set[str] = set()
    for key in canonical:
        k = _norm(key)
        matched = False
        for group in _RELATION_ALIASES.values():
            if k in group:
                wanted |= set(group)
                matched = True
                break
        if not matched:
            wanted.add(k)
    for name, prop in props.items():
        if _norm(name) not in wanted:
            continue
        if prop.get("type") != "relation":
            continue
        return [r["id"] for r in (prop.get("relation") or []) if r.get("id")]
    return []


def _register_index(fetcher: NotionFetcher, reg: SiteLinkRegistry) -> None:
    from extract.pull._common import database_url

    db = database_url("index")
    for page in fetcher.iter_database_pages(db):
        pid = page.get("id") or ""
        term = (page_title(page) or "").strip()
        if not pid or not term:
            continue
        reg.add(
            pid,
            SiteTarget(kind="index", path=f"dictionnaire/#{dict_slugify(term)}", title=term),
        )


def _register_manuel(fetcher: NotionFetcher, reg: SiteLinkRegistry) -> None:
    from extract.pull._common import database_url

    db = database_url("manuel")
    for page in fetcher.iter_database_pages(db):
        pid = page.get("id") or ""
        if not pid:
            continue
        title = (page_title(page) or "").strip() or "Sans titre"
        digits = manuel_digits(page_reference(page))
        if not digits:
            continue
        segs = path_segments_for(pad_digits(digits))
        reg.add(
            pid,
            SiteTarget(
                kind="manuel",
                path="manuel/" + "/".join(segs) + "/",
                title=title,
            ),
        )


def _register_arrets(fetcher: NotionFetcher, reg: SiteLinkRegistry) -> None:
    from extract.pull._common import database_url

    db = database_url("jurisprudence")
    for page in fetcher.iter_database_pages(db):
        pid = page.get("id") or ""
        if not pid:
            continue
        title = arret_title(page)
        if not title or title == "Sans titre":
            continue
        reg.add(
            pid,
            SiteTarget(
                kind="arrets",
                path=f"arrets/{arret_slugify(title)}/",
                title=title,
            ),
        )


def build_site_link_registry(
    fetcher: NotionFetcher | None,
    *,
    include: Iterable[str] = ("index", "manuel", "arrets"),
) -> SiteLinkRegistry:
    reg = SiteLinkRegistry()
    if fetcher is None:
        return reg
    wanted = {_norm(x) for x in include}
    try:
        if "index" in wanted:
            _register_index(fetcher, reg)
    except Exception:
        pass
    try:
        if "manuel" in wanted:
            _register_manuel(fetcher, reg)
    except Exception:
        pass
    try:
        if "arrets" in wanted or "jurisprudence" in wanted:
            _register_arrets(fetcher, reg)
    except Exception:
        pass
    return reg


def rewrite_site_links(body: str, registry: SiteLinkRegistry, *, prefix: str) -> str:
    """Remplace les liens Notion connus par des URLs du site."""
    if not body or not registry:
        return body

    def repl(m: re.Match[str]) -> str:
        target = registry.resolve(m.group(1))
        if not target:
            return m.group(0)
        href = registry.href(target, prefix=prefix)
        return (
            f'<a class="{target.css_class}" '
            f'href="{html.escape(href, quote=True)}">{m.group(2)}</a>'
        )

    return _NOTION_LINK_RE.sub(repl, body)


def render_relation_extras(
    props: dict[str, Any],
    registry: SiteLinkRegistry,
    *,
    keys: Iterable[str],
    prefix: str,
    resolve_title: Callable[[str], str] | None = None,
    section: bool = True,
) -> str:
    """Liens relationnels Notion → pages du site (pied de page ou lignes dict-extra)."""
    link_bits: list[str] = []
    dict_blocks: list[str] = []

    for key in keys:
        ids = relation_ids(props, key)
        if not ids:
            continue
        row_links: list[str] = []
        for pid in ids:
            target = registry.resolve(pid)
            if not target:
                continue
            href = registry.href(target, prefix=prefix)
            title = target.title
            if resolve_title:
                try:
                    resolved = (resolve_title(pid) or "").strip()
                    if resolved:
                        title = resolved
                except Exception:
                    pass
            row_links.append(
                f'<a class="{target.css_class}" '
                f'href="{html.escape(href, quote=True)}">{html.escape(title)}</a>'
            )
        if not row_links:
            continue
        if section:
            link_bits.extend(row_links)
        else:
            label = _LABELS.get(_norm(key), key.strip().capitalize())
            dict_blocks.append(
                f'<p class="dict-extra">{label} : {" · ".join(row_links)}</p>'
            )

    if section:
        if not link_bits:
            return ""
        sep = '<span class="site-linked-resources-sep" aria-hidden="true">·</span>'
        return (
            '<aside class="site-linked-resources" aria-label="Ressources liées">'
            '<p class="site-linked-resources-title">Ressources liées…</p>'
            f'<p class="site-linked-resources-links">{sep.join(link_bits)}</p>'
            "</aside>"
        )
    return "\n".join(dict_blocks)


# Compat : anciennes API manuel_links
def build_glossary_slug_map(fetcher: NotionFetcher | None) -> dict[str, str]:
    reg = build_site_link_registry(fetcher, include=("index",))
    out: dict[str, str] = {}
    for pid, target in reg._by_id.items():
        if target.kind == "index" and "#" in target.path:
            out[pid] = target.path.split("#", 1)[1]
    return out


def rewrite_glossary_links(body: str, slug_map: dict[str, str], *, dict_prefix: str) -> str:
    """Compat : glossaire seul (préfère rewrite_site_links)."""
    if not slug_map or not body:
        return body
    reg = SiteLinkRegistry()
    for pid, slug in slug_map.items():
        reg.add(pid, SiteTarget(kind="index", path=f"dictionnaire/#{slug}", title=slug))
    return rewrite_site_links(body, reg, prefix=dict_prefix)
