'use strict';
(()=>{
 const $=id=>document.getElementById(id);let lastRoute=null;
 function status(text){$('routeEngineStatus').textContent=text;}
 async function refresh(){try{const [r,m]=await Promise.all([fetch('/api/route/status',{cache:'no-store'}),fetch('/api/street/status',{cache:'no-store'})]);const d=await r.json(),map=await m.json();
 status(`${d.ready?'ROTA HAZIR':'ROTA EKSİK'} · BRouter ${d.engine_online?'çalışıyor':'kapalı'} · Veri ${d.segments_found}/${d.segments_required} bölge · Sokak haritası: ${map.installed?'kurulu':'yüklü değil'}.`);}
 catch(e){status('Sunucuya bağlanılamadı.');}}
 async function getRoute(){const btn=$('routeFind');btn.disabled=true;$('routeResult').textContent='Yerel BRouter yol ağı hesaplıyor…';
  try{const q=new URLSearchParams();for(const [key,id] of [['start_lat','routeStartLat'],['start_lon','routeStartLon'],['end_lat','routeEndLat'],['end_lon','routeEndLon']])q.set(key,$(id).value);
   q.set('mode',$('routeMode').value);const response=await fetch('/api/route?'+q,{cache:'no-store'});const d=await response.json();if(!response.ok)throw Error(d.error||'Rota bulunamadı');
   const route=d.features?.[0],coords=route?.geometry?.coordinates;if(!Array.isArray(coords)||coords.length<2)throw Error('Rota geometrisi yok');
   lastRoute=d;window.KALEshowRoute(coords);$('routeExport').disabled=false;
   const len=route.properties?.track_length_m;const mins=route.properties?.total_time_s;
   $('routeResult').textContent=`GERÇEK YOL ROTASI: ${len===null?'Mesafe yok':(len/1000).toFixed(1)+' km'} · Tahmini süre ${mins===null?'belirtilmemiş':Math.round(mins/60)+' dk'}. Bu rota canlı kapanma/tehlike verisi içermez.`;
  }catch(e){lastRoute=null;$('routeExport').disabled=true;window.KALEshowRoute(null);$('routeResult').textContent='Rota hesaplanamadı: '+e.message;}
  finally{btn.disabled=false;}}
 $('routeFind').addEventListener('click',getRoute);
 $('routeUseGps').addEventListener('click',()=>{const g=window.KALEgetGps?.();if(!g){$('routeResult').textContent='Önce "Konumumu Bul" düğmesiyle GPS al.';return;} $('routeStartLat').value=g.lat.toFixed(6);$('routeStartLon').value=g.lon.toFixed(6);$('routeResult').textContent='GPS başlangıç olarak alındı.';});
 $('routeExport').addEventListener('click',()=>{if(!lastRoute)return;const file=new Blob([JSON.stringify(lastRoute,null,2)],{type:'application/geo+json'});
  const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download='KALE-yol-rotasi.geojson';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 refresh();
})();
