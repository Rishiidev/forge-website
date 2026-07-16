# Changelog

All notable changes documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [1.0.0] — 2026-07-17

### Added
- `scripts/build.py` — generates 5-page static site from any of:
  - `--from-client <path>` (forge-audit `.client.json`, preferred)
  - `--from-gbp <url>` (skip audit, just a Maps link)
  - `--from-url <website>` (audit-then-build in one shot)
- 8 industry templates with curated 6-card service copy (salon, restaurant, clinic, contractor, retail, fitness, auto, other)
- Industry-aware color palette + font family (Playfair Display for salon/restaurant, Inter for transactional)
- Self-hosted photo downloader (1.5MB max per photo; falls back to branded placeholders if Maps URL fails)
- Live "Open Now / Closed" pill computed client-side from scraped hours with 60s refresh
- LocalBusiness JSON-LD + OG meta tags
- Pre-composed `wa.me` deep-link token — no broken links even with masked numbers
- Host-agnostic: Vercel + Cloudflare Pages as first-class adapters with auto-installer for both CLIs
- Token lint pass — fails the build if any `{{TOKEN}}` ships literal
- Append-only log at `~/.forge/delivered.jsonl` for analytics
- Wired into `forge-audit` — the T+7d `offer.delivery_command` in `.client.json` points here

### Held back (upsells in v2)
- Working contact form (₹1,499 setup)
- Analytics (₹999/mo)
- Custom domain (₹999 + domain)
- Sub-landing pages per service line (₹4,999 each)
