# ::ILANG [TYPE:file][PROJECT:TicketScout]
# ::STATE{@ROLE, responsibility:Render static pages and indexes from configuration and verified offer data}
# ::RULE{Read .ilang/site.ilang and data/offers.json; never fabricate commercial facts}
# ::BOUNDARY{never:render an unverified price or discount|scope:permanent}
"""Build a static, data-driven attraction discount directory."""
from __future__ import annotations

import html
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent


def load_config():
    text = (ROOT / ".ilang" / "site.ilang").read_text(encoding="utf-8")
    match = re.search(r"::STATE\{@SITE,(.*?)\}", text, re.S)
    if not match:
        raise ValueError("Missing @SITE state")
    site = dict(re.findall(r"([\w_]+):\s*([^,]+)", match.group(1)))
    providers = []
    section = re.search(r"::MODULE\{PROVIDERS[^\n]*\}\s*(.*?)(?=\n::MODULE|\Z)", text, re.S)
    for line in (section.group(1) if section else "").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 3 and parts[0]:
            providers.append({"name": parts[0], "url": parts[1], "source": parts[2], "affiliate": parts[3] if len(parts) > 3 else ""})
    return site, providers


def esc(value):
    return html.escape(str(value), quote=True)


def canonical(base, path=""):
    return base.rstrip("/") + "/" + path.lstrip("/")


def layout(title, description, canonical_url, body, jsonld=None):
    site, providers = load_config()
    brand = esc(site.get('brand', 'TicketScout'))
    if site.get('brand', 'TicketScout') not in title:
        title = f"{title} | {site.get('brand', 'TicketScout')}"
    style_version = hashlib.sha256(CSS.encode('utf-8')).hexdigest()[:12]
    disclosure = '<p>Some provider links are affiliate links. We may earn a commission from purchases through those links.</p>' if any(p.get('affiliate') for p in providers) else ''
    schema = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    measurement_id = site.get('ga4_measurement_id', '').strip()
    if measurement_id and not re.fullmatch(r'G-[A-Z0-9]+', measurement_id):
        raise ValueError('Invalid configured GA4 measurement ID')
    analytics = f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}', {{'allow_google_signals': false, 'allow_ad_personalization_signals': false}});
</script>''' if measurement_id else ''
    return f'''<!doctype html>
<html lang="en-US"><head>{analytics}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(canonical_url)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical_url)}"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/styles.css?v={style_version}">{schema}</head><body><header><a class="brand" href="/">{brand}</a><nav aria-label="Main navigation"><a href="/guides/">Guides</a><a href="/providers/">Providers</a><a href="/compare/">Compare</a></nav></header><main>{body}</main><footer><p>{brand} — attraction and theme-park ticket offers.</p><p>Offers are included only when a current discount is evidenced by the official source. Prices and availability can change; confirm details with the provider.</p>{disclosure}<nav class="footer-links" aria-label="Footer"><a href="/about/">About</a><a href="/privacy/">Privacy</a><a href="/contact/">Contact</a><a href="/sitemap.xml">Sitemap</a></nav></footer></body></html>'''


def static_pages(out, base, site):
    contact_email = site.get("contact_email", "").strip()
    operator = site.get("operator", "").strip()
    operator_line = f'<p>TicketScout is created and maintained by {esc(operator)}.</p>' if operator else ''
    contact = (f'<a href="mailto:{esc(contact_email)}">{esc(contact_email)}</a>' if contact_email
               else "A dedicated site contact email has not been configured yet.")
    analytics_privacy = '<h2>Google Analytics 4</h2><p>TicketScout uses Google Analytics 4 to measure visits, page views and website interactions. Google Analytics uses cookies and processes information such as page URLs, browser and device details and approximate location. Advertising personalization and Google signals are disabled in our site tag. We do not send names, email addresses or ticket payment information to Google Analytics.</p><p>Read <a href="https://policies.google.com/technologies/partner-sites">how Google uses information from sites that use its services</a> and the <a href="https://policies.google.com/privacy">Google Privacy Policy</a>. You can use the <a href="https://tools.google.com/dlpage/gaoptout">Google Analytics opt-out browser add-on</a> or browser privacy controls to limit collection.</p>' if site.get('ga4_measurement_id') else ''
    pages = {
        "about": (
            "About TicketScout",
            "How TicketScout selects and presents attraction and theme park ticket offers.",
            '<h1>About TicketScout</h1>' + operator_line + '<p>TicketScout is a directory of attraction and theme park ticket offers checked against public official sources.</p><p>An offer is listed only when the official source provides evidence of a current discount and a ticket price. Each offer links to the source so visitors can confirm its terms, dates, availability and final price with the provider.</p><p>TicketScout does not sell tickets or process ticket payments. Offer details can change; the provider’s current terms apply.</p>',
        ),
        "privacy": (
            "Privacy | TicketScout",
            "Privacy information for visitors to the static TicketScout website.",
            f'<h1>Privacy</h1><p>Last updated: {date.today():%B %d, %Y}</p><p>TicketScout is a static information site. It does not provide visitor accounts, ticket checkout, newsletter subscriptions, or a contact form. The live site includes Cloudflare Web Analytics, which Cloudflare documents as collecting page-performance metrics through browser performance APIs without cookies or personal visitor data. See <a href="https://developers.cloudflare.com/web-analytics/about/">Cloudflare Web Analytics</a> and the <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare Privacy Policy</a> for details.</p>{analytics_privacy}<h2>Third-party advertising</h2><p>No advertising network code is currently installed in the site source. Before enabling advertisements, this policy will identify the network and its actual data collection and privacy choices.</p><h2>Hosting and external links</h2><p>When you request a page, the hosting and network services that deliver and protect this site may process technical request information, such as an IP address, requested URL, browser details and request time.</p><p>Offer links take you to attraction providers’ websites. Those sites have their own privacy practices, which apply when you visit them. TicketScout does not control those sites.</p><p>For a privacy question about TicketScout, contact: {contact}</p>',
        ),
        "contact": (
            "Contact | TicketScout",
            "Contact TicketScout about site content or privacy questions.",
            f'<h1>Contact TicketScout</h1><p>For a question about a ticket offer, check its official source linked on the offer page; the attraction provider can confirm current terms, availability and checkout price.</p><p>For a correction to TicketScout or a privacy question, email: {contact}</p>',
        ),
    }
    entries = []
    for slug, (title, description, body) in pages.items():
        path = f"{slug}/"
        directory = out / path
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(layout(title, description, canonical(base, path), body), encoding="utf-8")
        entries.append({"path": path, "title": title})
    not_found = '<h1>Page not found</h1><p>We could not find that page. Check the address or return to the <a href="/">TicketScout home page</a>.</p>'
    (out / "404.html").write_text(layout("Page not found | TicketScout", "The requested TicketScout page could not be found.", canonical(base, "404.html"), not_found), encoding="utf-8")
    return entries


def item_list(entries, base):
    return {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": canonical(base, entry["path"])} for i, entry in enumerate(entries, 1)
    ]}


def main():
    site, providers = load_config()
    brand = site.get("brand", "TicketScout")
    base = site.get("base_url", "https://ticket-scout.pages.dev")
    data_file = ROOT / "data" / "offers.json"
    data = json.loads(data_file.read_text(encoding="utf-8")) if data_file.exists() else {"fetched_at": "", "offers": []}
    offers = [o for o in data.get("offers", []) if not o.get("valid_until") or o["valid_until"] >= date.today().isoformat()]
    out = ROOT / "site"
    out.mkdir(exist_ok=True)
    # Remove stale generated pages while keeping the source tree untouched.
    for path in out.rglob("*"):
        if path.is_file():
            path.unlink()
    entries = []
    provider_cards = []
    for provider in providers:
        matches = [o for o in offers if o.get("provider_id") == provider["name"].lower()]
        slug = re.sub(r"[^a-z0-9]+", "-", provider["name"].lower()).strip("-")
        path = f"providers/{slug}/"
        provider_dir = out / path
        provider_dir.mkdir(parents=True, exist_ok=True)
        cards = "".join(offer_card(o, f"/deals/{deal_slug(o)}/") for o in matches)
        status = f"{len(matches)} verified offer{'s' if len(matches) != 1 else ''} currently listed." if matches else "No verified discount offers are available from this provider right now."
        body = f'<p class="eyebrow">Provider</p><h1>{esc(provider["name"])}</h1><p>{esc(status)}</p><p><a class="button" href="{esc(provider["url"])}" rel="nofollow">Visit official website</a></p><p class="source">Public source: <a href="{esc(provider["source"])}">{esc(provider["source"])}</a></p>{cards or ""}'
        schema = {"@context": "https://schema.org", "@type": "Service", "name": provider["name"], "url": canonical(base, path), "provider": {"@type": "Organization", "name": provider["name"], "url": provider["url"]}}
        priced = [o for o in matches if "price" in o and o.get("currency")]
        if priced:
            vals = [float(o["price"]) for o in priced]
            schema["offers"] = {"@type": "AggregateOffer", "lowPrice": min(vals), "highPrice": max(vals), "priceCurrency": priced[0]["currency"], "offerCount": len(priced)}
        (provider_dir / "index.html").write_text(layout(f"{provider['name']} ticket discounts | {date.today():%B %Y} | {brand}", status, canonical(base, path), body, schema), encoding="utf-8")
        provider_cards.append(f'<article class="card"><h2><a href="/{path}">{esc(provider["name"])}</a></h2><p>{esc(status)}</p></article>')
        entries.append({"path": path, "title": provider["name"]})
    deal_cards = []
    for offer in offers:
        slug = deal_slug(offer)
        path = f"deals/{slug}/"
        deal_dir = out / path
        deal_dir.mkdir(parents=True, exist_ok=True)
        price_line = f'<p class="price">{esc(offer["currency"])} {esc(offer["price"])}</p>' if "price" in offer and offer.get("currency") else ""
        if offer.get("discount_percent") is not None:
            desc = f"{offer.get('provider', 'Provider')} lists a verified {offer['discount_percent']}% discount for {offer.get('product_name')} at the official source."
            discount_line = f'<p class="discount">{esc(offer["discount_percent"])}% off</p>'
        else:
            desc = f"{offer.get('provider', 'Provider')} lists an official online advance ticket price for {offer.get('product_name')}. The source describes an online advance discount without stating an exact percentage."
            discount_line = f'<p class="discount">{esc(offer.get("discount_label", "Official discount"))}</p>'
        body = f'<p class="eyebrow">Verified ticket discount</p><h1>{esc(offer.get("title", "Verified discount"))}</h1><p>{esc(desc)}</p>{discount_line}{price_line}<p>Source checked: {esc(offer.get("fetched_at", ""))}</p><p><a class="button" href="{esc(offer.get("offer_url", offer.get("source_url", "")))}" rel="nofollow">Check offer at official source</a></p><p class="source">Source: <a href="{esc(offer.get("source_url", ""))}">{esc(offer.get("provider", "official provider"))}</a></p>'
        schema = {"@context": "https://schema.org", "@type": "Offer", "url": offer.get("offer_url") or canonical(base, path)}
        if offer.get("availability"):
            schema["availability"] = offer["availability"]
        if "price" in offer and offer.get("currency"):
            schema.update({"price": offer["price"], "priceCurrency": offer["currency"]})
        if offer.get("valid_until"):
            schema["priceValidUntil"] = offer["valid_until"]
        deal_title = f"{offer['provider']} {offer['discount_percent']}% off" if offer.get("discount_percent") is not None else f"{offer['provider']} online advance ticket offer"
        (deal_dir / "index.html").write_text(layout(f"{deal_title} | {date.today():%B %Y}", desc, canonical(base, path), body, schema), encoding="utf-8")
        deal_cards.append(offer_card(offer, f"/{path}"))
        entries.append({"path": path, "title": offer.get("title", "Verified offer")})
    entries.extend(static_pages(out, base, site))
    from editorial import render_guides
    guides = render_guides(out, base, layout)
    entries.extend(guides)
    state_line = f'<p class="meta">Last source check: {esc(data.get("fetched_at") or "No completed fetch yet")}</p>'
    hero = f'<section class="hero"><p class="eyebrow">TicketScout · Official sources</p><h1>Find verified ticket discounts</h1><p>Compare evidenced offers, then confirm your ticket with the provider.</p><p class="stats">{len(offers)} verified offers · {len(providers)} providers</p><a class="button" href="#offers">Browse offers</a> <a class="button secondary" href="/guides/">Read ticket guides</a>{state_line}</section>'
    empty = '<section class="empty"><h2>No verified discounts at the moment</h2><p>We could not confirm a current discount from the configured official provider. Visit the provider for standard ticket options and availability.</p></section>' if not offers else ""
    guide_cards = ''.join(f'<article class="card"><h2><a href="/{e["path"]}">{esc(e["title"])}</a></h2><p>{esc(e.get("answer", ""))}</p></article>' for e in guides if e['path'] != 'guides/')
    home_body = hero + empty + '<section id="offers"><h2>Current offers</h2><div class="cards-grid">' + ("".join(deal_cards) if deal_cards else '<p class="muted">No deals meet our verification rules yet.</p>') + '</div></section><section><h2>Ticket guides</h2>' + guide_cards + '</section><section><h2>Providers</h2><div class="provider-grid">' + "".join(provider_cards) + '</div></section>'
    (out / "index.html").write_text(layout(f"Verified attraction ticket discounts | {date.today():%B %Y} | {brand}", "Find current attraction and theme park ticket discounts verified against official sources.", canonical(base), home_body, item_list(entries, base)), encoding="utf-8")
    provider_index = '<h1>Official ticket providers</h1>' + "".join(provider_cards)
    (out / "providers").mkdir(exist_ok=True)
    (out / "providers" / "index.html").write_text(layout(f"Providers | {brand}", "Official sources monitored for verified attraction discounts.", canonical(base, "providers/"), provider_index, item_list([e for e in entries if e["path"].startswith("providers/")], base)), encoding="utf-8")
    compare_dir = out / "compare"
    compare_dir.mkdir(exist_ok=True)
    compare_body = '<h1>Compare verified ticket offers</h1><p>Comparison includes only offers with an explicit discount in the official source.</p>' + ("".join(deal_cards) if offers else '<p class="muted">No comparable verified offers are available right now.</p>')
    (compare_dir / "index.html").write_text(layout(f"Compare ticket discounts | {brand}", "Compare verified attraction and theme park ticket discounts.", canonical(base, "compare/"), compare_body, item_list([e for e in entries if e["path"].startswith("deals/")], base)), encoding="utf-8")
    urls = [canonical(base), canonical(base, "providers/"), canonical(base, "compare/")] + [canonical(base, e["path"]) for e in entries]
    stamp = (data.get("fetched_at") or date.today().isoformat())[:10]
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{esc(url)}</loc><lastmod>{stamp}</lastmod></url>\n" for url in urls) + "</urlset>\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {canonical(base, 'sitemap.xml')}\n", encoding="utf-8")
    (out / "styles.css").write_text(CSS, encoding="utf-8")
    print(f"Built {len(urls)} pages at {out}")


def deal_slug(offer):
    source = f"{offer.get('provider_id', '')}-{offer.get('product_name', '')}"
    return re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-") or "verified-offer"


def offer_card(offer, url):
    price = f' · {esc(offer["currency"])} {esc(offer["price"])}' if "price" in offer and offer.get("currency") else ""
    discount = f'{esc(offer["discount_percent"])}% off' if offer.get("discount_percent") is not None else esc(offer.get("discount_label", "Official discount"))
    return f'<article class="card"><p class="source">{esc(offer.get("provider", ""))}</p><h2><a href="{esc(url)}">{esc(offer.get("product_name", offer.get("title", "Verified discount")))}</a></h2><p class="discount">{discount}</p><p class="price">{esc(offer.get("currency", ""))} {esc(offer.get("price", ""))}</p><p class="source">Verified from the <a href="{esc(offer.get("source_url", ""))}">official source</a>.</p></article>'


CSS = """html{overflow-wrap:anywhere}img{max-width:100%;height:auto}header{flex-wrap:wrap;gap:12px}nav{flex-wrap:wrap}nav a{display:inline-flex;align-items:center;min-height:44px}a:focus-visible{outline:3px solid #b34b10;outline-offset:3px}@media(max-width:480px){.hero{padding:26px}header,footer,main{padding:16px}}*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#152238;font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}header,footer,main{max-width:1080px;margin:auto;padding:22px}header{display:flex;justify-content:space-between;align-items:center}.brand{font-weight:800;font-size:1.3rem;color:#14233c;text-decoration:none}nav{display:flex;gap:20px}a{color:#1459b5}.hero{background:#142b4a;color:white;border-radius:22px;padding:48px;margin:14px 0 32px}.hero a{color:white}.hero h1{max-width:760px;font-size:clamp(2.2rem,6vw,4rem);line-height:1.08;margin:.2em 0}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;font-weight:700;color:#83c4ff}.hero .eyebrow{color:#9bd4ff}.meta,.muted{color:#66758a}.hero .meta{color:#c5d5e8}.card,.empty{background:white;border:1px solid #e1e7ef;border-radius:16px;padding:22px;margin:14px 0;box-shadow:0 4px 18px #182d4b0a}.card h2{margin:.1em 0}.discount{color:#a13217;font-size:1.2rem;font-weight:800}.price{font-size:1.7rem;font-weight:750}.button{display:inline-block;background:#155bb4;color:white;padding:11px 17px;border-radius:9px;text-decoration:none;font-weight:700}.source{font-size:.9rem;color:#64748b}footer{margin-top:40px;border-top:1px solid #dce3ec;color:#536175;font-size:.9rem}.footer-links{display:flex;gap:18px;flex-wrap:wrap}section{margin:30px 0}nav a{text-decoration:none}h1{line-height:1.15}article a{text-decoration:none}article a:hover{text-decoration:underline}@media(min-width:760px){main>section:not(.hero){display:block}.card{padding:24px}}"""


CSS += """.cards-grid,.provider-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.cards-grid .card,.provider-grid .card{margin:0}.card h2{font-size:1.3rem;line-height:1.3}.card .discount{display:inline-block;background:#e5f3ea;color:#17553a;border-radius:6px;padding:4px 9px;font-size:.86rem}.card .price{margin:.3em 0;font-size:1.75rem}.stats{font-weight:700}.secondary{background:transparent;border:1px solid #a9c4e5;margin-left:8px}.guide{max-width:780px;margin:auto}.answer{background:#eaf4ff;border-left:4px solid #1459b5;padding:18px;border-radius:8px;font-size:1.1rem}.guide h1{font-size:clamp(2rem,5vw,3rem)}.guide h2{margin-top:2em}.guide table{border-collapse:collapse;width:100%;font-size:.95rem}.guide td,.guide th{padding:12px;border:1px solid #dce3ec;text-align:left}.table-scroll{overflow-x:auto}figure{margin:24px 0}figcaption{font-size:.9rem;color:#536175}.guide img{display:block;width:100%}@media(max-width:600px){.cards-grid,.provider-grid{grid-template-columns:1fr}.hero{padding:24px}.hero h1{font-size:32px}header,footer,main{padding:16px}.secondary{margin:10px 0 0}.guide td,.guide th{padding:8px}}"""

if __name__ == "__main__":
    main()
