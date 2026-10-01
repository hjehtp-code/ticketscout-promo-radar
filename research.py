"""Configured public research, robots-aware. Standard library only."""
import concurrent.futures
import json
import re
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent
UA = 'TicketScoutResearch/1.0'

class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip+=1
        if tag=='a': self.links.append(dict(attrs).get('href',''))
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self, text):
        if not self.skip and text.strip(): self.parts.append(text.strip())

def request(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':UA}),timeout=25) as r:
        return r.geturl(), r.read().decode('utf-8','replace')

robots={}
def fetch(url):
    origin=urlsplit(url).scheme+'://'+urlsplit(url).netloc
    try:
        if origin not in robots:
            _, body=request(origin+'/robots.txt')
            rp=urllib.robotparser.RobotFileParser();rp.parse(body.splitlines());robots[origin]=rp
        if not robots[origin].can_fetch(UA,url): return {'url':url,'status':'robots disallowed'}
        final,body=request(url)
        # Do not follow redirects outside configured host into unrelated sites.
        if urlsplit(final).netloc!=urlsplit(url).netloc: return {'url':url,'status':'off-host redirect','final':final}
        d=Document();d.feed(body)
        return {'url':url,'final':final,'status':'read','text':' '.join(d.parts),'links':list(dict.fromkeys(urljoin(final,x).split('#')[0] for x in d.links if x))}
    except Exception as e: return {'url':url,'status':'unreadable','error':str(e)}

def main():
    config=(ROOT/'.ilang/site.ilang').read_text(encoding='utf-8')
    section=re.search(r'::MODULE\{RESEARCH_SOURCES[^\n]*\}\s*(.*?)(?=\n::MODULE|\n::RULE|\Z)',config,re.S).group(1)
    sources=[tuple(x.strip() for x in line.split('|')) for line in section.splitlines() if '|' in line]
    result=[]
    for name,url in sources:
        page=fetch(url); page['source_name']=name;result.append(page)
    target=ROOT/'research';target.mkdir(exist_ok=True)
    (target/'discovery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for p in result:
        print(p['source_name'],p['status'],p.get('final',''))
        if p['source_name'] in ('Undercover Tourist','My Park Tickets','FunEx'):
            for u in p.get('links',[]):
                if urlsplit(u).netloc==urlsplit(p['url']).netloc and re.search(r'disney|universal|legoland|carowinds|six-flags|knotts|knott|blog|theme-park|shop',u,re.I): print(' LINK',u)

if __name__=='__main__':main()
