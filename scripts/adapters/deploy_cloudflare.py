#!/usr/bin/env python3
"""
Cloudflare Pages deploy adapter for Forge Website.

Two-step because Pages requires the project to exist before first deploy:
  1. wrangler pages project create <slug> --production-branch main
     (idempotent — exit 0/1 both fine if project exists; we swallow the error)
  2. wrangler pages deploy . --project-name=<slug> --branch main
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOST = "cloudflare"


def ensure_cli() -> bool:
    if shutil.which("wrangler"):
        return True
    print("⚙️  `wrangler` CLI missing — installing via npm (one-time)…")
    r = subprocess.run(["npm", "install", "-g", "wrangler"], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"npm install failed:\n{r.stderr}", file=sys.stderr)
        return False
    return shutil.which("wrangler") is not None


def ensure_project(slug: str) -> bool:
    """
    Create the Pages project if it doesn't exist.
    Cloudflare returns a non-zero exit if the project exists, so we don't propagate.
    """
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    cmd = ["wrangler", "pages", "project", "create", slug, "--production-branch", "main"]
    env = os.environ.copy()
    if token:
        env["CLOUDFLARE_API_TOKEN"] = token
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if account_id:
        env["CLOUDFLARE_ACCOUNT_ID"] = account_id
    print(f"   wrangler pages project create {slug}  (idempotent)")
    subprocess.run(cmd, env=env, capture_output=True, text=True)  # ignore returncode
    return True


def deploy(site_dir: Path) -> tuple[bool, str | None, str]:
    if not site_dir.is_dir():
        return False, None, f"site_dir does not exist: {site_dir}"

    if not ensure_cli():
        return False, None, "wrangler CLI install failed"

    slug = site_dir.name
    ensure_project(slug)

    cmd = ["wrangler", "pages", "deploy", ".", "--project-name", slug, "--branch", "main"]
    env = os.environ.copy()
    if os.environ.get("CLOUDFLARE_API_TOKEN"):
        env["CLOUDFLARE_API_TOKEN"] = os.environ["CLOUDFLARE_API_TOKEN"]
    if os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        env["CLOUDFLARE_ACCOUNT_ID"] = os.environ["CLOUDFLARE_ACCOUNT_ID"]

    print(f"   wrangler pages deploy .  in  {site_dir}")
    r = subprocess.run(cmd, cwd=str(site_dir), env=env, capture_output=True, text=True)
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    print(out)
    if r.returncode != 0:
        return False, None, f"wrangler pages deploy failed (exit {r.returncode})"

    # Pages URLs are https://<slug>.pages.dev
    url = f"https://{slug}.pages.dev"
    # Optional override from wrangler output
    m = re.search(r"https?://[a-z0-9-]+\.pages\.dev", out)
    if m:
        url = m.group(0)

    print(f"\nDEPLOYED_TO=cloudflare {url}")
    print(f"DEPLOY_URL={url}")
    return True, url, ""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: deploy_cloudflare.py <site_dir>", file=sys.stderr)
        return 2
    ok, url, msg = deploy(Path(sys.argv[1]).expanduser().resolve())
    if not ok:
        print(f"❌ {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
