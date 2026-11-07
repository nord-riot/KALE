'use strict';const $=id=>document.getElementById(id);const tag=(n,c,t)=>{const el=document.createElement(n);if(c)el.className=c;if(t!==undefined)el.textContent=t;return el;};let plants=[];
function render(){const q=$('plantSearch').value.toLocaleLowerCase('tr'),h=$('plantHabitat').value.toLocaleLowerCase('tr');const dest=$('plants');dest.replaceChildren();let count=0;
 for(const x of plants){if(q&&!`${x.name} ${x.latin}`.toLocaleLowerCase('tr').includes(q))continue;if(h&&!x.habitat.toLocaleLowerCase('tr').includes(h))continue;
 const card=tag('article','plant');card.append(tag('div','danger','⚠ ZEHİRLENME RİSKİ — TÜKETME'),tag('h2','',x.name),tag('em','',x.latin),tag('p','',x.warning),tag('p','',x.habitat),tag('p','tag',x.review_status));const more=tag('details','nature-more'),sum=tag('summary','','AYRINTILI GÜVENLİK BİLGİSİ');
 for(const s of x.details||[])more.append(tag('h3','guide-expansion-title',s.heading),tag('p','guide-expansion-text',s.text));
 more.prepend(sum);card.append(more);
 const link=tag('a','',x.source+' kaynağı ↗');link.href=x.source_url;link.target='_blank';link.rel='noopener noreferrer';card.append(link);dest.append(card);count++;}
 if(!count)dest.append(tag('p','notice','Aranan bitki bulunamadı. Bu, güvenli olduğu anlamına gelmez.'));$('plantCount').textContent=plants.length;
}
fetch('/assets/poisonous-plants.json').then(r=>{if(!r.ok)throw Error('Veri okunamadı');return r.json()}).then(d=>{plants=d.plants;render()}).catch(e=>$('plants').replaceChildren(tag('p','alert',e.message)));
$('plantSearch').addEventListener('input',render);$('plantHabitat').addEventListener('change',render);
if('serviceWorker' in navigator && window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
