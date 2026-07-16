#!/usr/bin/env python3
"""
Vercel deploy adapter for Forge Website.

Order of operations:
  1. If `vercel` CLI missing → npm install -g vercel (one-time)
  2. If VERCEL_TOKEN env set, use it headlessly. Else prefer `vercel login` first.
  3. cd to site_dir, run `vercel deploy --prod --yes`
  4. Parse URL from stdout and print "DEPLOY_URL=<url>" as the last line.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOST = "vercel"


def ensure_cli() -> bool:
    if shutil.which("vercel"):
        return True
    print("⚙️  `vercel` CLI missing — installing via npm (one-time)…")
    r = subprocess.run(["npm", "install", "-g", "vercel"], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"npm install failed:\n{r.stderr}", file=sys.stderr)
        return False
    return shutil.which("vercel") is not None


def deploy(site_dir: Path) -> tuple[bool, str | None, str]:
    if not site_dir.is_dir():
        return False, None, f"site_dir does not exist: {site_dir}"

    if not ensure_cli():
        return False, None, "vercel CLI install failed"

    # If VERCEL_TOKEN is set, deploy with --token. Otherwise rely on `vercel login`.
    token = os.environ.get("VERCEL_TOKEN")
    cmd = ["vercel", "deploy", "--prod", "--yes"]
    if token:
        cmd += ["--token", token]

    print(f"   vercel deploy --prod --yes  in  {site_dir}")
    r = subprocess.run(cmd, cwd=str(site_dir), capture_output=True, text=True)
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    print(out)
    if r.returncode != 0:
        return False, None, f"vercel deploy failed (exit {r.returncode})"

    # Output URL can be either https://<slug>.vercel.app or the alias URL
    m = re.search(r"https?://[a-z0-9-]+\.vercel\.app", out)
    url = m.group(0) if m else None
    if not url:
        # Fallback: <slug> from site_dir name
        slug = site_dir.name
        url = f"https://{slug}.vercel.app"
        print(f"   (URL not parsed cleanly — defaulting to {url}; verify in dashboard)")

    print(f"\nDEPLOYED_TO=vercel {url}")
    print(f"DEPLOY_URL={url}")
    return True, url, ""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: deploy_vercel.py <site_dir>", file=sys.stderr)
        return 2
    ok, url, msg = deploy(Path(sys.argv[1]).expanduser().resolve())
    if not ok:
        print(f"❌ {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
