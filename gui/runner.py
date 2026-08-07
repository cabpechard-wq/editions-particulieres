"""Construction du plan GUI → PipelineRequest."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from packages.ep_core.paths import REPO_ROOT, resolve_path
from packages.ep_core.registers import REGISTRE_ORDER

from .format_opts import ensure_format
from .request import PipelineRequest

ROOT = REPO_ROOT
load_dotenv(ROOT / ".env")


def default_export_dir() -> Path:
    try:
        return resolve_path("export")
    except (KeyError, OSError):
        return ROOT / "output"


DEFAULT_OUT = default_export_dir()


def resolve_python() -> Path:
    if sys.platform == "win32":
        venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT / ".venv" / "bin" / "python"
    if venv_py.is_file():
        return venv_py
    return Path(sys.executable)


def parse_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return lines


def master_styles_path() -> Path:
    from extract.word.styles_master import master_styles_path as _msp

    return _msp()


def default_site_templates() -> Path:
    try:
        return resolve_path("templates_site")
    except (KeyError, OSError):
        return ROOT / "site" / "templates"


def postlink_cmdline(python: Path | str, out: Path | None = None) -> list[str]:
    cmd = [str(python), "-m", "gui.postlink", "--format", "docx"]
    if out:
        cmd += ["--out", str(out)]
    return cmd


def to_pdf_cmdline(python: Path | str, out: Path | None = None) -> list[str]:
    cmd = [str(python), "-m", "extract.word.convert_pdf"]
    if out:
        cmd += ["--out", str(out)]
    return cmd


def attach_styles_cmdline(python: Path | str, out: Path | None = None) -> list[str]:
    cmd = [str(python), "-m", "extract.word.attach_styles"]
    if out:
        cmd += ["--out", str(out)]
    return cmd


def build_request(
    *,
    registres: list[str],
    autres_text: str,
    pages_text: str,
    combine: bool,
    name: str,
    limit: str,
    out: str,
    arrets_refresh: bool,
    arrets_a5: bool,
    pages_by_registre: dict[str, list[str]] | None = None,
    format: str = "docx",
    site_templates: str = "",
    also_pdf: bool = False,
) -> tuple[PipelineRequest | None, str | None]:
    regs = [r for r in REGISTRE_ORDER if r in registres]
    autres = parse_lines(autres_text)
    pages = parse_lines(pages_text)
    by_reg = {
        k: list(v)
        for k, v in (pages_by_registre or {}).items()
        if k in REGISTRE_ORDER and v
    }

    lim: int | None = None
    raw = (limit or "").strip()
    if raw:
        try:
            lim = int(raw)
        except ValueError:
            return None, f"Limite invalide : {raw!r}"
        if lim <= 0:
            return None, "La limite doit être un entier positif."

    out_path = Path(out.strip()) if out.strip() else DEFAULT_OUT

    try:
        fmt = ensure_format(format)
    except ValueError as e:
        return None, str(e)

    site_tpl: Path | None = None
    if fmt == "html" and ("manuel" in regs or "index" in regs) and not combine:
        raw_tpl = (site_templates or "").strip()
        site_tpl = Path(raw_tpl) if raw_tpl else default_site_templates()

    req = PipelineRequest(
        registres=regs,
        autres=autres,
        pages=pages,
        pages_by_registre=by_reg,
        combine=combine,
        name=name.strip(),
        limit=lim,
        out=out_path,
        format=fmt,
        site_templates=site_tpl,
        arrets_refresh=arrets_refresh,
        arrets_a5=arrets_a5,
        also_pdf=also_pdf,
    )
    err = req.validate()
    if err:
        return None, err
    return req, None
