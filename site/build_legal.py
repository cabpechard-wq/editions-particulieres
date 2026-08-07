"""Convertit SITE_ROOT/legal/*.md en pages HTML du site."""
from __future__ import annotations

import html
import re
from pathlib import Path


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    return text


def markdown_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_ul = False
    in_ol = False
    in_table = False
    in_blockquote = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_bq() -> None:
        nonlocal in_blockquote
        if in_blockquote:
            out.append("</blockquote>")
            in_blockquote = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            close_lists()
            close_bq()
            close_table()
            i += 1
            continue

        if line.startswith("|") and "|" in line[1:]:
            close_lists()
            close_bq()
            cells = [c.strip() for c in line.strip("|").split("|")]
            # skip separator row
            if all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells):
                i += 1
                continue
            if not in_table:
                out.append('<table class="legal-table"><tbody>')
                in_table = True
                # first row as header if next is separator
                if i + 1 < len(lines) and re.match(
                    r"^\|?\s*:?-{3,}", lines[i + 1].strip()
                ):
                    out.append(
                        "<tr>"
                        + "".join(f"<th>{_inline(c)}</th>" for c in cells)
                        + "</tr>"
                    )
                    i += 2
                    continue
            out.append(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>"
            )
            i += 1
            continue

        close_table()

        if line.startswith("> "):
            close_lists()
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            out.append(f"<p>{_inline(line[2:])}</p>")
            i += 1
            continue
        close_bq()

        if line.startswith("# "):
            close_lists()
            out.append(f"<h1>{_inline(line[2:])}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            close_lists()
            out.append(f"<h2>{_inline(line[3:])}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            close_lists()
            out.append(f"<h3>{_inline(line[4:])}</h3>")
            i += 1
            continue

        m_ul = re.match(r"^[-*] (.+)$", line)
        if m_ul:
            close_bq()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline(m_ul.group(1))}</li>")
            i += 1
            continue

        m_ol = re.match(r"^(\d+)\. (.+)$", line)
        if m_ol:
            close_bq()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline(m_ol.group(2))}</li>")
            i += 1
            continue

        close_lists()
        out.append(f"<p>{_inline(line)}</p>")
        i += 1

    close_lists()
    close_bq()
    close_table()
    return "\n".join(out)


def build_legal_page(
    md_path: Path,
    tpl: str,
    *,
    title: str,
    crumb: str,
) -> str:
    body = markdown_to_html(md_path.read_text(encoding="utf-8"))
    return (
        tpl.replace("{{TITLE}}", html.escape(title))
        .replace("{{CRUMB}}", html.escape(crumb))
        .replace("{{BODY}}", body)
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    tpl = (root / "templates" / "legal-page.html").read_text(encoding="utf-8")
    print(
        build_legal_page(
            root / "legal" / "mentions-legales.md",
            tpl,
            title="Mentions légales",
            crumb="Mentions légales",
        )[:500]
    )
