#!/usr/bin/env python3
"""
Surface capture v3 — route-interception capture (RELIABLE request bodies).

DEFAULT = FAST: intercepts API-shaped traffic ONLY (static assets bypass routing —
full page speed; the I4 scar: intercepting **/* strangled page loads, user complained
twice). Pass --full to intercept everything (deep RE of unknown flows only).

WHY: v2's event-listener post_data came back null on key POSTs (PROGRAM_81 cart-compose
mystery, 2026-07-30). Route handlers reliably expose request.post_data.

USAGE:
  python3 capture_v3.py <out_dir> <start_url> [profile_dir] [--full]
  capture_v3_fast.py is a thin alias for the default mode (kept for muscle memory).
"""
from __future__ import annotations
import json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

# API-shaped traffic: endpoints where request BODIES live. Extended from the
# capture_v3_fast pattern — add target-specific shapes as learned.
API_PATTERN = re.compile(
    r".*(/api/|/graphql|/v[0-9]+/|sign-?up|login|logout|oauth|token|accounts?"
    r"|session|auth|billing|payment|checkout|cart|order|subscribe"
    r"|collector|ingest|events?|metrics?|log-?api|nr-data|nr-ops"
    r"|user|org|key|dashboard|entity|query|alert|notification).*", re.I)
INTEREST = re.compile(
    r"PROGRAM_85|PROGRAM_81|PROGRAM_64|adyen|PROGRAM_87|PROGRAM_68|klarna|api\.|/api/|auth|sign-up|billing|payment", re.I)


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main(out_dir: str, start_url: str, profile: str | None = None,
         headless: bool = False, full: bool = False):
    OUT = Path(out_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    EVENTS = OUT / "events_v3.jsonl"
    n = {"requests": 0, "with_body": 0}

    with sync_playwright() as p:
        if profile:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=profile, headless=headless,
                args=["--disable-blink-features=AutomationControlled", "--no-first-run",
                      "--no-default-browser-check", "--disable-extensions"],
                viewport={"width": 1440, "height": 900} if not headless else None,
                ignore_default_args=["--enable-automation"])
        else:
            browser = p.chromium.launch(headless=headless)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})

        def on_route(route):
            req = route.request
            try:
                body = None
                try:
                    body = req.post_data
                except Exception:
                    pass
                rec = {"ts": utc(), "method": req.method, "url": req.url,
                       "resource": req.resource_type, "req_body": body}
                with EVENTS.open("a") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n["requests"] += 1
                if body:
                    n["with_body"] += 1
                    if INTEREST.search(req.url):
                        print(f"[{req.method}] {req.url[:110]}\n  body={body[:250]}", flush=True)
            except Exception:
                pass
            route.continue_()

        if full:
            ctx.route("**/*", on_route)
            mode = "FULL (all traffic intercepted — page speed degraded)"
        else:
            ctx.route(API_PATTERN, on_route)
            mode = "API-only (static assets unintercepted — full page speed)"
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(start_url, wait_until="domcontentloaded", timeout=120000)
        print(f"[capv3] LIVE at {start_url} — {mode}. Ctrl-C to stop.", flush=True)
        while True:
            time.sleep(1)


if __name__ == "__main__":
    import tempfile
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if len(args) > 0 else tempfile.mkdtemp(prefix="capv3_")
    url = args[1] if len(args) > 1 else "https://www.PROGRAM_85.com/"
    prof = args[2] if len(args) > 2 else None
    main(out, url, prof, full=("--full" in sys.argv))
