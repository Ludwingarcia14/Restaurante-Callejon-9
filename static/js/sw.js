const CACHE = 'callejon9-tracking-v1';
const PRECACHE = ['/seguimiento/'];

self.addEventListener('install', e => {
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Network-first: siempre intenta la red, cae en caché si falla
self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    e.respondWith(
        fetch(e.request)
            .then(res => {
                if (res.ok) {
                    const clone = res.clone();
                    caches.open(CACHE).then(c => c.put(e.request, clone));
                }
                return res;
            })
            .catch(() => caches.match(e.request))
    );
});

// Push notifications (Web Push API)
self.addEventListener('push', e => {
    if (!e.data) return;
    let data = {};
    try { data = e.data.json(); } catch { data = { title: 'Callejón 9', body: e.data.text() }; }

    e.waitUntil(
        self.registration.showNotification(data.title || 'Callejón 9', {
            body:    data.body  || '',
            icon:    '/static/img/logo.png',
            badge:   '/static/img/logo.png',
            vibrate: [200, 100, 200, 100, 200],
            tag:     data.tag   || 'tracking',
            data:    { url: data.url || '/' },
        })
    );
});

self.addEventListener('notificationclick', e => {
    e.notification.close();
    const url = e.notification.data?.url || '/';
    e.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
            const existing = list.find(c => c.url.includes(url) && 'focus' in c);
            if (existing) return existing.focus();
            return clients.openWindow(url);
        })
    );
});
