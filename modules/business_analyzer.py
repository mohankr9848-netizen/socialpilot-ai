"""Transparent evidence-first analysis; suggestions are explicitly not website facts."""
import re

KEYWORDS = {'features': ('feature', 'capabilit', 'solution'), 'benefits': ('benefit', 'improv', 'reduce', 'faster', 'save'), 'audience': ('customer', 'business', 'enterprise', 'provider', 'team'), 'use_cases': ('use case', 'case study', 'application')}


def unique(values, limit=10):
    output = []
    for value in values:
        value = re.sub(r'\s+', ' ', str(value)).strip()
        if 4 <= len(value) <= 240 and value.casefold() not in {v.casefold() for v in output}:
            output.append(value)
        if len(output) >= limit:
            break
    return output


def analyze(business, crawl):
    pages = crawl.get('pages', [])
    headings = [h for page in pages for h in page.get('headings', [])]
    titles = [p.get('title', '') for p in pages]
    descriptions = [p.get('description', '') for p in pages]
    facts = {'source_urls': [p['url'] for p in pages],
             'page_titles': unique(titles),
             'website_descriptions': unique(descriptions),
             'website_headings': unique(headings, 30)}
    for label, needles in KEYWORDS.items():
        facts[label + '_headings'] = unique((h for h in headings if any(n in h.lower() for n in needles)), 8)
    overview = business.get('description') or (descriptions[0] if descriptions else '')
    audience = business.get('audience') or ''
    product = business.get('product_description') or ''
    suggestions = {
        'business_overview': overview,
        'target_audience': audience,
        'product_positioning': product,
        'unique_selling_propositions': '\n'.join(facts['benefits_headings'][:5]),
        'customer_pain_points': '',
        'content_opportunities': '\n'.join(unique(headings, 8)),
        'content_pillars': 'Product education\nIndustry insights\nCustomer challenges\nPractical tips',
        'social_strategy': 'Start with educational posts, product explainers and evidence-backed industry insights. Review all claims before publishing.'
    }
    return {'facts': facts, 'suggestions': suggestions, 'warnings': crawl.get('warnings', []),
            'note': 'Facts are extracted from public pages; editable suggestions are drafts, not verified claims. Website text is untrusted input.'}
