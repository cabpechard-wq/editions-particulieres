"""Passe finale de finiolage typographique français (espace insécable, etc.)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from docx.oxml.ns import qn

NBSP = "\u00a0"

_DEGREE_STICKY = ",.;:!?)»]…'\"”’"
_DEGREE_STICKY_RE = re.escape(_DEGREE_STICKY)

_ABBREV_NUM = re.compile(
    rf"(?i)\b("
    rf"art\.|al\.|alinéa|"
    rf"p\.|pp\.|chap\.|titre|"
    rf"§|"
    rf"L\.|R\.|D\.|"
    rf"vol\.|t\."
    rf")[{NBSP}\s]*(\d)"
)

_THOUSANDS = re.compile(rf"(\d)[{NBSP}\s]+(\d{{3}})(?!\d)")

_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def polish_text(text: str) -> str:
    if not text:
        return text

    s = text
    protected: list[str] = []

    def _protect(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return f"\0P{len(protected) - 1}\0"

    s = re.sub(r"https?://[^\s<>\0]+", _protect, s)

    s = re.sub(rf"°[{NBSP}\s]+(?=[{_DEGREE_STICKY_RE}])", "°", s)
    s = re.sub(
        rf"°[{NBSP}\s]*(?=(?![{_DEGREE_STICKY_RE}])\S)",
        f"°{NBSP}",
        s,
    )

    times: list[str] = []

    def _protect_time(m: re.Match[str]) -> str:
        times.append(m.group(0))
        return f"\0T{len(times) - 1}\0"

    s = re.sub(r"\b\d{1,2}:\d{2}\b", _protect_time, s)

    for mark in ";:!?":
        esc = re.escape(mark)
        s = re.sub(rf"[{NBSP}\s]*{esc}", f"{NBSP}{mark}", s)
        s = re.sub(rf"{esc}[{NBSP}\s]+(?=\S)", f"{mark} ", s)
        s = re.sub(rf"(?<![\s{NBSP}]){esc}", f"{NBSP}{mark}", s)

    for i, raw in enumerate(times):
        s = s.replace(f"\0T{i}\0", raw)

    s = re.sub(rf"«[{NBSP}\s]*", f"«{NBSP}", s)
    s = re.sub(rf"[{NBSP}\s]*»", f"{NBSP}»", s)

    s = re.sub(rf"[{NBSP}\s]+%", f"{NBSP}%", s)
    s = re.sub(r"(?<=\d)%", f"{NBSP}%", s)

    s = _ABBREV_NUM.sub(rf"\1{NBSP}\2", s)
    s = re.sub(rf"(?i)\b(n°|nº)[{NBSP}\s]*(\d)", rf"\1{NBSP}\2", s)

    prev = None
    while prev != s:
        prev = s
        s = _THOUSANDS.sub(rf"\1{NBSP}\2", s)

    for i, raw in enumerate(protected):
        s = s.replace(f"\0P{i}\0", raw)

    return s


def _redistribute(parts: list[str], polished: str) -> list[str]:
    if len(parts) <= 1:
        return [polished]

    orig = "".join(parts)
    if orig == polished:
        return list(parts)

    per_old = [""] * len(orig)
    matcher = SequenceMatcher(None, orig, polished, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                per_old[i1 + k] += polished[j1 + k]
        elif tag == "replace":
            repl = polished[j1:j2]
            if i2 > i1:
                per_old[i1] += repl
            elif i1 > 0:
                per_old[i1 - 1] += repl
            elif orig:
                per_old[0] = repl + per_old[0]
        elif tag == "delete":
            continue
        elif tag == "insert":
            ins = polished[j1:j2]
            if i1 < len(orig):
                per_old[i1] = ins + per_old[i1]
            elif orig:
                per_old[-1] += ins

    out: list[str] = []
    idx = 0
    for part in parts:
        length = len(part)
        out.append("".join(per_old[idx : idx + length]))
        idx += length
    return out


def _preserve_xml_space(t_el, text: str) -> None:
    if text[:1] in {" ", NBSP} or text[-1:] in {" ", NBSP}:
        t_el.set(_XML_SPACE, "preserve")


def _polish_paragraph_element(p_el) -> int:
    nodes = list(p_el.iter(qn("w:t")))
    if not nodes:
        return 0

    parts = [n.text or "" for n in nodes]
    joined = "".join(parts)
    if not joined:
        return 0

    polished = polish_text(joined)
    if len(polished) >= 2 and polished[0] == NBSP and polished[1] in ";:!?":
        polished = polished[1:]

    if polished == joined:
        return 0

    new_parts = _redistribute(parts, polished)
    changed = 0
    for t_el, new in zip(nodes, new_parts):
        old = t_el.text or ""
        if new != old:
            t_el.text = new
            _preserve_xml_space(t_el, new)
            changed += 1
    return changed


def _iter_paragraphs(host: Any):
    if hasattr(host, "paragraphs"):
        for p in host.paragraphs:
            yield p
    if hasattr(host, "tables"):
        for table in host.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from _iter_paragraphs(cell)


def polish_document(document: Any) -> int:
    """Passe finale sur tout le document Word. Retourne le nb de w:t modifiés."""
    total = 0
    for p in _iter_paragraphs(document):
        total += _polish_paragraph_element(p._element)
    return total
