/* KALE v1.8 local-only personal backup validation (portable Node/browser). */
(function(root,factory){const api=factory();if(typeof module!=='undefined'&&module.exports)module.exports=api;root.KaleSync=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const FORMAT='KALE-PERSONAL-TRANSFER-v1';
const LIMIT=2_000_000;
const LABELS=Object.freeze({
 'kale-inventory-v16':'Stok envanteri',
 'kale_plan_v11':'72 saat aile planı',
 'kale_v1_private_points':'Koordinat defteri',
 'kale_v02_private':'Eski küçük envanter ve çanta',
 'kale_favs':'Kaydedilen rehberler',
 'kale-editor-v12':'İçerik Atölyesi taslakları'
});
const keys=Object.keys(LABELS);
const plain=obj=>obj!==null&&typeof obj==='object'&&!Array.isArray(obj);
const finite=(n,min,max)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
const str=(s,max)=>typeof s==='string'&&s.length<=max;
function validate(key,value){
 if(!Object.hasOwn(LABELS,key))throw Error('Bilinmeyen veri anahtarı: '+key);
 switch(key){
 case 'kale-inventory-v16':{
  const stock=typeof globalThis!=='undefined'?globalThis.KaleStock:undefined;
  if(!stock||typeof stock.validateBackup!=='function')throw Error('Stok doğrulayıcı yüklenemedi');
  stock.validateBackup(value);
  if(value.log!==undefined&&(!Array.isArray(value.log)||value.log.length>100||value.log.some(x=>!plain(x)||!str(x.at,50)||!str(x.message,180))))throw Error('Stok hareket kaydı geçersiz');
  break;}
 case 'kale_plan_v11':{
  if(!plain(value)||!Number.isInteger(Number(value.people))||!finite(Number(value.people),1,30)||!finite(Number(value.water),0,100000)||!finite(Number(value.daily),.5,20)||!str(value.meeting,140)||!str(value.contact,160)||!plain(value.checks))throw Error('Afet planı geçersiz');
  if(Object.keys(value.checks).length>50||Object.values(value.checks).some(x=>typeof x!=='boolean'))throw Error('Plan işaretleri geçersiz');break;}
 case 'kale_v1_private_points':
  if(!Array.isArray(value)||value.length>500||value.some(p=>!plain(p)||!str(p.name,80)||!p.name.trim()||!finite(p.lat,-85,85)||!finite(p.lon,-180,180)))throw Error('Koordinat listesi geçersiz');break;
 case 'kale_v02_private':
  if(!plain(value)||!Array.isArray(value.inventory)||value.inventory.length>3000||!plain(value.checks)||Object.keys(value.checks).length>50)throw Error('Eski envanter geçersiz');
  if(value.inventory.some(x=>!plain(x)||!str(x.name,80)||!x.name.trim()||!finite(x.qty,0,100000)||!['adet','litre','kg','paket','kutu','Wh'].includes(x.unit)))throw Error('Eski stok satırı geçersiz');
  if(Object.values(value.checks).some(x=>typeof x!=='boolean'))throw Error('Çanta işaretleri geçersiz');break;
 case 'kale_favs':
  if(!Array.isArray(value)||value.length>5000||value.some(x=>!Number.isSafeInteger(x)||x<1||x>1000000))throw Error('Kaydedilmiş rehber listesi geçersiz');break;
 case 'kale-editor-v12':
  if(!plain(value)||Object.keys(value).length>500||Object.entries(value).some(([id,x])=>!/^\d{1,7}$/.test(id)||!plain(x)||Number(id)!==x.id||!str(x.title,160)||!str(x.body,20000)||!str(x.category,50)||!Array.isArray(x.sources)||x.sources.length>20||x.sources.some(u=>typeof u!=='string'||!u.startsWith('https://'))))throw Error('Editör taslakları geçersiz');break;
 }
 return value;
}
function backup(read){const data={};for(const key of keys){let raw=read(key);if(raw===null)continue;if(raw.length>LIMIT)throw Error('Çok büyük kayıt: '+key);let val=JSON.parse(raw);validate(key,val);data[key]=val;}
 const bundle={format:FORMAT,exported_utc:new Date().toISOString(),data};if(JSON.stringify(bundle).length>LIMIT)throw Error('Yedek 2 MB sınırını aşıyor');return bundle;}
function inspect(bundle){if(!plain(bundle)||bundle.format!==FORMAT||!plain(bundle.data)||!str(bundle.exported_utc,80))throw Error('KALE kişisel yedek biçimi yanlış');
 if(JSON.stringify(bundle).length>LIMIT)throw Error('Yedek 2 MB sınırını aşıyor');const data=bundle.data;
 for(const [key,val] of Object.entries(data))validate(key,val);
 return {count:Object.keys(data).length,keys:Object.keys(data)};
}
function apply(bundle,read,write,remove,mode='replace'){
 const info=inspect(bundle);if(mode!=='replace'&&mode!=='missing')throw Error('Geçersiz geri yükleme modu');
 const targets=info.keys.filter(k=>mode==='replace'||read(k)===null);
 const previous=new Map(targets.map(k=>[k,read(k)]));let done=[];
 try{for(const key of targets){write(key,JSON.stringify(bundle.data[key]));done.push(key);}}
 catch(e){for(const key of [...done].reverse()){const old=previous.get(key);if(old===null)remove(key);else write(key,old);}throw Error('Yükleme başarısız; mümkün olan eski kayıtlar geri alındı: '+e.message);}
 return {restored:done.length,skipped:info.count-done.length};
}
return {FORMAT,LIMIT,LABELS,keys,validate,backup,inspect,apply};
});
