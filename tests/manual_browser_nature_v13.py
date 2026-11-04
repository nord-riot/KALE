"""Browser smoke with local catalog responses; does not claim offline real-device verification."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
web=root/'web'
html=(web/'doga.html').read_text('utf8')
css=(web/'assets/module.css').read_text('utf8')+'\n'+(web/'assets/nature.css').read_text('utf8')
js=(web/'assets/nature.js').read_text('utf8')
plants=json.loads((web/'assets/poisonous-plants.json').read_text('utf8'))
mushrooms=json.loads((web/'assets/dangerous-mushrooms.json').read_text('utf8'))
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','').replace('<link rel="stylesheet" href="/assets/nature.css">','').replace('<script src="/assets/nature.js" defer></script>','')
html=html.replace('</head>',f'<style>{css}</style></head>')
mock='''<script>window.fetch=async (url)=>({ok:true,json:async ()=>url.includes('dangerous-mushrooms.json')?__M__:__P__});</script>'''
mock=mock.replace('__M__',json.dumps(mushrooms,ensure_ascii=False)).replace('__P__',json.dumps(plants,ensure_ascii=False))
html=html.replace('</body>',mock+'<script>'+js+'</script></body>')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':900})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='load')
    page.wait_for_function("document.querySelectorAll('.nature-card').length===44",timeout=10000)
    assert page.locator('.nature-card').count()==44
    assert page.locator('#plantCount').inner_text()=='28'
    assert page.locator('#mushCount').inner_text()=='16'
    page.locator('#natureType').select_option('mantar')
    assert page.locator('.nature-card').count()==16
    page.locator('#natureSearch').fill('Amanita')
    assert page.locator('.nature-card').count()>=3
    page.locator('#natureType').select_option('')
    page.locator('#natureSearch').fill('zakkum')
    assert page.locator('.nature-card').count()==1
    page.locator('#natureSearch').fill('')
    page.locator('#natureRisk').select_option('böbrek')
    assert page.locator('.nature-card').count()>0
    page.locator('#natureRisk').select_option('')
    assert not errors,errors
    page.screenshot(path='/mnt/data/KALE-v1.3-doga-onizleme.png',full_page=True)
    print('Chromium UI OK: 44 records, category filter, search, risk filter, zero JS errors')
    browser.close()
