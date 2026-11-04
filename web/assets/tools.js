'use strict';
/* KALE local-only calculators, checklist and inventory. No network calls. */
(()=>{
 const $=id=>document.getElementById(id);
 const key='kale_v02_private';
 const defaultData=()=>({inventory:[],checks:{}});
 const CHECKS=[
  'Güvenli içme suyu','Dayanıklı gıda ve açacak','El feneri ve yedek pil',
  'İlk yardım çantası','Kişisel ilaçlar ve reçeteler','Radyo / telsiz',
  'Powerbank ve şarj kablosu','Battaniye ve mevsimlik kıyafet',
  'Düdük ve temel el aletleri','Hijyen ve temizlik malzemeleri',
  'Önemli belgelerin kopyaları','Aile buluşma ve iletişim planı'
 ];
 const text=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;n.textContent=String(value);return n;};
 const get=()=>{
  try {
   const d=JSON.parse(localStorage.getItem(key)||'null');
   if(d&&Array.isArray(d.inventory)&&d.checks&&typeof d.checks==='object'&&!Array.isArray(d.checks))return d;
  }catch{}
  return defaultData();
 };
 let state=get();
 function store(){try{localStorage.setItem(key,JSON.stringify(state));return true;}catch{alert('Tarayıcı kayıt alanına yazılamıyor. Özel sekme veya depolama doluluğunu kontrol edin.');return false;}}
 function numeric(id){return Number($(id).value);}
 const fmt=n=>new Intl.NumberFormat('tr-TR',{maximumFractionDigits:2}).format(n);
 function calcWater(){
  const people=numeric('waterPeople'),liters=numeric('waterLiters'),daily=numeric('waterPerPerson');
  $('waterResult').textContent=(Number.isFinite(people)&&Number.isInteger(people)&&people>=1&&people<=100&&Number.isFinite(liters)&&liters>=0&&liters<=100000&&Number.isFinite(daily)&&daily>=.5&&daily<=20)
    ? `${fmt(liters/(people*daily))} gün · ${fmt(people*daily)} L/gün` : 'Geçerli miktarlar girin';
 }
 function calcBattery(){
  const wh=numeric('batteryWh'),watts=numeric('batteryWatts'),eff=numeric('batteryEfficiency');
  $('batteryResult').textContent=(Number.isFinite(wh)&&wh>0&&wh<=1000000&&Number.isFinite(watts)&&watts>0&&watts<=100000&&Number.isFinite(eff)&&eff>=1&&eff<=100)
    ? `${fmt(wh*(eff/100)/watts)} saat (yaklaşık)` : 'Geçerli değerler girin';
 }
 function renderInventory(){
  const el=$('inventoryList');el.replaceChildren();
  if(!state.inventory.length){el.append(text('p','empty-inventory','Henüz malzeme eklenmedi.'));return;}
  for(const item of state.inventory){
   const row=text('div','inventory-item','');
   row.append(text('span','',`${item.name} — ${fmt(item.qty)} ${item.unit}`));
   const del=text('button','','Sil');del.type='button';
   del.addEventListener('click',()=>{state.inventory=state.inventory.filter(x=>x.id!==item.id);store();renderInventory();});
   row.append(del);el.append(row);
  }
 }
 function renderChecks(){
  const el=$('checklist');el.replaceChildren();
  CHECKS.forEach((label,i)=>{
   const row=text('label','check-item',''),input=document.createElement('input');input.type='checkbox';input.checked=!!state.checks[i];
   input.addEventListener('change',()=>{state.checks[i]=input.checked;store();});
   row.append(input,text('span','',label));el.append(row);
  });
 }
 function backup(){
  const data={format:'KALE-private-v0.2',exported_at:new Date().toISOString(),inventory:state.inventory,checks:state.checks};
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download='KALE-kisisel-yedek.json';
  document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
 }
 function validImported(d){
  if(!d||d.format!=='KALE-private-v0.2'||!Array.isArray(d.inventory)||d.inventory.length>3000||!d.checks||typeof d.checks!=='object'||Array.isArray(d.checks))throw Error('Geçersiz KALE yedeği');
  const inventory=d.inventory.map((x,i)=>{
   if(typeof x.name!=='string'||!x.name.trim()||x.name.length>80||!Number.isFinite(x.qty)||x.qty<=0||x.qty>100000||!['adet','litre','kg','paket','kutu','Wh'].includes(x.unit))throw Error('Geçersiz envanter satırı');
   return {id:i+1,name:x.name.trim(),qty:x.qty,unit:x.unit};
  });
  const checks={};CHECKS.forEach((_,i)=>{checks[i]=d.checks[i]===true;});
  return {inventory,checks};
 }
 function init(){
  for(const id of ['waterPeople','waterLiters','waterPerPerson'])$(id).addEventListener('input',calcWater);
  for(const id of ['batteryWh','batteryWatts','batteryEfficiency'])$(id).addEventListener('input',calcBattery);
  calcWater();calcBattery();renderInventory();renderChecks();
  $('inventoryForm').addEventListener('submit',event=>{
   event.preventDefault();const name=$('itemName').value.trim(),qty=numeric('itemQuantity'),unit=$('itemUnit').value;
   if(!name||name.length>80||!Number.isFinite(qty)||qty<=0||qty>100000||state.inventory.length>=3000)return;
   state.inventory.push({id:Date.now()+Math.random(),name,qty,unit});
   store();renderInventory();$('itemName').value='';$('itemName').focus();
  });
  $('resetChecklist').addEventListener('click',()=>{if(confirm('Kontrol listesindeki işaretleri temizlemek istiyor musun?')){state.checks={};store();renderChecks();}});
  $('exportData').addEventListener('click',backup);
  $('importData').addEventListener('change',async event=>{
   const file=event.target.files?.[0];if(!file)return;
   try{
    if(file.size>2_000_000)throw Error('Dosya 2 MB sınırını aşıyor');
    const imported=validImported(JSON.parse(await file.text()));
    if(confirm('Yedek mevcut envanter ve kontrol listesinin üzerine yazılacak. Devam edilsin mi?')){
     state=imported;store();renderChecks();renderInventory();
    }
   }catch(err){alert('Yedek yüklenemedi: '+err.message);}
   event.target.value='';
  });
 }
 document.addEventListener('DOMContentLoaded',init);
})();
