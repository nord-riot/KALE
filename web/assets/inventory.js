'use strict';
/* Standalone offline inventory: NO network traffic and NO server writes. */
(function () {
 const K=window.KaleStock;
 const $=id=>document.getElementById(id);
 const STORE='kale-inventory-v16';
 const MAX_LOG=100;
 const fmt=n=>Number(n).toLocaleString('tr-TR',{maximumFractionDigits:2});
 const node=(type,className,text)=>{const el=document.createElement(type);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el;};
 const starter=()=>({format:'KALE-STOK-v1',people:3,perPersonDay:3,items:[],log:[]});
 let state=starter(),editing=null,storageHealthy=true;
 function info(target,msg){$(target).textContent=msg;}
 function save() {
  try{localStorage.setItem(STORE,JSON.stringify(state));info('backupMessage','Kayıt bu tarayıcıya kaydedildi. Düzenli JSON yedeği al.');return true;}
  catch(e){info('backupMessage','KAYIT HATASI: Tarayıcı veri saklamıyor veya dolu. Hemen JSON yedek indir.');return false;}
 }
 function audit(text){state.log.unshift({at:new Date().toISOString(),message:text.slice(0,180)});state.log=state.log.slice(0,MAX_LOG);}
 function labelStatus(item,mark) {
  const labels=[];
  if(mark.empty)labels.push(['past','Stok tükendi']);
  else if(mark.low)labels.push(['low','Minimum altı']);
  if(mark.date==='past') labels.push(['past',item.dateType==='TETT'?'TETT geçti · kalite kontrolü':'Tarih geçti · kontrol']);
  else if(mark.date==='soon')labels.push(['soon',`Tarih ${mark.days} gün içinde`]);
  else if(mark.date==='no_date')labels.push(['unknown','Tarih bilinmiyor']);
  else labels.push(['ok','Tarih ileride']);
  return labels;
 }
 function categories(){for(const [key,label] of Object.entries(K.CATEGORIES)){
  const o=node('option','',label);o.value=key;$('category').append(o);
  const f=node('option','',label);f.value=key;$('categoryFilter').append(f);
 }
 for(const [key,label] of Object.entries(K.UNITS)){
  const o=node('option','',label);o.value=key;$('unit').append(o);
 }}
 function resetForm() {
  editing=null;$('itemForm').reset();$('itemId').value='';$('quantity').value='1';$('minQuantity').value='0';
  $('category').value='gida';$('unit').value='adet';$('dateType').value='SKT';$('potable').checked=false;
  $('formHeading').textContent='Yeni stok kaydı';info('formMessage','Yeni kayıt eklenebilir.');toggleWater();
 }
 function toggleWater(){
  $('waterFlag').hidden=$('category').value!=='su';
  if($('waterFlag').hidden)$('potable').checked=false;
 }
 function edit(item){editing=item.id;const map={name:'name',category:'category',unit:'unit',quantity:'quantity',minQuantity:'minQuantity',location:'location',batch:'batch',expiry:'expiry',dateType:'dateType',notes:'notes'};
  for(const [key,field] of Object.entries(map))$(field).value=item[key];$('potable').checked=item.potable;
  $('itemId').value=item.id;$('formHeading').textContent='Stok kaydını düzenle';toggleWater();info('formMessage',item.name+' düzenleniyor.');
  $('itemForm').scrollIntoView({behavior:'smooth',block:'center'});
 }
 function formValue(){return K.makeItem({
   name:$('name').value,category:$('category').value,quantity:Number($('quantity').value),unit:$('unit').value,
   minQuantity:Number($('minQuantity').value),location:$('location').value,batch:$('batch').value,
   expiry:$('expiry').value,dateType:$('dateType').value,potable:$('potable').checked,notes:$('notes').value
 },editing || K.newId());}
 function addOrUpdate(ev){ev.preventDefault();try{
  const item=formValue();let where=state.items.findIndex(i=>i.id===item.id);
  if(where<0){if(state.items.length>=K.LIMIT)throw Error('500 kayıt sınırına ulaşıldı.');
   if(state.items.some(i=>i.id===item.id))throw Error('Kayıt ID çakıştı.');state.items.push(item);audit('Stok eklendi: '+item.name);}
  else{state.items[where]=item;audit('Stok düzenlendi: '+item.name);}
  save();resetForm();render();info('formMessage','Kayıt başarıyla güncellendi.');
 }catch(e){info('formMessage','HATA: '+e.message);}}
 function onRowAction(action,id){const item=state.items.find(i=>i.id===id);if(!item)return;
  if(action==='edit'){edit(item);return;}
  if(action==='delete'){if(!confirm(item.name+' kaydı ve stok miktarı silinsin mi?'))return;
   state.items=state.items.filter(i=>i.id!==id);audit('Stok kaydı silindi: '+item.name);save();if(editing===id)resetForm();render();return;}
  if(action==='adjust'){
   const val=prompt(item.name+' — miktar değişikliği gir (örn: -2, 3). Birim: '+item.unit,'-1');if(val===null)return;
   const raw=val.trim().replace(',','.');if(!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(raw)){alert('Geçerli sayısal miktar gir.');return;}
   const delta=Number(raw),next=item.quantity+delta;
   if(!Number.isFinite(delta)||delta===0||next<0||next>1e9){alert('Yeni stok 0–1 milyar aralığında olmalı ve değişim sıfır olmamalı.');return;}
   item.quantity=Math.round(next*1e6)/1e6;
   audit(`Miktar ${delta>0?'+':''}${fmt(delta)} ${item.unit}: ${item.name}`);save();render();
  }
 }
 function renderTable(){const q=$('search').value.trim().toLocaleLowerCase('tr-TR'),cat=$('categoryFilter').value,statusFilter=$('stateFilter').value,sort=$('sortBy').value;
  let result=state.items.filter(item=>{
   if(cat&&item.category!==cat)return false;
   if(q&&!`${item.name} ${item.location} ${item.batch} ${item.notes}`.toLocaleLowerCase('tr-TR').includes(q))return false;
   if(statusFilter){const mark=K.status(item);if(statusFilter==='low'&&!mark.low)return false;
    if(['past','soon','no_date'].includes(statusFilter)&&mark.date!==statusFilter)return false;}
   return true;
  });
  const cmp=(a,b)=>a.name.localeCompare(b.name,'tr-TR');
  result.sort((a,b)=>sort==='expiry'?(a.expiry||'9999').localeCompare(b.expiry||'9999')||cmp(a,b):sort==='category'?a.category.localeCompare(b.category)||cmp(a,b):cmp(a,b));
  const body=$('inventoryRows');body.replaceChildren();
  for(const item of result){const mark=K.status(item),tr=node('tr',mark.date==='past'?'past':mark.low?'low':'');
   const a=node('td');a.append(node('strong','',item.name),node('small','',K.CATEGORIES[item.category]+' · '+(item.location||'Konum belirtilmedi')));
   if(item.batch)a.append(node('small','','Parti: '+item.batch));
   const b=node('td');b.append(node('span','amt',fmt(item.quantity)+' '+K.UNITS[item.unit]),node('small','','Minimum: '+fmt(item.minQuantity)+' '+item.unit));
   const c=node('td');c.append(node('span','date',item.expiry?item.expiry+' · '+item.dateType:'Tarih belirtilmedi'));
   for(const [klass,label] of labelStatus(item,mark))c.append(node('span','inv-badge '+klass,label));
   if(item.category==='su'&&item.potable)c.append(node('small','','İçme suyu olarak işaretli · doğrulama kullanıcıya ait'));
   const d=node('td'),actions=node('div','item-action');
   for(const [act,label] of [['adjust','± Miktar'],['edit','Düzenle'],['delete','Sil']]){
    const btn=node('button','',label);btn.type='button';btn.addEventListener('click',()=>onRowAction(act,item.id));actions.append(btn);}
   d.append(actions);tr.append(a,b,c,d);body.append(tr);
  }
  if(!result.length){const tr=node('tr'),td=node('td','inv-empty',state.items.length?'Bu filtre için stok kaydı bulunamadı.':'Envanter boş. İlk kaydını sağdaki formdan ekle.');td.colSpan=4;tr.append(td);body.append(tr);}
  info('listInfo',`${result.length} kayıt gösteriliyor / toplam ${state.items.length}. ${state.items.length>=K.LIMIT?'500 kayıt sınırına ulaşıldı.':''}`);
 }
 function renderHistory(){const box=$('history');box.replaceChildren();for(const entry of state.log){const row=node('div','line'),date=node('small','',new Date(entry.at).toLocaleString('tr-TR'));
  row.append(node('span','',entry.message),date);box.append(row);}
  if(!state.log.length)box.append(node('p','notice','Henüz stok hareketi yok.'));
 }
 function render(){const m=K.metrics(state.items,state.people,state.perPersonDay);
  for(const key of ['total','low','past','soon'])$(key).textContent=m[key];
  info('waterResult',`${fmt(m.waterLiters)} L işaretli içme suyu · ${fmt(state.people*state.perPersonDay)} L/gün örnek ihtiyaç · yaklaşık ${fmt(m.waterDays)} gün`);
  renderTable();renderHistory();
 }
 function updateWater(){const people=Number($('people').value),perDay=Number($('perPersonDay').value);
  if(!Number.isInteger(people)||people<1||people>30||!Number.isFinite(perDay)||perDay<0.5||perDay>30){alert('Kişi 1–30 ve günlük kişi başı su hedefi 0,5–30 L arasında olmalı.');$('people').value=state.people;$('perPersonDay').value=state.perPersonDay;return;}
  state.people=people;state.perPersonDay=perDay;save();render();
 }
 function download(filename,text,type){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
 function exportJSON(){download('KALE-stok-envanteri.json',JSON.stringify({...state,exportedAt:new Date().toISOString()},null,2),'application/json;charset=utf-8');info('backupMessage','JSON yedeği indirildi. Başka bir cihazda güvenli sakla.');}
 function exportCSV(){download('KALE-stok-listesi.csv',K.toCSV(state.items),'text/csv;charset=utf-8');info('backupMessage','Excel uyumlu CSV indirildi. JSON yedeğini de sakla.');}
 async function importJSON(e){const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>350000)throw Error('Yedek dosyası 350 KB sınırından büyük.');const parsed=JSON.parse(await file.text());const valid=K.validateBackup(parsed);
   const log=Array.isArray(parsed.log)&&parsed.log.length<=100&&parsed.log.every(x=>typeof x.message==='string'&&x.message.length<=180&&typeof x.at==='string'&&/^\d{4}-\d\d-\d\dT/.test(x.at))?parsed.log:[];
   if(!confirm(`${valid.items.length} stok kaydı mevcut envanterin yerine yüklensin mi? Önce mevcut kayıtların JSON yedeğini al.`))return;
   const backup=state;
   state={...valid,log};
   if(!save()){state=backup;return;}
   storageHealthy=true;$('itemForm').querySelector('button[type="submit"]').disabled=false;
   $('people').value=state.people;$('perPersonDay').value=state.perPersonDay;
   resetForm();render();info('backupMessage','Yedek yüklendi: '+state.items.length+' stok kaydı.');
  }catch(err){info('backupMessage','İÇE AKTARIM REDDEDİLDİ: '+err.message);}finally{e.target.value='';}
 }
 function startup(){try{const raw=localStorage.getItem(STORE);if(raw){const parsed=JSON.parse(raw);const valid=K.validateBackup(parsed);
   state={...valid,log:Array.isArray(parsed.log)?parsed.log.slice(0,MAX_LOG).filter(x=>x&&typeof x.message==='string'&&typeof x.at==='string'):[]};}
  }catch(e){info('backupMessage','Mevcut envanter okunamadı; eski veri korunuyor. Önce mevcut tarayıcı verilerini yedekle, üzerine yazma.');return false;}
  return true;
 }
 document.addEventListener('DOMContentLoaded',()=>{
  categories();resetForm();const ok=startup();
  $('people').value=state.people;$('perPersonDay').value=state.perPersonDay;
  $('category').addEventListener('change',toggleWater);
  $('itemForm').addEventListener('submit',e=>{if(!storageHealthy){e.preventDefault();info('formMessage','Veri okuma hatası: mevcut envanter bozulmasın diye kayıt kapalı.');return;}addOrUpdate(e);});
  $('cancelEdit').addEventListener('click',resetForm);
  $('newItem').addEventListener('click',()=>{resetForm();$('name').focus();});
  for(const id of ['search','categoryFilter','stateFilter','sortBy'])$(id).addEventListener(id==='search'?'input':'change',renderTable);
  $('people').addEventListener('change',updateWater);$('perPersonDay').addEventListener('change',updateWater);
  $('exportJSON').addEventListener('click',exportJSON);$('exportCSV').addEventListener('click',exportCSV);
  $('importJSON').addEventListener('change',importJSON);
  $('printList').addEventListener('click',()=>window.print());
  window.addEventListener('storage',e=>{if(e.key===STORE&&e.newValue){info('backupMessage','Başka sekmede stok değişti. Burayı yenilemeden düzenleme yapma.');}});
  if(!ok){storageHealthy=false;$('itemForm').querySelector('button[type="submit"]').disabled=true;}
  render();
 });
})();
