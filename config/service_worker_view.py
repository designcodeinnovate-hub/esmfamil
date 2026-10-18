# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.decorators.cache import never_cache


SW_CONTENT = r"""
// Service Worker for اسم فامیل آنلاین
const CACHE_NAME = 'esmfamil-v1';
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/audio/nature.mp3',
];

// Install — cache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('Cache addAll failed:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch — network first for HTML/API, cache first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip WebSocket and non-http(s)
  if (!url.protocol.startsWith('http')) return;

  // Skip admin / panel-admin / api
  if (url.pathname.startsWith('/panel-admin/') ||
      url.pathname.startsWith('/django-admin/') ||
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/beta-')) {
    return;
  }

  // Static files — cache first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((resp) => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return resp;
        });
      })
    );
    return;
  }

  // HTML/other — network first, cache fallback
  event.respondWith(
    fetch(event.request).then((resp) => {
      if (resp.ok && event.request.method === 'GET') {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
      }
      return resp;
    }).catch(() => {
      return caches.match(event.request).then((cached) => cached || new Response('offline', { status: 503 }));
    })
  );
});
"""


@never_cache
def service_worker(request):
    response = HttpResponse(SW_CONTENT, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response
