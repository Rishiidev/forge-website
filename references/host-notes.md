# Host setup notes (Vercel + Cloudflare Pages)

Both adapters are interactive-CC-free. Install once, login once, then deploy is a one-liner.

## Vercel

### First-time setup (per machine)
```bash
npm install -g vercel
vercel login              # opens browser, OAuth, no CC
```

Skip this if `VERCEL_TOKEN` env var is set — the adapter prefers the token (works headlessly).

### Get a token (headless option)
1. https://vercel.com/account/tokens → Create Token
2. Scope: Full Account (or limit to specific projects later)
3. `export VERCEL_TOKEN=<token>` in your shell rc

### Deploy
```bash
cd ~/Documents/forge/sites/<slug>
vercel deploy --prod --yes
```

That's it. First deploy creates the project automatically (`<slug>`). Output URL: `https://<slug>.vercel.app` (or `https://<slug>-<git-sha>-<user>.vercel.app` for preview deploys, but `--prod` locks to stable URL).

### Limits (free tier — Hobby plan)
- 100 GB bandwidth / month
- 6,000 build minutes / month
- Unlimited sites
- Custom domains free
- India edge: Mumbai (bom1)
- CC required: **no**

### Why this is the default
- Single CLI command after `vercel login`
- Project auto-creates on first deploy (vs Cloudflare needing a 2-step)
- `*.vercel.app` URLs read cleanly
- biz-site-builder already uses this — familiar surface

## Cloudflare Pages

### First-time setup (per machine)
```bash
npm install -g wrangler
wrangler login            # opens browser, OAuth, no CC
```

Skip if `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_ACCOUNT_ID` env vars are set — adapter uses those headlessly.

### Get tokens (headless option)
1. Cloudflare dashboard → My Profile → API Tokens
2. Template: "Edit Cloudflare Pages"
3. `export CLOUDFLARE_API_TOKEN=<token>` and `export CLOUDFLARE_ACCOUNT_ID=<id>` (Account ID is on the right sidebar of any CF page)

### Deploy (two-step because of project-first quirk)
```bash
cd ~/Documents/forge/sites/<slug>

# Step 1: ensure project exists (idempotent — exit 0 if already there)
wrangler pages project create <slug> --production-branch main || true

# Step 2: deploy
wrangler pages deploy . --project-name=<slug> --branch main
```

The adapter wraps both steps and handles the `project already exists` error silently.

### Limits (free tier)
- **Unlimited** bandwidth (this is the killer feature)
- 500 builds / month
- 100 custom domains / project
- Unlimited sites
- India edge: Mumbai (multiple BOM pops)
- CC required: **no**

### When to switch default to this
> 50 deliveries / month. The unlimited bandwidth matters once a prospect WhatsApps the link to 500 of their contacts and you don't want a surprise Vercel BW bill.

## Migration between hosts

Both hosts accept identical static output (`index.html` + `styles.css` + `assets/`). Migration is re-run deploy on the new adapter — zero rebuild needed.

## What neither host does well

| Need | Why both fail | Workaround |
|---|---|---|
| Form submission | Static sites don't have a backend | Formspree (or wait for upsell) |
| Server-side auth | Same | None — not in scope for ₹9,999 |
| Custom domain without DNS access | Need the prospect's domain registrar access | Deploy to `<slug>.vercel.app` / `<slug>.pages.dev` first, custom domain later |
| WordPress-style admin | Static, by definition | Decap CMS is the upsell (₹1,999 setup) |

## Tearing down (when a prospect churns)

```bash
# Vercel
vercel rm <slug>

# Cloudflare
wrangler pages project delete <slug>
```

Add to the .delivered.json sidecar so cleanup is part of the lifecycle.
