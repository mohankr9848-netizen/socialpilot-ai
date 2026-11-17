"""Offline, deterministic draft planner. No AI API or social posting."""
from datetime import date, timedelta
import calendar
import re

PLATFORMS = ('LinkedIn', 'Instagram', 'Facebook', 'X')
FORMATS = ('Single image', 'Carousel', 'Text', 'Infographic', 'Short video')
ANGLES = (
    ('Educational', 'Explain {topic}: a practical guide for {audience}', 'Share one useful framework and a practical takeaway.'),
    ('Problem/Solution', 'Common challenges with {topic}', 'Discuss a common operational challenge and possible approaches without promising outcomes.'),
    ('How-to', 'Getting started with {topic}', 'Outline three steps a team could evaluate.'),
    ('Industry insight', 'Questions to ask about {topic}', 'Offer a thoughtful checklist and invite discussion.'),
    ('Product education', 'Where {topic} fits in a modern workflow', 'Explain a relevant use case, avoiding unverified product claims.'),
    ('Engagement', 'How does your team approach {topic}?', 'Invite readers to share their experience.'),
)

def _lines(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip(' -•\t') for v in re.split(r'[\n,;|]+', str(value or '')) if v.strip(' -•\t')]

def make_plan(business, research, year, month, platforms, posts_per_week=3, start_hour=10):
    if not platforms or not all(p in PLATFORMS for p in platforms):
        raise ValueError('Select at least one supported platform.')
    if not 1 <= int(posts_per_week) <= 7:
        raise ValueError('Posts per week must be between 1 and 7.')
    if not 1 <= int(month) <= 12:
        raise ValueError('Invalid month.')
    suggestions = (research or {}).get('suggestions') or {}
    topics = _lines(suggestions.get('content_pillars')) or _lines(suggestions.get('content_opportunities'))
    topics = topics or _lines(business.get('product_description'))[:3] or _lines(business.get('industry')) or ['business operations', 'customer experience', 'team productivity']
    topics = [re.sub(r'\s+', ' ', t)[:90] for t in topics][:20]
    audience = _lines(suggestions.get('target_audience')) or _lines(business.get('audience'))
    audience_label = (audience[0][:75] if audience else 'your industry')
    voice = business.get('voice') or 'Professional'
    name = business.get('name') or 'Our team'
    colors = business.get('colors') or []
    _, days = calendar.monthrange(year, month)
    # Spread the selected number of dates evenly within each 7-day segment.
    selected_dates = []
    for begin in range(1, days+1, 7):
        end = min(days, begin+6)
        length = end-begin+1
        count = min(int(posts_per_week), length)
        for i in range(count):
            day = begin + (i * length // count)
            selected_dates.append(date(year, month, day))
    result = []
    for i, day in enumerate(selected_dates):
        topic = topics[i % len(topics)]
        category, title_template, instruction = ANGLES[i % len(ANGLES)]
        title = title_template.format(topic=topic, audience=audience_label)
        platform = platforms[i % len(platforms)]
        fmt = FORMATS[i % len(FORMATS)]
        caption = (f'{title}\n\n{instruction}\n\n'
                   f'What has worked for your team? Share your perspective in the comments.\n\n'
                   f'— {name}')
        hashtags = ' '.join('#'+s for s in ['IndustryInsights', 'BusinessGrowth', 'DigitalTransformation'])
        prompt = (f'Create a clean, accessible {fmt.lower()} social media creative for {name} on {platform}. '
                  f'Topic: {title}. Use a {voice.lower()} tone and brand colors {", ".join(colors) if colors else "from the brand profile"}. '
                  f'Use readable typography, strong hierarchy, minimal text, and a clear focal illustration. '
                  f'Leave space for the official logo. Do not invent facts, statistics, awards, or testimonials.')
        result.append({'scheduled_date':day.isoformat(),'scheduled_time':f'{int(start_hour):02d}:00',
                       'platform':platform,'content_type':fmt,'content_pillar':topic,'category':category,
                       'title':title,'caption':caption,'hashtags':hashtags,'cta':'Share your perspective',
                       'graphic_prompt':prompt,'status':'draft'})
    return result
