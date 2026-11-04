'use strict';
/* Diagnostic checks for *actual* PWA caches, not navigator.onLine. */
(()=>{
 const CACHE='kale-v1.8.0';
 const REQUIRED=[
  ['Ana sayfa','/index.html'],['Yaşam rehberleri','/api/catalog'],
  ['İlaç arşivi','/assets/medicines-offline.json'],
  ['İlaç ekranı','/ilaclar.html'],['Stok envanteri','/envanter.html'],['Saha rehberleri','/saha.html'],
  ['Doğa güvenliği','/doga.html'],['Mantar risk kataloğu','/assets/dangerous-mushrooms.json'],['Harita özeti','/assets/base-map.json'],
  ['72 saat planı','/plan.html'],['Offline denetim','/offline.html'],['Cihazlar arası aktarım','/aktarim.html'],
  ['Saha görselleri','/assets/field-guides.json'],['İçerik Atölyesi','/atolye.html'],['Barınak ve su kartları','/assets/shelter-water.json'],['Gıda / Enerji / Kış','/assets/food-energy-winter.json'],['İlk yardım kartları','/assets/first-aid.json']
 ];
 const $=id=>document.getElementById(id);
 function line(name,ok,extra){const row=document.createElement('div');row.className='task-row';const mark=document.createElement('strong');mark.textContent=ok?'✓':'!';mark.style.color=ok?'#9bd7b6':'#edb69e';const txt=document.createElement('span');txt.append(document.createTextNode(name));if(extra){const sm=document.createElement('small');sm.textContent=extra;txt.append(sm);}row.append(mark,txt);return row;}
 async function check(){const list=$('checks');list.replaceChildren();let count=0;
  if(!('serviceWorker' in navigator)||!('caches' in window)||!window.isSecureContext){$('overall').textContent='PWA önbelleği kullanılabilir değil';$('summary').textContent='HTTPS veya localhost gerekiyor. KALE mini sunucusu yerel ağda çalışıyorsa ayrı şekilde kullanılabilir.';list.append(line('Tarayıcı / güvenli bağlam',false,'PWA önbelleği mevcut değil.'));return;}
  const c=await caches.open(CACHE);
  for(const [label,path] of REQUIRED){let ok=false,extra='';try{
   const resp=await c.match(path);ok=Boolean(resp&&resp.ok);
   if(ok&&path==='/api/catalog'){const data=await resp.clone().json();const n=data.entries?.length||0;ok=n>=146;extra=n+' rehber';}
   if(ok&&path==='/assets/medicines-offline.json'){const data=await resp.clone().json();const n=data.medicines?.length||0;ok=n>=707;extra=n+' ilaç kaydı';}
   if(ok&&path==='/assets/dangerous-mushrooms.json'){const data=await resp.clone().json();const n=data.mushrooms?.length||0;ok=n>=16;extra=n+' mantar uyarısı';}
   if(ok&&path==='/assets/shelter-water.json'){const data=await resp.clone().json();const n=data.cards?.length||0;ok=n===18;extra=n+' barınak ve su kartı';}
   if(ok&&path==='/assets/food-energy-winter.json'){const data=await resp.clone().json();const n=data.cards?.length||0;ok=n===24;extra=n+' yeni rehber';}
   if(ok&&path==='/assets/first-aid.json'){const data=await resp.clone().json();const n=data.cards?.length||0;ok=n===24;extra=n+' ilk yardım kartı';}
   if(ok&&path==='/assets/field-guides.json'){const data=await resp.clone().json();const n=data.guides?.length||0;ok=n>=28;extra=n+' görselli rehber';}
  }catch{ok=false;}
   if(ok)count++;list.append(line(label,ok,extra||(!ok?'Önbellekte yok / okunamıyor':'')));
  }
  $('overall').textContent=count===REQUIRED.length?'Temel dosyalar saklandı':'Hazırlık eksik';
  $('summary').textContent=`${count} / ${REQUIRED.length} kritik kaynak denetlendi. ${count===REQUIRED.length?'Şimdi bağlantıyı kesip gerçek test yap.':'İnternet/yerel sunucu bağlantısı varken hazırlama işlemini çalıştır.'}`;
 }
 async function prepare(){const button=$('prepare');button.disabled=true;$('actionMessage').textContent='Dosyalar hazırlanıyor…';
  try{
   if(!window.isSecureContext||!('serviceWorker' in navigator)||!('caches' in window))throw Error('HTTPS veya localhost gerekli.');
   const reg=await navigator.serviceWorker.register('/sw.js');await reg.update();
   await navigator.serviceWorker.ready;
   const cache=await caches.open(CACHE);
   // addAll is atomic: do not claim success if one file fails to download.
   await cache.addAll(REQUIRED.map(x=>x[1]));
   $('actionMessage').textContent='Kritik dosyalar kaydedildi. Şimdi denetim ve gerçek offline testi yap.';
  }catch(e){$('actionMessage').textContent='Hazırlanamadı: '+e.message+' · Bağlantı ve depolama alanını kontrol et.';}
  finally{button.disabled=false;await check();}
 }
 document.addEventListener('DOMContentLoaded',()=>{
  $('recheck').addEventListener('click',()=>check().catch(e=>{$('summary').textContent=e.message;}));
  $('prepare').addEventListener('click',prepare);
  check().catch(e=>{$('summary').textContent='Denetim hatası: '+e.message;});
 });
})();
