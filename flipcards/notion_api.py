"""Notion API : data source, pages, propriétés (sous-ensemble flipcards)."""

from __future__ import annotations

import os
import time
from typing import Any, Iterator

from notion_client import Client
from notion_client.errors import APIResponseError

from .ids import page_url_from_id, to_uuid


def ssl_verify_from_env() -> bool:
    raw = (os.getenv("NOTION_SSL_VERIFY") or "0").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def make_notion_fetcher(
    token: str,
    *,
    pause_s: float = 0.35,
    verify: bool | None = None,
) -> "NotionFetcher":
    fetcher = NotionFetcher(token, pause_s=pause_s)
    use_verify = ssl_verify_from_env() if verify is None else verify
    if not use_verify:
        import httpx

        fetcher.client = Client(
            auth=token,
            client=httpx.Client(verify=False, timeout=60.0),
        )
    return fetcher


class NotionFetcher:
    def __init__(self, token: str, *, pause_s: float = 0.35):
        self.client = Client(auth=token)
        self.pause_s = pause_s

    def _pause(self) -> None:
        if self.pause_s:
            time.sleep(self.pause_s)

    def resolve_data_source_id(self, database_id_or_url: str) -> str:
        db_id = to_uuid(database_id_or_url)
        try:
            db = self.client.databases.retrieve(database_id=db_id)
            self._pause()
        except APIResponseError:
            try:
                self.client.data_sources.retrieve(data_source_id=db_id)
                self._pause()
                return db_id
            except APIResponseError as e:
                raise ValueError(
                    f"Impossible de récupérer la base / data source {db_id}: {e}"
                ) from e

        sources = db.get("data_sources") or []
        if not sources:
            return db_id
        return sources[0]["id"]

    def iter_database_pages(
        self,
        database_id_or_url: str,
        *,
        limit: int | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> Iterator[dict[str, Any]]:
        data_source_id = self.resolve_data_source_id(database_id_or_url)
        cursor = None
        yielded = 0
        use_sorts = bool(sorts)

        while True:
            kwargs: dict[str, Any] = {
                "data_source_id": data_source_id,
                "page_size": 100,
            }
            if cursor:
                kwargs["start_cursor"] = cursor
            if use_sorts and sorts:
                kwargs["sorts"] = sorts

            try:
                resp = self.client.data_sources.query(**kwargs)
            except APIResponseError:
                if use_sorts and "sorts" in kwargs:
                    use_sorts = False
                    kwargs.pop("sorts", None)
                    resp = self.client.data_sources.query(**kwargs)
                else:
                    raise
            self._pause()

            for page in resp.get("results", []):
                if page.get("object") != "page":
                    continue
                if page.get("archived") or page.get("in_trash"):
                    continue
                yield page
                yielded += 1
                if limit is not None and yielded >= limit:
                    return

            if not resp.get("has_more"):
                return
            cursor = resp.get("next_cursor")


def page_title(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title") or []
            text = "".join(p.get("plain_text", "") for p in parts).strip()
            if text:
                return text
    return page.get("id", "sans-titre")


def property_plain(prop: dict[str, Any]) -> str:
    t = prop.get("type")
    if not t:
        return ""
    val = prop.get(t)

    if t == "title":
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t == "select":
        return (val or {}).get("name") or ""
    if t == "status":
        return (val or {}).get("name") or ""
    if t == "multi_select":
        return ", ".join(x.get("name", "") for x in (val or []) if x.get("name"))
    if t == "date":
        if not val:
            return ""
        start = val.get("start") or ""
        end = val.get("end")
        return f"{start} → {end}" if end else start
    if t == "number":
        return "" if val is None else str(val)
    if t == "checkbox":
        return "Oui" if val else "Non"
    if t == "url":
        return val or ""
    if t == "relation":
        return ", ".join(page_url_from_id(r["id"]) for r in (val or []) if r.get("id"))
    if t == "formula":
        if not val:
            return ""
        ft = val.get("type")
        return "" if val.get(ft) is None else str(val.get(ft))
    if t == "created_time" or t == "last_edited_time":
        return val or ""
    return ""
