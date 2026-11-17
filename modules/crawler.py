"""Bounded, robots-aware public website extraction with DNS/IP safety checks."""
import ipaddress
import re
import socket
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

AGENT = 'SocialPilotResearchBot/0.2 (+manual research; respects robots.txt)'
MAX_BYTES = 1_000_000


def safe_url(url):
    url = (url or '').strip()
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Enter a valid public http:// or https:// website URL.')
    if parsed.port and parsed.port not in (80, 443):
        raise ValueError('Only standard web ports are allowed.')
    host = parsed.hostname.rstrip('.').lower()
    if host == 'localhost' or host.endswith(('.local', '.internal', '.localhost')):
        raise ValueError('Local or internal addresses are not permitted.')
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError('Could not resolve the website hostname.') from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Private, loopback, or reserved network addresses are not permitted.')
    return parsed._replace(fragment='').geturl()


def fetch(url, session, max_bytes=MAX_BYTES):
    # Recheck each URL, including redirect destinations. Disable automatic redirects.
    for _ in range(4):
        safe_url(url)
        response = session.get(url, timeout=(5, 12), allow_redirects=False, stream=True,
                               headers={'User-Agent': AGENT, 'Accept': 'text/html'})
        try:
            if response.status_code in (301, 302, 303, 307, 308):
                destination = response.headers.get('Location')
                if not destination:
                    raise ValueError('Website returned a redirect without a destination.')
                url = urljoin(url, destination)
                continue
            response.raise_for_status()
            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                raise ValueError('The URL did not return an HTML page.')
            content = bytearray()
            for chunk in response.iter_content(chunk_size=16384):
                content.extend(chunk)
                if len(content) > max_bytes:
                    raise ValueError('Website page exceeds the research size limit.')
            return response.url, bytes(content)
        finally:
            response.close()
    raise ValueError('Too many redirects.')


def extract_page(url, html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(['script', 'style', 'nav', 'footer', 'noscript', 'svg', 'form']):
        node.decompose()
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    description = soup.find('meta', attrs={'name': re.compile('^description$', re.I)})
    meta = description.get('content', '').strip() if description else ''
    headings = [h.get_text(' ', strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])][:30]
    main = soup.find('main') or soup.find('article') or soup.body or soup
    text = re.sub(r'\s+', ' ', main.get_text(' ', strip=True))[:12000]
    links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
    return {'url': url, 'title': title, 'description': meta, 'headings': headings, 'text': text, 'links': links}


def crawl_website(url, max_pages=4):
    url = safe_url(url)
    origin = urlparse(url)
    root = f'{origin.scheme}://{origin.netloc}'
    session = requests.Session()
    session.trust_env = False  # Avoid proxy credentials and unexpected proxy routing
    robots = RobotFileParser()
    robots.set_url(root + '/robots.txt')
    try:
        # Fail closed if robots rules cannot be retrieved.
        robots.read()
    except Exception as exc:
        raise ValueError('Could not verify robots.txt; research was stopped.') from exc
    queue = deque([url])
    seen, pages, errors = set(), [], []
    max_pages = min(max(int(max_pages), 1), 8)
    while queue and len(pages) < max_pages:
        current = urldefrag(queue.popleft()).url
        if current in seen:
            continue
        seen.add(current)
        if urlparse(current).netloc.lower() != origin.netloc.lower():
            continue
        if not robots.can_fetch(AGENT, current):
            errors.append(f'Robots rules disallow: {current}')
            continue
        try:
            final_url, raw = fetch(current, session)
            if urlparse(final_url).netloc.lower() != origin.netloc.lower():
                errors.append('A redirect left the original website and was skipped.')
                continue
            page = extract_page(final_url, raw)
            pages.append({k: v for k, v in page.items() if k != 'links'})
            for link in page['links']:
                parsed = urlparse(link)
                if parsed.scheme in ('http', 'https') and parsed.netloc.lower() == origin.netloc.lower():
                    clean = urldefrag(link).url
                    if clean not in seen and clean not in queue and len(queue) < 40:
                        queue.append(clean)
            if queue:
                time.sleep(0.5)
        except Exception as exc:
            errors.append(f'{current}: {str(exc)[:180]}')
    return {'website': url, 'pages': pages, 'warnings': errors}
