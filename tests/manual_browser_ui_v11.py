"""Render KALE v1.1 personal plan in sandboxed Chromium (no local HTTP)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'web/plan.html').read_text()
css=(ROOT/'web/assets/module.css').read_text()+'\n'+(ROOT/'web/assets/plan.css').read_text()
js=(ROOT/'web/assets/plan.js').read_text()
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','')
html=html.replace('<link rel="stylesheet" href="/assets/plan.css">','')
html=html.replace('<script defer src="/assets/plan.js"></script>','')
html=html.replace('</head>',f'<style>{css}</style><script>{js}</script></head>')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1100,'height':820},accept_downloads=True)
 errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
 page.set_content(html,wait_until='load')
 assert page.locator('.task-row').count()==24
 assert '0 / 24' in page.locator('#progress').inner_text()
 page.locator('#water').fill('30')
 page.locator('#water').dispatch_event('change')
 assert '3,3 günlük' in page.locator('#waterCalc').inner_text()
 page.locator('#people').fill('4')
 page.locator('#people').dispatch_event('change')
 assert '2,5 günlük' in page.locator('#waterCalc').inner_text()
 page.locator('.task-row input').first.check()
 assert '1 / 24' in page.locator('#progress').inner_text()
 page.locator('[data-stage="ilk"]').click()
 assert page.locator('.task-row').count()==6
 page.locator('[data-stage="all"]').click()
 assert page.locator('.task-row').count()==24
 with page.expect_download() as dl:page.locator('#downloadPlan').click()
 assert dl.value.suggested_filename=='KALE-72-saat-plan-yedek.json'
 assert not errors,errors
 print('Chromium UI: 24 görev, hesap, seçim, filtre ve JSON indirme OK')
 # Render screenshot only for QA.
 page.screenshot(path='/mnt/data/KALE-v1.1-plan-preview.png',full_page=True)
 b.close()
