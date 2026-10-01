"""Build evidence-backed editorial pages from durable sources; standard library."""
import html
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def render_guides(out,base,layout):
    source=ROOT/'content'/'guides.json'
    guides=json.loads(source.read_text(encoding='utf-8')) if source.exists() else []
    entries=[]
    assets=ROOT/'content'/'assets'
    if assets.exists(): shutil.copytree(assets,out/'assets',dirs_exist_ok=True)
    cards=[]
    for g in guides:
        path='guides/'+g['slug']+'/'
        body='<article class="guide"><p class="eyebrow">Ticket guide</p><h1>'+html.escape(g['title'])+'</h1><p class="answer">'+html.escape(g['answer'])+'</p><p class="source">Checked '+html.escape(g['checked_at'])+' · '+html.escape(g['scope'])+'</p>'+g['body_html']+'</article>'
        dest=out/path;dest.mkdir(parents=True,exist_ok=True)
        schema={'@context':'https://schema.org','@type':'Article','headline':g['title'],'datePublished':g['published_at'],'dateModified':g['checked_at'],'author':{'@type':'Organization','name':'TicketScout'}}
        (dest/'index.html').write_text(layout(g['title'],g['answer'],base.rstrip('/')+'/'+path,body,schema),encoding='utf-8')
        entries.append({'path':path,'title':g['title'],'answer':g['answer']})
        cards.append('<article class="card"><h2><a href="/'+path+'">'+html.escape(g['title'])+'</a></h2><p>'+html.escape(g['answer'])+'</p></article>')
    dest=out/'guides';dest.mkdir(exist_ok=True)
    (dest/'index.html').write_text(layout('Ticket guides','Official-source ticket guides and practical comparisons.',base.rstrip('/')+'/guides/','<h1>Ticket guides</h1>'+(''.join(cards) or '<p>No guides published yet.</p>')),encoding='utf-8')
    entries.append({'path':'guides/','title':'Ticket guides'})
    return entries
