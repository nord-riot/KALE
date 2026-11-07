'use strict';
/* No external map, geolocation, analytics or service dependencies. */
const $=id=>document.getElementById(id),canvas=$('mapCanvas'),ctx=canvas.getContext('2d');
const KEY='kale_v1_private_points';
let center={lat:39,lon:35},zoom=5,selectedMap='turkiye',raster=false,minMapZoom=2,maxMapZoom=16,drag=null,tileCache=new Map(),points=[],baseMap=null,gps=null,targetPoint=null,vector=false,vectorCache=new Map(),drawnRoute=null;
window.KALEshowRoute=function(coords){drawnRoute=Array.isArray(coords)?coords:null;
 if(drawnRoute&&drawnRoute.length>=2){const lon=drawnRoute.reduce((a,p)=>a+p[0],0)/drawnRoute.length;
  const lat=drawnRoute.reduce((a,p)=>a+p[1],0)/drawnRoute.length;center={lat,lon};zoom=11;}
 draw();};window.KALEgetGps=()=>gps;
const tileSize=256,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function llToWorld(lat,lon,z){const p=clamp(lat,-85,85)*Math.PI/180,scale=tileSize*2**z;return {x:(lon+180)/360*scale,y:(1-Math.log(Math.tan(p)+1/Math.cos(p))/Math.PI)/2*scale};}
function worldToLl(x,y,z){const scale=tileSize*2**z;return {lon:(x/scale)*360-180,lat:Math.atan(Math.sinh(Math.PI*(1-2*y/scale)))*180/Math.PI};}
function viewport(){const dpr=window.devicePixelRatio||1;const rect=canvas.getBoundingClientRect();const width=Math.max(200,Math.round(rect.width)),height=Math.max(200,Math.round(rect.height));
 if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);}
 ctx.setTransform(dpr,0,0,dpr,0,0);return {width,height};}
function imgTile(z,x,y){const n=2**z;if(y<0||y>=n)return null;const wrapped=((x%n)+n)%n,key=`${selectedMap}/${z}/${wrapped}/${y}`;
 if(tileCache.has(key))return tileCache.get(key);
 if(tileCache.size>380){tileCache.clear();}
 const img=new Image();const item={img,loaded:false};tileCache.set(key,item);img.onload=()=>{item.loaded=true;draw();};img.onerror=()=>{item.failed=true;};img.src=`/api/tiles/${z}/${wrapped}/${y}?map=${encodeURIComponent(selectedMap)}`;return item;}
let pendingVector=0,streetTilesLoaded=0,streetTilesFailed=0,streetDecodeFailed=false;
function showStreetTileStatus(){
 if(!vector)return;
 const box=$('mapStatus');
 if(streetDecodeFailed){
  box.textContent='SOKAK ÇİZİM HATASI: Yerel vektör karosu tarayıcıda çözülemedi. KALE dosyalarını güncelle, harita paketini doğrula: python3 tools/check_streets.py';
 }else if(streetTilesLoaded===0&&streetTilesFailed>=4){
  box.textContent='SOKAKLAR YÜKLENEMEDİ: MBTiles kurulu görünüyor ancak bu bölgede sokak karosu dönmüyor. Terminal: cd ~/KALE && python3 tools/check_streets.py';
 }else if(streetTilesLoaded>0){
  box.textContent='GERÇEK SOKAK KAROLARI YÜKLENDİ · © OpenStreetMap katkıcıları (ODbL) · Ayrıntılar için 13–14 seviyesinde yakınlaştır.';
 }
}
function getVectorTile(z,x,y){const n=2**z;if(y<0||y>=n)return null;const col=((x%n)+n)%n;const key=`${z}/${col}/${y}`;
 if(vectorCache.has(key))return vectorCache.get(key);
 if(vectorCache.size>=100){const first=vectorCache.keys().next().value;vectorCache.delete(first);}
 const item={ready:false,failed:false,layers:null};vectorCache.set(key,item);
 if(pendingVector>=10){vectorCache.delete(key);return null;}
 pendingVector++;
 fetch(`/api/street/tiles/${z}/${col}/${y}`,{cache:'force-cache'}).then(async r=>{
  if(!r.ok)throw Error('Karo yok ('+r.status+')');
  const raw=await r.arrayBuffer();if(raw.byteLength>5_000_000)throw Error('Karo çok büyük');
  item.layers=window.KALEVector.decode(raw);
  if(!Array.isArray(item.layers)||!item.layers.length)throw Error('MVT katmanı boş');
  item.ready=true;streetTilesLoaded++;showStreetTileStatus();draw();
 }).catch(()=>{item.failed=true;streetTilesFailed++;showStreetTileStatus();})
  .finally(()=>{pendingVector--;});return item;
}
function drawBasemap(c,w,h){
 if(!baseMap)return;
 ctx.fillStyle='#28454b';ctx.strokeStyle='#83a8a5';ctx.lineWidth=1.25;
 for(const area of baseMap.areas)for(const poly of area.polygons){
  if(poly.length<3)continue;
  ctx.beginPath();let first=true;
  for(const [lon,lat] of poly){const pos=llToWorld(lat,lon,zoom);const x=pos.x-c.x+w/2,y=pos.y-c.y+h/2;
   if(first){ctx.moveTo(x,y);first=false}else ctx.lineTo(x,y);}
  ctx.closePath();ctx.fill();ctx.stroke();
 }
 const cities=[['Ankara',39.93,32.86],['İstanbul',41.01,28.98],['İzmir',38.42,27.14],['Antalya',36.89,30.70],['Samsun',41.29,36.33],['Gaziantep',37.07,37.38],['Van',38.50,43.38],['Erzurum',39.91,41.27]];
 ctx.font='12px Arial';ctx.textAlign='left';
 for(const [name,lat,lon] of cities){const pt=llToWorld(lat,lon,zoom),x=pt.x-c.x+w/2,y=pt.y-c.y+h/2;
  if(x<0||y<0||x>w||y>h)continue;ctx.fillStyle='#e9c186';ctx.beginPath();ctx.arc(x,y,3.2,0,6.283);ctx.fill();ctx.fillStyle='#e8f1e9';ctx.fillText(name,x+6,y+3);}
}
function draw(){if(!ctx)return;const {width:w,height:h}=viewport();ctx.clearRect(0,0,w,h);ctx.fillStyle='#17303a';ctx.fillRect(0,0,w,h);const c=llToWorld(center.lat,center.lon,zoom);
 if(!vector&&!raster)drawBasemap(c,w,h);
 const xStart=Math.floor((c.x-w/2)/256),xEnd=Math.floor((c.x+w/2)/256),yStart=Math.floor((c.y-h/2)/256),yEnd=Math.floor((c.y+h/2)/256);
 for(let x=xStart;x<=xEnd;x++)for(let y=yStart;y<=yEnd;y++){const px=Math.round(x*256-c.x+w/2),py=Math.round(y*256-c.y+h/2);if(y<0||y>=2**zoom)continue;
  if(vector){const t=getVectorTile(zoom,x,y);if(t&&t.ready&&!t.failed){try{window.KALEVector.paint(ctx,t.layers,px,py,256,zoom);}catch(e){t.failed=true;streetDecodeFailed=true;showStreetTileStatus();}continue;}}
  else if(raster){const t=imgTile(zoom,x,y);if(t&&t.loaded){ctx.drawImage(t.img,px,py,256,256);continue;}}
  ctx.strokeStyle='#36565b77';ctx.strokeRect(px,py,256,256);
 }
 if(!raster&&!vector){ctx.fillStyle='#061a22bd';ctx.fillRect(10,h-49,252,37);ctx.textAlign='left';ctx.fillStyle='#f0d2a3';ctx.font='bold 12px Arial';ctx.fillText('DOĞAL EARTH: ÖZET COĞRAFYA',18,h-33);ctx.font='10px Arial';ctx.fillStyle='#b7cbcb';ctx.fillText('Detay/rota verisi içermez',18,h-19);}
 if(drawnRoute&&drawnRoute.length>=2){ctx.beginPath();let first=true;for(const pt of drawnRoute){const wp=llToWorld(pt[1],pt[0],zoom),rx=wp.x-c.x+w/2,ry=wp.y-c.y+h/2;
   if(first){ctx.moveTo(rx,ry);first=false;}else ctx.lineTo(rx,ry);}
  ctx.strokeStyle='#0a3036';ctx.lineWidth=7;ctx.lineJoin='round';ctx.stroke();ctx.strokeStyle='#fc9e52';ctx.lineWidth=4;ctx.stroke();}
 if(gps){const wp=llToWorld(gps.lat,gps.lon,zoom),sx=wp.x-c.x+w/2,sy=wp.y-c.y+h/2;
   const metersPixel=156543.03392*Math.cos(gps.lat*Math.PI/180)/(2**zoom);
   if(metersPixel>0){ctx.beginPath();ctx.arc(sx,sy,Math.min(160,Math.max(8,gps.accuracy/metersPixel)),0,2*Math.PI);ctx.strokeStyle='#7fd6e5aa';ctx.lineWidth=2;ctx.stroke();}
   ctx.beginPath();ctx.arc(sx,sy,8,0,2*Math.PI);ctx.fillStyle='#5fc8ec';ctx.fill();ctx.strokeStyle='#effbff';ctx.lineWidth=3;ctx.stroke();
   ctx.fillStyle='#f5ffff';ctx.font='bold 12px Arial';ctx.fillText('GPS',sx+14,sy+4);
   if(targetPoint){const dest=llToWorld(targetPoint.lat,targetPoint.lon,zoom);ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(dest.x-c.x+w/2,dest.y-c.y+h/2);ctx.strokeStyle='#f3c778';ctx.lineWidth=2;ctx.setLineDash([6,6]);ctx.stroke();ctx.setLineDash([]);}
 }
 for(const p of points){const wp=llToWorld(p.lat,p.lon,zoom);let px=wp.x-c.x+w/2,py=wp.y-c.y+h/2;const span=tileSize*2**zoom;if(px<-(span/2))px+=span;if(px>w+span/2)px-=span;if(px<-30||px>w+30||py<-30||py>h+30)continue;
  ctx.beginPath();ctx.arc(px,py,8,0,Math.PI*2);ctx.fillStyle='#edb86d';ctx.fill();ctx.lineWidth=2;ctx.strokeStyle='#14242c';ctx.stroke();ctx.font='bold 12px Arial';ctx.fillStyle='#fff';ctx.shadowColor='#061318';ctx.shadowBlur=4;ctx.fillText(p.name.slice(0,25),px+13,py+4);ctx.shadowBlur=0;
 }
 $('mapInfo').textContent=`Merkez ${center.lat.toFixed(5)}, ${center.lon.toFixed(5)} · Yakınlık ${zoom}`;
}
function jump(lat,lon){center={lat:clamp(lat,-85,85),lon:((lon+180)%360+360)%360-180};draw();}
function getCoordAt(ev){const r=canvas.getBoundingClientRect(),w=r.width,h=r.height,c=llToWorld(center.lat,center.lon,zoom);return worldToLl(c.x+(ev.clientX-r.left)-w/2,c.y+(ev.clientY-r.top)-h/2,zoom);}
function changeZoom(delta){zoom=clamp(zoom+delta,minMapZoom,maxMapZoom);draw();}
function save(){try{localStorage.setItem(KEY,JSON.stringify(points));return true;}catch{alert('Noktalar kaydedilemedi: yerel depolama dolu veya kapalı.');return false;}}
function validatePoint(p){return p&&typeof p.name==='string'&&p.name.trim()&&p.name.length<=80&&typeof p.lat==='number'&&Number.isFinite(p.lat)&&Math.abs(p.lat)<=85&&typeof p.lon==='number'&&Number.isFinite(p.lon)&&Math.abs(p.lon)<=180;}
function load(){try{const d=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(d)&&d.length<=500)points=d.filter(validatePoint);}catch{points=[];}}
function renderPoints(){const list=$('pointList');list.replaceChildren();$('pointCount').textContent=`(${points.length}/500)`;
 for(const p of points){const row=document.createElement('div');row.className='point-item';const n=document.createElement('div'),title=document.createElement('strong'),coords=document.createElement('small');title.textContent=p.name;coords.textContent=`${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}`;n.append(title,coords);const actions=document.createElement('div');
 const go=document.createElement('button');go.className='secondary';go.textContent='GİT';go.addEventListener('click',()=>jump(p.lat,p.lon));
 const goal=document.createElement('button');goal.className='secondary goal';goal.textContent=targetPoint?.id===p.id?'HEDEF ✓':'HEDEF';goal.addEventListener('click',()=>{targetPoint=targetPoint?.id===p.id?null:p;updateGuidance();renderPoints();draw();});
 const del=document.createElement('button');del.className='secondary';del.textContent='SİL';del.setAttribute('aria-label',p.name+' noktasını sil');del.addEventListener('click',()=>{if(confirm('Bu nokta silinsin mi?')){points=points.filter(x=>x.id!==p.id);if(targetPoint?.id===p.id)targetPoint=null;save();updateGuidance();renderPoints();draw();}});
 actions.append(go,goal,del);row.append(n,actions);list.append(row);}
 if(!points.length){const p=document.createElement('p');p.className='notice';p.textContent='Henüz kaydedilmiş nokta yok.';list.append(p);}}
function download(obj,name){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/geo+json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
$('pointForm').addEventListener('submit',ev=>{ev.preventDefault();const p={id:Date.now()+Math.random(),name:$('pointName').value.trim(),lat:Number($('pointLat').value),lon:Number($('pointLon').value)};
 if(!validatePoint(p)||points.length>=500){alert('Geçerli koordinat girin (enlem ±85, boylam ±180) ve 500 nokta sınırını aşmayın.');return;}
 points.push(p);save();renderPoints();jump(p.lat,p.lon);$('pointName').value='';});
$('zoomIn').addEventListener('click',()=>changeZoom(1));$('zoomOut').addEventListener('click',()=>changeZoom(-1));$('centerTurkey').addEventListener('click',()=>{zoom=clamp(selectedMap==='ege'?7:5,minMapZoom,maxMapZoom);jump(selectedMap==='ege'?38.5:39,selectedMap==='ege'?28.7:35)});
$('exportPoints').addEventListener('click',()=>download({type:'FeatureCollection',features:points.map(p=>({type:'Feature',properties:{name:p.name},geometry:{type:'Point',coordinates:[p.lon,p.lat]}}))},'KALE-koordinat-noktalari.geojson'));
$('importPoints').addEventListener('change',async ev=>{const file=ev.target.files?.[0];if(!file)return;try{if(file.size>400000)throw Error('Dosya 400 KB sınırını aşıyor');const d=JSON.parse(await file.text());if(d.type!=='FeatureCollection'||!Array.isArray(d.features)||d.features.length>500)throw Error('GeoJSON FeatureCollection gerekli (en çok 500 nokta)');
 const incoming=d.features.map((f,i)=>{if(f.type!=='Feature'||f.geometry?.type!=='Point'||!Array.isArray(f.geometry.coordinates)||f.geometry.coordinates.length<2)throw Error('Yalnız nokta geometrisi desteklenir');const [lon,lat]=f.geometry.coordinates;const name=String(f.properties?.name||`Nokta ${i+1}`).trim();return {id:Date.now()+i+Math.random(),name,lat,lon};});
 if(incoming.some(p=>!validatePoint(p)))throw Error('Geçersiz nokta / koordinat');if(confirm(`${incoming.length} nokta mevcut noktaların yerine yüklensin mi?`)){points=incoming;targetPoint=null;save();updateGuidance();renderPoints();draw();}
 }catch(e){alert('İçe aktarma başarısız: '+e.message)}finally{ev.target.value='';}});
canvas.addEventListener('pointerdown',ev=>{canvas.setPointerCapture(ev.pointerId);drag={x:ev.clientX,y:ev.clientY,initial:llToWorld(center.lat,center.lon,zoom),moved:false};});
canvas.addEventListener('pointermove',ev=>{if(!drag)return;const dx=ev.clientX-drag.x,dy=ev.clientY-drag.y;if(Math.hypot(dx,dy)>5)drag.moved=true;const ll=worldToLl(drag.initial.x-dx,drag.initial.y-dy,zoom);center.lat=clamp(ll.lat,-85,85);center.lon=((ll.lon+180)%360+360)%360-180;draw();});
canvas.addEventListener('pointerup',ev=>{if(drag&&!drag.moved){const p=getCoordAt(ev);$('pointLat').value=p.lat.toFixed(6);$('pointLon').value=p.lon.toFixed(6);}drag=null;});
canvas.addEventListener('pointercancel',()=>{drag=null;});canvas.addEventListener('wheel',ev=>{ev.preventDefault();changeZoom(ev.deltaY<0?1:-1)},{passive:false});
window.addEventListener('resize',draw);

// No location is fetched until an explicit user click. No watchPosition/background GPS.
function haversineAndBearing(a,b){const rad=Math.PI/180,p1=a.lat*rad,p2=b.lat*rad,dl=(b.lon-a.lon)*rad;
 const h=Math.sin((p2-p1)/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;
 const km=6371*2*Math.atan2(Math.sqrt(h),Math.sqrt(Math.max(0,1-h)));
 const y=Math.sin(dl)*Math.cos(p2),x=Math.cos(p1)*Math.sin(p2)-Math.sin(p1)*Math.cos(p2)*Math.cos(dl);
 return {km,bearing:(Math.atan2(y,x)/rad+360)%360};}
function updateGuidance(){if(!gps){$('targetStatus').textContent=targetPoint?'Hedef seçildi; mesafe için GPS konumu al.':'Hedef seçilmedi. Kaydedilen noktadan HEDEF seç.';return;}
 if(!targetPoint){$('targetStatus').textContent='GPS hazır. Kayıtlı noktadan HEDEF seçerek kuş uçuşu mesafe hesapla.';return;}
 const d=haversineAndBearing(gps,targetPoint),cardinal=['K','KD','D','GD','G','GB','B','KB'][Math.round(d.bearing/45)%8];
 $('targetStatus').textContent=`HEDEF: ${targetPoint.name} · Kuş uçuşu ${d.km.toFixed(2)} km · ${Math.round(d.bearing)}° (${cardinal}). Güvenli yol/rota değil!`;}
function setGps(lat,lon,accuracy,provider){if(!Number.isFinite(lat)||!Number.isFinite(lon)||!Number.isFinite(accuracy)||Math.abs(lat)>85||Math.abs(lon)>180||accuracy<0||accuracy>100000)throw Error('Geçersiz GPS ölçümü.');
 gps={lat,lon,accuracy};$('gpsStatus').textContent=`${provider}: ${lat.toFixed(6)}, ${lon.toFixed(6)} · doğruluk ±${Math.round(accuracy)} m (tahmin)`;
 $('gpsToPoint').disabled=false;zoom=clamp(Math.max(zoom,raster?12:7),minMapZoom,maxMapZoom);jump(lat,lon);updateGuidance();}
$('gpsBrowser').addEventListener('click',()=>{const b=$('gpsBrowser');if(!navigator.geolocation){$('gpsStatus').textContent='Tarayıcı konumu desteklemiyor. Termux GPS deneyebilirsin.';return;}
 b.disabled=true;$('gpsStatus').textContent='Tek GPS ölçümü isteniyor…';navigator.geolocation.getCurrentPosition(pos=>{
  try{setGps(pos.coords.latitude,pos.coords.longitude,pos.coords.accuracy||0,'Tarayıcı GPS');}catch(e){$('gpsStatus').textContent=e.message;}finally{b.disabled=false;}
 },err=>{b.disabled=false;$('gpsStatus').textContent='Konum alınamadı ('+err.code+'). Android konum izni, GPS ve açık alanı kontrol et. Alternatif: Termux GPS.';},{enableHighAccuracy:true,maximumAge:0,timeout:16000});});
$('gpsTermux').addEventListener('click',async()=>{const b=$('gpsTermux');b.disabled=true;$('gpsStatus').textContent='Termux:API ile tek GPS ölçümü isteniyor…';
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),21000);
 try{const res=await fetch('/api/gps/once',{signal:ctrl.signal,cache:'no-store'}),data=await res.json();if(!res.ok)throw Error(data.error||'GPS okunamadı.');
  setGps(Number(data.latitude),Number(data.longitude),Number(data.accuracy),'Termux GPS');
 }catch(e){$('gpsStatus').textContent='Termux GPS başarısız: '+e.message;}finally{clearTimeout(timer);b.disabled=false;}});
$('gpsToPoint').addEventListener('click',()=>{if(!gps)return;$('pointLat').value=gps.lat.toFixed(6);$('pointLon').value=gps.lon.toFixed(6);$('pointName').focus();});

load();renderPoints();draw();
fetch('/assets/base-map.json').then(r=>r.json()).then(m=>{if(Array.isArray(m.areas)){baseMap=m;draw();}}).catch(()=>{});
function applyMap(info){vector=selectedMap==='sokak'&&!!info.installed;raster=selectedMap!=='sokak'&&!!info.installed;const box=$('mapStatus');if(vector){minMapZoom=clamp(Number(info.minzoom)||3,2,17);maxMapZoom=clamp(Number(info.maxzoom)||14,minMapZoom,17);zoom=clamp(zoom,minMapZoom,maxMapZoom);box.textContent=`SOKAK HARİTASI AKTİF: ${info.name} · ${(info.size_bytes/1048576).toFixed(0)} MiB · Yakından bakmak için zoom 12–14 · © OpenStreetMap katkıcıları.`;}else if(raster){minMapZoom=clamp(Number(info.minzoom)||2,2,16);maxMapZoom=clamp(Number(info.maxzoom)||16,minMapZoom,16);zoom=clamp(zoom,minMapZoom,maxMapZoom);box.textContent=`SOKAKLAR HENÜZ YOK: Bu yalnızca özet coğrafya paketidir (${info.name}). Türkiye OSM sokaklarını internet varken kur: cd ~/KALE && python3 tools/turkiye_full.py map · Sonra: python3 tools/check_streets.py`;}
 else box.textContent='SOKAK VERİSİ EKSİK: Terminalde cd ~/KALE && python3 tools/turkiye_full.py map komutunu internet varken çalıştır. Sonrasında python3 tools/check_streets.py ile doğrula.';draw();}
function loadMap(id){selectedMap=id;tileCache.clear();vectorCache.clear();streetTilesLoaded=0;streetTilesFailed=0;streetDecodeFailed=false;const endpoint=id==='sokak'?'/api/street/status':'/api/maps/status?map='+encodeURIComponent(id);
 fetch(endpoint,{cache:'no-store'}).then(r=>r.json()).then(applyMap).catch(()=>{$('mapStatus').textContent='Harita sunucusuna ulaşılamıyor.';});}
Promise.all([fetch('/api/maps/list',{cache:'no-store'}).then(r=>r.json()),fetch('/api/street/status',{cache:'no-store'}).then(r=>r.json())]).then(([data,street])=>{const select=$('mapChoice');select.replaceChildren();
 if(street.installed){const option=document.createElement('option');option.value='sokak';option.textContent='TÜRKİYE SOKAKLAR (OSM)';select.append(option);}
 for(const item of data.maps){if(!item.installed)continue;const option=document.createElement('option');option.value=item.id;option.textContent=item.name;select.append(option);}
 if(!select.options.length){const opt=document.createElement('option');opt.textContent='Özet coğrafya';select.append(opt);}
 const preferred=street.installed?'sokak':'turkiye';if(street.installed){center={lat:38.42,lon:27.14};zoom=14;}select.value=preferred;loadMap(preferred);}).catch(()=>loadMap('turkiye'));
$('mapChoice').addEventListener('change',()=>{const id=$('mapChoice').value;zoom=id==='ege'?7:id==='sokak'?14:5;center=id==='ege'?{lat:38.5,lon:28.7}:id==='sokak'?{lat:38.42,lon:27.14}:{lat:39,lon:35};loadMap(id);});
if('serviceWorker' in navigator && window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
