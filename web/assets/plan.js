'use strict';
/* KALE v1.1: all personal data stays in browser localStorage, never uploaded. */
(()=>{
 const $=id=>document.getElementById(id), KEY='kale_plan_v11';
 const groups=[
  {id:'once',name:'Afetten önce',note:'Hazırlıkları mümkünse ailece, sakince tamamlayın.',tasks:[
   ['evriski','Evin ve çevrenin risklerini değerlendir','Yapısal riskler için yetkin uzmanlardan destek alın; ağır eşyaları güvenli sabitleyin.'],
   ['toplanma','Buluşma ve iletişim planı oluştur','Birbirinizden ayrı düşerseniz nerede buluşacağınızı ve alternatif irtibatı belirleyin.'],
   ['canta','Afet çantasını hazırla','Mevsimlik giysi, ışık, pil, temel hijyen ve kişisel ihtiyaçları gözden geçirin.'],
   ['su','Güvenli su stoğunu kontrol et','İçilebilir suyu uygun kaplarda saklayın; hijyen ve özel gereksinimleri de düşünün.'],
   ['gida','Dayanıklı erzak ve açacak ayır','Son kullanma tarihlerini kontrol edin; alerji ve özel beslenme ihtiyaçlarını düşünün.'],
   ['ilac','Kişisel ilaç ve sağlık bilgilerini hazırla','Düzenli reçeteler, önemli alerji bilgileri ve gerekli tıbbi malzemeleri hekim önerisiyle planlayın.']
  ]},
  {id:'ilk',name:'İlk dakikalar',note:'Her afetin güvenli davranışı farklıdır. Tehlikenin türüne uygun resmî yönergeleri izleyin.',tasks:[
   ['tehlike','Önce mevcut tehlikeyi değerlendir','Düşen parçalar, yangın, gaz kokusu, su baskını veya hasarlı yapılar gibi riskleri gözleyin.'],
   ['guvenlik','Güvenli konuma geç','Afet türüne uygun korunma ve tahliye talimatlarına uyun; hasarlı binalara girmeyin.'],
   ['yarali','Acil yardıma ihtiyacı olan var mı bak','Kendinizi riske atmadan kontrol edin; acil durumlarda 112’yi arayın.'],
   ['112','Gerekiyorsa 112’ye bilgi ver','Konumunuzu, olay türünü ve yardım ihtiyacını mümkün olduğunca açık aktarın.'],
   ['bilgi','Resmî duyuruları takip et','Teyitsiz bilgi yaymayın, güvenilir haberleşme kanallarını kullanın.'],
   ['aile','Aile üyelerinin durumunu teyit et','Önceden belirlenen güvenli buluşma ve irtibat planını kullanın.']
  ]},
  {id:'gun',name:'İlk 24 saat',note:'Temel ihtiyaçları, güvenli çevreyi ve iletişimi düzenleyin.',tasks:[
   ['barinak','Güvenli barınma seçeneğini belirle','Tahliye ve toplanma alanları için resmî yönlendirmeleri esas alın.'],
   ['icme','İçme suyu güvenliğini kontrol et','Su kaynağı şüpheliyse güvenli olduğunu varsaymayın; KALE su rehberine bakın.'],
   ['stok','Erzak ve temel malzeme envanteri çıkar','Kişi sayısını ve özel ihtiyaçları hesaba katarak kullanılabilir stokları kaydedin.'],
   ['hijyen','Tuvalet ve hijyen düzeni planla','Atık ve kirli suyun içme suyu ve yiyecekleri kirletmesini önleyin.'],
   ['sarj','Enerji ve iletişim kaynaklarını tasarruflu kullan','Telefon, radyo ve aydınlatma için öncelik belirleyin.'],
   ['not','Önemli gelişmeleri ve ihtiyaçları not al','Yardım taleplerini, güvenilir duyuruları ve mevcut kaynakları kaydedin.']
  ]},
  {id:'ucgun',name:'24–72 saat',note:'Koşullar değiştikçe durumu yeniden değerlendirin.',tasks:[
   ['suplan','Su tüketimini yeniden hesapla','Günlük içme suyu, hijyen ve kişisel sağlık ihtiyaçlarına göre planınızı güncelleyin.'],
   ['gida_plan','Gıda stokunu yeniden değerlendir','Bozulmuş, şüpheli veya güvenliği belirsiz gıdaları tüketmeyin.'],
   ['konum','Güvenli barınma durumunu yeniden kontrol et','Hava koşullarını ve resmî tahliye uyarılarını takip edin.'],
   ['ilac_durum','Sağlık ve ilaç ihtiyaçlarını yeniden kontrol et','Gereken tedaviyi kendiniz değiştirmeyin; uygun sağlık desteği arayın.'],
   ['yardim','Resmî yardım ve bilgilendirme kanallarını takip et','Yerel ihtiyaçlar ve yardım dağıtımı için doğrulanmış bilgi kullanın.'],
   ['yedek','Planın kâğıt/dosya yedeğini ayır','Tarayıcı verileri silinebilir. İrtibat ve buluşma bilgilerini ayrıca saklayın.']
  ]}
 ];
 const ALL=new Set(groups.flatMap(g=>g.tasks.map(t=>t[0])));
 const initial=()=>({people:3,water:0,daily:3,meeting:'',contact:'',checks:{}});
 let state=initial(),stage='all';
 function valid(obj){
  if(!obj||typeof obj!=='object'||Array.isArray(obj))throw Error('Geçersiz veri');
  const p=Number(obj.people),w=Number(obj.water),d=Number(obj.daily);
  if(!Number.isInteger(p)||p<1||p>30||!Number.isFinite(w)||w<0||w>100000||!Number.isFinite(d)||d<.5||d>20)throw Error('Geçersiz miktar');
  if(typeof obj.meeting!=='string'||obj.meeting.length>140||typeof obj.contact!=='string'||obj.contact.length>160)throw Error('Geçersiz not');
  if(!obj.checks||typeof obj.checks!=='object'||Array.isArray(obj.checks))throw Error('Geçersiz işaretleme');
  const checks={};for(const [key,val] of Object.entries(obj.checks)){if(!ALL.has(key)||typeof val!=='boolean')throw Error('Geçersiz görev');if(val)checks[key]=true;}
  return {people:p,water:w,daily:d,meeting:obj.meeting,contact:obj.contact,checks};
 }
 try{const s=localStorage.getItem(KEY);if(s)state=valid(JSON.parse(s));}catch{state=initial();}
 const elem=(tag,cls,value)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(value!==undefined)e.textContent=value;return e};
 function persist(){try{localStorage.setItem(KEY,JSON.stringify(state));$('storageState').textContent='Veriler bu tarayıcıya kaydedildi. Ayrı bir JSON/kâğıt yedeği önerilir.';}catch{$('storageState').textContent='Tarayıcıya kayıt yapılamadı! Lütfen planı yazdırın.';}}
 function calc(){const days=state.water/(state.people*state.daily);const f=n=>new Intl.NumberFormat('tr-TR',{maximumFractionDigits:1}).format(n);
  $('waterCalc').textContent=`Örnek: ${f(state.people*state.daily)} L/gün · Mevcut stok yaklaşık ${f(days)} günlük içme suyu (${f(state.water)} L).`;
  const marked=Object.values(state.checks).filter(Boolean).length;$('progress').textContent=`${marked} / ${ALL.size} görev işaretlendi`;$('progressFill').style.width=(100*marked/ALL.size).toFixed(1)+'%';
 }
 function render(){const list=$('taskList');list.replaceChildren();for(const group of groups){if(stage!=='all'&&stage!==group.id)continue;
   const p=elem('section','task-panel');p.append(elem('div','eyebrow','KALE / '+group.name.toLocaleUpperCase('tr-TR')),elem('h2','',group.name),elem('p','',group.note));
   for(const [key,title,detail] of group.tasks){const row=elem('label','task-row'),check=document.createElement('input');check.type='checkbox';check.checked=state.checks[key]===true;check.dataset.task=key;check.addEventListener('change',()=>{state.checks[key]=check.checked;persist();calc();});const text=elem('span');text.append(elem('strong','',title),elem('small','',detail));row.append(check,text);p.append(row);}list.append(p);
  }calc();
 }
 function syncFields(){for(const id of ['people','water','daily','meeting','contact'])$(id).value=state[id];}
 function download(){const blob=new Blob([JSON.stringify({format:'KALE-PLAN-1.1',exported_at:new Date().toISOString(),...state},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='KALE-72-saat-plan-yedek.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
 document.addEventListener('DOMContentLoaded',()=>{
  syncFields();render();
  for(const id of ['people','water','daily','meeting','contact'])$(id).addEventListener('change',()=>{const next={...state,[id]:['people','water','daily'].includes(id)?Number($(id).value):$(id).value.trim()};try{state=valid(next);persist();calc();}catch{alert('Geçersiz değer. Lütfen düzeltin.');syncFields();}});
  document.querySelectorAll('[data-stage]').forEach(b=>b.addEventListener('click',()=>{stage=b.dataset.stage;document.querySelectorAll('[data-stage]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});render();}));
  $('printPlan').addEventListener('click',()=>{stage='all';render();window.print();});
  $('downloadPlan').addEventListener('click',download);
  $('clearPlan').addEventListener('click',()=>{if(confirm('İşaretlenen görevleri temizleyelim mi?')){state.checks={};persist();render();}});
  $('uploadPlan').addEventListener('change',async ev=>{const file=ev.target.files?.[0];if(!file)return;try{if(file.size>100000)throw Error('Yedek 100 KB sınırını aşıyor');const raw=JSON.parse(await file.text());if(raw.format!=='KALE-PLAN-1.1')throw Error('Uyumsuz yedek');const next=valid(raw);if(confirm('Mevcut planın üzerine yazılsın mı?')){state=next;syncFields();persist();render();}}catch(e){alert('Yedek yüklenemedi: '+e.message);}finally{ev.target.value='';}});
 });
})();
