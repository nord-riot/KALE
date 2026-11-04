"""Standalone Chromium first aid GUI smoke using embedded JSON/SVG, no network or patient data."""
import json,base64
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web'
html=(WEB/'ilk-yardim.html').read_text('utf-8')
css=(WEB/'assets/module.css').read_text('utf-8')+'\n'+(WEB/'assets/first-aid.css').read_text('utf-8')
js=(WEB/'assets/first-aid.js').read_text('utf-8')
data=json.loads((WEB/'assets/first-aid.json').read_text('utf-8'))
for x in data['cards']:
 png=(WEB/x['diagram'].lstrip('/')).read_bytes()
 x['diagram']='data:image/svg+xml;base64,'+base64.b64encode(png).decode()
for uri in ('/assets/module.css','/assets/first-aid.css'):
 html=html.replace(f'<link rel="stylesheet" href="{uri}">','')
html=html.replace('<script defer src="/assets/first-aid.js"></script>','')
html=html.replace('</head>',f'<style>{css}</style></head>')
fixture='window.fetch=async ()=>({ok:true,json:async()=>('+json.dumps(data,ensure_ascii=False)+')});'
html=html.replace('</body>','<script>'+fixture+'</script><script>'+js+'</script></body>')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1280,'height':880},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='load')
 page.wait_for_function('document.querySelectorAll(".aid-card").length===24',timeout=10000)
 assert page.locator('.aid-card').count()==24
 assert '24 / 24' in page.locator('#aidCount').inner_text()
 assert page.locator('a[href="tel:112"]').count()>=1
 assert page.locator('a[href="tel:114"]').count()>=1
 cats=page.locator('#aidCategory option').count()
 assert cats>=5,cats
 page.select_option('#aidCategory','Zehirlenme')
 assert page.locator('.aid-card').count()==4,page.locator('#aidCount').inner_text()
 page.select_option('#aidCategory','all')
 page.fill('#aidSearch','kanama')
 assert page.locator('.aid-card').count()>=2
 page.fill('#aidSearch','')
 page.select_option('#aidUrgency','112 HEMEN')
 assert page.locator('.aid-card').count()>=10
 page.select_option('#aidUrgency','all')
 page.locator('button[data-jump="KALE-AY-01"]').click()
 assert page.locator('#aidDialog').evaluate('(el)=>el.open') is True
 detail=page.locator('#aidDetail').inner_text()
 assert '100–120' in detail and '112' in detail and 'Uzman' not in detail[:20]
 assert page.locator('#aidDetail a[href="tel:112"]').count()==1
 assert page.locator('#aidDetail .aid-source-list a').count()>=2
 page.locator('#closeAid').click()
 assert page.locator('#aidDialog').evaluate('(el)=>el.open') is False
 page.fill('#aidSearch','mantar')
 assert page.locator('.aid-card').count()>=1
 page.fill('#aidSearch','')
 page.wait_for_function('Array.from(document.querySelectorAll(".aid-card img")).every(i=>i.complete&&i.naturalWidth>0)',timeout=10000)
 page.evaluate('window.scrollTo(0,0)')
 page.screenshot(path='/mnt/data/KALE-v1.7-Ilk-Yardim-Onizleme.png',full_page=False)
 assert not errors,errors
 print('CHROMIUM OK: 24 kart, kategori filtreleri, arama, 112/114 linkleri, hızlı geçiş, kaynak bağlantıları, 24 SVG ve diyalog', 'errors=',errors)
 browser.close()
