# 🔨 Forge Website — the ₹9,999 deliverable

> The sibling skill to [`forge-audit`](https://github.com/Rishiidev/forge-audit-skill). The audit names the leaks and pitches the website; this skill is what ships when the prospect says yes.
>
> `Tally → audit PDF → .client.json → Forge Website → live 5-page site → WhatsApp handoff`

---

## What this does

One command. Five static pages. Hosted on Vercel or Cloudflare Pages. Free tier.

```bash
python3 ~/.hermes/skills/forge/website/scripts/build.py \
    --from-client ~/Documents/forge/audits/de-bella--2026-07-17.client.json \
    --deploy vercel
```

Output:

```
~/Documents/forge/sites/de-bella/
  index.html
  about.html
  services.html
  reviews.html
  contact.html
  styles.css
  open-now.js
  assets/logo.svg
  assets/images/business-1.webp ... business-6.webp
~/Documents/forge/sites/de-bella--2026-07-17.delivered.json
```

Then on Vercel:
```
https://de-bella-beau.vercel.app     ← live URL
+ wa.me/<number>?text=…handoff message ready to paste
```

## Three input modes

The skill works without an audit — useful when you've only got a Maps URL.

```bash
# Most complete — uses forge-audit's .client.json (preferred)
python3 scripts/build.py --from-client <path>.client.json --deploy vercel

# Just a Maps link
python3 scripts/build.py --from-gbp "https://share.google/abc123" \
    --name "Priya Sharma" --business "De Bella" --whatsapp "+919876543210"

# Existing website (audit-then-build in one shot)
python3 scripts/build.py --from-url "https://old-site.com" --deploy cloudflare
```

## Features

| Shipped in every site | Why |
|---|---|
| WhatsApp-CTA above the fold | Indian SMBs prefer WhatsApp over a phone tap |
| LocalBusiness JSON-LD schema | Free SEO |
| Live "Open Now" indicator from scraped hours | Trust signal |
| Click-to-call, click-to-email, click-to-directions | Backup CTAs |
| 3 real GBP reviews | Social proof |
| Mobile-first layout | 80%+ mobile traffic in India |
| 6 industry-specific service cards | Tone-matched copy, not generic |
| Self-hosted photos | GBP photo URLs rot — we download to local |
| Industry-template colors & fonts | Brand tone per industry, not a palette swap |

## 8 industry templates

| Category | Industry key | Primary CTA | Font | Color |
|---|---|---|---|---|
| salon / hair / spa | `salon` | WhatsApp to Book | Playfair Display | `#c2185b` |
| restaurant / cafe | `restaurant` | Reserve a Table | Cormorant Garamond | `#bf360c` |
| clinic / doctor / dentist | `clinic` | Book Appointment | Inter | `#00695c` |
| contractor / plumber / electrician | `contractor` | Get a Free Quote | Inter | `#1565c0` |
| retail / boutique | `retail` | Get Directions | Inter | `#6a1b9a` |
| gym / yoga / fitness | `fitness` | Start Free Trial | Inter | `#2e7d32` |
| auto / mechanic | `auto` | Get a Quote | Inter | `#37474f` |
| anything else | `other` | WhatsApp Us | Inter | `#37474f` |

Service cards copy is curated per industry in `references/industry-copy.md`.

## Host adapters (host-agnostic)

| Host | CLI | Free tier | Why pick it |
|---|---|---|---|
| **Vercel** (default) | `vercel deploy --prod --yes` | 100GB BW/month, no CC | Fastest first deploy, auto-creates project |
| **Cloudflare Pages** | `wrangler pages deploy` | **Unlimited BW**, no CC | Best at scale — pick when prospect WhatsApps link to 500 people |

Both deploy the same artifact at `~/Documents/forge/sites/<slug>/`. Pick at runtime:

```bash
--deploy vercel        # default if --deploy omitted? no — must be explicit
--deploy cloudflare    # free unlimited BW
--deploy none          # build only, deploy later
```

CLI is auto-installed on first run via `npm install -g`. Need a `VERCEL_TOKEN` / `CLOUDFLARE_API_TOKEN` env var for headless deploys — see [`references/host-notes.md`](references/host-notes.md).

## What ships vs. what's held back (the upsell ladder)

| Base | Upsell | Price (₹) |
|---|---|---|
| ✅ WhatsApp CTA + 5 pages + JSON-LD | — | ₹9,999 one-time |
| ❌ Working contact form | Formspree wired in | ₹1,499 setup + ₹499/mo |
| ❌ Analytics | Plausible / GoatCounter | ₹999/mo |
| ❌ Custom domain | Domain registrar + setup | ₹999 + domain |
| ❌ Sub-landing pages (e.g. bridal) | Add-landing subcommand | ₹4,999 each |
| ❌ Monthly maintenance | Update + perf report | ₹1,999/mo |

The hooks are already wired into the HTML (commented-out blocks). Switching them on = 15-min follow-up call. LTV 4-6x the base price.

## Install

```bash
git clone https://github.com/Rishiidev/forge-website
mkdir -p ~/.hermes/skills/forge
ln -s "$(pwd)/forge-website" ~/.hermes/skills/forge/website

# Make sure the audit skill is also installed (the .client.json source)
# See https://github.com/Rishiidev/forge-audit-skill

# First-time host setup (one-time per host)
npm install -g vercel       # or wrangler for cloudflare
vercel login                # opens browser, OAuth, no CC needed
```

## Cost

| | Cost |
|---|---|
| Skill | Free, MIT licensed |
| Vercel free tier | 100GB BW/mo, 6000 build-min/mo — covers ~200 site/months |
| Cloudflare free tier | Unlimited BW, 500 builds/mo — covers everything |
| Domain (opt) | ₹500–800/year per site |
| **Total per site at scale** | **₹0 hosting** |

> We never recommend paid tiers. The free tier *is* the production tier for an Indian SMB funnel. See [`references/host-notes.md`](references/host-notes.md) for the math.

## Position in the audit funnel

```
T+0   Audit PDF delivered
T+48h Free cleanup gift (auto-picked highest-impact leak)
T+7d  ₹9,999 5-page website offer ───┐
T+14d Soft close                    │   ←─ THIS SKILL
                                    ▼
              python3 build.py --from-client x.client.json
                                    │
                                    ▼
                        https://<slug>.vercel.app
                                    │
                                    ▼
                          wa.me draft message
```

The `.client.json` from `forge-audit` ships with a copy-pasteable `delivery_command` field at `messages.T+7d_website_offer.offer.delivery_command`. So at T+7d your runbook is paste-and-run, not think-and-decode.

## License

MIT — same as `forge-audit`. Ship it, fork it, brand it, sell the deliverable.

## Author

Built and maintained by [Rishabh Sethiya](https://github.com/Rishiidev) as the ₹9,999 ship-half of the Forge funnel. See [`forge-audit-skill`](https://github.com/Rishiidev/forge-audit-skill) for the audit half.
