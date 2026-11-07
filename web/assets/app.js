'use strict';
// Entire catalog is searched locally in-browser. No remote APIs, tracking or clinical input uploads.
const CATEGORIES = [
 ['TÜMÜ','◈','Tüm rehberler'],['ACİL','✳','Acil durum'],['BARINAK','⌂','Barınak'],
 ['SU','◉','Su ve arıtma'],['ATEŞ','♨','Ateş ve ısınma'],['GIDA','◕','Gıda ve doğa'],
 ['SAĞLIK','✚','Sağlık ve ilk yardım'],['İLAÇ','▣','İlaç rehberi'],
 ['BÖLGE','◎','Bölgesel rehber'],['HİJYEN','✧','Hijyen'],['İLETİŞİM','⌁','İletişim'],
 ['ENERJİ','⚡','Enerji'],['NAVİGASYON','◈','Yön bulma'],['ONARIM','⚒','Onarım'],
 ['TOPLULUK','☷','Topluluk'],['HAKKINDA','ⓘ','Hakkında']
];
const $ = id => document.getElementById(id);
let entries=[],filter='TÜMÜ',query='',region='',favoritesOnly=false,selected=null;
function normalize(s){return String(s||'').toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i');}
function favorites(){try{return JSON.parse(localStorage.getItem('kale_favs')||'[]')}catch{return []}}
function setFavorites(list){try{localStorage.setItem('kale_favs',JSON.stringify(list))}catch{};$('savedCount').textContent=String(list.length);}
function one(s){return document.createTextNode(String(s||''))}
function create(tag,cls,content){const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.textContent=String(content);return e}
function button(txt,cls,onClick){const b=create('button',cls,txt);b.type='button';b.addEventListener('click',onClick);return b}
function selectCategory(cat){filter=cat;favoritesOnly=false;render();scrollToSearch();}
function scrollToSearch(){if(window.scrollY>600)document.querySelector('.section-top').scrollIntoView({behavior:'smooth',block:'start'});}
function renderNav(){const nav=$('sideNav');nav.replaceChildren();for(const [id,icon,label] of CATEGORIES){const count=id==='TÜMÜ'?entries.length:entries.filter(e=>e.category===id).length;const b=button('',`nav-link${filter===id&&!favoritesOnly?' active':''}`,()=>selectCategory(id));const ico=create('span','nav-icon',icon),txt=create('span','',label),n=create('span','nav-count',count);b.append(ico,txt,n);nav.append(b);}}
function renderTabs(){const tabs=$('tabs');tabs.replaceChildren();for(const [id,,label] of CATEGORIES){if(id==='HAKKINDA')continue;const b=button(label,`tab${filter===id&&!favoritesOnly?' active':''}`,()=>selectCategory(id));tabs.append(b);}}
function matches(e){if(region && (e.regions||[]).length && !(e.regions||[]).includes(region))return false;if(favoritesOnly&&!favorites().includes(e.id))return false;if(!favoritesOnly&&filter!=='TÜMÜ'&&e.category!==filter)return false;if(!query)return true;const haystack=normalize([e.title,e.category,e.tags,e.body].join(' '));return normalize(query).split(/\s+/).filter(Boolean).every(word=>haystack.includes(word));}
function card(e){const b=button('','entry-card',()=>showDetail(e.id));const head=create('div','card-head');head.append(create('span','card-tag',e.category),create('span','card-num',`#${String(e.id).padStart(3,'0')}`));const h=create('h3','',e.title),p=create('p','',e.body.split('\n').join(' ').slice(0,260));const foot=create('div','card-bottom');foot.append(create('span','',favorites().includes(e.id)?'★ KAYDEDİLDİ':'REHBERİ AÇ'),create('span','read-arrow','↗'));b.append(head,h,p,foot);return b;}
function render(){renderNav();renderTabs();const filtered=entries.filter(matches);$('cards').replaceChildren();if(!filtered.length){$('cards').append(create('div','no-results','Eşleşen kayıt bulunamadı. Farklı kelimelerle tekrar ara.'));}else{const frag=document.createDocumentFragment();filtered.forEach(e=>frag.append(card(e)));$('cards').append(frag);}$('countInfo').textContent=`${entries.length} REHBER · ${new Set(entries.map(e=>e.category)).size} KATEGORİ`;$('resultsLabel').textContent=favoritesOnly?'KAYDEDİLEN REHBERLER':query?`${filtered.length} ARAMA SONUCU`:filter==='TÜMÜ'?'TÜM REHBERLER':`${filter} / REHBERLER`;$('crumb').textContent=favoritesOnly?'KAYDEDİLENLER':filter==='TÜMÜ'?'KOMUTA MERKEZİ':filter+' / REHBER';$('clearFilters').hidden=!(query||filter!=='TÜMÜ'||favoritesOnly||region);$('savedCount').textContent=String(favorites().length);}
// Render editorial text as readable sections. Uses textContent only (no HTML injection).
function renderGuideText(container,body){
 container.replaceChildren();
 const parts=String(body||'').split(/\n\n+/).filter(Boolean);
 for(const part of parts){
  const lines=part.split('\n');
  const first=lines[0].trim();
  const section=(/^[A-ZÇĞİÖŞÜ0-9 \/—:-]{5,90}$/.test(first)||/^KONUYU ANLA — /.test(first))&&lines.length>1;
  if(section){
   const block=create('section','guide-section');
   block.append(create('h3','guide-section-title',first));
   const paragraph=create('p','guide-section-content',lines.slice(1).join('\n'));
   block.append(paragraph);container.append(block);
  }else{
   container.append(create('p','guide-section-content',part));
  }
 }
}
function showDetail(id){const e=entries.find(x=>x.id===id);if(!e)return;selected=e;$('detailCategory').textContent=e.category+' / '+String(e.id).padStart(3,'0');$('detailTitle').textContent=e.title;$('detailStatus').textContent='⚠ '+(e.review_status||'EDİTORYAL TASLAK').toUpperCase()+' · '+((e.regions||[]).join(', ')||'TÜRKİYE GENELİ');renderGuideText($('detailText'),e.body);$('detailWarning').hidden=!e.warning;$('detailWarning').textContent=e.warning||'';const links=$('detailLinks');links.replaceChildren();if(e.sources?.length){for(const url of e.sources){if(!url.startsWith('https://'))continue;const a=create('a','',new URL(url).hostname+' · Bağlantı internet gerektirir');a.href=url;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}else{links.append(create('span','', 'Bu kayda özel doğrulanmış kaynak henüz eklenmedi.'));}setSaveDetailText();$('detailDialog').showModal();}
function setSaveDetailText(){if(selected)$('saveDetail').textContent=favorites().includes(selected.id)?'★ Kaydedildi':'☆ Kaydet';}
function closeDetail(){$('detailDialog').close();}
// Deliberately cautious: simple keyword links; it does NOT diagnose, triage reliably or choose medication.
const FLAGS=['nefes alam','nefes darl','bilinc','bayıl','bayildi','gögüs agr','gogus agr','göğüs ağr','siddetli kanama','şiddetli kanama','kanli diski','kanlı dışkı','nöbet','nobet','felç','felc','konusamiyor','konuşamıyor','dudak mor','bogul','boğul'];
const SYMPTOMS=[
 {terms:['ishal','sulu diski','dışkı','kusma','susuz','sivi kaybi'],ids:[10,23,11,33]},
 {terms:['su','kirli su','dere suyu','arıtma','kaynatma'],ids:[7,8,9,10]},
 {terms:['kanama','kesik','yara','yaralan'],ids:[25,22]},
 {terms:['ateş','ates','titreme','enfeksiyon'],ids:[27,22]},
 {terms:['alerji','kaşıntı','kasinti','kurdeşen','kurdesen'],ids:[24,22]},
 {terms:['soğuk','soguk','üşüme','usume','hipotermi'],ids:[26,12,5]},
 {terms:['yanık','yanik'],ids:[15,22]},
 {terms:['mantar','bitki','ot'],ids:[19,20,22]}
];
function evaluateSymptom(event){event.preventDefault();const raw=$('symptomInput').value.trim();const out=$('symptomResult');out.replaceChildren();if(!raw){out.textContent='Belirtileri yaz. Belirti değerlendirmesi tanı veya reçete değildir.';return;}const x=normalize(raw);const highRisk=FLAGS.some(t=>x.includes(normalize(t)));out.append(create('div',highRisk?'triage-urgent':'triage-note',highRisk?'ACİL UYARI: Yazdıkların ciddi bir belirti içerebilir. Türkiye’de 112’yi ara; gecikmeden sağlık yardımı al.':'Bu bir tanı değil. İlgili ilk yardım başlıkları aşağıda; kötüleşme veya şüphede sağlık yardımı al.'));
let ids=[];for(const group of SYMPTOMS){if(group.terms.some(t=>x.includes(normalize(t))))ids.push(...group.ids);}ids=[...new Set(ids)].filter(id=>entries.some(e=>e.id===id));if(!ids.length){out.append(create('div','', 'Eşleşen rehber yok. Uygulama her tehlikeli belirtiyi tanıyamaz; ciddi durumlarda 112.'));return;}const wrap=create('div','triage-links');ids.slice(0,6).forEach(id=>{const e=entries.find(e=>e.id===id);wrap.append(button(e.title+' ↗','',()=>showDetail(id)));});out.append(wrap);}
async function start(){
 $('homeBrand').addEventListener('click',()=>{query='';$('search').value='';selectCategory('TÜMÜ');window.scrollTo({top:0,behavior:'smooth'})});
 $('emergencyBtn').addEventListener('click',()=>showDetail(1));
 $('savedOpen').addEventListener('click',()=>{filter='TÜMÜ';favoritesOnly=true;render();scrollToSearch()});
 $('search').addEventListener('input',ev=>{query=ev.target.value.trim();render()});
 $('clearFilters').addEventListener('click',()=>{filter='TÜMÜ';query='';region='';$('regionFilter').value='';favoritesOnly=false;$('search').value='';render()});
 $('symptomForm').addEventListener('submit',evaluateSymptom);
 $('closeDialog').addEventListener('click',closeDetail);$('closeBottom').addEventListener('click',closeDetail);
 $('detailDialog').addEventListener('click',ev=>{if(ev.target===$('detailDialog'))closeDetail()});
 $('saveDetail').addEventListener('click',()=>{if(!selected)return;const old=favorites();setFavorites(old.includes(selected.id)?old.filter(x=>x!==selected.id):[...old,selected.id]);setSaveDetailText();render()});
 $('regionFilter').addEventListener('change',ev=>{region=ev.target.value;render()});
 $('printDetail').addEventListener('click',()=>{document.body.classList.add('printing-detail');window.print();});
 window.addEventListener('afterprint',()=>document.body.classList.remove('printing-detail'));
 $('exportBackup').addEventListener('click',exportBackup);
 $('restoreBackup').addEventListener('change',importBackup);
 document.addEventListener('keydown',ev=>{if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==='k'){ev.preventDefault();$('search').focus();}});
 try{const resp=await fetch('/api/catalog',{cache:'no-store'});if(!resp.ok)throw Error('HTTP '+resp.status);const payload=await resp.json();entries=Array.isArray(payload.entries)?payload.entries:[];if(!entries.length)throw Error('Boş katalog');$('contentState').textContent='';$('heroCount').textContent=entries.length+' REHBER KARTI';
 const areas=[...new Set(entries.flatMap(e=>e.regions||[]))].sort((a,b)=>a.localeCompare(b,'tr'));
 const sel=$('regionFilter');areas.forEach(a=>{const opt=document.createElement('option');opt.value=a;opt.textContent=a;sel.append(opt)});render();}catch(err){$('contentState').textContent='İçerik yüklenemedi: '+err.message+' · Sunucuyu ve content.json dosyasını kontrol edin.';}
}
start();

function exportBackup(){
 const data={app:'KALE',version:1,exported_at:new Date().toISOString(),favorites:favorites()};
 const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='kale-kaydedilenler.json';
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1500);
}
async function importBackup(ev){
 const file=ev.target.files?.[0];if(!file)return;
 if(file.size>100000){alert('Yedek 100 KB sınırını aşıyor.');ev.target.value='';return;}
 try{const parsed=JSON.parse(await file.text());
 if(parsed.app!=='KALE'||!Array.isArray(parsed.favorites))throw Error('Geçersiz KALE dosyası');
 const known=new Set(entries.map(x=>x.id));
 const valid=[...new Set(parsed.favorites.filter(x=>Number.isInteger(x)&&known.has(x)))];
 if(!confirm('Mevcut kaydedilenleri bu dosyadakilerle değiştirelim mi?'))return;
 setFavorites(valid);render();alert(valid.length+' kayıt geri yüklendi.');
 }catch(e){alert('Dosya okunamadı: '+e.message);}finally{ev.target.value='';}
}
if('serviceWorker' in navigator && window.isSecureContext){
 window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}
