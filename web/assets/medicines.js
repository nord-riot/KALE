'use strict';
const $=id=>document.getElementById(id);
const LIMIT=35;let current=0,total=0,lastQuery='',sourced=false;
const DATA_FIELDS=[
 ['active_ingredients','Etken maddeler'],['indications','Ne için kullanılır?'],
 ['effects','Etki / farmakolojik bilgi'],['side_effects','Yan etkiler'],
 ['allergies','Alerji / kullanılmaması gereken durumlar'],
 ['contraindications','Kontrendikasyonlar ve hastalık uyarıları'],
 ['warnings','Ciddi uyarılar'],['interactions','İlaç etkileşimleri'],
 ['inactive_ingredients','Yardımcı maddeler (hepsi alerjen değildir)'],
 ['pregnancy','Gebelik / emzirme / özel gruplar'],['storage','Saklama koşulları']
];
// Every medicine opens a practical reading guide without inventing drug-specific
// dosing, interactions, contraindications or a clinical approval.
const FIELD_HELP={
 active_ingredients:'İlaç kutusunda etken madde adını, miktarını ve formunu karşılaştır. Benzer isimli iki ürün farklı derişimde olabilir. Etken maddeyi bilmek kişiye uygunluğu kanıtlamaz.',
 indications:'Bu bölüm ilacın hangi durumlar için kayıtlarda geçtiğini açıklar; sende o hastalık bulunduğu veya ilacın sana uygun olduğu anlamına gelmez. Tanı ve seçim için sağlık profesyoneli gerekir.',
 effects:'Buradaki açıklama ilacın genel etki mekanizmasına ilişkindir. Etkinin ne zaman başlayacağı, ne kadar süreceği ve kişideki karşılığı bu özetten kesin çıkarılamaz.',
 side_effects:'Olası yan etkiler herkes için aynı değildir. Ciddi veya hızla ilerleyen alerjik belirti, nefes güçlüğü, bilinç değişikliği gibi acil durumda 112 ile iletişime geç.',
 allergies:'Daha önce bir ilaca reaksiyon gelişmiş olması önemlidir. Etken ve yardımcı maddeleri karşılaştır; belirsiz alerjiyi kendi kendine deneme yaparak test etme.',
 contraindications:'Kontrendikasyon bir ilacın belirli durumda kullanılmaması gerektiğini anlatır. Eşlik eden hastalık, organ işlevi, yaş ve diğer ilaçlar için bu kayıt tek başına yeterli değildir.',
 warnings:'Kutudaki ve ruhsatlı ürün bilgisindeki özel uyarılar önceliklidir. Kırmızı bayrak görürsen kullanımı kendi başına başlatma veya değiştirme; uzman görüşü iste.',
 interactions:'İki reçeteli ilaç kadar reçetesiz ürün, takviye ve alkol de etkileşim açısından önemli olabilir. Güncel ilaç listesini eczacıya göster.',
 inactive_ingredients:'Yardımcı maddelerin hepsi alerjen değildir. Ancak bilinen duyarlılık varsa ürünün gerçek içerik listesini etiket/KÜB üzerinden doğrula.',
 pregnancy:'Gebelik, emzirme, çocukluk, ileri yaş ve böbrek/karaciğer hastalıkları özel değerlendirme gerektirebilir. Genel metinden kişisel uygunluk çıkarma.',
 storage:'Sıcaklık, nem ve ışık koşulları ürünün saklanmasını etkileyebilir. Kesin koşulu ürün etiketinden öğren; uygunluğu bilinmeyen ürünü kullanma.'
};
function appendReadingGuide(panels,data){
 const section=el('section','med-section med-howto');
 section.append(el('h3','','BU İLAÇ KAYDINI NASIL OKUYACAĞIM?'));
 const tips=[
  '1. İLAÇ KİMLİĞİ: Kutudaki ürün adı, etken madde ve ilaç formunu bu kayıtla karşılaştır. Aynı ad her ürünün aynı olduğunu kanıtlamaz.',
  '2. KİŞİSEL DURUM: Yaş, gebelik/emzirme, bilinen alerji, kronik hastalık ve kullanılan diğer ilaçlar uygunluğu değiştirebilir. Bunları hekim/eczacıya bildir.',
  '3. KAYNAĞI KONTROL ET: Bu kayıt için kaynak '+String(data.source||'belirtilmemiş')+'; güncellenme '+String(data.source_updated||'doğrulanmadı')+'. ABD ürün etiketi Türkiye ruhsatlı ürünü otomatik doğrulamaz.',
  '4. EKSİK BİLGİ: Boş yan etki, kontrendikasyon veya etkileşim alanı risk olmadığı anlamına gelmez. Eksik alanı tahminle doldurma.',
  '5. ACİL DURUM: Ciddi reaksiyon, nefes alamama veya bilinç değişikliği varsa Türkiye’de 112; zehirlenme şüphesinde 114 danışma hattından yönlendirme al.',
  '6. KARAR: KALE ilaç önermez, doz hesaplamaz, reçete vermez. Kullanma/değiştirme/bırakma kararını yalnız bu ekrana dayanarak verme.'
 ];
 const list=el('ol','med-reading-list');
 for(const tip of tips)list.append(el('li','',tip));
 section.append(list);
 panels.append(section);
}
const el=(tag,cls,txt)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x;};
const list=$('medList');
const fallback='Bu bölüm için doğrulanmış kaynak bilgisi henüz eklenmedi. Bu, ilacın güvenli olduğu anlamına gelmez.';
let offlinePromise;
const stripTr=s=>String(s||'').replaceAll('İ','I').replaceAll('ı','i').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
async function offlineCatalog(){
 if(!offlinePromise) offlinePromise=fetch('/assets/medicines-offline.json',{cache:'force-cache'}).then(r=>{if(!r.ok)throw Error('Offline arşiv bulunamadı');return r.json()});
 return offlinePromise;
}
async function offlineGet(url){
 const meds=(await offlineCatalog()).medicines;
 $('medOfflineState').textContent='ÇEVRİMDIŞI KATALOG · SON ÖNBELLEK';
 const u=new URL(url,location.origin);
 if(u.pathname==='/api/medicines/stats')return {total:meds.length,turkish_summaries:meds.length,official_label_records:0,name_only_records:0};
 if(u.pathname==='/api/medicines'){
  const terms=stripTr(u.searchParams.get('q')||'').trim().split(/\s+/).filter(Boolean);
  const filtered=meds.filter(m=>{
   const txt=stripTr([m.name,m.generic_name,m.brand_names,m.active_ingredients,m.category].join(' '));
   return terms.every(t=>txt.includes(t));
  });
  const off=Math.max(0,Number(u.searchParams.get('offset')||0));
  const lim=Math.min(100,Math.max(1,Number(u.searchParams.get('limit')||35)));
  return {total:filtered.length,items:filtered.slice(off,off+lim),offset:off,limit:lim};
 }
 if(u.pathname.startsWith('/api/medicines/')){
  const med=meds.find(m=>m.id===decodeURIComponent(u.pathname.split('/').pop()));
  if(!med)throw Error('İlaç arşivde bulunamadı');
  return {...med,doctor_review:{review_record:'ÇEVRİMDIŞI BİLİNMİYOR',verified_clinical_safety:false}};
 }
 throw Error('Bu veri çevrimdışı bulunamadı');
}
async function get(url){
 try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
 catch(e){return offlineGet(url)}
}
async function stats(){try{const d=await get('/api/medicines/stats');$('medStats').textContent=`${d.total} kayıt · ${d.turkish_summaries} Türkçe inceleme taslağı · ${d.official_label_records} FDA etiketi · ${d.name_only_records} isim dizini`;}catch{$('medStats').textContent='Yerel veritabanı bağlantısı yok.';}}
async function search(){const q=lastQuery,off=current*LIMIT;list.replaceChildren(el('div','med-loading','Kayıtlar aranıyor…'));
 try{const data=await get(`/api/medicines?${new URLSearchParams({q,offset:off,limit:LIMIT,sourced:sourced?'1':'0'})}`);total=data.total;list.replaceChildren();
   if(!data.items.length)list.append(el('p','med-empty','Eşleşen ilaç bulunamadı. Eşleşme olmaması güvenlik değerlendirmesi değildir.'));
   for(const med of data.items){const b=el('button','med-item');b.type='button';b.append(el('span','med-item-badge',med.source.startsWith('openFDA')?'FDA ETİKET':med.review_status.includes('TASLAK')?'TÜRKÇE TASLAK':med.review_status.includes('ÖZET')?'TÜRKÇE ÖZET':'İSİM DİZİNİ'),el('strong','',med.name),el('small','',med.generic_name||med.category),el('small','med-category',med.category));b.addEventListener('click',()=>detail(med.id));list.append(b)}
   $('medCounter').textContent=`${total} sonuç`;
   $('medPrev').disabled=current===0;$('medNext').disabled=(current+1)*LIMIT>=total;
   $('medPage').textContent=`${current+1} / ${Math.max(1,Math.ceil(total/LIMIT))}`;
 }catch(err){list.replaceChildren(el('p','med-empty','İlaç veritabanı açılamadı: '+err.message));}
}
async function detail(id){try{const data=await get('/api/medicines/'+encodeURIComponent(id));
 $('medTitle').textContent=data.name;
 $('medDetailBadge').textContent=data.review_status;
 $('medDetailSummary').textContent=[data.generic_name,data.category].filter(Boolean).join(' · ');
 const hasSource=data.source.startsWith('openFDA');const isSummary=data.review_status.includes('ÖZET');const isDraft=data.review_status.includes('TASLAK');
 $('medDetailAlert').textContent=hasSource?'ABD ürün etiketinden aktarılmış İngilizce metindir. Türkiye uygunluğu ve içerik tamlığı doğrulanmadı.':(isSummary||isDraft)?'DOKTOR/ECZACI ONAYI YOK — Bu Türkçe içerik editoryal taslaktır. Ürün, doz, hastalık ve alerjen uygunluğu doğrulanmadı; uygulama veya ilaç seçimi için tek kaynak olarak kullanılamaz.':'SADECE İSİM DİZİNİ — Kullanım, yan etki ve kontrendikasyonlar bu kayıt için yüklenmedi. Bilgi eksikliği güvenlik onayı değildir.';
 const review=data.doctor_review||{review_record:'YOK'};
 $('medReviewState').textContent=review.review_record==='İŞLENDİ'?`HEKİM İNCELEME KAYDI: ${review.decision} (${review.reviewed_on}). Bu kayıt, ilaç güvenliğinin bağımsız onayı değildir.`:'HEKİM İNCELEMESİ: Onaylı bir klinik değerlendirme bulunmuyor veya çevrimdışı doğrulanamıyor.';
 const panels=$('medSections');panels.replaceChildren();
 for(const [key,label] of DATA_FIELDS){const panel=el('section','med-section');panel.append(el('h3','',label));const content=el('p',data[key]?'':'med-missing',data[key]||fallback);panel.append(content);
  const explanation=el('p','med-field-explanation',FIELD_HELP[key]||'Ürün etiketini ve sağlık profesyoneli bilgisini doğrula.');
  panel.append(explanation);panels.append(panel)}
 appendReadingGuide(panels,data);
 const source=$('medSource');source.replaceChildren(el('strong','','Kaynak: '+data.source));source.append(el('p','','Dil: '+data.locale+' · Kaynak kontrol tarihi: '+(data.source_updated||'henüz doğrulanmadı')));if(data.source.toLocaleLowerCase('tr').includes('editoryal')) source.append(el('p','','Bağlantı ilaca özgü doğrulanmış KÜB/KT değil, genel referans merkezidir. Kayda özel kaynak hekim/eczacı kontrolünde eklenmelidir.'));
 if(data.source_url&&data.source_url.startsWith('https://')){const a=el('a','',hasSource?'Ürün etiketini aç (internet gerekir) ↗':'Kaynak / başvuru merkezini aç (internet gerekir) ↗');a.href=data.source_url;a.rel='noopener noreferrer';a.target='_blank';source.append(a)}
 $('medDialog').showModal();
 }catch(e){list.prepend(el('p','med-empty','Detay yüklenemedi: '+e.message))}}
$('medSearchForm').addEventListener('submit',event=>{event.preventDefault();lastQuery=$('medQuery').value.trim();current=0;search();});
let timer;$('medQuery').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{lastQuery=$('medQuery').value.trim();current=0;search()},240)});
$('medSourceFilter').addEventListener('change',event=>{sourced=event.target.checked;current=0;search()});
$('medPrev').addEventListener('click',()=>{if(current>0){current--;search()}});
$('medNext').addEventListener('click',()=>{if((current+1)*LIMIT<total){current++;search()}});
$('medClose').addEventListener('click',()=>$('medDialog').close());
$('medBottomClose').addEventListener('click',()=>$('medDialog').close());
$('medDialog').addEventListener('click',e=>{if(e.target===$('medDialog'))$('medDialog').close()});
stats();search();

if('serviceWorker' in navigator && window.isSecureContext){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));}
