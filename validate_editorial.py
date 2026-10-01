"""Verify release invariants for independently authored static guides."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
ALLOWED = {'disneyland tickets discount', 'cheap disneyland tickets',
           'costco universal studios tickets', 'legoland ticket',
           'carowinds tickets', 'six flags tickets', "knott's berry farm tickets"}

def main():
    guides = json.loads((ROOT/'content/guides.json').read_text(encoding='utf-8'))
    sitemap = ET.parse(ROOT/'site/sitemap.xml')
    urls = {node.text for node in sitemap.findall('.//{*}loc')}
    gaps = set()
    for guide in guides:
        assert guide['target_keyword'] in ALLOWED, 'Unapproved target'
        assert guide['gap_id'] not in gaps, 'Duplicate gap'
        gaps.add(guide['gap_id'])
        path = 'guides/' + guide['slug'] + '/'
        page = (ROOT/'site'/path/'index.html').read_text(encoding='utf-8')
        assert any(urlparse(u).path == '/' + path for u in urls), 'Missing from sitemap'
        assert page.index('class="answer"') < page.index('<h2'), 'Answer must precede sections'
        assert not re.search('[\u4e00-\u9fff]', guide['title'] + guide['answer'] + guide['body_html']), 'Chinese source trace'
        for asset in re.findall(r'<img[^>]+src="([^"]+)"', page):
            assert (ROOT/'site'/asset.lstrip('/')).is_file(), 'Missing diagram: ' + asset
        assert '<h2' in page and re.search(r'<a[^>]+href="https://', guide['body_html']), 'Missing sections/source'
        from build import load_config
        measurement_id = load_config()[0].get('ga4_measurement_id', '').strip()
        if measurement_id:
            assert page.count('gtag/js?id=' + measurement_id) == 1, 'Missing or duplicate measurement tag'
    print(f'Validated {len(guides)} guides: approved targets, unique gaps, answer order, assets and sitemap')

if __name__ == '__main__':
    main()
