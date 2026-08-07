"""Helpers CLI."""

from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def normalize_argv(argv: list[str], *, extra_colon_flags: tuple[str, ...] = ()) -> list[str]:
    known = ("page", "limit", "jobs", *extra_colon_flags)
    out: list[str] = []
    for a in argv:
        matched = False
        for name in known:
            prefix = f"--{name}:"
            if a.startswith(prefix) and not a.startswith(f"--{name}:="):
                out.extend([f"--{name}", a[len(prefix) :]])
                matched = True
                break
        if not matched:
            out.append(a)
    return out
