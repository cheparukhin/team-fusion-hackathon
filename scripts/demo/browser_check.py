"""Optional Playwright browser smoke test; install separately from runtime dependencies."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/demo/');page.wait_for_selector('#detail h2');assert 'Gsdmd' in page.locator('#detail h2').inner_text()
 assert page.locator('#candidate-list tr').count()==479
 assert 'RNA ON MATCHED COHORT' in page.locator('#detail').inner_text()
 expected_hic=page.evaluate('window.CHRNA_DATA.candidates.filter(c => c.score_hic != null).length')
 page.locator('#sort').select_option('score_hic');assert page.locator('#candidate-list tr').count()==expected_hic
 page.locator('#sort').select_option('score_rna')
 page.screenshot(path=str(ROOT/'results/demo/explorer_desktop.png'),full_page=True)
 page.locator('#search').fill('Psap:Lgals3');assert page.locator('#candidate-list tr').count()==1
 page.locator('.pair-button').click();assert 'Psap' in page.locator('#detail h2').inner_text();assert 'Not reported' in page.locator('#detail').inner_text()
 page.locator('#search').fill('no_such_candidate');assert page.locator('#empty').is_visible()
 page.locator('#search').fill('');page.locator('#label-filter').select_option('1');assert page.locator('#candidate-list tr').count()==109
 page.locator('[data-view=evaluation]').click();assert page.locator('#evaluation').is_visible();assert '0.296' in page.locator('#evaluation-content').inner_text()
 page.screenshot(path=str(ROOT/'results/demo/evaluation_desktop.png'),full_page=True)
 page.locator('[data-view=about]').click();assert page.locator('video').is_visible()
 assert 'Cached run status:' in page.locator('#nvidia-pilot').inner_text()
 page.screenshot(path=str(ROOT/'results/demo/methods_desktop.png'),full_page=True)
 page.locator('#nvidia-pilot').screenshot(path=str(ROOT/'results/demo/nvidia_pilot.png'))
 assert page.request.get('http://127.0.0.1:8000/results/classifier/MODEL_CARD.md').status==200
 page.set_viewport_size({'width':390,'height':844});page.locator('[data-view=explorer]').click();page.screenshot(path=str(ROOT/'results/demo/explorer_mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 page.goto((ROOT/'demo/index.html').as_uri());page.wait_for_selector('#detail h2');assert 'Gsdmd' in page.locator('#detail h2').inner_text()
 assert not errors,errors
 (ROOT/'results/demo/browser_validation.json').write_text(json.dumps({'status':'passed','browser':'Chromium via Playwright','checks':['479 real candidates','default Gsdmd selection','search and selection','empty search','109 reported-supported filter','evaluation metrics','methods and animation element','390px mobile without horizontal overflow','file:// offline loading','no browser JavaScript errors','Hi-C ranking includes observed scores only','matched-score detail card','model card source link resolves','actual NVIDIA status renders'],'javascript_errors':errors},indent=2))
 browser.close()
print('Browser validation passed')
