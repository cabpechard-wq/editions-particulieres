"""Liens Cours → pages du site (compat : délègue à site_links)."""

from __future__ import annotations

from typing import Any

from packages.ep_core.notion import NotionFetcher

from .manuel_tree import asset_prefix
from .site_links import (
    SiteLinkRegistry,
    build_glossary_slug_map,
    build_site_link_registry,
    rewrite_glossary_links,
    rewrite_site_links,
)

__all__ = [
    "SiteLinkRegistry",
    "build_glossary_slug_map",
    "build_site_link_registry",
    "rewrite_glossary_links",
    "rewrite_site_links",
    "dict_prefix_for_chapter",
    "dict_prefix_for_aside",
]


def dict_prefix_for_chapter(chapter: dict[str, Any]) -> str:
    return asset_prefix(len(chapter.get("segments") or []))


def dict_prefix_for_aside() -> str:
    return asset_prefix(2)


def build_registry(fetcher: NotionFetcher | None) -> SiteLinkRegistry:
    return build_site_link_registry(fetcher)
