"""Chromium UI smoke with offline API/local-storage fixtures (no real server)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
html=(WEB/'atolye.html').read_text('utf-8')
css=(WEB/'assets/module.css').read_text('utf-8')+'\n'+(WEB/'assets/editor.css').read_text('utf-8')
js=(WEB/'assets/editor.js').read_text('utf-8')
catalog=(ROOT/'data/content.json').read_text('utf-8')
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','').replace('<link rel="stylesheet" href="/assets/editor.css">','').replace('<script defer src="/assets/editor.js"></script>','')
html=html.replace('</head>',f'<style>{css}</style></head>')
fixture='''<script>
const __kaleStore={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>__kaleStore[k]||null,setItem:(k,v)=>{__kaleStore[k]=v;},removeItem:k=>{delete __kaleStore[k];}}});
window.fetch=async ()=>({ok:true,json:async()=>(__KALE_CATALOG__)});
</script>'''.replace('__KALE_CATALOG__',catalog)
html=html.replace('</body>',fixture+'<script>'+js+'</script></body>')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='load')
 print('ERRORS BEFORE',errors,'MESSAGE',page.locator('#message').inner_text() if page.locator('#message').count() else 'none','HTML',len(page.content()));page.wait_for_selector('.editor-item',timeout=5000)
 assert page.locator('.editor-item').count()==146
 page.locator('#newBtn').click()
 page.locator('#title').fill('Ekipman deneme rehberi')
 page.locator('#body').fill('Malzemeler güvenli ve temiz biçimde kontrol edilmelidir. Kaynaklar ve güvenlik önlemleri her zaman araştırılmalıdır.')
 page.locator('#warning').fill('Bu kaydın uzman onayı yoktur.')
 page.locator('#sources').fill('https://www.afad.gov.tr/')
 page.locator('#editForm button[type=submit]').click()
 assert 'Taslak kaydedildi' in page.locator('#message').inner_text(),page.locator('#message').inner_text()
 assert page.locator('.editor-item').count()==147
 with page.expect_download() as dl:page.locator('#exportBtn').click()
 assert dl.value.suggested_filename=='KALE-rehber-duzenleme.json'
 payload=json.loads(dl.value.path().read_text('utf-8'))
 assert len(payload['entries'])==147
 assert payload['entries'][-1]['review_status']=='taslak—uzman onayı bekliyor'
 assert not errors,errors
 print('Chromium UI smoke OK: 146 list, add, save, local-storage fixture, 147-record JSON export')
 page.screenshot(path='/mnt/data/KALE-v1.2-atolye-preview.png',full_page=True)
 b.close()
