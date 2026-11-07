'use strict';
/* Admin panel: only accessible via KALE host loopback. No external requests. */
(()=>{
 const $=s=>document.getElementById(s);let eco=true,timer=0,alive=true;
 const set=(id,value)=>{$(id).textContent=value;};
 const fmt=(v,suffix='')=>v==null?'Bilinmiyor':`${new Intl.NumberFormat('tr-TR',{maximumFractionDigits:1}).format(v)}${suffix}`;
 const span=secs=>{const d=Math.floor(secs/86400),h=Math.floor((secs%86400)/3600),m=Math.floor((secs%3600)/60);return d?`${d} gün ${h} sa`:`${h} sa ${m} dk`;};
 const render=d=>{
  eco=!!d.energy_saving_mode;
  set('overall',d.server_running?'Sunucu çalışıyor':'Sunucu erişilemiyor');
  set('battery',d.battery?.available?fmt(d.battery.percentage,'%'):'Ölçüm yok');
  set('charge',d.battery?.available?`Durum: ${d.battery.status||'bilinmiyor'} · Güç: ${d.battery.plugged||'bilinmiyor'}`:(d.battery?.message||'Termux:API kurulu değil'));
  set('temperature',`Batarya sıcaklığı: ${fmt(d.battery?.temperature_c,' °C')}`);
  set('estimate',`Kalan süre (anlık akıma göre, yaklaşık): ${d.battery?.remaining_hours_estimate==null?'hesaplanamıyor':fmt(d.battery.remaining_hours_estimate,' sa')}`);
  set('cpu',fmt(d.cpu_percent,'%'));set('cpuCores',`Çekirdek: ${d.cpu_cores??'bilinmiyor'}`);
  set('ram',fmt(d.memory?.percent,'%'));set('ramUsage',`Kullanım: ${fmt(d.memory?.used_mb,' MB')} / ${fmt(d.memory?.total_mb,' MB')}`);
  set('uptime',span(d.uptime_seconds||0));set('chatUsers',`Sohbette aktif: ${d.online_chat_users??'bilinmiyor'}`);
  set('hotspotUsers','Hotspot bağlı cihaz sayısı: Android izin vermezse bilinmiyor');
  set('watchdog',d.supervisor?.state||'Gözetime bağlanmamış');
  set('restarts',`Otomatik yeniden başlatma: ${d.supervisor?.restarts??'bilinmiyor'}`);
  set('ecoStatus',eco?'Ekonomik':'Normal');
  const events=$('events');events.replaceChildren();for(const item of (d.events||[]).slice().reverse()){
   const row=document.createElement('div'),t=document.createElement('time'),p=document.createElement('span');
   t.textContent=new Date(item.time).toLocaleString('tr-TR');p.textContent=item.message;row.append(t,p);events.append(row);
  }set('lastUpdate','Son ölçüm: '+new Date().toLocaleTimeString('tr-TR'));
 };
 const poll=async()=>{if(!alive)return;try{const r=await fetch('/api/device/status',{cache:'no-store'});if(!r.ok)throw Error('Yönetici erişimi engellendi ('+r.status+')');render(await r.json());set('error','');}
 catch(e){set('overall','Bağlantı yok');set('error','Durum alınamadı: '+e.message);}
 finally{if(alive)timer=setTimeout(poll,eco?45000:15000);}};
 document.addEventListener('DOMContentLoaded',()=>{
  $('refreshBtn').addEventListener('click',()=>{clearTimeout(timer);poll();});
  $('ecoBtn').addEventListener('click',async()=>{
   try{const r=await fetch('/api/device/eco',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!eco})});
    if(!r.ok)throw Error('Tasarruf tercihi kaydedilemedi');const obj=await r.json();eco=obj.enabled;clearTimeout(timer);await poll();}
   catch(e){set('error',e.message);}
  });
  window.addEventListener('pagehide',()=>{alive=false;clearTimeout(timer);});
  poll();
 });
})();
