# Per-industry template overrides

Drop an `index.html`, `about.html`, `services.html`, `reviews.html`, `contact.html`, or `styles.css` in this directory to override the base template for this industry.

The build picks `templates/<industry>/<page>.html` if it exists, else falls back to `templates/_base/<page>.html`. Most industries ship fine from the base templates + the curated 6-card copy in `references/industry-copy.md` — so these directories are **reserved for future per-industry specialisation** (e.g. a restaurant template that includes a menu PDF link).
