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


class VisibleTextParser(HTMLParser):
    """Collect user-visible text and simple table/paragraph boundaries."""
    HIDDEN = {"script", "style", "noscript", "svg", "template"}

    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.HIDDEN:
            self.hidden += 1
        elif not self.hidden and tag.lower() in {"p", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.HIDDEN and self.hidden:
            self.hidden -= 1
        elif not self.hidden and tag.lower() in {"p", "li", "tr", "td", "th", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(re.sub(r"\s+", " ", data).strip())


def visible_text(html):
    parser = VisibleTextParser()
    parser.feed(html)
    return re.sub(r"[ \t]+", " ", " ".join(parser.parts)).strip()


def explicit_discount_records(text, page_url, provider_id, provider_name, fetched_at):
    """Extract only well-bounded visible discount statements with explicit prices.

    This intentionally supports a small set of source wording/markup patterns;
    it does not turn ordinary ticket prices into offers.
    """
    records = []
    # A source must explicitly say it is a discount/offer/free/2-for-1. Capture
    # a compact sentence/row, never the whole page or a marketing paragraph.
    statements = [re.sub(r"\s+", " ", s).strip(" .\t") for s in re.split(r"[\n.!?]+", text) if s.strip()]
    seen = set()
    for statement in statements:
        low = statement.casefold()
        if not re.search(r"\b(discount|offer|voucher|2.for.1|two.for.one)\b|%\s*(?:discount|off)", low):
            continue
        if not re.search(r"\d", statement) or not re.search(r"£|€|\bDKK\b|\bEUR\b|\bGBP\b", statement, re.I):
            continue
        # Explicit coupon terms price the full-paying ticket, while the actual
        # discounted admission price is not stated; £39.50 is therefore not a
        # verified offer price. Paultons £167 is the value ceiling of the free
        # day, not a payable ticket price. Both are deliberately excluded.
        if re.search(r"worth up to|full-paying|discount of DKK|gift card|win an", low):
            continue
        currency = "GBP" if "£" in statement else ("EUR" if "€" in statement or re.search(r"\bEUR\b", statement, re.I) else ("DKK" if re.search(r"\bDKK\b", statement, re.I) else "GBP"))
        price_match = re.search(r"(?:£|€)\s*(\d+(?:[.,]\d{1,2})?)|\b(DKK|EUR|GBP)\s*(\d+(?:[.,]\d{1,2})?)", statement, re.I)
        if not price_match:
            continue
        raw_price = price_match.group(1) or price_match.group(3)
        try:
            price = float(raw_price.replace(",", "."))
        except ValueError:
            continue
        # The discount must be explicit; currency/price alone is not evidence.
        pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:discount|off)|(?:discount|save|saving)[^%]{0,35}(\d+(?:[.,]\d+)?)\s*%", statement, re.I)
        amount = re.search(r"(?:discount|save|saving)[^£€\d]{0,24}(?:£|€|DKK\s*)(\d+(?:[.,]\d{1,2})?)|(?:£|€|DKK\s*)(\d+(?:[.,]\d{1,2})?)[^.!?]{0,30}(?:discount|save|saving)", statement, re.I)
        explicit = bool(pct or amount or re.search(r"\b(2.for.1|two.for.one)\b", low))
        if not explicit:
            continue
        # Require a concise, named deal title. Exclude generic menus and terms.
        title = statement[:120]
        if len(title) < 12 or title.casefold() in seen:
            continue
        seen.add(title.casefold())
        discount_percent = None
        if pct:
            try:
                discount_percent = float((pct.group(1) or pct.group(2)).replace(",", "."))
            except ValueError:
                pass
        # Phrase must identify a payable ticket price, not the value of a free
        # extra or the amount saved. Current configured public pages only expose
        # those distinctions clearly for Gulliver's table (handled separately).
        if re.search(r"worth up to|full-paying|discount of DKK|gift card|win an", low):
            continue
        record = {
            "provider_id": provider_id, "provider": provider_name,
            "product_name": title, "title": title,
            "offer_url": page_url, "source_url": page_url,
            "price": price, "currency": currency,
            "fetched_at": fetched_at,
        }
        if discount_percent is not None and discount_percent > 0:
            record["discount_percent"] = discount_percent
        records.append(record)
    return records


def gullivers_price_rows(html, page_url, provider_id, provider_name, fetched_at):
    """Parse the official ticket table where the Online Advance column is priced."""
    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_row = False
            self.in_cell = False
            self.cell = []
            self.row = []
            self.rows = []

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag == "tr":
                self.in_row, self.row = True, []
            elif self.in_row and tag in {"td", "th"}:
                self.in_cell, self.cell = True, []

        def handle_data(self, data):
            if self.in_cell:
                self.cell.append(data.strip())

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag in {"td", "th"} and self.in_cell:
                self.row.append(re.sub(r"\s+", " ", " ".join(self.cell)).strip())
                self.in_cell = False
            elif tag == "tr" and self.in_row:
                self.rows.append(self.row)
                self.in_row = False

    parser = TableParser()
    parser.feed(html)
    header = next((row for row in parser.rows if any("Online Advance" in cell for cell in row)), None)
    text = visible_text(html).casefold()
    if not header or "approximate online discount rate when booked in advance" not in text:
        return []
    advance_index = next(i for i, cell in enumerate(header) if "Online Advance" in cell)
    records = []
    for row in parser.rows:
        if row is header or len(row) <= advance_index or len(row) < 2:
            continue
        name, price_text = row[0], row[advance_index]
        match = re.fullmatch(r"£\s*(\d+(?:\.\d{1,2})?)", price_text)
        if not name or not match or name.casefold() == "ticket type":
            continue
        # The same official page explicitly labels these prices Online Advance
        # and states “Approximate online discount rate when booked in advance.”
        price = float(match.group(1))
        record = {
            "provider_id": provider_id, "provider": provider_name,
            "product_name": f"{name} ticket — online advance", "title": f"{provider_name}: {name} ticket, online advance",
            "offer_url": page_url, "source_url": page_url,
            "price": price, "currency": "GBP", "fetched_at": fetched_at,
            "discount_evidence": "Official page labels Online Advance prices and states an approximate online discount when booked in advance.",
            "discount_label": "Online advance discount",
        }
        records.append(record)
    return records


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
            # Publish only when all required commercial facts are explicitly
            # present. The official source URL is retained for every record.
            if price is None or not currency:
                continue
            try:
                verified_price = float(price)
            except (ValueError, TypeError):
                continue
            record = {
                "provider_id": provider_id, "provider": provider_name,
                "product_name": name.strip(), "title": f"{provider_name}: {name.strip()}",
                "offer_url": item.get("url") or page_url, "source_url": page_url,
                "discount_percent": discount_num, "price": verified_price,
                "currency": str(currency), "fetched_at": fetched_at,
            }
            availability = item.get("availability")
            if availability:
                record["availability"] = availability if isinstance(availability, str) else str(availability)
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
                page_html = raw.decode("utf-8", "replace")
                provider_id = provider["name"].lower()
                parsed = parse_offers(page_html, final_url, provider_id, provider["name"], fetched_at)
                parsed.extend(explicit_discount_records(visible_text(page_html), final_url, provider_id, provider["name"], fetched_at))
                if provider_id == "gulliver's":
                    parsed.extend(gullivers_price_rows(page_html, final_url, provider_id, provider["name"], fetched_at))
                records.extend(parsed)
                time.sleep(0.25)
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                print(f"Skip {page}: {exc}")
    # Stable deduplication: provider + product + currency; discard expired offers.
    today = datetime.now(timezone.utc).date().isoformat()
    unique = {}
    for record in records:
        if record.get("valid_until") and record["valid_until"] < today:
            continue
        if not all(record.get(k) for k in ("title", "source_url", "currency")):
            continue
        if not isinstance(record.get("price"), (int, float)) or record["price"] <= 0:
            continue
        if not record.get("discount_percent") and not record.get("discount_evidence"):
            continue
        key = (record["provider_id"], record["product_name"].casefold(), record.get("currency", ""))
        unique[key] = record
    out = ROOT / "data" / "offers.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"fetched_at": fetched_at, "offers": list(unique.values())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(unique)} verified offers")


if __name__ == "__main__":
    main()
