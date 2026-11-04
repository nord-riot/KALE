/* KALE v1.6 — inventory validation, deterministic status and safe exports.
 * No browser APIs needed for core calculations. No clinical or food safety guarantee. */
(function (root, factory) {
  const lib = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = lib;
  root.KaleStock = lib;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const CATEGORIES = Object.freeze({su:'Su',gida:'Gıda',ilac:'İlaç',ilk_yardim:'İlk yardım',enerji:'Enerji',ekipman:'Ekipman',hijyen:'Hijyen',diger:'Diğer'});
  const UNITS = Object.freeze({adet:'adet',L:'litre',mL:'mililitre',kg:'kilogram',g:'gram',paket:'paket',kutu:'kutu'});
  const DATE_TYPES = Object.freeze({SKT:'Son kullanma tarihi',TETT:'Tavsiye edilen tüketim tarihi',belirsiz:'Etiket türü belirtilmemiş'});
  const LIMIT = 500;
  const strictDate = s => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
    const d = new Date(s+'T00:00:00Z');
    return Number.isFinite(d.getTime()) && d.toISOString().slice(0,10) === s ? d : null;
  };
  const trim = (v,n) => typeof v === 'string' ? v.trim().slice(0,n) : '';
  const qty = (v,max=1e9) => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= max;
  function validateItem(item) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) throw Error('Kayıt nesnesi geçersiz.');
    if (!/^k[a-zA-Z0-9_-]{8,48}$/.test(item.id||'')) throw Error('Geçersiz kayıt ID.');
    const name=trim(item.name,100);
    if (!name || name!==item.name) throw Error('Ürün adı 1–100 karakter olmalı.');
    if (!Object.hasOwn(CATEGORIES,item.category)) throw Error('Geçersiz kategori.');
    if (!Object.hasOwn(UNITS,item.unit)) throw Error('Geçersiz miktar birimi.');
    if (!qty(item.quantity)) throw Error('Miktar 0–1.000.000.000 arası olmalı.');
    if (!qty(item.minQuantity)) throw Error('Asgari stok sayısı geçersiz.');
    for (const k of ['location','batch','notes']) {
      const lim=k==='notes'?500:100;
      if (typeof item[k] !== 'string' || item[k].length > lim) throw Error(k+' alanı geçersiz.');
    }
    if (item.expiry !== '' && !strictDate(item.expiry)) throw Error('Geçersiz tarih.');
    if (!Object.hasOwn(DATE_TYPES,item.dateType)) throw Error('Tarih etiketi tipi geçersiz.');
    if (typeof item.potable !== 'boolean') throw Error('İçilebilir su işareti geçersiz.');
    if (item.category!=='su' && item.potable) throw Error('İçilebilir su işareti yalnız su kategorisine uygulanır.');
    return {
      id:item.id,name,category:item.category,quantity:item.quantity,unit:item.unit,
      minQuantity:item.minQuantity,location:item.location.trim(),batch:item.batch.trim(),
      expiry:item.expiry,dateType:item.dateType,potable:item.potable,notes:item.notes.trim()
    };
  }
  const newId = () => 'k'+ Array.from({length:20},()=>Math.floor(Math.random()*16).toString(16)).join('');
  function makeItem(form, id=newId()) {
    const obj={...form,id,quantity:Number(form.quantity),minQuantity:Number(form.minQuantity),potable:Boolean(form.potable)};
    return validateItem(obj);
  }
  function status(item, now=new Date(), soonDays=30) {
    const d= item.expiry ? strictDate(item.expiry) : null;
    let date='no_date', days=null;
    if (d) {
      const today=Date.UTC(now.getFullYear(),now.getMonth(),now.getDate());
      days=Math.round((d.getTime()-today)/86400000);
      date=days<0?'past':days<=soonDays?'soon':'dated';
    }
    const low=item.quantity<item.minQuantity;
    // Date state is a warning to check the product. It is never a food/medicine safety verdict.
    return {date,days,low,empty:item.quantity===0};
  }
  function metrics(items, people, perPersonDay, now=new Date()) {
    const arr=items.map(i=>({item:i,mark:status(i,now)}));
    const counts={total:items.length,low:arr.filter(x=>x.mark.low).length,past:arr.filter(x=>x.mark.date==='past').length,soon:arr.filter(x=>x.mark.date==='soon').length};
    let liters=0;
    for(const item of items) {
      if(item.category!=='su'||!item.potable)continue;
      // Do not count past-date stock as known-good drinking water; even counted water requires separate safety checks.
      if(status(item,now).date==='past')continue;
      if(item.unit==='L')liters+=item.quantity;
      if(item.unit==='mL')liters+=item.quantity/1000;
    }
    const daily=people*perPersonDay;
    return {...counts,waterLiters:liters,waterDays:daily>0?liters/daily:0};
  }
  function validateBackup(payload) {
    if(!payload || payload.format!=='KALE-STOK-v1' || !Array.isArray(payload.items) || payload.items.length>LIMIT)
      throw Error('Desteklenmeyen stok yedeği veya fazla kayıt (en çok 500).');
    if(!Number.isInteger(payload.people)||payload.people<1||payload.people>30||!qty(payload.perPersonDay,30)||payload.perPersonDay<0.5)
      throw Error('Hane veya günlük su hedefi geçersiz.');
    const items=payload.items.map(validateItem),ids=new Set(items.map(i=>i.id));
    if(ids.size!==items.length)throw Error('Yedekte mükerrer kayıt ID var.');
    return {format:'KALE-STOK-v1',people:payload.people,perPersonDay:payload.perPersonDay,items};
  }
  const csvCell = value => {
    let s=String(value==null?'':value);
    if (/^[\s]*[=+@-]/.test(s))s="'"+s; // avoid spreadsheet formula injection, especially imported names/notes
    return '"'+s.replace(/"/g,'""')+'"';
  };
  function toCSV(items) {
    const cols=[['name','Ürün'],['category','Kategori'],['quantity','Miktar'],['unit','Birim'],['minQuantity','Minimum'],['location','Konum'],['expiry','Tarih'],['dateType','Tarih türü'],['batch','Parti'],['potable','İçilebilir olarak işaretlendi'],['notes','Not']];
    return '\ufeff'+[cols.map(([,label])=>csvCell(label)).join(';'),...items.map(item=>cols.map(([key])=>csvCell(item[key])).join(';'))].join('\r\n');
  }
  return {CATEGORIES,UNITS,DATE_TYPES,LIMIT,validateItem,makeItem,newId,status,metrics,validateBackup,toCSV,strictDate};
});
