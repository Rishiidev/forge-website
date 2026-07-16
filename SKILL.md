---
name: forge-website
description: When the user says "build the site", "ship the website", "deliver the ₹9,999", or runs `python3 ~/.hermes/skills/forge/website/scripts/build.py` — turn a Forge audit `.client.json` (or GBP URL / website URL) into a deployed 5-page static website that visually closes every leak the audit found. Host-agnostic (Vercel + Cloudflare Pages as first-class adapters, --deploy flag selects). Output: 5 HTML pages + assets in `~/Documents/forge/sites/<slug>/`, a `.delivered.json` manifest, and (with --deploy) a live URL.
---

# Forge Website — the ₹9,999 deliverable

A sibling skill to `forge-audit`. The audit names the leaks and pitches the website; this skill is what actually ships when the prospect says yes.

**Position in funnel:** T+7d → prospect replies YES to offer → paste `.client.json` + run → live URL in 60 seconds → WhatsApp handoff.

## When to invoke

- "build the site", "ship the website", "deliver the 9,999"
- After audit pipeline emits `<business>--<date>.client.json`
- Slash: `/forge-website --from-client <path>`
- Slash: `/forge-website --from-gbp <share.google URL>` (skips audit, less complete)
- Slash: `/forge-website --from-url <website>` (redo an existing site)

## Workflow

```
1. Receive input (.client.json OR GBP URL OR website URL)
2. Resolve business signals:
     .client.json  → use as-is (name, phone, whatsapp, address, photos, hours, rating, leaks[])
     GBP URL       → run forge-audit investigate, take signals
     website URL   → run forge-audit website mode, take signals
3. Pick industry template (salon | restaurant | clinic | contractor | retail | fitness | auto | other)
     → matches audit's category field; fallback to "other"
4. Generate 5 static pages: Home, About, Services, Reviews, Contact
5. Self-host photos to ./images/ (Maps URLs expire — copy locally)
6. Emit lint report (unresolved {{TOKEN}} check)
7. [optional --deploy] upload via adapter:
     vercel   → `vercel deploy --prod --yes`
     cloudflare → wrangler pages: project create (idempotent) + pages deploy
8. Write <business>--<date>.delivered.json with: build_seconds, files, deploy_url, sha
9. Open WhatsApp handoff draft (wa.me deep link)
```

## The five pages

Every site ships exactly these 5 — that's the ₹9,999 promise, no more:

| Page | Purpose | Built from |
|---|---|---|
| `index.html` | Hero + rating + CTA above fold | name, tagline, rating, primary CTA |
| `about.html` | Story + hours + WhatsApp-CTA | description, hours, address |
| `services.html` | Services grid | inferred from category (8 templates ship 6-card copy) |
| `reviews.html` | 3 best reviews from GBP | reviews[] (or generic 4.8★ copy fallback) |
| `contact.html` | WhatsApp button + map + hours table | whatsapp, phone, address, hours |

## Tokens the build resolves

```
{{NAME}}, {{TAGLINE}}, {{DESCRIPTION}}, {{PHONE}}, {{PHONE_RAW}},
{{PHONE_INTL}}, {{WHATSAPP}}, {{WHATSAPP_RAW}}, {{WHATSAPP_MESSAGE}},
{{ADDRESS}}, {{ADDRESS_ENCODED}}, {{CITY}},
{{RATING}}, {{REVIEW_COUNT}}, {{STARS_HTML}},
{{HOURS_ROWS}}, {{HOURS_JSON}}, {{SERVICES_CARDS}}, {{REVIEW_CARDS}},
{{PHOTO_1}}…{{PHOTO_6}}, {{YEAR}},
{{COLOR_PRIMARY}}, {{FONT_HEADING}}, {{FONT_BODY}},
{{INDUSTRY}}, {{INDUSTRY_LABEL}}, {{CTA_PRIMARY}}, {{CTA_SECONDARY}}
```

If any required token is missing (e.g. no hours scraped), the build emits a deterministic default per industry — never ships with `{{TOKEN}}` left literal. Lint pass catches stragglers.

## Deploy adapters

| Host | Adapter | First-time prep | Deploy command |
|---|---|---|---|
| **vercel** | `scripts/adapters/deploy_vercel.py` | `npm i -g vercel && vercel login` | `vercel deploy --prod --yes` |
| **cloudflare** | `scripts/adapters/deploy_cloudflare.py` | `npm i -g wrangler && wrangler login` | (1) `wrangler pages project create <slug>` if missing, then (2) `wrangler pages deploy . --project-name=<slug>` |

The skill auto-installs both CLIs (npm i -g) if missing. Both are interactive-CC-free.

## Usage

### From a client.json (most complete)
```bash
python3 ~/.hermes/skills/forge/website/scripts/build.py \
    --from-client ~/Documents/forge/audits/de-bella--2026-07-17.client.json \
    --deploy vercel
```

### From a GBP URL only (no audit done)
```bash
python3 ~/.hermes/skills/forge/website/scripts/build.py \
    --from-gbp "https://share.google/abc123" \
    --name "Priya Sharma" \
    --whatsapp "+919812345678" \
    --deploy cloudflare
```

### From a website URL (audit + site in one shot — for existing-site prospects)
```bash
python3 ~/.hermes/skills/forge/website/scripts/build.py \
    --from-url "https://old-business.com" \
    --deploy vercel
```

### Build only, deploy later
```bash
python3 ~/.hermes/skills/forge/website/scripts/build.py --from-client x.client.json
ls ~/Documents/forge/sites/<slug>/
# then later:
python3 ~/.hermes/skills/forge/website/scripts/adapters/deploy_vercel.py ~/Documents/forge/sites/<slug>/
```

## Output

```
~/Documents/forge/sites/<slug>/
  index.html
  about.html
  services.html
  reviews.html
  contact.html
  styles.css
  assets/
    logo.svg          (Forge mark, optional)
    images/
      business-1.webp … business-6.webp  (self-hosted)
~/Documents/forge/sites/<slug>--<date>.delivered.json
```

The `.delivered.json` records build time, file count, sha of each page, and the live URL when deployed. Append-only log → `~/.forge/delivered.jsonl` for analytics.

## What ships vs. what's held back

| Shipped in base | Why |
|---|---|
| WhatsApp-CTA above the fold | Indian SMBs prefer WhatsApp to a phone tap |
| LocalBusiness JSON-LD | Free SEO |
| Click-to-call + click-to-email | Backup CTAs |
| 3 real GBP reviews | Social proof |
| Mobile-first layout | 80%+ mobile traffic |
| Open/Closed indicator | Built from scraped hours |

| Held back (upsell in v2) | Why |
|---|---|
| Working contact form | Formspree at ₹1,499 setup |
| Analytics | GoatCounter/Plausible at ₹999/mo |
| Custom domain | ₹999 setup, billed per domain |
| 2nd microsite | ₹4,999 per landing page |
| Maintenance retainer | ₹1,999/mo (3 updates + perf report) |

The hooks are already wired into the HTML (commented-out CTA blocks). Switching them on = 15-minute follow-up call. LTV 4-6x the base price.

## Cost discipline

Default deploy = vercel (already a known-good host from biz-site-builder). Cloudflare Pages is the unlimited-bandwidth alternative — flip default at >50 deliveries/month. Never recommend a paid tier; verify the free tier suffices first.

## Key invariants

1. **No {{TOKEN}} ships literal.** Lint pass hard-fails otherwise.
2. **Photos are self-hosted.** GBP photo URLs expire; map URLs are blocked in India 30% of the time.
3. **Both deploys use the same artifact.** `~/Documents/forge/sites/<slug>/` is build-output-pure. Adapters only upload.
4. **Idempotent builds.** Running twice with same input → same artifact (sha-verifiable).
5. **The .delivered.json is append-only.** Never overwritten, so the analytics log survives.

## See also

- `forge-audit` — produces the `.client.json` this skill consumes
- `references/industry-copy.md` — what copy each template ships
- `references/host-notes.md` — CLI install + first-time setup per host
- `templates/<industry>/` — 8 industry-specific override directories
- `templates/_base/` — shared partials (nav, schema, open-now.js)
