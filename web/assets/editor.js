'use strict';
/* Safe, offline draft editor: NEVER sends data to the web server. */
(()=>{
 const $=id=>document.getElementById(id);
 const STORAGE='kale-editor-v12';
 let original=[],drafts={},selected=null;
 const fields=['title','category','body','tags','warning'];
 function status(msg){$('message').textContent=msg;}
 function showList(){const q=$('searchList').value.toLocaleLowerCase('tr');const list=$('entryList');list.replaceChildren();
  let count=0;for(const item of merged()){if(q&&!(`${item.title} ${item.category} ${item.tags||''}`.toLocaleLowerCase('tr').includes(q)))continue;
   const b=document.createElement('button');b.type='button';b.className='editor-item'+(String(item.id)===String(selected)?' active':'')+(drafts[item.id]?' dirty':'');
   b.textContent=item.title;const sm=document.createElement('small');sm.textContent='#'+item.id+' · '+item.category+(drafts[item.id]?' · TASLAK':'');b.append(sm);b.addEventListener('click',()=>select(item.id));list.append(b);count++;}
  $('itemCount').textContent='('+merged().length+')';if(!count){const p=document.createElement('p');p.textContent='Eşleşen kayıt yok.';list.append(p);}}
 function merged(){let byId=new Map(original.map(x=>[x.id,x]));Object.values(drafts).forEach(x=>byId.set(x.id,x));return [...byId.values()].sort((a,b)=>a.id-b.id);}
 function blank(id){return {id,title:'',category:'HAZIRLIK',body:'',tags:'',warning:'',diagram:'',review_status:'taslak—uzman onayı bekliyor',last_reviewed:null,sources:[],regions:[],priority:'normal',origin:'KALE v1.2 İçerik Atölyesi'};}
 function select(id){selected=Number(id);const obj=merged().find(x=>x.id===selected);if(!obj)return;
  fields.forEach(f=>$(f).value=obj[f]||'');$('regions').value=(obj.regions||[]).join(', ');$('sources').value=(obj.sources||[]).map(s=>typeof s==='string'?s:s.url).join('\n');
  $('recordId').textContent='ID: '+selected;$('formTitle').textContent=obj.title||'Yeni rehber';$('draftState').textContent=drafts[id]?'YEREL TASLAK':'KATALOG KAYDI';showList();status('Düzenleme bu cihazda saklanır. Yayınlamak için JSON dışa aktar.');}
 function parseSources(text){const rows=[];for(const line of text.split(/\r?\n/).filter(s=>s.trim())){
  const [raw,label]=line.split('|',2).map(s=>(s||'').trim());let url;
  try{url=new URL(raw);}catch{throw Error('Kaynak adresi geçersiz: '+raw);}
  if(url.protocol!=='https:'||url.username||url.password)throw Error('Kaynak yalnız HTTPS olmalı.');
  rows.push(url.toString());if(rows.length>20)throw Error('En fazla 20 kaynak.');}return rows;}
 function saveDrafts(){try{localStorage.setItem(STORAGE,JSON.stringify(drafts));}catch{throw Error('Cihaz depolama alanı dolu; JSON dışa aktar.');}}
 function save(e){e.preventDefault();if(selected===null)return;
  try{const prior=merged().find(x=>x.id===selected)||blank(selected);const x={...prior};fields.forEach(f=>x[f]=$(f).value.trim());
   x.sources=parseSources($('sources').value);x.regions=$('regions').value.split(',').map(s=>s.trim()).filter(Boolean).slice(0,20);
   if(!x.title||!x.category||!x.body)throw Error('Başlık, kategori ve açıklama boş olamaz.');
   x.review_status='taslak—uzman onayı bekliyor';x.last_reviewed=null;
   x.origin='KALE v1.2 İçerik Atölyesi';drafts[x.id]=x;saveDrafts();select(x.id);status('Taslak kaydedildi. Sunucuda henüz yayınlanmadı.');}
  catch(err){status('Kaydedilemedi: '+err.message);}}
 function download(name,object){const blob=new Blob([JSON.stringify(object,null,2)],{type:'application/json;charset=utf-8'});
  const href=URL.createObjectURL(blob),a=document.createElement('a');a.href=href;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),1000);}
 function validateFile(p){if(p.format!=='KALE-EDITOR-v1'||!Array.isArray(p.entries)||p.entries.length<original.length||p.entries.length>5000)throw Error('Beklenmeyen KALE JSON dosyası.');
  const ids=new Set();for(const e of p.entries){if(!Number.isSafeInteger(e.id)||e.id<1||ids.has(e.id))throw Error('Eksik/çift kayıt kimliği.');ids.add(e.id);
   if(!e.title||!e.body||!e.category||String(e.body).length>20000)throw Error('Eksik veya uzun rehber alanı.');
   if(!Array.isArray(e.sources)||!Array.isArray(e.regions)||e.sources.length>20)throw Error('Geçersiz kaynak veya bölge.');
   for(const src of e.sources){if(typeof src!=='string'||!src.startsWith('https://'))throw Error('HTTPS olmayan kaynak.');}}
  for(const x of original){if(!ids.has(x.id))throw Error('Mevcut rehber silinemez: '+x.id);}
  return p.entries;}
 async function start(){try{const r=await fetch('/api/catalog');if(!r.ok)throw Error('Katalog okunamadı.');const d=await r.json();original=d.entries||[];
   if(!original.length)throw Error('Katalog boş.');try{const stored=JSON.parse(localStorage.getItem(STORAGE)||'{}');if(stored&&typeof stored==='object'&&!Array.isArray(stored)){
    drafts=Object.fromEntries(Object.entries(stored).filter(([k,v])=>v&&Number(k)===v.id&&Number.isSafeInteger(v.id)));}}
   catch{drafts={};}select(original[0].id);}catch(err){status('Katalog açılamadı: '+err.message);}}
 $('editForm').addEventListener('submit',save);$('searchList').addEventListener('input',showList);
 $('newBtn').addEventListener('click',()=>{const id=Math.max(0,...merged().map(x=>x.id))+1;drafts[id]=blank(id);select(id);status('Yeni rehber oluşturuldu. Metni yazıp kaydet.');});
 $('undoBtn').addEventListener('click',()=>{if(selected===null)return;delete drafts[selected];saveDrafts();select(original.some(x=>x.id===selected)?selected:original[0].id);status('Seçili rehberin taslağı silindi.');});
 $('exportBtn').addEventListener('click',()=>{download('KALE-rehber-duzenleme.json',{format:'KALE-EDITOR-v1',editor_version:'1.2',entries:merged()});status('JSON indirildi. Terminalde kontrol edip uygula.');});
 $('importFile').addEventListener('change',async e=>{const f=e.target.files?.[0];if(!f)return;
   try{if(f.size>3_000_000)throw Error('Dosya çok büyük.');const entries=validateFile(JSON.parse(await f.text()));
    const compare=new Map(original.map(x=>[x.id,JSON.stringify(x)]));const diff={};for(const x of entries){if(compare.get(x.id)!==JSON.stringify(x)){diff[x.id]=x;}}drafts=diff;saveDrafts();select(entries[0].id);status(Object.keys(diff).length+' yerel taslak içe aktarıldı.');}
   catch(err){status('İçe aktarım reddedildi: '+err.message);}finally{e.target.value='';}});
 $('resetAllBtn').addEventListener('click',()=>{if(!confirm('Tüm yerel taslaklar silinsin mi? Önce JSON yedeği al.'))return;drafts={};saveDrafts();select(original[0].id);status('Yerel taslaklar temizlendi.');});
 if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
 start();
})();
