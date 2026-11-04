"use strict";
async function load(){
 try{
  const [a,b]=await Promise.all([fetch('/api/medicines/stats',{cache:'no-store'}),fetch('/api/reviews/stats',{cache:'no-store'})]);
  if(!a.ok||!b.ok)throw Error('Sunucu bağlantısı kesildi');
  const m=await a.json(),r=await b.json();
  document.getElementById('drugTotal').textContent=m.total;
  document.getElementById('reviewed').textContent=r.reviewed;
  document.getElementById('approved').textContent=r.approved_by_reviewer;
  document.getElementById('problems').textContent=r.needs_correction+r.rejected;
  document.getElementById('reviewNotice').textContent=`${m.total-r.reviewed} kayıt için henüz karar yok. ${r.reviewed} kayıt doktor Excel'inden içe aktarılmış. Excel kayıtları klinik bilgi doğruluğunun bağımsız kanıtı değildir.`;
 }catch{
  document.getElementById('reviewNotice').textContent='Sunucuya ulaşılamıyor; inceleme durumları çevrimdışı doğrulanamaz.';
 }
}
if('serviceWorker' in navigator && window.isSecureContext){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}))}
load();