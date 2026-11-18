"""Safe product URL validation, bounded page extraction and source-grounded topics."""
import re
from urllib.parse import urlparse
from modules.crawler import crawl_website


def parse_product_lines(text):
    """One product per line: Name | https://... ; URL alone is accepted."""
    items = []
    seen = set()
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split('|', 1)]
        if len(parts) == 1:
            name, url = '', parts[0]
        else:
            name, url = parts
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            raise ValueError(f'Invalid public product URL: {url[:120]}')
        key = url.rstrip('/').casefold()
        if key not in seen:
            items.append({'name': name[:150] or parsed.path.rstrip('/').split('/')[-1].replace('-', ' ').title() or parsed.hostname, 'url': url})
            seen.add(key)
    return items


def extract_product_page(product, crawl):
    pages = crawl.get('pages') or []
    page = pages[0] if pages else {}
    # Preserve attributable extracts, not model-invented claims.
    headings = [re.sub(r'\s+', ' ', h).strip()[:180] for h in page.get('headings', []) if h.strip()][:20]
    return {'name': product['name'], 'url': product['url'], 'source_url': page.get('url', ''),
            'title': page.get('title', '')[:240], 'description': page.get('description', '')[:600],
            'headings': headings, 'excerpt': page.get('text', '')[:3000],
            'warnings': crawl.get('warnings', []), 'approved': False}


def crawl_product(product):
    return extract_product_page(product, crawl_website(product['url'], max_pages=1))


def product_topics(products):
    result = []
    for product in products:
        if not product.get('approved'):
            continue
        facts = product.get('facts') or {}
        name = product.get('name', '')
        for phrase in [facts.get('title', ''), facts.get('description', '')] + facts.get('headings', []):
            phrase = re.sub(r'\s+', ' ', str(phrase)).strip()
            if 8 <= len(phrase) <= 135 and phrase.casefold() not in ('features', 'benefits', 'overview', 'contact us', 'learn more'):
                result.append({'topic': phrase, 'source': f'Approved product: {name}', 'product': name, 'source_url': facts.get('source_url') or product.get('url', '')})
    return result
