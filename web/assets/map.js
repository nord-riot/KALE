'use strict';
/* No external map, geolocation, analytics or service dependencies. */
const $=id=>document.getElementById(id),canvas=$('mapCanvas'),ctx=canvas.getContext('2d');
const KEY='kale_v1_private_points';
let center={lat:39,lon:35},zoom=5,raster=false,drag=null,tileCache=new Map(),points=[],baseMap=null;
const tileSize=256,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function llToWorld(lat,lon,z){const p=clamp(lat,-85,85)*Math.PI/180,scale=tileSize*2**z;return {x:(lon+180)/360*scale,y:(1-Math.log(Math.tan(p)+1/Math.cos(p))/Math.PI)/2*scale};}
function worldToLl(x,y,z){const scale=tileSize*2**z;return {lon:(x/scale)*360-180,lat:Math.atan(Math.sinh(Math.PI*(1-2*y/scale)))*180/Math.PI};}
function viewport(){const dpr=window.devicePixelRatio||1;const rect=canvas.getBoundingClientRect();const width=Math.max(200,Math.round(rect.width)),height=Math.max(200,Math.round(rect.height));
 if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);}
 ctx.setTransform(dpr,0,0,dpr,0,0);return {width,height};}
function imgTile(z,x,y){const n=2**z;if(y<0||y>=n)return null;const wrapped=((x%n)+n)%n,key=`${z}/${wrapped}/${y}`;
 if(tileCache.has(key))return tileCache.get(key);
 if(tileCache.size>380){tileCache.clear();}
 const img=new Image();const item={img,loaded:false};tileCache.set(key,item);img.onload=()=>{item.loaded=true;draw();};img.onerror=()=>{item.failed=true;};img.src=`/api/tiles/${z}/${wrapped}/${y}`;return item;}
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
 drawBasemap(c,w,h);
 const xStart=Math.floor((c.x-w/2)/256),xEnd=Math.floor((c.x+w/2)/256),yStart=Math.floor((c.y-h/2)/256),yEnd=Math.floor((c.y+h/2)/256);
 for(let x=xStart;x<=xEnd;x++)for(let y=yStart;y<=yEnd;y++){const px=Math.round(x*256-c.x+w/2),py=Math.round(y*256-c.y+h/2);if(y<0||y>=2**zoom)continue;
  if(raster){const t=imgTile(zoom,x,y);if(t&&t.loaded){ctx.drawImage(t.img,px,py,256,256);continue;}}
  ctx.strokeStyle='#36565b77';ctx.strokeRect(px,py,256,256);
 }
 if(!raster){ctx.fillStyle='#061a22bd';ctx.fillRect(10,h-49,252,37);ctx.textAlign='left';ctx.fillStyle='#f0d2a3';ctx.font='bold 12px Arial';ctx.fillText('DOĞAL EARTH: ÖZET COĞRAFYA',18,h-33);ctx.font='10px Arial';ctx.fillStyle='#b7cbcb';ctx.fillText('Detay/rota verisi içermez',18,h-19);}
 for(const p of points){const wp=llToWorld(p.lat,p.lon,zoom);let px=wp.x-c.x+w/2,py=wp.y-c.y+h/2;const span=tileSize*2**zoom;if(px<-(span/2))px+=span;if(px>w+span/2)px-=span;if(px<-30||px>w+30||py<-30||py>h+30)continue;
  ctx.beginPath();ctx.arc(px,py,8,0,Math.PI*2);ctx.fillStyle='#edb86d';ctx.fill();ctx.lineWidth=2;ctx.strokeStyle='#14242c';ctx.stroke();ctx.font='bold 12px Arial';ctx.fillStyle='#fff';ctx.shadowColor='#061318';ctx.shadowBlur=4;ctx.fillText(p.name.slice(0,25),px+13,py+4);ctx.shadowBlur=0;
 }
 $('mapInfo').textContent=`Merkez ${center.lat.toFixed(5)}, ${center.lon.toFixed(5)} · Yakınlık ${zoom}`;
}
function jump(lat,lon){center={lat:clamp(lat,-85,85),lon:((lon+180)%360+360)%360-180};draw();}
function getCoordAt(ev){const r=canvas.getBoundingClientRect(),w=r.width,h=r.height,c=llToWorld(center.lat,center.lon,zoom);return worldToLl(c.x+(ev.clientX-r.left)-w/2,c.y+(ev.clientY-r.top)-h/2,zoom);}
function changeZoom(delta){zoom=clamp(zoom+delta,2,16);draw();}
function save(){try{localStorage.setItem(KEY,JSON.stringify(points));return true;}catch{alert('Noktalar kaydedilemedi: yerel depolama dolu veya kapalı.');return false;}}
function validatePoint(p){return p&&typeof p.name==='string'&&p.name.trim()&&p.name.length<=80&&typeof p.lat==='number'&&Number.isFinite(p.lat)&&Math.abs(p.lat)<=85&&typeof p.lon==='number'&&Number.isFinite(p.lon)&&Math.abs(p.lon)<=180;}
function load(){try{const d=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(d)&&d.length<=500)points=d.filter(validatePoint);}catch{points=[];}}
function renderPoints(){const list=$('pointList');list.replaceChildren();$('pointCount').textContent=`(${points.length}/500)`;
 for(const p of points){const row=document.createElement('div');row.className='point-item';const n=document.createElement('div'),title=document.createElement('strong'),coords=document.createElement('small');title.textContent=p.name;coords.textContent=`${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}`;n.append(title,coords);const actions=document.createElement('div');
 const go=document.createElement('button');go.className='secondary';go.textContent='GİT';go.addEventListener('click',()=>jump(p.lat,p.lon));
 const del=document.createElement('button');del.className='secondary';del.textContent='SİL';del.setAttribute('aria-label',p.name+' noktasını sil');del.addEventListener('click',()=>{if(confirm('Bu nokta silinsin mi?')){points=points.filter(x=>x.id!==p.id);save();renderPoints();draw();}});
 actions.append(go,del);row.append(n,actions);list.append(row);}
 if(!points.length){const p=document.createElement('p');p.className='notice';p.textContent='Henüz kaydedilmiş nokta yok.';list.append(p);}}
function download(obj,name){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/geo+json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
$('pointForm').addEventListener('submit',ev=>{ev.preventDefault();const p={id:Date.now()+Math.random(),name:$('pointName').value.trim(),lat:Number($('pointLat').value),lon:Number($('pointLon').value)};
 if(!validatePoint(p)||points.length>=500){alert('Geçerli koordinat girin (enlem ±85, boylam ±180) ve 500 nokta sınırını aşmayın.');return;}
 points.push(p);save();renderPoints();jump(p.lat,p.lon);$('pointName').value='';});
$('zoomIn').addEventListener('click',()=>changeZoom(1));$('zoomOut').addEventListener('click',()=>changeZoom(-1));$('centerTurkey').addEventListener('click',()=>{zoom=5;jump(39,35)});
$('exportPoints').addEventListener('click',()=>download({type:'FeatureCollection',features:points.map(p=>({type:'Feature',properties:{name:p.name},geometry:{type:'Point',coordinates:[p.lon,p.lat]}}))},'KALE-koordinat-noktalari.geojson'));
$('importPoints').addEventListener('change',async ev=>{const file=ev.target.files?.[0];if(!file)return;try{if(file.size>400000)throw Error('Dosya 400 KB sınırını aşıyor');const d=JSON.parse(await file.text());if(d.type!=='FeatureCollection'||!Array.isArray(d.features)||d.features.length>500)throw Error('GeoJSON FeatureCollection gerekli (en çok 500 nokta)');
 const incoming=d.features.map((f,i)=>{if(f.type!=='Feature'||f.geometry?.type!=='Point'||!Array.isArray(f.geometry.coordinates)||f.geometry.coordinates.length<2)throw Error('Yalnız nokta geometrisi desteklenir');const [lon,lat]=f.geometry.coordinates;const name=String(f.properties?.name||`Nokta ${i+1}`).trim();return {id:Date.now()+i+Math.random(),name,lat,lon};});
 if(incoming.some(p=>!validatePoint(p)))throw Error('Geçersiz nokta / koordinat');if(confirm(`${incoming.length} nokta mevcut noktaların yerine yüklensin mi?`)){points=incoming;save();renderPoints();draw();}
 }catch(e){alert('İçe aktarma başarısız: '+e.message)}finally{ev.target.value='';}});
canvas.addEventListener('pointerdown',ev=>{canvas.setPointerCapture(ev.pointerId);drag={x:ev.clientX,y:ev.clientY,initial:llToWorld(center.lat,center.lon,zoom),moved:false};});
canvas.addEventListener('pointermove',ev=>{if(!drag)return;const dx=ev.clientX-drag.x,dy=ev.clientY-drag.y;if(Math.hypot(dx,dy)>5)drag.moved=true;const ll=worldToLl(drag.initial.x-dx,drag.initial.y-dy,zoom);center.lat=clamp(ll.lat,-85,85);center.lon=((ll.lon+180)%360+360)%360-180;draw();});
canvas.addEventListener('pointerup',ev=>{if(drag&&!drag.moved){const p=getCoordAt(ev);$('pointLat').value=p.lat.toFixed(6);$('pointLon').value=p.lon.toFixed(6);}drag=null;});
canvas.addEventListener('pointercancel',()=>{drag=null;});canvas.addEventListener('wheel',ev=>{ev.preventDefault();changeZoom(ev.deltaY<0?1:-1)},{passive:false});
window.addEventListener('resize',draw);
load();renderPoints();draw();
fetch('/assets/base-map.json').then(r=>r.json()).then(m=>{if(Array.isArray(m.areas)){baseMap=m;draw();}}).catch(()=>{});
fetch('/api/maps/status',{cache:'no-store'}).then(r=>r.json()).then(info=>{raster=!!info.installed;const box=$('mapStatus');if(raster){box.textContent=`YEREL HARİTA AKTİF: ${info.name} · ${info.format.toUpperCase()} · ${Math.round(info.size_bytes/1048576)} MB. Haritalar sadece bu sunucudan okunur.`;}
 else box.textContent=`DETAY HARİTA PAKETİ YOK: Basitleştirilmiş Natural Earth coğrafyası ve koordinat işaretleri kullanılabilir. Daha ayrıntılı harita için data/maps/turkiye.mbtiles konumuna raster MBTiles ekleyebilirsin.`;draw();}).catch(()=>{$('mapStatus').textContent='Harita sunucusuna ulaşılamıyor. Koordinat defterindeki kayıtlar çalışır; harita karoları görüntülenemez.';});
if('serviceWorker' in navigator && window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
