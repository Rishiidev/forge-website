// Forge Website — Open/Closed pill
// Re-renders every 60s. Reads HOURS_JSON injected into body[data-hours].
(function () {
  const body = document.body;
  if (!body || !body.dataset.hours) return;
  let hours;
  try { hours = JSON.parse(body.dataset.hours); } catch (e) { return; }

  function isOpenAt(date, rows) {
    const day = date.toLocaleDateString('en-US', { weekday: 'long' });
    const now = date.getHours() * 60 + date.getMinutes();
    const row = rows.find(r => r.day.toLowerCase() === day.toLowerCase());
    if (!row) return false;
    const text = (row.hours || '').toLowerCase();
    if (text.includes('closed') || text.includes('emergency only')) return false;
    const match = text.match(/(\d{1,2}):(\d{2})\s*(am|pm)?\s*[–-]\s*(\d{1,2}):(\d{2})\s*(am|pm)?/i);
    if (!match) return false;
    const parseMins = (h, m, ap) => {
      let hh = parseInt(h, 10);
      if (ap) {
        const isPm = ap.toLowerCase() === 'pm';
        if (isPm && hh !== 12) hh += 12;
        if (!isPm && hh === 12) hh = 0;
      }
      return hh * 60 + parseInt(m, 10);
    };
    const open = parseMins(match[1], match[2], match[3]);
    const close = parseMins(match[4], match[5], match[6]);
    return now >= open && now <= close;
  }

  function updatePill() {
    document.querySelectorAll('[data-open-pill]').forEach(pill => {
      const open = isOpenAt(new Date(), hours);
      pill.classList.toggle('is-closed', !open);
      pill.textContent = open ? '● Open Now' : '● Closed';
      pill.setAttribute('aria-label', open ? 'Currently open' : 'Currently closed');
    });
  }
  updatePill();
  setInterval(updatePill, 60000);

  // Mobile nav toggle
  const burger = document.querySelector('.nav__hamburger');
  const menu = document.querySelector('.nav__menu');
  if (burger && menu) {
    burger.addEventListener('click', () => menu.classList.toggle('is-open'));
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => menu.classList.remove('is-open')));
  }
})();
