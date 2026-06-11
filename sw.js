/* sw.js — offline support for 虫药轮替 · Pest MoA
 *
 * The app is a single self-contained index.html (React, CSS, JS, and icons are
 * all inlined). The only external runtime resource is Google Fonts, which also
 * has a system-font fallback — so once the page is cached, the whole app works
 * with no connection.
 *
 * Strategy:
 *   1) Page (navigation): network-first → always fresh when online, cached copy
 *      when offline. This means app updates flow automatically; no manual cache
 *      busting needed for content changes.
 *   2) Google Fonts: cache-first, refreshed in the background (works offline
 *      once they've been seen at least once).
 *   3) Other same-origin GETs: cache-first, then network.
 *   4) Other cross-origin (e.g. the FoodMate / PPDB external links): untouched —
 *      handled normally by the browser.
 *
 * Bump CACHE_VERSION if you ever need to force every device to drop old caches.
 */
const CACHE_VERSION = 'pestmoa-v25-notes-label';

self.addEventListener('install', (event) => {
  // Activate this worker as soon as it finishes installing.
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) =>
      // Pre-cache the shell so even the very first offline open works.
      cache.addAll(['./', './index.html']).catch(() => {})
    )
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 1) The HTML page itself — network-first, fall back to cache (enables offline).
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() =>
          caches
            .match(req)
            .then((r) => r || caches.match('./index.html'))
            .then((r) => r || caches.match('./'))
        )
    );
    return;
  }

  // 2) Google Fonts — cache-first, refresh in the background.
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req)
          .then((res) => {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((c) => c.put(req, copy)).catch(() => {});
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // 3) Any other same-origin GET — cache-first, fall back to network.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req).then(
        (cached) =>
          cached ||
          fetch(req)
            .then((res) => {
              const copy = res.clone();
              caches.open(CACHE_VERSION).then((c) => c.put(req, copy)).catch(() => {});
              return res;
            })
            .catch(() => cached)
      )
    );
  }
  // 4) Other cross-origin requests fall through to the network untouched.
});
