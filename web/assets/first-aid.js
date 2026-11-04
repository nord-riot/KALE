'use strict';
/* KALE v1.7. Static offline-first safety cards; no medical data is collected, transmitted or stored. */
(()=>{
 const $=id=>document.getElementById(id);let cards=[];
 const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
 const lower=s=>String(s||'').toLocaleLowerCase('tr-TR').normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
 function putText(parent,tag,cls,text){const n=el(tag,cls,text);parent.append(n);return n;}
 function addList(parent,items,cls,heading){putText(parent,'h3','',heading);const list=el('ol',cls);for(const item of items)putText(list,'li','',item);parent.append(list);}
 function show(id){const x=cards.find(v=>v.id===id);if(!x)return;const target=$('aidDetail');target.replaceChildren();
  putText(target,'p','aid-tag',x.category+' · '+x.urgency+' · '+x.id);
  putText(target,'h2','',x.title);putText(target,'p','summary',x.summary);
  const img=el('img');img.src=x.diagram;img.alt=x.title+' için genel amaçlı şematik başlık';img.loading='lazy';target.append(img);
  addList(target,x.signs,'','Ne zaman akla gelmeli?');addList(target,x.steps,'','Yapılabilecek ilk adımlar');addList(target,x.avoid,'aid-avoid','Kaçın');
  const div=el('div','aid-callout');const title=putText(div,'strong','','Acil yardım: ');div.append(document.createTextNode(x.call112+' '));const phone=el('a','', '112’yi ara');phone.href='tel:112';div.append(phone);target.append(div);
  putText(target,'h3','','Resmî/kurumsal başvuru kaynakları');const sources=el('div','aid-source-list');for(const src of x.sources){const a=el('a','',src.title+' ↗');a.href=src.url;a.target='_blank';a.rel='noopener noreferrer';sources.append(a);}target.append(sources);
  putText(target,'p','aid-disclaimer','Bu kayıt editoryal taslaktır; klinik uzman incelemesi yapılmamıştır. Kaynak bağlantısı içeriklerin uzman tarafından onaylandığını kanıtlamaz. Türkiye’de acil yardım 112, zehir danışma 114. Çocuk, bebek, hamile veya özel hastalık durumlarında uygulama farklı olabilir.');
  const print=putText(target,'button','aid-print','Bu kartı yazdır');print.type='button';print.addEventListener('click',()=>window.print());$('aidDialog').showModal();
 }
 function render(){const q=lower($('aidSearch').value.trim()),cat=$('aidCategory').value,urgency=$('aidUrgency').value;const root=$('aidCards');root.replaceChildren();let n=0;
  for(const x of cards){if(cat!=='all'&&cat!==x.category)continue;if(urgency!=='all'&&urgency!==x.urgency)continue;
   const blob=lower([x.title,x.category,x.summary,...x.signs,...x.avoid].join(' '));if(q&&!blob.includes(q))continue;
   const card=el('article','aid-card'+(x.urgency==='112 HEMEN'?' critical':''));const img=el('img');img.src=x.diagram;img.alt=x.title+' şematik görsel';img.loading='lazy';card.append(img);
   const body=el('div','aid-card-content');putText(body,'span','aid-tag',x.urgency+' · '+x.category);putText(body,'h3','',x.title);putText(body,'p','',x.summary);
   const btn=putText(body,'button','','REHBERİ AÇ →');btn.type='button';btn.addEventListener('click',()=>show(x.id));card.append(body);root.append(card);n++;
  }
  if(!n)putText(root,'p','notice','Eşleşen rehber yok. Acil tehlike varsa 112’yi ara.');$('aidCount').textContent=n+' / '+cards.length+' rehber gösteriliyor';
 }
 async function load(){try{const response=await fetch('/assets/first-aid.json');if(!response.ok)throw Error('Katalog okunamadı');const data=await response.json();if(data.format!=='KALE-FIRSTAID-1'||!Array.isArray(data.cards)||data.cards.length!==24)throw Error('Beklenen katalog sürümü yok');cards=data.cards;
  const cats=[...new Set(cards.map(x=>x.category))].sort((a,b)=>a.localeCompare(b,'tr'));for(const c of cats){const opt=el('option','',c);opt.value=c;$('aidCategory').append(opt);}render();
 }catch(error){const root=$('aidCards');root.replaceChildren();putText(root,'p','alert strong','Rehberler yüklenemedi. Acil durumda 112’yi ara.');$('aidCount').textContent='Rehber erişim hatası';}}
 $('aidSearch').addEventListener('input',render);$('aidCategory').addEventListener('change',render);$('aidUrgency').addEventListener('change',render);
 document.querySelectorAll('[data-jump]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.jump)));
 $('closeAid').addEventListener('click',()=>$('aidDialog').close());$('aidDialog').addEventListener('click',e=>{if(e.target===$('aidDialog'))$('aidDialog').close();});
 if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));load();
})();
