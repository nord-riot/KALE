'use strict';
/* KALE v1.5 — Source-linked offline field guidance, not food-safety certification. */
(()=>{
 const $=id=>document.getElementById(id);
 const create=(kind,cls,txt)=>{const n=document.createElement(kind);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;};
 let all=[];const categories={gida:'GIDA / SAKLAMA',pisirme:'GÜVENLİ PİŞİRME',enerji:'ENERJİ',kis:'KIŞ'};
 const lower=s=>String(s||'').toLocaleLowerCase('tr');
 function msg(id,tone,message){const box=$(id);box.textContent=message;box.className='advice '+tone;}
 function foodDecision(){const kind=$('foodKind').value,h=Number($('outageHours').value),door=$('doorClosed').value,verified=$('foodVerified').value;
  if(!Number.isFinite(h)||h<0||h>720){msg('foodResult','danger','Geçerli kesinti süresi gir (0–720 saat).');return;}
  if(verified==='warm'){msg('foodResult','danger','DUR — Gıda 4°C üzerinde uzun süre kaldı veya soğuk zincir şüpheli. Bozulabilir gıdayı yeme; şüphede at. Yüksek sıcaklıkta kalan gıdayı tekrar pişirmek bütün riskleri gidermez.');return;}
  if(door!=='yes'){msg('foodResult','unknown','KAPI GEÇMİŞİ BELİRSİZ — Genel 4/24/48 saat varsayımı geçerli sayılmaz. Ürün sıcaklığını, buz kristallerini ve maruziyet süresini kontrol et; şüpheli bozulabilir gıdayı at. Bu sonuç tüketim onayı değildir.');return;}
  const limit={fridge:4,half:24,full:48}[kind];
  if(h>=limit){
   if(kind==='fridge'){msg('foodResult','danger','4 SAATLİK GENEL SINIRA GELİNDİ/AŞILDI — Et, süt, yumurta, balık ve artan yemekler gibi bozulabilir buzdolabı gıdalarını güvenilir soğutma sürmediyse at. Tat testi yapma.');return;}
   msg('foodResult','unknown',`${limit} SAATLİK GENEL DONDURUCU SÜRESİNE GELİNDİ/AŞILDI — Gıda bazında buz kristali, gerçek sıcaklık (4°C veya altı) ve önceki sıcaklık geçmişini değerlendir. Bu süre gıdayı otomatik güvensiz veya güvenli saymaz; şüpheliyse at.`);return;
  }
  msg('foodResult','unknown',`KAPAK KAPALIYSA GENEL TAHMİN ${limit} SAAT — Kesinti ${h} saat. Ancak gıda termometresi ve saklama geçmişi olmadan tüketilebilir onayı verilemez. Soğuk zinciri koru; kapağı açma. Her ürün ayrı değerlendirilmeli.`);
 }
 function powerDecision(){const cap=Number($('capacityWh').value),watts=Number($('loadW').value),eff=Number($('efficiency').value),res=Number($('reserve').value);
  if(![cap,watts,eff,res].every(Number.isFinite)||cap<=0||cap>1e6||watts<=0||watts>1e5||eff<20||eff>100||res<0||res>90){msg('energyResult','danger','Girilen değerler geçersiz: kapasite, tüketim, verim veya rezerv sınırlarını kontrol et.');return;}
  const available=cap*(eff/100)*(1-res/100),hours=available/watts;
  const fmt=n=>new Intl.NumberFormat('tr-TR',{maximumFractionDigits:1}).format(n);
  msg('energyResult','info',`TEORİK TAHMİN: ${fmt(available)} Wh kullanılabilir kabul edildiğinde yaklaşık ${fmt(hours)} saat (${fmt(hours/24)} gün). Ölçülen gerçek güç, sıcaklık, pil sağlığı, ilk kalkış akımı ve kablo kayıpları nedeniyle değişebilir. Hayati/tıbbi cihazlar için bu tahmine güvenme.`);
 }
 function winterDecision(){const flags=[...document.querySelectorAll('input[name="coldFlag"]:checked')].map(x=>x.value);
  if(flags.includes('confusion')||flags.includes('drowsy')){msg('winterResult','danger','ACİL UYARI — Bilinç/konuşma değişikliği veya olağandışı uyuklama hipotermide görülebilir. 112’yi ara, kişiyi güvenli ve ılık yere al, ıslak giysileri değiştir. Bilinci kapalı kişiye ağızdan yiyecek/içecek verme.');return;}
  if(flags.includes('frost')){msg('winterResult','danger','DONMA ŞÜPHESİ — Uyuşmuş, beyaz/gri veya sert deriyi ovalama, aşırı sıcakla ısıtma. Soğuktan koru ve acil tıbbi değerlendirme iste; yeniden donma riski varsa profesyonel yönlendirme gerekir.');return;}
  if(flags.includes('shiver')||flags.includes('wet')){msg('winterResult','unknown','SOĞUK MARUZİYETİ — Islak giysiyi değiştir, kuru ve güvenli barınağa geç, katmanlı giyin. Titreme sürüyor veya belirtiler kötüleşiyorsa 112 ile iletişime geç. Bu değerlendirme hipotermiyi dışlamaz.');return;}
  msg('winterResult','unknown','BELİRTİ İŞARETLENMEDİ — Bu, hipotermi veya donma riskinin bulunmadığı anlamına gelmez. Soğukta kuru ve korunmuş kal; durum değişirse yeniden değerlendir.');
 }
 function switchTab(tab){for(const [name,id] of [['food','foodForm'],['energy','energyForm'],['winter','winterForm']]){
  const selected=name===tab;$(id).hidden=!selected;$(name+'Tab').setAttribute('aria-selected',String(selected));$(name+'Tab').classList.toggle('tab-current',selected);
 }}
 function detail(g){const box=$('guideDetail');box.replaceChildren();box.append(create('h2','',g.title),create('p','stamp',categories[g.category]+' · '+g.review_status));
  const img=create('img');img.src=g.diagram;img.alt=g.title+' için özgün şematik çizim';box.append(img,create('p','',g.summary));
  function list(title,values,ordered=false){box.append(create('h3','',title));const ul=create(ordered?'ol':'ul');for(const value of values)ul.append(create('li','',value));box.append(ul);}
  list('Gerekli malzemeler',g.materials);list('Adımlar',g.steps,true);list('Burada dur / yeniden değerlendir',g.stop);
  for(const s of g.details||[]){box.append(create('h3','guide-expansion-title',s.heading),create('p','guide-expansion-text',s.text));}
  box.append(create('div','warn','ÖNEMLİ: '+g.warning));const source=create('div','source-links');source.append(create('h3','','Kaynak ve durum'));
  for(const s of g.sources){const a=create('a','source-line',s.title+' ↗');a.href=s.url;a.rel='noopener noreferrer';a.target='_blank';source.append(a);}
  source.append(create('p','stamp','Kaynak, bu metnin uzman tarafından onaylandığı anlamına gelmez. Bağlantılar çevrimdışıyken açılamaz.'));
  const print=create('button','primary','YAZDIR');print.type='button';print.addEventListener('click',()=>window.print());source.append(print);box.append(source);$('guideDialog').showModal();}
 function render(){const q=lower($('guideSearch').value),cat=$('guideCategory').value,list=$('guideCards');list.replaceChildren();let found=0;
  for(const g of all){if(cat!=='all'&&g.category!==cat)continue;if(q&&!lower([g.title,g.summary,g.warning,...g.steps].join(' ')).includes(q))continue;
   const card=create('article','guide');const img=create('img');img.src=g.diagram;img.alt=g.title+' çizimi';img.loading='lazy';card.append(img);
   const body=create('div','guide-body');body.append(create('p','guide-meta',categories[g.category]),create('h2','',g.title),create('p','',g.summary),create('p','warning','! '+g.warning));const btn=create('button','','AYRINTIYI GÖR →');btn.type='button';btn.addEventListener('click',()=>detail(g));body.append(btn);card.append(body);list.append(card);found++;
  }
  $('visibleCount').textContent=found+' / '+all.length+' kart';if(!found)list.append(create('p','notice','Bu aramada kart bulunamadı.'));
 }
 async function init(){try{const r=await fetch('/assets/food-energy-winter.json');if(!r.ok)throw Error('HTTP '+r.status);const data=await r.json();if(!Array.isArray(data.cards))throw Error('Geçersiz katalog');all=data.cards; $('guideTotal').textContent=all.length;render();}
 catch(e){$('guideCards').append(create('p','alert','Katalog yüklenemedi: '+e.message));}}
 for(const name of ['food','energy','winter'])$(name+'Tab').addEventListener('click',()=>switchTab(name));
 $('foodForm').addEventListener('submit',e=>{e.preventDefault();foodDecision();});$('energyForm').addEventListener('submit',e=>{e.preventDefault();powerDecision();});$('winterForm').addEventListener('submit',e=>{e.preventDefault();winterDecision();});
 $('guideSearch').addEventListener('input',render);$('guideCategory').addEventListener('change',render);
 $('closeGuide').addEventListener('click',()=>$('guideDialog').close());$('guideDialog').addEventListener('click',e=>{if(e.target===$('guideDialog'))$('guideDialog').close()});
 init();if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
})();
