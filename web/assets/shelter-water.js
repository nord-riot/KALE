'use strict';
/* KALE v1.4 — local-only risk pre-screening. Does not approve a site or drinking water. */
(()=>{
 const $=id=>document.getElementById(id);
 const element=(type,cls,txt)=>{const e=document.createElement(type);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
 const source=(src)=>{const a=element('a','',src.title);a.href=src.url;a.target='_blank';a.rel='noopener noreferrer';return a;};
 let cards=[];
 const clean=s=>String(s||'').toLocaleLowerCase('tr');
 function presentRisk(el,text,status){el.textContent=text;el.className='assessment-result '+status;}
 function evaluateSite(){const flags=[...document.querySelectorAll('#shelterCheck [data-flag]')].map(e=>({name:e.dataset.flag,value:e.value}));
  if(flags.some(x=>x.value==='yes')){presentRisk($('siteResult'),'DUR / ALTERNATİF YER ARA: Bildirilen risklerden en az biri mevcut. Tehlikeli alanı barınak için kullanma. Resmî tahliye ve güvenli sığınma yönlendirmesini izle.','danger');return;}
  if(flags.some(x=>x.value==='unknown')){presentRisk($('siteResult'),'BİLGİ EKSİK: Tehlikeleri dışlayamıyorsun. Bu alanın güvenli olduğu söylenemez. Resmî risk duyurularını ve daha güvenli barınmayı değerlendir.','uncertain');return;}
  presentRisk($('siteResult'),'ÖN KONTROL: Listelenen riskleri gözlemlemedin. Bu, alanın güvenli/sağlam olduğu anlamına gelmez. Hava, zemin, yapı, yerel tehlikeler ve izin koşulları ayrıca doğrulanmalı.','uncertain');
 }
 function evaluateWater(){const src=$('waterOrigin').value,chemical=$('waterChemical').value,cloudy=$('waterCloudy').value,boil=$('waterBoil').value;
  if(chemical==='yes'){presentRisk($('waterResult'),'İÇME / YEMEKTE KULLANMA. Kimyasal, yakıt, pestisit veya radyasyon şüphesinde kaynatma, bez süzme ve sıradan filtreleme suyu güvenli kılmaz. Ambalajlı veya yetkililerin güvenli dediği farklı kaynağa geç.','danger');return;}
  if(chemical==='unknown'){presentRisk($('waterResult'),'BİLİNMEYEN KİRLİLİK: Suyun kimyasal güvenliği bilinmiyor. Suya içme onayı verme; güvenilir ambalajlı su ve sağlık/yerel otorite değerlendirmesini tercih et.','uncertain');return;}
  if(src==='sealed'){presentRisk($('waterResult'),'AMBALAJ KONTROLÜ: Güvenilir, açılmamış ve hasarsız ambalajlı içme suyu öncelikli kaynaktır. Etiket ve saklama durumunu kontrol et. Bu ekran ürünün güvenliğini doğrulamaz.','uncertain');return;}
  if(src==='official'){presentRisk($('waterResult'),'RESMÎ KAYNAK: Yerel yetkililerin güncel “kullanılabilir” duyurusunu ve kapsamını doğrula. Su kullanım uyarıları değişebilir; bu ekran gerçek zamanlı onay vermez.','uncertain');return;}
  if(src==='unknown'){presentRisk($('waterResult'),'KAYNAK BİLİNMİYOR: Bu suyu güvenli içme suyu sayma. Ambalajlı veya güncel resmî kaynağa öncelik ver.','danger');return;}
  if(boil!=='yes'){presentRisk($('waterResult'),'AÇIK KAYNAK — GÜVENLİLİK DOĞRULANMADI: Dere, kuyu veya yağmur suyunu doğrudan içme. Uygun ve kaynağa özgü işlem bilinmiyorsa güvenilir alternatif su kullan.','danger');return;}
  presentRisk($('waterResult'),(cloudy==='yes'?'ÖNCE TORTUYU AYIR: Suyu beklet ve temiz bezle kaba parçacıkları süz; tek başına yeterli değildir. ':'')+'MİKROBİYOLOJİK RİSK İÇİN: Kimyasal bulaş şüphesi yoksa CDC, berrak suyu güçlü kaynama noktasında 1 dakika; 2.000 m üzerindeki rakımda 3 dakika kaynatmayı önerir. Sonra soğutup temiz kapalı kapta sakla. BU EKRAN SUYU İÇİLEBİLİR OLARAK ONAYLAMAZ.','uncertain');
 }
 function show(g){const target=$('dialogContent');target.replaceChildren();
  target.append(element('h2','',g.title),element('p','review-line',g.category==='barinak'?'BARINAK / TASLAK':'SU / TASLAK'));
  const img=element('img');img.src=g.diagram;img.alt=g.title+' şeması';target.append(img);
  target.append(element('p','',g.summary));
  const list=(title,arr)=>{target.append(element('h3','',title));const ul=element('ul');for(const item of arr)ul.append(element('li','',item));target.append(ul);};
  list('Gerekli malzemeler / kontroller',g.materials);list('Adım adım uygulama',g.steps);list('Durdurma / kırmızı bayraklar',g.stop);
  for(const s of g.details||[]){target.append(element('h3','guide-expansion-title',s.heading),element('p','guide-expansion-text',s.text));}
  target.append(element('p','warning-block','KRİTİK: '+g.warning));
  const refs=element('div','source-links');refs.append(element('h3','','İlgili güvenlik kaynakları (çevrimdışı bağlantı açılmaz)'));
  for(const s of g.sources)refs.append(source(s));refs.append(element('p','review-line',g.review_status));target.append(refs);
  const print=element('button','primary','BU KARTI YAZDIR');print.type='button';print.addEventListener('click',()=>window.print());target.append(print);
  $('guideDialog').showModal();
 }
 function render(){const search=clean($('cardSearch').value).trim(),cat=$('cardCategory').value;const list=$('cardList');list.replaceChildren();let shown=0;
  for(const g of cards){if(cat!=='all'&&g.category!==cat)continue;
   const terms=clean([g.title,g.summary,g.category,...g.steps].join(' '));if(search&&!terms.includes(search))continue;
   const box=element('article','guide');const img=element('img');img.loading='lazy';img.alt=g.title+' için özgün şematik görsel';img.src=g.diagram;box.append(img);
   const content=element('div','guide-body');content.append(element('div','tag',g.category==='barinak'?'BARINAK · EDİTORYAL TASLAK':'SU · EDİTORYAL TASLAK'),element('h2','',g.title),element('p','',g.summary),element('p','warning','⚠ '+g.warning));
   const button=element('button','','MALZEME + AŞAMALARI GÖR →');button.type='button';button.addEventListener('click',()=>show(g));content.append(button);box.append(content);list.append(box);shown++;
  }
  $('visibleCount').textContent=shown+' / '+cards.length+' kart';if(!shown)list.append(element('p','notice','Eşleşen rehber bulunamadı. Arama sonucu güvenli olduğu anlamına gelmez.'));
 }
 async function init(){try{const response=await fetch('/assets/shelter-water.json');if(!response.ok)throw Error('Rehber dosyası açılamadı.');const data=await response.json();cards=data.cards;
  if(!Array.isArray(cards)||cards.length!==18)throw Error('Beklenmeyen katalog sürümü.');$('totalCards').textContent=cards.length;render();
 }catch(e){$('cardList').replaceChildren(element('p','alert','Barınak-su rehberi okunamadı: '+e.message));}}
 $('shelterCheck').addEventListener('submit',e=>{e.preventDefault();evaluateSite()});$('waterCheck').addEventListener('submit',e=>{e.preventDefault();evaluateWater()});
 function switchTab(water){$('waterCheck').hidden=!water;$('shelterCheck').hidden=water;$('waterTab').setAttribute('aria-selected',String(water));$('shelterTab').setAttribute('aria-selected',String(!water));}
 $('waterTab').addEventListener('click',()=>switchTab(true));$('shelterTab').addEventListener('click',()=>switchTab(false));
 $('cardCategory').addEventListener('change',render);$('cardSearch').addEventListener('input',render);
 $('closeDialog').addEventListener('click',()=>$('guideDialog').close());$('guideDialog').addEventListener('click',e=>{if(e.target===$('guideDialog'))$('guideDialog').close()});
 init();if('serviceWorker' in navigator && window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
})();
