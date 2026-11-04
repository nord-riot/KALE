'use strict';
const $=id=>document.getElementById(id);
const tag=(name,cls,value)=>{const n=document.createElement(name);if(cls)n.className=cls;if(value!==undefined)n.textContent=value;return n;};
let all=[];
function show(g){
 const target=$('guideDetail');target.replaceChildren();
 target.append(tag('h2','',g.title));
 const img=tag('img');img.src=g.diagram;img.alt=g.title+' için şematik çizim';target.append(img);
 target.append(tag('p','tag',g.review_status+' · '+g.updated));
 const steps=tag('ol');for(const t of g.steps)steps.append(tag('li','',t));target.append(steps);
 target.append(tag('p','alert strong','ÖNEMLİ: '+g.warning));
 const sources=tag('div','sources','Kaynaklar / başvuru merkezleri (bağlantı için internet gerekir):');
 if(!g.sources.length)sources.append(tag('p','','Bu şema genel hazırlık önerisidir; kaynak ve uzman kontrolü henüz tamamlanmadı.'));
 for(const src of g.sources){const link=tag('a','',src.title);link.href=src.url;link.target='_blank';link.rel='noopener noreferrer';sources.append(link);}
 const print=tag('button','primary','YAZDIR');print.addEventListener('click',()=>window.print());sources.append(print);target.append(sources);
 $('guideDialog').showModal();
}
function render(){const q=$('guideSearch').value.toLocaleLowerCase('tr'),cat=$('guideCategory').value;const list=$('guideList');list.replaceChildren();
 let count=0;for(const g of all){if(cat&&g.category!==cat)continue;if(q&&!`${g.title} ${g.category} ${g.steps.join(' ')}`.toLocaleLowerCase('tr').includes(q))continue;
  const card=tag('article','guide');const img=tag('img');img.src=g.diagram;img.loading='lazy';img.alt='Şematik '+g.title;card.append(img);const body=tag('div','guide-body');
  body.append(tag('div','tag',g.category+' · '+g.review_status),tag('h2','',g.title),tag('p','',g.steps[0]),tag('p','warning','! '+g.warning));
  const btn=tag('button','','ADIMLARI GÖR →');btn.type='button';btn.addEventListener('click',()=>show(g));body.append(btn);card.append(body);list.append(card);count++;
 }
 if(!count)list.append(tag('p','notice','Aradığın başlık bulunamadı.'));
 $('guideCount').textContent=all.length;
}
async function init(){try{const r=await fetch('/assets/field-guides.json');if(!r.ok)throw Error('Dosya açılamadı');all=(await r.json()).guides;
 const cats=[...new Set(all.map(x=>x.category))].sort((a,b)=>a.localeCompare(b,'tr'));for(const c of cats){const opt=tag('option','',c);opt.value=c;$('guideCategory').append(opt);}render();
}catch(e){$('guideList').replaceChildren(tag('p','alert','Rehberler yüklenemedi: '+e.message));}}
$('guideSearch').addEventListener('input',render);$('guideCategory').addEventListener('change',render);
$('closeGuide').addEventListener('click',()=>$('guideDialog').close());$('guideDialog').addEventListener('click',e=>{if(e.target===$('guideDialog'))$('guideDialog').close()});init();
if('serviceWorker' in navigator && window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
