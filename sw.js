/* 서비스 워커 템플릿. build-standalone.sh가 2e9223531d18을 index.html 해시로
   바꿔 sw.js를 생성한다. 내용이 바뀌면 캐시 이름이 달라져 자동으로 갱신된다.
   이 파일이 아니라 sw.js를 직접 고치면 다음 빌드 때 덮어써진다. */

var CACHE = "sigvet-2e9223531d18";
var ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-maskable-512.png",
  "./apple-touch-icon.png",
  "./favicon-32.png",
  "./favicon-16.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;

  // 문서는 네트워크 우선 — 온라인이면 항상 최신 계산기를, 오프라인이면 캐시본을 쓴다.
  // 캐시 우선으로 하면 배포해도 갱신이 안 되므로 의도적으로 분리한다.
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put("./index.html", copy); });
        return res;
      }).catch(function () {
        return caches.match("./index.html").then(function (r) {
          return r || caches.match("./");
        });
      })
    );
    return;
  }

  // 아이콘·매니페스트 등 정적 자원은 캐시 우선
  e.respondWith(
    caches.match(req).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === "basic") {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
