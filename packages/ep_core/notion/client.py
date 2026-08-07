"""Notion API client: databases, pages, blocks."""

from __future__ import annotations

import os
import time
from typing import Any, Iterator

from notion_client import Client
from notion_client.errors import APIResponseError

from .ids import to_uuid


def ssl_verify_from_env() -> bool:
    raw = (os.getenv("NOTION_SSL_VERIFY") or "0").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def make_notion_client(
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
            client=httpx.Client(verify=False, timeout=120.0),
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

    def get_page(self, page_id_or_url: str) -> dict[str, Any]:
        from .ids import to_uuid

        page_id = to_uuid(page_id_or_url)
        page = self.client.pages.retrieve(page_id=page_id)
        self._pause()
        return page

    def get_block_tree(self, block_id: str) -> list[dict[str, Any]]:
        block_id = to_uuid(block_id)
        children = self._list_children(block_id)
        for block in children:
            if block.get("has_children"):
                block["_children"] = self.get_block_tree(block["id"])
            else:
                block["_children"] = []
        return children

    def _list_children(self, block_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor = None
        while True:
            kwargs: dict[str, Any] = {"block_id": block_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            resp = self.client.blocks.children.list(**kwargs)
            self._pause()
            results.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
        return results
