"""Read-only public-site audit; Python standard library only."""
import concurrent.futures
import json
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from build import load_config

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.text, self.images, self.scripts = [], [], [], []
        self.main = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main': self.main = True
        if tag == 'a': self.links.append(attrs.get('href', ''))
        if tag == 'img': self.images.append(attrs.get('src'))
        if tag == 'script' and attrs.get('src'): self.scripts.append(attrs['src'])
    def handle_endtag(self, tag):
        if tag == 'main': self.main = False
    def handle_data(self, data):
        if self.main and data.strip(): self.text.append(data.strip())

def fetch(url):
    start = time.perf_counter()
    try:
        response = subprocess.run(['curl.exe', '-sS', '--max-time', '20', '-w', '\n%{http_code}', url], capture_output=True, check=True)
        raw, status = response.stdout.rsplit(b'\n', 1)
        result = dict(url=url, status=int(status), bytes=len(raw), seconds=round(time.perf_counter()-start, 3))
        if b'<html' in raw:
            page = Page(); page.feed(raw.decode('utf-8'))
            result.update(main_text=' '.join(page.text), links=page.links, images=page.images, scripts=page.scripts)
        return result
    except Exception as exc:
        return dict(url=url, error=str(exc))

if __name__ == '__main__':
    import sys
    base = load_config()[0]['base_url']
    response = subprocess.run(['curl.exe', '-fsS', '--max-time', '20', base+'/sitemap.xml'], capture_output=True, check=True)
    tree = ET.fromstring(response.stdout)
    urls = {element.text for element in tree.findall('.//{*}loc')}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(fetch, sorted(urls)))
    links = {urljoin(page['url'], link) for page in pages for link in page.get('links', []) if link and not link.startswith('mailto:')}
    internal = {url for url in links if urlsplit(url).netloc == urlsplit(base).netloc}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        extra = list(pool.map(fetch, sorted(internal-urls)))
    result = dict(checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), pages=pages, extra_internal_links=extra,
                  note='HTTP timings are single requests from this machine, not browser paint or mobile-network measurements.')
    target = Path(sys.argv[1] if len(sys.argv)>1 else 'audit-before.json')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(pages=len(pages), failures=[p for p in pages+extra if p.get('status') != 200], extra_links=len(extra), report=str(target)), ensure_ascii=False))
