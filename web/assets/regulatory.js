'use strict';
/* Separate regulatory products are unverified matches; never auto-merge them into KALE drugs. */
(()=>{
 const AGENCIES={FDA:'FDA / ABD',TITCK:'TİTCK / Türkiye',EMA:'EMA / Avrupa',
  MHRA:'MHRA / İngiltere',PMDA:'PMDA / Japonya',HEALTH_CANADA:'Health Canada / Kanada',
  TGA:'TGA / Avustralya',SFDA:'SFDA / Suudi Arabistan',WHO:'DSÖ / WHO'};
 const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
 const base='/api/regulatory/';
 const validUrl=u=>{try{const o=new URL(u);return o.protocol==='https:'?o.href:null;}catch{return null;}};
 const request=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json();};
 let opened=0,statsCache=null;
 async function getStats(){if(!statsCache)statsCache=await request(base+'status');return statsCache;}
 const names={indications_and_usage:'Kullanım endikasyonları (kaynak dili)',purpose:'Amaç',
  warnings:'Uyarılar',boxed_warning:'Kritik uyarı',contraindications:'Kullanılmaması gereken durumlar',
  adverse_reactions:'Yan etkiler',drug_interactions:'İlaç etkileşimleri',
  pregnancy:'Gebelik',nursing_mothers:'Emzirme',storage_and_handling:'Saklama',
  dosage_and_administration:'Etiket doz bilgisi — kişisel doz önerisi değildir'};
 async function showDetails(item,holder){
  const token=opened;
  const box=el('div','reg-detail','Kaynak metni açılıyor…');holder.replaceChildren(box);
  try{
   const record=await request(base+'detail/'+encodeURIComponent(item.regulator)+'/'+encodeURIComponent(item.source_id));
   if(token!==opened)return;
   box.replaceChildren(el('strong','',record.product_name),el('p','',record.market+' · '+record.source_type));
   const entries=Object.entries(record.sections||{});
   if(!entries.length)box.append(el('p','','Bu kaynak yalnız ürün bilgisi içerir; yan etki/endikasyon metni bulunmuyor.'));
   for(const [key,value] of entries.slice(0,20)){
    const details=el('details','reg-source-field');
    details.append(el('summary','',names[key]||key.replaceAll('_',' ')));
    const p=el('p','',String(value));p.style.whiteSpace='pre-line';details.append(p);box.append(details);
   }
  }catch(e){box.textContent='Yerel kaynak okunamadı: '+e.message;}
 }
 function itemNode(item){
  const card=el('article','reg-candidate');
  card.append(el('strong','',item.product_name),el('p','',AGENCIES[item.regulator]||item.regulator));
  if(item.active_substance)card.append(el('p','','Etken madde: '+item.active_substance));
  card.append(el('p','','Kurum statüsü: '+item.product_status));
  if(item.source_updated)card.append(el('small','','Tarih: '+item.source_updated));
  const actions=el('div','reg-actions');
  const source=validUrl(item.source_url);
  if(source){const a=el('a','reg-url','Resmî kaynak');a.href=source;a.target='_blank';a.rel='noopener noreferrer';actions.append(a);}
  const btn=el('button','reg-view','Yerel detayları aç');btn.type='button';
  const holder=el('div','');btn.addEventListener('click',()=>showDetails(item,holder));
  actions.append(btn);card.append(actions,holder);return card;
 }
 async function open(payload){
  opened++;
  const token=opened,panel=el('section','med-section reg-panel'),results=el('div','reg-results');
  const container=document.getElementById('medSections');if(!container)return;
  panel.append(el('h3','','9 DÜZENLEYİCİ KURUM — KAYNAKLI ÜRÜN BİLGİLERİ'));
  panel.append(el('p','reg-note','Bunlar yalnız ARAMA ADAYLARIDIR. Aynı isim veya etken madde, ürün eşdeğerliği, Türkiye ruhsatı veya tedavi güvenliği kanıtı değildir.'));
  results.append(el('p','reg-loading','Yerel kurum arşivi kontrol ediliyor…'));
  panel.append(results);container.append(panel);
  try{
   const s=await getStats();if(token!==opened)return;
   const sources=el('details','reg-portals');sources.append(el('summary','','9 kurumun resmî portalları ve veri durumu'));
   const list=el('ul','');
   for(const [key,value] of Object.entries(s.regulators||{})){
    const li=el('li','');
    const url=validUrl(value.portal);
    if(url){const a=el('a','',AGENCIES[key]||key);a.href=url;a.target='_blank';a.rel='noopener noreferrer';li.append(a);}
    else li.append(el('span','',key));
    li.append(document.createTextNode(' · yerelde '+value.count+' kayıt'));list.append(li);
   }
   sources.append(list);panel.append(sources);
   panel.append(el('p','reg-note',s.installed?'Telefonda ayrı arşiv: '+s.total+' düzenleyici kurum ürün kaydı.':'Düzenleyici kurum arşivi henüz kurulmadı.'));
   const query=String(payload.generic_name||payload.active_ingredients||payload.name||'').trim().slice(0,100);
   if(query.length<3||!s.total){results.replaceChildren(el('p','reg-note','Yerel arşivde sorgulanabilecek ürün kaydı yok.'));return;}
   const data=await request(base+'search?'+new URLSearchParams({q:query}));if(token!==opened)return;
   results.replaceChildren();
   if(!data.items?.length){results.append(el('p','reg-note','Eşleşme bulunamadı; bu sonuç ürün onayı veya reddi anlamına gelmez.'));return;}
   results.append(el('p','reg-note',data.items.length+' olası kaynak kaydı. Ürün kimliği birebir doğrulanmadı.'));
   for(const item of data.items)results.append(itemNode(item));
  }catch(e){if(token===opened)results.replaceChildren(el('p','reg-note','Kurum arşivi açılamadı: '+e.message));}
 }
 document.addEventListener('kale:medicine-opened',e=>open(e.detail||{}));
})();
