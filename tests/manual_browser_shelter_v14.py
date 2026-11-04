"""Chromium smoke UI for shelter & water using embedded local fixtures, no HTTP."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,base64
R=Path(__file__).resolve().parents[1];WEB=R/'web'
html=(WEB/'barinak-su.html').read_text('utf8')
css=(WEB/'assets/module.css').read_text('utf8')+'\n'+(WEB/'assets/shelter-water.css').read_text('utf8')
js=(WEB/'assets/shelter-water.js').read_text('utf8')
data=json.loads((WEB/'assets/shelter-water.json').read_text('utf8'))
for row in data['cards']:
    svg=(WEB/row['diagram'].lstrip('/')).read_bytes()
    row['diagram']='data:image/svg+xml;base64,'+base64.b64encode(svg).decode('ascii')
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','').replace('<link rel="stylesheet" href="/assets/shelter-water.css">','').replace('<script defer src="/assets/shelter-water.js"></script>','')
html=html.replace('</head>','<style>'+css+'</style></head>')
fixture='window.fetch=async ()=>({ok:true,json:async()=>('+json.dumps(data,ensure_ascii=False)+')});'
html=html.replace('</body>','<script>'+fixture+'</script><script>'+js+'</script></body>')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1260,'height':900},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='load')
    page.wait_for_function('document.querySelectorAll(".guide").length===18',timeout=10000)
    print('CARDS',page.locator('.guide').count())
    page.locator('#cardCategory').select_option('su')
    assert page.locator('.guide').count()==9
    page.locator('#cardCategory').select_option('barinak')
    assert page.locator('.guide').count()==9
    page.locator('#cardCategory').select_option('all')
    page.locator('#cardSearch').fill('kaynatma')
    assert page.locator('.guide').count()>=1
    page.locator('#cardSearch').fill('')
    page.locator('#shelterCheck button[type=submit]').click()
    assert 'BİLGİ EKSİK' in page.locator('#siteResult').inner_text()
    page.locator('[data-flag="sel"]').select_option('yes')
    page.locator('#shelterCheck button[type=submit]').click()
    assert 'DUR / ALTERNATİF YER ARA' in page.locator('#siteResult').inner_text()
    for v in page.locator('#shelterCheck [data-flag]').all():v.select_option('no')
    page.locator('#shelterCheck button[type=submit]').click()
    assert 'Bu, alanın güvenli' in page.locator('#siteResult').inner_text()
    page.locator('#waterTab').click()
    page.locator('#waterChemical').select_option('yes')
    page.locator('#waterCheck button[type=submit]').click()
    assert 'İÇME / YEMEKTE KULLANMA' in page.locator('#waterResult').inner_text()
    page.locator('#waterChemical').select_option('unknown')
    page.locator('#waterCheck button[type=submit]').click()
    assert 'BİLİNMEYEN KİRLİLİK' in page.locator('#waterResult').inner_text()
    page.locator('#waterChemical').select_option('no')
    page.locator('#waterOrigin').select_option('natural')
    page.locator('#waterBoil').select_option('yes')
    page.locator('#waterCloudy').select_option('yes')
    page.locator('#waterCheck button[type=submit]').click()
    assert '1 dakika' in page.locator('#waterResult').inner_text()
    assert 'SUYU İÇİLEBİLİR OLARAK ONAYLAMAZ' in page.locator('#waterResult').inner_text()
    page.locator('#waterBoil').select_option('no')
    page.locator('#waterCheck button[type=submit]').click()
    assert 'GÜVENLİLİK DOĞRULANMADI' in page.locator('#waterResult').inner_text()
    page.locator('#shelterTab').click()
    page.locator('.guide button').first.click()
    assert page.locator('#guideDialog').evaluate('(e)=>e.open') is True
    assert page.locator('#dialogContent li').count()>=8
    page.locator('#closeDialog').click()
    assert not errors,errors
    page.evaluate('document.querySelectorAll(".guide img").forEach(x=>x.loading="eager")')
    page.wait_for_function('Array.from(document.querySelectorAll(".guide img")).every(i=>i.complete&&i.naturalWidth>0)',timeout=10000)
    page.screenshot(path='/mnt/data/KALE-v1.4-Barinak-Su-Onizleme.png',full_page=True)
    print('BROWSER PASS: 18 cards, filters, risk rules, details, no JS errors')
    browser.close()
