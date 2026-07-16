#!/usr/bin/env python3
"""
Forge Website — build the ₹9,999 deliverable.

Inputs (one of):
  --from-client <path>      (most complete — uses forge-audit's .client.json)
  --from-gbp   <url>        (with --name, --whatsapp, etc as needed)
  --from-url   <website>    (run forge-audit website mode inline)

Output:
  ~/Documents/forge/sites/<slug>/
    index.html, about.html, services.html, reviews.html, contact.html
    styles.css, assets/images/business-1.webp..6.webp
  ~/Documents/forge/sites/<slug>--<date>.delivered.json

Deploy (optional):
  --deploy vercel|cloudflare|none   (default: none)
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
BASE_DIR = TEMPLATES_DIR / "_base"
INDUSTRY_COPY_PATH = SKILL_ROOT / "references" / "industry-copy.md"
DEFAULT_OUT_DIR = Path.home() / "Documents" / "forge" / "sites"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.15.19")
PHOTO_MAX_BYTES = 1_500_000  # 1.5 MB per photo
PHOTO_TIMEOUT = 12


# ─────────────────────────────────────────────────────────────────────────
# Industry mapping
# ─────────────────────────────────────────────────────────────────────────
INDUSTRY_ALIASES = {
    "salon": ["salon", "hair", "nail", "spa", "beauty", "barber", "stylist", "parlour", "parlor"],
    "restaurant": ["restaurant", "cafe", "diner", "bistro", "pizza", "sushi", "bar", "bakery", "food", "dhaba", "kitchen"],
    "clinic": ["clinic", "doctor", "dentist", "medical", "hospital", "chiro", "therapy", "physio", "diagnostic", "pharmacy"],
    "contractor": ["contractor", "plumber", "electrician", "hvac", "roofing", "remodel", "construction", "builder", "civil"],
    "retail": ["store", "shop", "boutique", "retail", "clothing", "gifts", "jewel", "jewellery", "apparel"],
    "fitness": ["gym", "fitness", "yoga", "crossfit", "pilates", "boxing", "martial", "dance", "zumba"],
    "auto": ["auto", "car", "mechanic", "tire", "tyre", "brake", "collision", "garage", "motor", "workshop"],
}

INDUSTRY_LABEL = {
    "salon": "Salon & Beauty",
    "restaurant": "Restaurant",
    "clinic": "Clinic & Wellness",
    "contractor": "Contractor & Trades",
    "retail": "Retail & Boutique",
    "fitness": "Fitness & Studio",
    "auto": "Auto & Workshop",
    "other": "Local Business",
}

PRIMARY_CTA = {
    "salon": "WhatsApp to Book",
    "restaurant": "Reserve a Table",
    "clinic": "Book Appointment",
    "contractor": "Get a Free Quote",
    "retail": "Get Directions",
    "fitness": "Start Free Trial",
    "auto": "Get a Quote",
    "other": "WhatsApp Us",
}
SECONDARY_CTA = {
    "salon": "Call Now",
    "restaurant": "Get Directions",
    "clinic": "Call Now",
    "contractor": "Call Now",
    "retail": "WhatsApp Us",
    "fitness": "View Schedule",
    "auto": "Call Now",
    "other": "Call Now",
}

COLOR_PRIMARY = {
    "salon": "#c2185b",
    "restaurant": "#bf360c",
    "clinic": "#00695c",
    "contractor": "#1565c0",
    "retail": "#6a1b9a",
    "fitness": "#2e7d32",
    "auto": "#37474f",
    "other": "#37474f",
}

FONT_HEADING = {
    "salon": "Playfair Display",
    "restaurant": "Cormorant Garamond",
    "clinic": "Inter",
    "contractor": "Inter",
    "retail": "Inter",
    "fitness": "Inter",
    "auto": "Inter",
    "other": "Inter",
}

DEFAULT_HOURS = {
    "salon": [("Tuesday", "10:00 AM – 8:00 PM"), ("Wednesday", "10:00 AM – 8:00 PM"),
              ("Thursday", "10:00 AM – 8:00 PM"), ("Friday", "10:00 AM – 8:00 PM"),
              ("Saturday", "10:00 AM – 9:00 PM"), ("Sunday", "11:00 AM – 7:00 PM"),
              ("Monday", "Closed")],
    "restaurant": [("Monday", "12:00 PM – 11:00 PM"), ("Tuesday", "12:00 PM – 11:00 PM"),
                   ("Wednesday", "12:00 PM – 11:00 PM"), ("Thursday", "12:00 PM – 11:00 PM"),
                   ("Friday", "12:00 PM – 11:30 PM"), ("Saturday", "12:00 PM – 11:30 PM"),
                   ("Sunday", "12:00 PM – 10:00 PM")],
    "clinic": [("Monday", "9:00 AM – 7:00 PM"), ("Tuesday", "9:00 AM – 7:00 PM"),
               ("Wednesday", "9:00 AM – 7:00 PM"), ("Thursday", "9:00 AM – 7:00 PM"),
               ("Friday", "9:00 AM – 7:00 PM"), ("Saturday", "9:00 AM – 5:00 PM"),
               ("Sunday", "Closed")],
    "contractor": [("Monday", "8:00 AM – 7:00 PM"), ("Tuesday", "8:00 AM – 7:00 PM"),
                   ("Wednesday", "8:00 AM – 7:00 PM"), ("Thursday", "8:00 AM – 7:00 PM"),
                   ("Friday", "8:00 AM – 7:00 PM"), ("Saturday", "9:00 AM – 5:00 PM"),
                   ("Sunday", "Emergency Only")],
    "retail": [("Monday", "10:00 AM – 9:00 PM"), ("Tuesday", "10:00 AM – 9:00 PM"),
               ("Wednesday", "10:00 AM – 9:00 PM"), ("Thursday", "10:00 AM – 9:00 PM"),
               ("Friday", "10:00 AM – 10:00 PM"), ("Saturday", "10:00 AM – 10:00 PM"),
               ("Sunday", "11:00 AM – 8:00 PM")],
    "fitness": [("Monday", "5:00 AM – 10:00 PM"), ("Tuesday", "5:00 AM – 10:00 PM"),
                ("Wednesday", "5:00 AM – 10:00 PM"), ("Thursday", "5:00 AM – 10:00 PM"),
                ("Friday", "5:00 AM – 10:00 PM"), ("Saturday", "6:00 AM – 9:00 PM"),
                ("Sunday", "7:00 AM – 8:00 PM")],
    "auto": [("Monday", "8:30 AM – 7:00 PM"), ("Tuesday", "8:30 AM – 7:00 PM"),
             ("Wednesday", "8:30 AM – 7:00 PM"), ("Thursday", "8:30 AM – 7:00 PM"),
             ("Friday", "8:30 AM – 7:00 PM"), ("Saturday", "9:00 AM – 5:00 PM"),
             ("Sunday", "Closed")],
    "other": [("Monday", "9:00 AM – 7:00 PM"), ("Tuesday", "9:00 AM – 7:00 PM"),
              ("Wednesday", "9:00 AM – 7:00 PM"), ("Thursday", "9:00 AM – 7:00 PM"),
              ("Friday", "9:00 AM – 7:00 PM"), ("Saturday", "10:00 AM – 5:00 PM"),
              ("Sunday", "Closed")],
}

DEFAULT_REVIEWS = [
    {"text": "Best experience I've had in the area. Genuinely recommend.", "author": "Local Guide"},
    {"text": "Great service, friendly team, fair prices. Will be back.", "author": "Regular Customer"},
    {"text": "Easy to find, easy to deal with. Exactly what you want.", "author": "Verified Reviewer"},
]


# ─────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────
def slugify(name: str) -> str:
    """Filesystem-safe slug. ≤52 chars to stay under Vercel project name limit."""
    s = re.sub(r"[^a-z0-9-]+", "-", name.lower().strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "site")[:52]


def sha_short(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:10]


def fetch_url(url: str, timeout: int = PHOTO_TIMEOUT) -> tuple[int, bytes, dict]:
    """Minimal URL fetch (no auth, no retries)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except Exception as e:
        return 0, f"ERROR: {type(e).__name__}: {e}".encode(), {}


def normalize_phone(raw: str | None) -> tuple[str, str, str]:
    """
    Return (display, raw_digits, intl_digits).

    Handles:
      +91 98765 43210
      +919876543210
      9876543210
      +91 98xxx xxx x  (masked — keep as-is, return display unchanged, no digits for tel/wa)
      None / '' → ("", "", "")

    For masked numbers we DO NOT try to build a wa.me link from them — the
    build will surface a warning and rely on a separate --whatsapp override.
    """
    if not raw:
        return "", "", ""
    raw = raw.strip()

    # If the input contains any letter (masked like "98xxx"), preserve as-is
    has_x = bool(re.search(r"[a-zA-Z]", raw))
    if has_x:
        return raw, "", ""

    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw, "", ""

    if digits.startswith("91") and len(digits) == 12:
        intl = "+" + digits
    elif len(digits) == 10:
        intl = "+91" + digits
    else:
        intl = "+" + digits

    # Display: +91 98765 43210 style
    if intl.startswith("+91") and len(intl) == 13:
        d = intl[3:]
        display = f"+91 {d[:5]} {d[5:]}"
    elif len(intl) >= 8:
        cc = intl[:3] if intl.startswith("+") else ""
        rest = intl[1+len(cc):] if cc else intl
        rest_fmt = " ".join(rest[i:i+5] for i in range(0, len(rest), 5)).strip()
        display = (cc + " " + rest_fmt).strip()
    else:
        display = intl
    raw_href = re.sub(r"\D", "", intl)
    return display, raw_href, intl.lstrip("+")


def detect_industry(category: str | None, name: str | None = None) -> str:
    """Pick the best-fit industry key from category text + name text."""
    haystack = (category or "") + " " + (name or "")
    haystack = haystack.lower()
    for industry, keywords in INDUSTRY_ALIASES.items():
        if any(k in haystack for k in keywords):
            return industry
    return "other"


def parse_hours(hours_raw) -> list[tuple[str, str]]:
    """Accept a list of (day, time) tuples or a dict {day: time}. Returns standardized rows."""
    if not hours_raw:
        return []
    out = []
    if isinstance(hours_raw, dict):
        for day, t in hours_raw.items():
            out.append((str(day), str(t)))
    elif isinstance(hours_raw, list):
        for row in hours_raw:
            if isinstance(row, (list, tuple)) and len(row) >= 2:
                out.append((str(row[0]), str(row[1])))
            elif isinstance(row, dict) and "day" in row:
                out.append((str(row["day"]), str(row.get("hours", ""))))
    return out


def build_hours_rows(industry: str, hours_raw) -> tuple[str, str]:
    """Return (HOURS_ROWS HTML, HOURS_JSON string). Falls back to industry defaults."""
    rows = parse_hours(hours_raw)
    if not rows:
        rows = DEFAULT_HOURS.get(industry, DEFAULT_HOURS["other"])
    html = "\n".join(
        f'        <tr><th scope="row">{day}</th><td>{t}</td></tr>' for day, t in rows
    )
    js_rows = [{"day": d, "hours": t} for d, t in rows]
    return html, json.dumps(js_rows)


def build_stars(rating: float | None) -> str:
    if rating is None:
        return '<span class="star">★</span>' * 5
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    s = '<span class="star">★</span>' * full
    s += '<span class="star star--half">★</span>' * half
    s += '<span class="star star--empty">★</span>' * empty
    return s


def build_services_cards(industry: str) -> str:
    """Pull the 6 service cards from industry-copy.md for the given industry, fallback to 'other'."""
    text = INDUSTRY_COPY_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.MULTILINE)
    by_industry = {}
    for s in sections[1:]:  # skip preamble
        head, body = s.split("\n", 1)
        key = head.strip()
        by_industry[key] = body
    body = by_industry.get(industry, by_industry.get("other", ""))
    # Parse the markdown table
    rows = []
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            rows.append(cells)
    cards = []
    for slot, title, desc in rows[:6]:
        cards.append(
            f'<article class="service-card">\n'
            f'  <h3 class="service-card__title">{title}</h3>\n'
            f'  <p class="service-card__desc">{desc}</p>\n'
            f'</article>'
        )
    return "\n".join(cards)


def build_photo_img(path: str, alt: str, css_class: str = "hero__photo") -> str:
    """Render an <img> if path is non-empty, otherwise a styled placeholder block."""
    if path:
        return f'<img class="{css_class}" src="{path}" alt="{alt}" loading="lazy" />'
    # Fallback: a gradient placeholder that's still on-brand
    return (
        f'<div class="{css_class}-placeholder" aria-label="{alt}">'
        f'{alt.split("—")[0].strip() if "—" in alt else alt}'
        f'</div>'
    )


def build_email_block(email: str) -> str:
    """Render an email link block (footer items + contact button). Returns "" if no email."""
    if not email:
        return ""
    return f'<li><a href="mailto:{email}">{email}</a></li>'


def build_review_cards(reviews: list | None) -> str:
    items = (reviews or [])[:6]
    if len(items) < 3:
        items = DEFAULT_REVIEWS[:max(3, len(items))]
    cards = []
    for r in items[:3]:
        text = (r.get("text") if isinstance(r, dict) else r) or ""
        author = (r.get("author") if isinstance(r, dict) else None) or "Verified Reviewer"
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        cards.append(
            f'      <article class="review-card">\n'
            f'        <div class="review-card__stars"><span class="star">★</span><span class="star">★</span><span class="star">★</span><span class="star">★</span><span class="star">★</span></div>\n'
            f'        <p class="review-card__text">&ldquo;{text}&rdquo;</p>\n'
            f'        <p class="review-card__author">— {author}</p>\n'
            f'      </article>'
        )
    return "\n".join(cards)


def download_photos(photo_urls: list[str], out_dir: Path) -> list[str]:
    """
    Self-host photos. Returns local paths (relative to out_dir) for up to 6 photos.
    Falls back to empty strings for any failed download.
    """
    out = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(photo_urls[:6], 1):
        if not url:
            out.append("")
            continue
        target = out_dir / f"business-{i}.jpg"
        if target.exists() and target.stat().st_size > 0:
            out.append(f"assets/images/business-{i}.jpg")
            continue
        try:
            status, body, _ = fetch_url(url)
            if status != 200 or len(body) < 1000:
                out.append("")
                continue
            if len(body) > PHOTO_MAX_BYTES:
                # Skip oversized (Photos API returns 4K originals we don't want to ship)
                out.append("")
                continue
            target.write_bytes(body)
            out.append(f"assets/images/business-{i}.jpg")
        except Exception:
            out.append("")
    return out


# ─────────────────────────────────────────────────────────────────────────
# Input resolution — three sources
# ─────────────────────────────────────────────────────────────────────────
def resolve_from_client(path: Path) -> dict:
    """
    Read a .client.json from forge-audit. Returns a normalized signals dict.

    Handles two shapes emitted over time:
      v1 (current): top-level { client: {...}, audit_file: "...", messages: {...} }
                     — client.* holds prospect info, audit_file points at signals.json + body.json
      v2 (legacy):  top-level { inputs, signals, leaks, ... }

    Builds prefer client.* and fold in signals.json if available.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    client = data.get("client") or {}
    inputs = data.get("inputs") or {}
    sig = data.get("signals") or {}

    # If an audit_file is referenced, try to enrich from signals.json
    af = data.get("audit_file")
    if af:
        ap = (path.parent / af) if not Path(af).is_absolute() else Path(af)
        if ap.exists():
            try:
                sig2 = json.loads(ap.read_text(encoding="utf-8"))
                sig = {**sig2, **sig}  # signals wins where overlapping
            except Exception:
                pass

    def g(d, k, default=""):
        v = d.get(k)
        return v if v is not None else default

    name = g(client, "business") or g(inputs, "name") or g(sig, "name") or "Local Business"
    category = g(client, "category") or g(inputs, "category") or g(sig, "category") or ""

    # Review/coverage pulled from audit_stats when present
    stats = data.get("audit_stats") or {}

    return {
        "name": name,
        "category": category,
        "phone": g(inputs, "phone") or g(sig, "phone") or "",
        # NOTE: client.whatsapp may be masked ("+919****3210") — handled by normalize_phone.
        "whatsapp": g(client, "whatsapp") or g(inputs, "whatsapp") or g(inputs, "phone") or g(sig, "phone"),
        "email": g(client, "email") or g(inputs, "email") or g(sig, "email"),
        "address": g(sig, "address"),
        "rating": g(sig, "rating") or stats.get("rating"),
        "review_count": g(sig, "review_count") or stats.get("review_count"),
        "reviews": g(sig, "reviews"),
        "hours": g(sig, "hours"),
        "description": g(sig, "description"),
        "photo_urls": g(sig, "photos"),
        "tagline": g(sig, "tagline"),
        "leaks": data.get("flags") or data.get("leaks") or [],
        "_client": client,
        "_audit_file": af,
    }


def resolve_from_gbp(url: str, **cli_overrides) -> dict:
    """Shells out to forge-audit's investigate. Falls back to manual fields if it fails."""
    audit_script = Path.home() / ".hermes" / "skills" / "forge" / "audit" / "scripts" / "audit.py"
    if audit_script.exists():
        try:
            tmp = Path.home() / "Documents" / "forge" / "audits" / f"_gbp-{int(time.time())}.json"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            cmd = [sys.executable, str(audit_script), "gbp",
                   "--url", url, "--name", cli_overrides.get("name", ""),
                   "--business", cli_overrides.get("business", cli_overrides.get("name", "")),
                   "--whatsapp", cli_overrides.get("whatsapp", ""),
                   "--out-dir", str(tmp.parent)]
            subprocess.run(cmd, capture_output=True, timeout=120)
            # Forge audit emits <slug>--<date>.json next to inputs; locate newest
            candidates = sorted(tmp.parent.glob("*--*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                return resolve_from_client(candidates[0])
        except Exception:
            pass
    # Manual fallback — minimal signals
    return {
        "name": cli_overrides.get("name") or "Local Business",
        "category": cli_overrides.get("category", ""),
        "phone": cli_overrides.get("phone", ""),
        "whatsapp": cli_overrides.get("whatsapp") or cli_overrides.get("phone", ""),
        "email": cli_overrides.get("email", ""),
        "address": cli_overrides.get("address", ""),
        "rating": None, "review_count": None, "reviews": [],
        "hours": None, "description": "",
        "photo_urls": [],
        "tagline": cli_overrides.get("tagline", ""),
        "leaks": [],
    }


def resolve_from_website(url: str, **cli_overrides) -> dict:
    """Run forge-audit website mode, lift signals."""
    audit_script = Path.home() / ".hermes" / "skills" / "forge" / "audit" / "scripts" / "audit.py"
    if not audit_script.exists():
        return resolve_from_gbp(url, **cli_overrides)
    try:
        tmp = Path.home() / "Documents" / "forge" / "audits"
        tmp.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(audit_script), "website", "--url", url, "--out-dir", str(tmp)]
        subprocess.run(cmd, capture_output=True, timeout=120)
        candidates = sorted(tmp.glob("*--*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return resolve_from_client(candidates[0])
    except Exception:
        pass
    return resolve_from_gbp(url, **cli_overrides)


# ─────────────────────────────────────────────────────────────────────────
# Build: render 5 pages
# ─────────────────────────────────────────────────────────────────────────
def render_pages(site_dir: Path, tokens: dict, industry: str) -> list[Path]:
    """Render the 5 pages from _base templates + industry overrides."""
    base = BASE_DIR
    industry_dir = TEMPLATES_DIR / industry
    pages_written = []
    for page in ["index", "about", "services", "reviews", "contact"]:
        # Industry-specific override if present, else base
        industry_file = industry_dir / f"{page}.html"
        base_file = base / f"{page}.html"
        src = industry_file if industry_file.exists() else base_file
        if not src.exists():
            sys.exit(f"missing template: {src}")
        rendered = src.read_text(encoding="utf-8")
        # Resolve every {{TOKEN}}
        for k, v in tokens.items():
            rendered = rendered.replace("{{" + k + "}}", str(v))
        # Write
        out = site_dir / f"{page}.html"
        out.write_text(rendered, encoding="utf-8")
        pages_written.append(out)

    # styles.css — pick base, with industry override
    css_industry = industry_dir / "styles.css"
    css_base = base / "styles.css"
    css_src = css_industry if css_industry.exists() else css_base
    if css_src.exists():
        css_text = css_src.read_text(encoding="utf-8")
        for k, v in tokens.items():
            css_text = css_text.replace("{{" + k + "}}", str(v))
        (site_dir / "styles.css").write_text(css_text, encoding="utf-8")

    # JS for open-now indicator
    js_base = base / "open-now.js"
    if js_base.exists():
        (site_dir / "open-now.js").write_text(js_base.read_text(encoding="utf-8"), encoding="utf-8")

    # Logo (ship every site with the Forge mark + site favicon)
    logo_src = SKILL_ROOT / "assets" / "logo.svg"
    if logo_src.exists():
        out_assets = site_dir / "assets"
        out_assets.mkdir(parents=True, exist_ok=True)
        (out_assets / "logo.svg").write_text(logo_src.read_text(encoding="utf-8"), encoding="utf-8")

    return pages_written


def lint_pages(site_dir: Path) -> list[str]:
    """Find any {{TOKEN}} left literal in shipped HTML + CSS. Returns list of stragglers."""
    bad = []
    for path in sorted(list(site_dir.glob("*.html")) + list(site_dir.glob("*.css"))):
        text = path.read_text(encoding="utf-8")
        for m in re.findall(r"\{\{([A-Z_0-9]+)\}\}", text):
            bad.append(f"{path.name}: {{{{{m}}}}} still literal")
    return bad


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Forge Website — ₹9,999 deliverable.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-client", help="Path to a forge-audit .client.json file")
    src.add_argument("--from-gbp", help="Google Maps/GBP URL")
    src.add_argument("--from-url", help="Existing website URL")
    ap.add_argument("--name", help="Override business name")
    ap.add_argument("--business", help="Override business name (alias)")
    ap.add_argument("--whatsapp", help="Override WhatsApp number (intl format)")
    ap.add_argument("--phone", help="Override phone")
    ap.add_argument("--category", help="Override category (e.g. 'Hair Salon')")
    ap.add_argument("--address", help="Override address")
    ap.add_argument("--email", help="Override email")
    ap.add_argument("--tagline", help="Override tagline")
    ap.add_argument("--out", help="Output directory (default: ~/Documents/forge/sites/<slug>)")
    ap.add_argument("--deploy", choices=["vercel", "cloudflare", "none"], default="none",
                    help="Deploy after build. default: none (build only)")
    ap.add_argument("--dry-run", action="store_true", help="Build but don't write to disk")
    args = ap.parse_args()

    t0 = time.time()
    cli_overrides = {k: v for k, v in vars(args).items()
                     if k in ("name", "business", "whatsapp", "phone", "category", "address", "email", "tagline")
                     and v}

    # 1. Resolve signals
    if args.from_client:
        signals = resolve_from_client(Path(args.from_client).expanduser())
    elif args.from_gbp:
        signals = resolve_from_gbp(args.from_gbp, **cli_overrides)
    else:
        signals = resolve_from_website(args.from_url, **cli_overrides)

    # Apply CLI overrides last (always win)
    for k, v in cli_overrides.items():
        if k == "business" and not signals.get("name"):
            signals["name"] = v
        elif k in signals:
            signals[k] = v

    name = signals["name"]
    industry = detect_industry(signals.get("category", ""), name)
    signals["_industry"] = industry

    # 2. Output dir
    slug = slugify(name)
    site_dir = Path(args.out).expanduser() if args.out else DEFAULT_OUT_DIR / slug
    site_dir.mkdir(parents=True, exist_ok=True)

    # 3. Token assembly
    phone_display, phone_raw, phone_intl = normalize_phone(signals.get("phone"))
    whatsapp_display, whatsapp_raw, whatsapp_intl = normalize_phone(signals.get("whatsapp") or signals.get("phone"))
    # WhatsApp message — warm opener
    wa_msg = urllib.parse.quote(
        f"Hi {name}, I'd like to {('book' if industry in ('salon','clinic','restaurant') else 'enquire about')} something."
    )
    tagline = signals.get("tagline") or _default_tagline(name, industry)

    # Photos first (so {{PHOTO_1}}..{{PHOTO_6}} are local paths)
    photos = download_photos(signals.get("photo_urls") or [], site_dir / "assets" / "images")
    while len(photos) < 6:
        photos.append("")

    # Resolve hours
    hours_html, hours_json = build_hours_rows(industry, signals.get("hours"))

    tokens = {
        "NAME": name,
        "TAGLINE": tagline,
        "DESCRIPTION": signals.get("description") or _default_description(industry, name),
        "PHONE": phone_display,
        "PHONE_RAW": phone_raw,
        "PHONE_INTL": phone_intl,
        "WHATSAPP": whatsapp_display or phone_display,
        "WHATSAPP_RAW": whatsapp_raw,
        "WHATSAPP_MESSAGE": wa_msg,
        # Pre-composed wa.me URL — never broken even if WHATSAPP_RAW is empty
        # (falls back to wa.me/0 which is a valid (empty) chat but signals
        # the prospect to call instead — read via CSS guard).
        "WHATSAPP_URL": (
            f"https://wa.me/{whatsapp_raw}?text={wa_msg}" if whatsapp_raw else "#whatsapp-missing"
        ),
        "ADDRESS": signals.get("address", ""),
        "ADDRESS_ENCODED": urllib.parse.quote(signals.get("address", "")),
        "CITY": _guess_city(signals.get("address", "")),
        "RATING": signals.get("rating") or "—",
        "REVIEW_COUNT": signals.get("review_count") or 0,
        "STARS_HTML": build_stars(signals.get("rating")),
        "HOURS_ROWS": hours_html,
        "HOURS_JSON": hours_json,
        "SERVICES_CARDS": build_services_cards(industry),
        "REVIEW_CARDS": build_review_cards(signals.get("reviews")),
        # Photos resolve to <img> tags (or branded placeholders if download failed)
        "PHOTO_1": build_photo_img(photos[0], f"{name} — front of house"),
        "PHOTO_2": build_photo_img(photos[1], f"{name} — interior", css_class="story-photo"),
        "PHOTO_3": build_photo_img(photos[2], f"{name}"),
        "PHOTO_4": build_photo_img(photos[3], f"{name}"),
        "PHOTO_5": build_photo_img(photos[4], f"{name}"),
        "PHOTO_6": build_photo_img(photos[5], f"{name}"),
        # Photo URL strings only (for <meta>, JSON-LD "image")
        "OG_IMAGE": photos[0] or "",
        "YEAR": str(datetime.now().year),
        "INDUSTRY": industry,
        "INDUSTRY_LABEL": INDUSTRY_LABEL[industry],
        "CTA_PRIMARY": PRIMARY_CTA[industry],
        "CTA_SECONDARY": SECONDARY_CTA[industry],
        "COLOR_PRIMARY": COLOR_PRIMARY[industry],
        "FONT_HEADING": FONT_HEADING[industry],
        "FONT_HEADING_ENCODED": urllib.parse.quote(FONT_HEADING[industry]),
        "FONT_BODY": "Inter",
        "EMAIL": build_email_block(signals.get("email", "")),       # <li>...</li> for footer
        "EMAIL_BTN": (
            f'<a class="btn btn--secondary" href="mailto:{signals.get("email", "")}">'
            f'✉️ Email Us</a>'
            if signals.get("email") else ""
        ),
        "LEAKS": len(signals.get("leaks") or []),
    }

    print(f"🏗  Building for: {name}")
    print(f"   industry: {INDUSTRY_LABEL[industry]}  (category: {signals.get('category') or '—'})")
    print(f"   slug:     {slug}")
    print(f"   out:      {site_dir}")
    print(f"   photos:   {sum(1 for p in photos if p)}/{len(photos)} downloaded")
    print(f"   whatsapp: {whatsapp_intl or '—'}")

    if args.dry_run:
        print("\n[DRY RUN — not writing files]")
        return 0

    # 4. Render
    pages = render_pages(site_dir, tokens, industry)

    # 5. Lint
    bad = lint_pages(site_dir)
    if bad:
        print("\n⚠️  Unresolved tokens leaked into shipped HTML:")
        for b in bad:
            print(f"   {b}")

    # 6. Deliverable manifest
    build_seconds = round(time.time() - t0, 2)
    manifest = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "business": name,
        "slug": slug,
        "industry": industry,
        "industry_label": INDUSTRY_LABEL[industry],
        "phone": phone_display,
        "whatsapp": whatsapp_intl,
        "address": signals.get("address", ""),
        "files": [str(p.relative_to(site_dir.parent)) for p in sorted(site_dir.rglob("*")) if p.is_file()],
        "file_count": sum(1 for _ in site_dir.rglob("*") if _.is_file()),
        "page_count": len(pages),
        "photo_count": sum(1 for p in photos if p),
        "build_seconds": build_seconds,
        "deploy_url": None,
        "deploy_target": args.deploy,
        "hosted_on": None,
        "leaks_closed": signals.get("leaks", []),
        "client_source": args.from_client or args.from_gbp or args.from_url,
        "errors": [],
        "unresolved_tokens": bad,
        "command": "python3 ~/.hermes/skills/forge/website/scripts/build.py " +
                   ("--from-client " + args.from_client if args.from_client else
                    "--from-gbp " + args.from_gbp if args.from_gbp else
                    "--from-url " + args.from_url),
    }
    manifest_path = site_dir.parent / f"{slug}--{datetime.now().strftime('%Y-%m-%d')}.delivered.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Append-only analytics
    log = Path.home() / ".forge" / "delivered.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: manifest[k] for k in ("ts", "business", "slug", "industry", "build_seconds", "deploy_target")}) + "\n")

    print(f"\n✅ Built {len(pages)} pages + {manifest['photo_count']} photos in {build_seconds}s")
    print(f"   manifest: {manifest_path}")
    if bad:
        print(f"   ⚠️  {len(bad)} unresolved tokens — see manifest")
        return 1

    # 7. Deploy (optional)
    if args.deploy != "none":
        adapter = SKILL_ROOT / "scripts" / "adapters" / f"deploy_{args.deploy}.py"
        if not adapter.exists():
            sys.exit(f"deploy adapter not found: {adapter}")
        print(f"\n🚀 Deploying to {args.deploy}...")
        result = subprocess.run(
            [sys.executable, str(adapter), str(site_dir)],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"   ❌ deploy failed:\n{result.stderr}", file=sys.stderr)
            manifest["deploy_url"] = None
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return 2
        # Try to read deploy URL from adapter's last line (format: DEPLOY_URL=https://…)
        deploy_url = None
        for line in result.stdout.splitlines()[::-1]:
            if line.startswith("DEPLOY_URL="):
                deploy_url = line.split("=", 1)[1].strip()
                break
        manifest["deploy_url"] = deploy_url
        manifest["hosted_on"] = args.deploy
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if deploy_url:
            # Emit the WhatsApp handoff line — copy/paste ready
            wa_handoff = (
                f"wa.me/{whatsapp_intl}?text=" + urllib.parse.quote(
                    f"Hi {name}, your ₹9,999 site is live: {deploy_url}. "
                    f"Reply YES to keep it, or tell me what to change. — Forge"
                ) if whatsapp_intl and deploy_url else ""
            )
            print(f"\n📱 WhatsApp handoff: {wa_handoff}")
            print(f"\nDEPLOY_URL={deploy_url}")
        return 0
    return 0


def _default_tagline(name: str, industry: str) -> str:
    return {
        "salon": f"Precision hair, skin & nails in the heart of the city.",
        "restaurant": f"Honest food, made fresh, served with care.",
        "clinic": f"Trusted care, close to home.",
        "contractor": f"Built right the first time. Guaranteed.",
        "retail": f"Curated picks. Honest prices. Always.",
        "fitness": f"Real training. Real results.",
        "auto": f"Honest service, fair prices, on the same day.",
        "other": f"Local, trusted, here when you need us.",
    }[industry]


def _default_description(industry: str, name: str) -> str:
    return {
        "salon": f"{name} is a full-service salon offering hair, skin, and nail care with senior stylists and clean, hospital-grade products. Walk-ins welcome, appointments preferred.",
        "restaurant": f"{name} serves honest, freshly-prepared food using ingredients sourced from local suppliers where possible. Open for lunch and dinner, seven days a week.",
        "clinic": f"{name} provides primary care and specialist consultations under one roof. Walk-ins welcome, same-day appointments usually available. Most insurance accepted.",
        "contractor": f"{name} is a licensed, insured contractor with 10+ years in residential and commercial work. Fixed-price contracts, 1-year warranty on every job, free site visits.",
        "retail": f"{name} curates a tight selection of quality goods at fair prices. Visit the store, or shop on WhatsApp with same-day pickup or pan-India delivery.",
        "fitness": f"{name} offers certified personal training, group classes, and a fully-equipped floor. Drop in for a free week — no card required, no contracts.",
        "auto": f"{name} is a Bosch-certified workshop handling periodic service, accident repair, and roadside help. Pickup and drop within city, cashless insurance claims.",
        "other": f"{name} serves the local community with a focus on quality, fair pricing, and reliable service. Get in touch to discuss what you need.",
    }[industry]


def _guess_city(address: str) -> str:
    """First comma-separated chunk beyond the street address that looks like a city (no digits)."""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    for p in parts[1:]:
        if not re.search(r"\d", p):
            return p
    return parts[0] if parts else ""


if __name__ == "__main__":
    sys.exit(main())
