"""Miroir manuel/dictionnaire depuis le site live (seed CI, évite l'export Notion)."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import warnings
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import httpx

OVH_RE = re.compile(r"Site en construction|OVHcloud|/__ovh/", re.I)
SKIP_HREF = re.compile(r"^(?:#|mailto:|tel:|javascript:)", re.I)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def under_section(url: str, section: str) -> bool:
    path = urlparse(url).path
    return path == f"/{section}" or path.startswith(f"/{section}/")


def dest_for_url(url: str, section: str, dest_root: Path) -> Path:
    path = urlparse(url).path
    if path.endswith("/"):
        rel = path[len(f"/{section}/") :]
        if not rel:
            return dest_root / section / "index.html"
        return dest_root / section / rel / "index.html"
    if path.endswith(".html"):
        rel = path[len(f"/{section}/") :]
        return dest_root / section / rel
    return dest_root / section / path[len(f"/{section}/") :] / "index.html"


def crawl_section(
    client: httpx.Client,
    base: str,
    section: str,
    dest_root: Path,
) -> int:
    start = urljoin(base.rstrip("/") + "/", f"{section}/")
    seen: set[str] = set()
    queue: deque[str] = deque([start])
    saved = 0

    while queue:
        url = queue.popleft()
        url, _ = urldefrag(url)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = client.get(url, follow_redirects=True)
        except httpx.HTTPError as exc:
            print(f"! GET {url} : {exc}", file=sys.stderr)
            continue
        if resp.status_code != 200:
            continue

        final = str(resp.url)
        if not under_section(final, section):
            continue

        text = resp.text
        if OVH_RE.search(text):
            raise RuntimeError(f"Page OVH détectée : {final}")

        out = dest_for_url(final, section, dest_root)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        saved += 1

        parser = LinkParser()
        try:
            parser.feed(text)
        except Exception:
            continue

        for href in parser.links:
            if not href or SKIP_HREF.search(href):
                continue
            linked = urljoin(final, href)
            linked, _ = urldefrag(linked)
            if "?" in linked:
                continue
            if not under_section(linked, section):
                continue
            if linked not in seen:
                queue.append(linked)

    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="https://www.editions-particulieres.fr",
        help="URL racine du site live",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("site/dist/site"),
        help="Dossier artefact Pages (site/dist/site)",
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        default=["manuel", "dictionnaire"],
        help="Sections à miroirer",
    )
    parser.add_argument(
        "--min-manuel-pages",
        type=int,
        default=15,
        help="Seuil minimal de pages manuel",
    )
    args = parser.parse_args()

    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    dest = args.out
    dest.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    with httpx.Client(verify=False, timeout=60.0, follow_redirects=True) as client:
        for section in args.sections:
            section_dest = dest / section
            if section_dest.exists():
                shutil.rmtree(section_dest)
            print(f"Seed {section} depuis {args.base} …")
            counts[section] = crawl_section(client, args.base, section, dest)
            print(f"  {counts[section]} page(s)")

    manuel_n = counts.get("manuel", 0)
    dict_n = counts.get("dictionnaire", 0)
    print(f"Seed pages : manuel={manuel_n} dictionnaire={dict_n}")

    if manuel_n < args.min_manuel_pages:
        print(
            f"::warning::Seed manuel incomplet ({manuel_n} pages, attendu >= {args.min_manuel_pages})",
            file=sys.stderr,
        )
        return 1
    if dict_n < 1:
        print("::warning::Seed dictionnaire vide", file=sys.stderr)
        return 1

    print("Seed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
