"""Business-aware, deterministic calendar planner. No API, scraping or publishing.

Uses approved research and saved business fields only. Suggestions and website
headings are planning inputs, NOT proof that a product has a capability.
"""
from datetime import date
import calendar
import re

PLATFORMS = ('LinkedIn', 'Instagram', 'Facebook', 'X')
from modules.format_briefs import FORMATS, choose_format, make_brief

GENERIC = {'product education', 'industry insights', 'customer challenges', 'practical tips',
           'business operations', 'customer experience', 'team productivity',
           'product features', 'thought leadership', 'brand awareness', 'tips',
           'how to', 'educational', 'industry trends', 'engagement', 'case studies'}
STOP = {'the','and','for','with','from','into','that','this','your','our','their','are','was',
        'you','all','can','will','have','has','how','why','what','when','where','about','more',
        'best','top','new','use','using','get','solutions','solution','software','platform',
        'business','product','products','services','service','technology','technologies',
        'overview','home','contact','blog','read','learn','explore','features','feature',
        'benefits','benefit','industry','insights','customer','customers'}


def _clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip(' \t\n\r-–—:;|•')


def _items(value):
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            parts.extend(_items(item))
        return parts
    # Keep commas within names and feature phrases; split lines and semicolons.
    return [_clean(p) for p in re.split(r'[\n;|•]+', str(value or '')) if _clean(p)]


def _specific(value):
    value = _clean(value)
    if not 5 <= len(value) <= 145 or value.casefold() in GENERIC:
        return False
    words = re.findall(r'[\w-]+', value.lower())
    return len(words) >= 2 and any(w not in STOP and len(w) >= 3 for w in words)


def _phrases(value):
    """Extract meaningful phrases without presenting prose as an invented product name."""
    result = []
    for item in _items(value):
        item = re.sub(r'^\s*(?:\d+[.)-]|[-*])\s*', '', item)
        # Website descriptions can be long. Split into sentences first.
        chunks = re.split(r'(?<=[.!?])\s+', item)
        for chunk in chunks:
            chunk = _clean(chunk)
            if len(chunk) > 145:
                # Long sentences often contain multiple independent claims; don't truncate mid-claim.
                continue
            if _specific(chunk):
                result.append(chunk)
    return result


def _dedupe(values, limit=30):
    result, seen = [], set()
    for item in values:
        item = _clean(item)
        key = re.sub(r'[^a-z0-9]+', '', item.casefold())
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _source_topics(business, research):
    suggestions = (research or {}).get('suggestions') or {}
    facts = (research or {}).get('facts') or {}
    # Website headings and edited product positioning take precedence over generic pillars.
    inputs = [
        ('Website heading', facts.get('website_headings')),
        ('Website page title', facts.get('page_titles')),
        ('Website description', facts.get('website_descriptions')),
        ('Product positioning', suggestions.get('product_positioning')),
        ('Business product description', business.get('product_description')),
        ('Content opportunity', suggestions.get('content_opportunities')),
        ('Customer pain point', suggestions.get('customer_pain_points')),
        ('Unique selling proposition', suggestions.get('unique_selling_propositions')),
        ('Business description', business.get('description')),
        ('Content pillar', suggestions.get('content_pillars')),
    ]
    candidates = []
    for source, raw in inputs:
        for phrase in _phrases(raw):
            # Discard website navigation and boilerplate.
            if phrase.casefold() in GENERIC or re.fullmatch(r'(home|about us|contact us|blog|privacy policy)', phrase, re.I):
                continue
            candidates.append({'topic': phrase, 'source': source})
    unique, seen = [], set()
    for item in candidates:
        key = re.sub(r'[^a-z0-9]+', '', item['topic'].casefold())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:60]


def _audiences(business, research):
    suggestions = (research or {}).get('suggestions') or {}
    audience = _items(suggestions.get('target_audience')) or _items(business.get('audience'))
    audience = _dedupe([a for a in audience if len(a) <= 110], 12)
    return audience or ['the intended audience']


def _title(topic, audience, angle):
    if angle == 0:
        return f'How {topic} connects to the priorities of {audience}'
    if angle == 1:
        return f'What {audience} should evaluate about {topic}'
    if angle == 2:
        return f'3 questions to ask before adopting {topic}'
    if angle == 3:
        return f'{topic}: a practical workflow checklist'
    if angle == 4:
        return f'Common implementation challenges around {topic}'
    return f'Where {topic} fits into a broader operating strategy'


def _caption(title, topic, audience, category, business_name):
    openings = {
        'Audience insight': f'For {audience}, a useful starting point is understanding how {topic} affects day-to-day work.',
        'Evaluation': f'Before investing in {topic}, teams should clarify their requirements and operational constraints.',
        'Decision checklist': f'Considering {topic}? Ask who owns the process, what needs to integrate, and how success will be measured.',
        'Workflow': f'A practical way to examine {topic} is to map the current workflow, identify handoffs, and document gaps.',
        'Challenges': f'When teams work with {topic}, unclear ownership, disconnected information, and manual steps may create friction.',
        'Strategy': f'{topic} deserves a place in the conversation about operational priorities and long-term planning.',
    }
    return (f'{title}\n\n{openings[category]}\n\n'
            'Suggested discussion points:\n'
            '• Identify the current process and its biggest friction point.\n'
            '• Evaluate the requirements and stakeholders involved.\n'
            '• Define what a measurable improvement would look like.\n\n'
            f'What would you add to this checklist?\n\n— {business_name}\n\n'
            '[Editorial review: verify product capabilities, examples and claims before publishing.]')


def _hashtags(topic, business):
    words = re.findall(r'[A-Za-z][A-Za-z0-9]+', topic)
    meaningful = [w for w in words if w.casefold() not in STOP and len(w) > 3]
    tags = []
    for word in meaningful[:3]:
        tag = '#' + word[0].upper() + word[1:]
        if tag.casefold() not in {t.casefold() for t in tags}:
            tags.append(tag)
    industry = re.findall(r'[A-Za-z][A-Za-z0-9]+', str(business.get('industry') or ''))
    if industry:
        tags.append('#' + ''.join(w.capitalize() for w in industry[:3]))
    return ' '.join(_dedupe(tags, 5)) or '#BusinessStrategy'


def make_plan(business, research, year, month, platforms, posts_per_week=3, start_hour=10, products=None, selected_formats=None, product_only=False):
    """Return drafts compatible with the existing Phase 3 content_posts table.

    If no specific business evidence exists, raise a useful error rather than
    silently producing generic marketing filler.
    """
    if not platforms or not all(p in PLATFORMS for p in platforms):
        raise ValueError('Select at least one supported platform.')
    if not 1 <= int(posts_per_week) <= 7:
        raise ValueError('Posts per week must be between 1 and 7.')
    if not 1 <= int(month) <= 12:
        raise ValueError('Invalid month.')
    if not 0 <= int(start_hour) <= 23:
        raise ValueError('Invalid posting hour.')
    from modules.product_intelligence import product_topics
    product_candidates = product_topics(products or [])
    topics = product_candidates if product_only else product_candidates + _source_topics(business, research)
    seen_topics = set()
    topics = [t for t in topics if not (t['topic'].casefold() in seen_topics or seen_topics.add(t['topic'].casefold()))]
    if not topics:
        raise ValueError('No specific product or website topics found. Add product names, features, use cases, or customer problems under Businesses / Website Research, approve the research, and try again.')
    audiences = _audiences(business, research)
    name = _clean(business.get('name')) or 'Our team'
    colors = business.get('colors') or []
    voice = _clean(business.get('voice')) or 'Professional'
    _, days = calendar.monthrange(int(year), int(month))
    selected_dates = []
    for begin in range(1, days + 1, 7):
        length = min(7, days - begin + 1)
        count = min(int(posts_per_week), length)
        for i in range(count):
            selected_dates.append(date(int(year), int(month), begin + i * length // count))
    categories = ('Audience insight', 'Evaluation', 'Decision checklist', 'Workflow', 'Challenges', 'Strategy')
    result = []
    for i, day in enumerate(selected_dates):
        # Rotate the topic list and audience independently to vary perspectives.
        item = topics[i % len(topics)]
        topic = item['topic']
        audience = audiences[(i // max(1, len(topics))) % len(audiences)]
        category = categories[(i // max(1, len(topics))) % len(categories)]
        angle = (i // max(1, len(topics))) % len(categories)
        title = _title(topic, audience, angle)
        platform = platforms[i % len(platforms)]
        fmt = choose_format(i, platform, selected_formats)
        graphic_prompt = (
            f'Design a professional {fmt.lower()} for {platform} about: "{title}". '
            f'Business: {name}. Intended audience: {audience}. '
            f'Core source phrase ({item["source"]}): "{topic}". '
            f'Use a {voice.lower()} tone and brand colors {", ".join(map(str, colors)) if colors else "from the brand profile"}. '
            'Create an editorial visual that explains the idea using simple 2D icons, a process diagram, or a concise checklist. '
            'Use short, readable text, clean spacing, and leave room for the official logo. '
            'Do not invent metrics, customer names, product features, certifications, or testimonials. '
            'The designer must verify any claims before publishing.'
        )
        result.append({
            'scheduled_date': day.isoformat(), 'scheduled_time': f'{int(start_hour):02d}:00',
            'platform': platform, 'content_type': fmt, 'content_pillar': topic,
            'category': category, 'title': title,
            'caption': _caption(title, topic, audience, category, name),
            'hashtags': _hashtags(topic, business), 'cta': 'Share your perspective',
            'graphic_prompt': graphic_prompt, 'content_brief': make_brief(fmt, title, topic, audience, item.get('product',''), item.get('source_url','')), 'status': 'draft'
        })
    return result


def topic_sources(business, research, limit=20, products=None):
    """Preview the exact source phrases used for planning."""
    from modules.product_intelligence import product_topics
    return (product_topics(products or []) + _source_topics(business, research))[:limit]
