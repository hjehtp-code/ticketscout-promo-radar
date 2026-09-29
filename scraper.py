# ::ILANG [TYPE:file][PROJECT:TicketScout]
# ::STATE{@ROLE, responsibility:Fetch configured public official sources for verifiable discounts}
# ::RULE{Read .ilang/site.ilang; honor robots.txt; never infer or fabricate discount prices}
# ::BOUNDARY{never:login scrape blocked paths or bypass controls|scope:permanent}
"""Collect explicitly verified offers from public official sources."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_AGENT = "TicketScoutBot/1.0 (+public static offer index)"


def load_config():
    text = (ROOT / ".ilang" / "site.ilang").read_text(encoding="utf-8")
    state = re.search(r"::STATE\{@SITE,(.*?)\}", text, re.S)
    if not state:
        raise ValueError("Missing @SITE state in .ilang/site.ilang")
    site = dict(re.findall(r"([\w_]+):\s*([^,]+)", state.group(1)))
    providers = []
    section = re.search(r"::MODULE\{PROVIDERS[^\n]*\}\s*(.*?)(?=\n::MODULE|\Z)", text, re.S)
    for row in (section.group(1) if section else "").splitlines():
        parts = [part.strip() for part in row.split("|")]
        if len(parts) >= 3 and parts[0] and not row.lstrip().startswith("::"):
            providers.append({"name": parts[0], "url": parts[1], "source": parts[2], "affiliate": parts[3] if len(parts) > 3 else ""})
    return site, providers


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.geturl(), response.read(3_000_000), response.headers.get_content_type()


def allowed_by_robots(url):
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        _, data, _ = fetch(robots_url)
        rules = []
        active = False
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = [x.strip() for x in line.split(":", 1)]
            if key.lower() == "user-agent":
                active = value == "*" or value.lower() in USER_AGENT.lower()
            elif active and key.lower() == "disallow" and value and parsed.path.startswith(value.rstrip("*")):
                return False
        return True
    except Exception:
        return False


def urls_from_sitemap(url, depth=0):
    if depth > 2 or not allowed_by_robots(url):
        return []
    try:
        _, data, _ = fetch(url)
        root = ET.fromstring(data)
    except Exception:
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    if root.tag.endswith("sitemapindex"):
        out = []
        for loc in root.findall(".//sm:sitemap/sm:loc", ns)[:20]:
            out.extend(urls_from_sitemap((loc.text or "").strip(), depth + 1))
        return out
    return [(loc.text or "").strip() for loc in root.findall(".//sm:url/sm:loc", ns) if loc.text]


class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_jsonld = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.in_jsonld, self.parts = True, []

    def handle_data(self, data):
        if self.in_jsonld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_jsonld:
            self.blocks.append("".join(self.parts))
            self.in_jsonld = False


def flatten(value):
    if isinstance(value, list):
        for item in value:
            yield from flatten(item)
    elif isinstance(value, dict):
        yield value
        if "@graph" in value:
            yield from flatten(value["@graph"])


def parse_offers(html, page_url, provider_id, provider_name, fetched_at):
    parser = JsonLdParser()
    parser.feed(html)
    records = []
    for block in parser.blocks:
        try:
            payload = json.loads(block)
        except (ValueError, TypeError):
            continue
        for item in flatten(payload):
            if item.get("@type") not in ("Offer", "AggregateOffer"):
                continue
            # A schema Offer with a numeric price is not proof of a discount.
            # Require an explicit, positive discount property and an actual item name.
            discount = item.get("discount") or item.get("discountPercentage") or item.get("discount_percent")
            if discount is None:
                continue
            product = item.get("itemOffered") or {}
            name = product.get("name") if isinstance(product, dict) else str(product)
            if not name:
                continue
            try:
                discount_num = float(re.sub(r"[^0-9.]", "", str(discount)))
            except ValueError:
                continue
            if discount_num <= 0:
                continue
            price = item.get("price")
            currency = item.get("priceCurrency")
            record = {
                "provider_id": provider_id, "provider": provider_name,
                "product_name": name.strip(), "title": f"{provider_name}: {name.strip()}",
                "offer_url": item.get("url") or page_url, "source_url": page_url,
                "discount_percent": discount_num, "fetched_at": fetched_at,
            }
            if price is not None and currency:
                try:
                    record["price"] = float(price)
                    record["currency"] = str(currency)
                except (ValueError, TypeError):
                    pass
            valid_until = item.get("validThrough") or item.get("priceValidUntil")
            if valid_until:
                record["valid_until"] = str(valid_until)[:10]
            records.append(record)
    return records


def main():
    _, providers = load_config()
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records = []
    for provider in providers:
        if not allowed_by_robots(provider["source"]):
            print(f"Skip disallowed source: {provider['source']}")
            continue
        pages = [provider["source"]]
        if provider["source"].lower().endswith(".xml"):
            pages = urls_from_sitemap(provider["source"])
        for page in pages[:300]:
            if not allowed_by_robots(page):
                continue
            try:
                final_url, raw, content_type = fetch(page)
                if content_type not in ("text/html", "application/xhtml+xml"):
                    continue
                records.extend(parse_offers(raw.decode("utf-8", "replace"), final_url, provider["name"].lower(), provider["name"], fetched_at))
                time.sleep(0.25)
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                print(f"Skip {page}: {exc}")
    # Stable deduplication: provider + product + currency; discard expired offers.
    today = datetime.now(timezone.utc).date().isoformat()
    unique = {}
    for record in records:
        if record.get("valid_until") and record["valid_until"] < today:
            continue
        key = (record["provider_id"], record["product_name"].casefold(), record.get("currency", ""))
        unique[key] = record
    out = ROOT / "data" / "offers.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"fetched_at": fetched_at, "offers": list(unique.values())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(unique)} verified offers")


if __name__ == "__main__":
    main()
