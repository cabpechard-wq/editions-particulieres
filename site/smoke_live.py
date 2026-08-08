"""Smoke HTTP sur le site publié (post-déploiement Pages).

Usage :
  python site/smoke_live.py
  python site/smoke_live.py --base https://www.editions-particulieres.fr
  python site/smoke_live.py --base https://cabpechard-wq.github.io/editions-particulieres --retries 8
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable

DEFAULT_BASE = "https://www.editions-particulieres.fr"
FALLBACK_BASE = "https://cabpechard-wq.github.io/editions-particulieres"

OVH_POISON = re.compile(r"Site en construction|OVHcloud|/__ovh/", re.I)

CheckFn = Callable[[int, str, dict], None]
INSECURE = False


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def _ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch(
    url: str,
    *,
    timeout: float = 30.0,
    expect_json: bool = False,
    insecure: bool = False,
) -> tuple[int, str, dict[str, str]]:
    # Préférer httpx (meilleure chaîne CA) si disponible
    try:
        import httpx

        r = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            verify=not insecure and not INSECURE,
            headers={
                "User-Agent": "editions-particulieres-smoke/1.0",
                "Accept": "application/json, text/html, */*",
            },
        )
        body = r.text
        headers = {k.lower(): v for k, v in r.headers.items()}
        if expect_json:
            json.loads(body)
        return int(r.status_code), body, headers
    except ImportError:
        pass

    ctx = (
        ssl._create_unverified_context()
        if (insecure or INSECURE)
        else _ssl_context()
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "editions-particulieres-smoke/1.0",
            "Accept": "application/json, text/html, */*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = getattr(resp, "status", 200) or 200
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            if expect_json:
                json.loads(body)
            return int(status), body, headers
    except urllib.error.HTTPError as e:
        raw = e.read() if hasattr(e, "read") else b""
        body = raw.decode("utf-8", errors="replace")
        return int(e.code), body, {}


def must_status(status: int, _body: str, _headers: dict, *, code: int = 200) -> None:
    if status != code:
        fail(f"HTTP {status} (attendu {code})")


def must_contain(*needles: str) -> CheckFn:
    def _check(status: int, body: str, headers: dict) -> None:
        must_status(status, body, headers)
        for n in needles:
            if n not in body:
                fail(f"contenu attendu manquant : {n!r}")

    return _check


def must_not_ovh(status: int, body: str, headers: dict) -> None:
    must_status(status, body, headers)
    if OVH_POISON.search(body):
        fail("reponse = page OVH site en construction")


def must_json_docs(status: int, body: str, headers: dict) -> None:
    must_status(status, body, headers)
    data = json.loads(body)
    docs = data.get("docs") or []
    if len(docs) < 100:
        fail(f"search-index trop petit ({len(docs)} docs)")


def join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


PATH_CHECKS: list[tuple[str, list[CheckFn], dict]] = [
    ("", [must_not_ovh, must_contain("Éditions Particulières")], {}),
    ("checkout/", [must_contain("buy.stripe.com")], {}),
    ("demo/", [must_contain("html")], {}),
    ("membre/", [must_contain("html")], {}),
    ("manuel/", [must_not_ovh, must_contain("html")], {}),
    ("dictionnaire/", [must_not_ovh, must_contain("Dictionnaire")], {}),
    ("arrets/", [must_not_ovh, must_contain("html")], {}),
    ("site-nav.js", [must_contain("site-nav")], {}),
    ("site-search.js", [must_contain("search-index")], {}),
    ("search-index.json", [must_json_docs], {"expect_json": True}),
    ("auth.js", [must_contain("http")], {}),
    ("cgv/", [must_contain("html")], {}),
    ("mentions-legales/", [must_contain("html")], {}),
]


def probe_base(base: str) -> bool:
    status, body, _ = fetch(join_url(base, ""))
    if status != 200:
        return False
    if OVH_POISON.search(body):
        return False
    return "Éditions Particulières" in body or "editions" in body.lower()


def run_suite(base: str) -> None:
    print(f"Base : {base}")
    for path, checkers, opts in PATH_CHECKS:
        url = join_url(base, path) if path else base.rstrip("/") + "/"
        status, body, headers = fetch(url, expect_json=bool(opts.get("expect_json")))
        label = path or "/"
        try:
            for check in checkers:
                check(status, body, headers)
            ok(f"{label} ({status})")
        except SystemExit:
            print(f"  URL : {url}")
            raise


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", default="", help="URL canonique du site")
    p.add_argument("--retries", type=int, default=10, help="Tentatives (propagation CDN)")
    p.add_argument("--sleep", type=float, default=15.0, help="Pause entre tentatives (s)")
    p.add_argument(
        "--insecure",
        action="store_true",
        help="Ignore les erreurs SSL (dev local Windows uniquement)",
    )
    args = p.parse_args(argv)

    global INSECURE
    INSECURE = bool(args.insecure)

    bases: list[str] = []
    if args.base.strip():
        bases.append(args.base.strip().rstrip("/"))
    else:
        bases.extend([DEFAULT_BASE, FALLBACK_BASE])

    last_err: BaseException | None = None
    for attempt in range(1, max(1, args.retries) + 1):
        print(f"--- tentative {attempt}/{args.retries} ---")
        chosen = None
        for b in bases:
            print(f"Probe {b} ...")
            try:
                if probe_base(b):
                    chosen = b
                    break
                print("  (indisponible ou page invalide)")
            except Exception as e:
                print(f"  (erreur probe : {e})")
        if not chosen:
            last_err = RuntimeError("aucune base joignable")
            if attempt < args.retries:
                time.sleep(args.sleep)
            continue
        try:
            run_suite(chosen)
            print("SMOKE LIVE OK")
            return 0
        except SystemExit as e:
            last_err = e
            if attempt < args.retries:
                print(f"Nouvelle tentative dans {args.sleep}s ...")
                time.sleep(args.sleep)
            else:
                raise

    fail(f"smoke live echoue apres {args.retries} tentative(s) : {last_err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
