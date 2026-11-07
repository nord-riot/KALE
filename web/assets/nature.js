'use strict';
/* Offline hazard-awareness index. No species classification from images, no edibility claims. */
(()=>{
 const $=id=>document.getElementById(id), card=document.getElementById('natureCards');
 let all=[];
 const clean=t=>String(t||'').toLocaleLowerCase('tr');
 const make=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
 function render(){const search=clean($('natureSearch').value).trim(),group=$('natureType').value,risk=clean($('natureRisk').value);card.replaceChildren();let count=0;
  for(const x of all){if(group&&x.group!==group)continue;
   if(search&&!clean([x.name,x.latin,x.warning,x.danger_type].join(' ')).includes(search))continue;
   if(risk&&!clean([x.warning,x.danger_type].join(' ')).includes(risk))continue;
   const item=make('article','nature-card'+(x.group==='mantar'?' mushroom':''));
   item.append(make('div','kicker',(x.group==='mantar'?'🍄 MANTAR':'🌿 BİTKİ')+' · TÜKETME'),make('h2','',x.name),make('em','',x.latin));
   item.append(make('p','alert-line',x.warning),make('p','',x.habitat||''),make('div','unverified','Bölgesel dağılım ve tür teşhisi uzman tarafından doğrulanmadı.'));
   const more=make('details','nature-more');const summary=make('summary','','AYRINTILI GÜVENLİK BİLGİSİNİ AÇ');
   more.append(summary);
   for(const s of x.details||[]){more.append(make('h3','guide-expansion-title',s.heading),make('p','guide-expansion-text',s.text));}
   item.append(more);
   const a=make('a','',x.source+' · Kaynak ↗');a.href=x.source_url;a.rel='noopener noreferrer';a.target='_blank';item.append(a);
   card.append(item);count++;
  }
  $('shownCount').textContent=String(count);
  if(!count)card.append(make('p','notice','Eşleşen kayıt yok. Bu sonuç bitki veya mantarın güvenli olduğu anlamına gelmez.'));
 }
 async function load(){try{
  const [p,m]=await Promise.all(['/assets/poisonous-plants.json','/assets/dangerous-mushrooms.json'].map(url=>fetch(url).then(r=>{if(!r.ok)throw Error('Kaynak yüklenemedi');return r.json();})));
  const plants=p.plants.map(x=>({...x,group:'bitki'})),mushrooms=m.mushrooms.map(x=>({...x,group:'mantar'}));
  if(plants.some(x=>x.consumable!==false)||mushrooms.some(x=>x.consumable!==false))throw Error('Güvenli olmayan katalog bilgisi');
  all=[...plants,...mushrooms];$('plantCount').textContent=plants.length;$('mushCount').textContent=mushrooms.length;render();
  }catch(e){card.replaceChildren(make('p','alert','Doğa arşivi yüklenemedi: '+e.message));}}
 ['natureSearch','natureType','natureRisk'].forEach(id=>$(id).addEventListener(id==='natureSearch'?'input':'change',render));load();
 if('serviceWorker'in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
})();
