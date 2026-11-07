'use strict';
(()=>{
 const $=id=>document.getElementById(id), STORE='kale_chat_name', TOKEN='kale_chat_session';
 let token='',lastId=0,pollTimer=null,working=false,myName='',closed=false,seen=new Set();
 const setStatus=s=>{$('chatStatus').textContent=s;};
 async function api(action,payload){const r=await fetch('/api/chat/'+action,{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',body:JSON.stringify(payload)});
  let v;try{v=await r.json();}catch{throw Error('Sunucu yanıtı okunamadı.');}if(!r.ok)throw Error(v.error||'Sunucu bağlantı hatası');return v;}
 function renderOne(m){if(seen.has(m.id))return;seen.add(m.id);const sc=$('messages'),bottom=sc.scrollHeight-sc.scrollTop-sc.clientHeight<120;
  const b=document.createElement('div');b.className='chat-bubble'+(m.name===myName?' mine':'');
  const meta=document.createElement('div');meta.className='name';meta.textContent=m.name;
  const t=document.createElement('span');t.className='time';try{t.textContent=new Date(m.time).toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit'});}catch{t.textContent='';}
  meta.append(t);const msg=document.createElement('p');msg.textContent=m.text;b.append(meta,msg);
  if(sc.querySelector('.note'))sc.replaceChildren();sc.append(b);
  while(sc.children.length>180){sc.firstElementChild.remove();}
  if(bottom)sc.scrollTop=sc.scrollHeight;
 }
 function showRoster(online){const list=$('onlineList');list.replaceChildren();for(const name of online){const e=document.createElement('div');e.className='online-item';e.textContent=name;list.append(e);}if(!online.length)list.textContent='Kimse bağlı değil.';$('onlineCount').textContent=online.length;}
 async function poll(){if(!token||working||closed)return;working=true;
  try{const data=await api('poll',{token,after:lastId});for(const m of data.messages){renderOne(m);lastId=Math.max(lastId,m.id);}
   if(!seen.size&&data.last_id>0)lastId=data.last_id;
   showRoster(data.online);setStatus('Bağlı · Son güncelleme '+new Date().toLocaleTimeString('tr-TR'));
  }catch(e){setStatus('Bağlantı: '+e.message);if(/oturum|yeniden giriş/i.test(e.message)){await leave(false);}}
  finally{working=false;}}
 function setupRoom(){myName=localStorage.getItem(STORE)||myName;$('myName').textContent='Giriş yapan: '+myName;$('loginCard').hidden=true;$('roomCard').hidden=false;closed=false;
  if(pollTimer)clearInterval(pollTimer);pollTimer=setInterval(poll,2500);poll();}
 async function leave(notify=true){closed=true;if(pollTimer)clearInterval(pollTimer);pollTimer=null;const old=token;token='';sessionStorage.removeItem(TOKEN);
  if(notify&&old){try{await api('leave',{token:old});}catch{}}
  $('roomCard').hidden=true;$('loginCard').hidden=false;seen.clear();lastId=0;showRoster([]);$('messages').replaceChildren();setStatus('Sohbetten çıkıldı.');}
 $('loginForm').addEventListener('submit',async e=>{e.preventDefault();const name=$('loginName').value.trim();setStatus('Sohbete katılınıyor…');
  try{const data=await api('join',{name});token=data.token;myName=data.name;localStorage.setItem(STORE,myName);sessionStorage.setItem(TOKEN,token);setupRoom();}catch(err){setStatus(err.message);}});
 $('sendForm').addEventListener('submit',async e=>{e.preventDefault();const input=$('messageInput');const text=input.value.trim();if(!text||!token)return;
  const button=$('sendForm').querySelector('button');button.disabled=true;
  try{await api('send',{token,text});input.value='';await poll();}catch(err){setStatus('Mesaj gönderilemedi: '+err.message);}finally{button.disabled=false;input.focus();}});
 $('leaveBtn').addEventListener('click',()=>leave());
 // Restore session only within the same browser tab; never persist secrets in localStorage.
 const prev=sessionStorage.getItem(TOKEN);if(prev){token=prev;myName=localStorage.getItem(STORE)||'';setupRoom();}
 $('loginName').value=localStorage.getItem(STORE)||'';
 if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
})();
