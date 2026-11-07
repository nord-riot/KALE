/* KALE v2.2 offline assets; no third-party network dependencies. */
const CACHE='kale-v2.2.0';
const CORE=['/','/index.html','/assets/style.css','/assets/app.js','/assets/tools.js',
 '/ilaclar.html','/assets/medicines.css','/assets/medicines.js','/assets/medicines-offline.json',
 '/doktor.html','/assets/doctor.js','/saha.html','/doga.html','/harita.html','/rota.html','/assets/vector-tile.js','/assets/route.js',
 '/atolye.html','/assets/editor.js','/assets/editor.css',
 '/plan.html','/assets/plan.js','/assets/plan.css','/offline.html','/assets/offline.js',
 '/assets/module.css','/assets/field.js','/assets/plants.js','/assets/map.js',
 '/barinak-su.html','/assets/shelter-water.css','/assets/shelter-water.js','/assets/shelter-water.json',
 '/gida-enerji.html','/assets/food-energy.css','/assets/food-energy.js','/assets/food-energy-winter.json',
 '/envanter.html','/assets/inventory.css','/assets/inventory-core.js','/assets/inventory.js',
 '/ilk-yardim.html','/assets/first-aid.css','/assets/first-aid.js','/assets/first-aid.json',
 '/yonetim.html','/assets/device.css','/assets/device.js',
 '/sohbet.html','/baglan.html','/assets/chat.js','/assets/network.js','/assets/chat.css',
 '/aktarim.html','/assets/transfer.css','/assets/transfer.js','/assets/sync-core.js',
 '/assets/field-guides.json','/assets/poisonous-plants.json','/assets/dangerous-mushrooms.json','/assets/nature.js','/assets/nature.css','/assets/base-map.json',
 '/assets/diagrams/afad.svg','/assets/diagrams/cantasi.svg','/assets/diagrams/su.svg',
 '/assets/diagrams/karbonmonoksit.svg','/assets/diagrams/barinak.svg','/assets/diagrams/aile.svg',
 '/assets/diagrams/konum.svg','/assets/diagrams/elektrik.svg',
 '/assets/diagrams/guide-09.svg',
 '/assets/diagrams/guide-10.svg',
 '/assets/diagrams/guide-11.svg',
 '/assets/diagrams/guide-12.svg',
 '/assets/diagrams/guide-13.svg',
 '/assets/diagrams/guide-14.svg',
 '/assets/diagrams/guide-15.svg',
 '/assets/diagrams/guide-16.svg',
 '/assets/diagrams/guide-17.svg',
 '/assets/diagrams/guide-18.svg',
 '/assets/diagrams/guide-19.svg',
 '/assets/diagrams/guide-20.svg',
 '/assets/diagrams/guide-21.svg',
 '/assets/diagrams/guide-22.svg',
 '/assets/diagrams/guide-23.svg',
 '/assets/diagrams/guide-24.svg',
 '/assets/diagrams/guide-25.svg','/assets/diagrams/guide-26.svg','/assets/diagrams/guide-27.svg','/assets/diagrams/guide-28.svg',
 '/assets/diagrams/bs-01.svg',
 '/assets/diagrams/bs-02.svg',
 '/assets/diagrams/bs-03.svg',
 '/assets/diagrams/bs-04.svg',
 '/assets/diagrams/bs-05.svg',
 '/assets/diagrams/bs-06.svg',
 '/assets/diagrams/bs-07.svg',
 '/assets/diagrams/bs-08.svg',
 '/assets/diagrams/bs-09.svg',
 '/assets/diagrams/bs-10.svg',
 '/assets/diagrams/bs-11.svg',
 '/assets/diagrams/bs-12.svg',
 '/assets/diagrams/bs-13.svg',
 '/assets/diagrams/bs-14.svg',
 '/assets/diagrams/bs-15.svg',
 '/assets/diagrams/bs-16.svg',
 '/assets/diagrams/bs-17.svg',
 '/assets/diagrams/bs-18.svg',
 '/assets/diagrams/ge-01.svg',
 '/assets/diagrams/ge-02.svg',
 '/assets/diagrams/ge-03.svg',
 '/assets/diagrams/ge-04.svg',
 '/assets/diagrams/ge-05.svg',
 '/assets/diagrams/ge-06.svg',
 '/assets/diagrams/ge-07.svg',
 '/assets/diagrams/ge-08.svg',
 '/assets/diagrams/ge-09.svg',
 '/assets/diagrams/ge-10.svg',
 '/assets/diagrams/ge-11.svg',
 '/assets/diagrams/ge-12.svg',
 '/assets/diagrams/ge-13.svg',
 '/assets/diagrams/ge-14.svg',
 '/assets/diagrams/ge-15.svg',
 '/assets/diagrams/ge-16.svg',
 '/assets/diagrams/ge-17.svg',
 '/assets/diagrams/ge-18.svg',
 '/assets/diagrams/ge-19.svg',
 '/assets/diagrams/ge-20.svg',
 '/assets/diagrams/ge-21.svg',
 '/assets/diagrams/ge-22.svg',
 '/assets/diagrams/ge-23.svg',
 '/assets/diagrams/ge-24.svg',
 '/assets/diagrams/aid-01.svg',
 '/assets/diagrams/aid-02.svg',
 '/assets/diagrams/aid-03.svg',
 '/assets/diagrams/aid-04.svg',
 '/assets/diagrams/aid-05.svg',
 '/assets/diagrams/aid-06.svg',
 '/assets/diagrams/aid-07.svg',
 '/assets/diagrams/aid-08.svg',
 '/assets/diagrams/aid-09.svg',
 '/assets/diagrams/aid-10.svg',
 '/assets/diagrams/aid-11.svg',
 '/assets/diagrams/aid-12.svg',
 '/assets/diagrams/aid-13.svg',
 '/assets/diagrams/aid-14.svg',
 '/assets/diagrams/aid-15.svg',
 '/assets/diagrams/aid-16.svg',
 '/assets/diagrams/aid-17.svg',
 '/assets/diagrams/aid-18.svg',
 '/assets/diagrams/aid-19.svg',
 '/assets/diagrams/aid-20.svg',
 '/assets/diagrams/aid-21.svg',
 '/assets/diagrams/aid-22.svg',
 '/assets/diagrams/aid-23.svg',
 '/assets/diagrams/aid-24.svg',
 '/assets/kale-emblem.webp','/assets/icon.svg','/favicon.svg','/manifest.webmanifest','/api/catalog'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('kale-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request;if(req.method!=='GET')return;
 const url=new URL(req.url);if(url.origin!==self.location.origin)return;
 if(url.pathname==='/api/catalog'){
  // Refresh locally edited guides when the server is reachable; offline falls back quickly.
  event.respondWith((async()=>{
   const cache=await caches.open(CACHE);
   const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),1400);
   try{const response=await fetch(req,{signal:ctrl.signal,cache:'no-store'});
    if(response.ok){try{await cache.put('/api/catalog',response.clone());}catch(_ignored){}}
    return response;
   }catch(e){const offline=await cache.match('/api/catalog');
    return offline||new Response(JSON.stringify({error:'Çevrimdışı katalog bulunamadı'}),{status:503,headers:{'Content-Type':'application/json'}});
   }finally{clearTimeout(timer);}
  })());return;
 }
 if(url.pathname.startsWith('/api/'))return; // tiles need local server, never pretend a map exists
 if(url.pathname==='/'||url.pathname==='/index.html'){
  event.respondWith(fetch(req).catch(()=>caches.match('/index.html')));return;
 }
 event.respondWith(caches.match(req).then(cached=>cached||fetch(req)));});
