'use strict';
(()=>{
 const $=id=>document.getElementById(id),K=window.KaleSync;
 let pending=null;
 function render(){const list=$('slotList');list.replaceChildren();for(const [key,label] of Object.entries(K.LABELS)){
  const row=document.createElement('div');row.className='transfer-slot';const n=document.createElement('span'),stat=document.createElement('small');n.textContent=label;
  let raw=null;try{raw=localStorage.getItem(key);}catch{}stat.textContent=raw===null?'KAYIT YOK':`${(new TextEncoder().encode(raw).length/1024).toFixed(1)} KB`;row.append(n,stat);list.append(row);
 }}
 function download(data){const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='KALE-kisisel-veriler-v1.8.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 $('exportBtn').addEventListener('click',()=>{try{download(K.backup(key=>localStorage.getItem(key)));$('result').textContent='Yedek dosyası oluşturuldu. Dosya şifreli değildir.';}catch(e){$('result').textContent='Yedekleme yapılamadı: '+e.message;}});
 $('importFile').addEventListener('change',async e=>{pending=null;$('applyBtn').disabled=true;const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>K.LIMIT*2)throw Error('Dosya çok büyük (en çok 2 MB içerik).');const obj=JSON.parse(await file.text());const info=K.inspect(obj);pending=obj;
   $('preview').textContent=`${info.count} veri alanı bulundu: ${info.keys.map(k=>K.LABELS[k]).join(', ')}. Devam etmek için seçim yap ve onayla.`;$('applyBtn').disabled=info.count===0;
  }catch(err){$('preview').textContent='DOSYA REDDEDİLDİ: '+err.message;}finally{e.target.value='';}});
 $('applyBtn').addEventListener('click',()=>{if(!pending)return;const mode=document.querySelector('input[name="mode"]:checked').value;
  if(!confirm(mode==='replace'?'DİKKAT: aktarılan veri alanları bu cihazdakilerin yerine geçecek. Devam?':'Yalnız bu cihazda bulunmayan veriler yüklensin mi?'))return;
  try{const r=K.apply(pending,key=>localStorage.getItem(key),(key,raw)=>localStorage.setItem(key,raw),key=>localStorage.removeItem(key),mode);
   pending=null;$('applyBtn').disabled=true;render();$('result').textContent=`${r.restored} alan yüklendi, ${r.skipped} mevcut alan korundu. Güncel veriyi görmek için ilgili sayfayı yeniden aç.`;
  }catch(err){$('result').textContent='Yükleme hatası: '+err.message;}
 });
 render();
 if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
})();
