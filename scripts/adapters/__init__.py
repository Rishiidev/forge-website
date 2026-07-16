"""
Forge Website host adapters — Vercel + Cloudflare Pages.

Each adapter exposes `deploy(site_dir: Path) -> (ok: bool, url: str | None, msg: str)`.

Contract:
  - print "DEPLOY_URL=<url>" on stdout as the final action line on success
  - print "DEPLOYED_TO=<host> <url>" extra context (allowed but optional)
  - on failure, return non-zero and write the stderr/explanation
"""
