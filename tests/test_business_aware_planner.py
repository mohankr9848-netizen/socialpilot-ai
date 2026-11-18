import pytest
from modules.content_planner import make_plan, topic_sources

BUSINESS = {'name':'Example ISP','industry':'Telecommunications','audience':'ISP CTOs\nNOC Managers',
            'product_description':'TR-069 remote device management\nFiber route planning and GIS mapping',
            'colors':['#24468F','#C62229']}
RESEARCH = {'suggestions':{'content_pillars':'Product education\nIndustry insights',
                           'target_audience':'ISP CTOs\nNetwork operations teams',
                           'product_positioning':'Zero-touch provisioning for customer routers'},
            'facts':{'website_headings':['Centralized AAA and subscriber billing','Remote firmware upgrades']}}

def test_business_specific_topics_override_generic_pillars():
    topics = topic_sources(BUSINESS, RESEARCH)
    assert topics[0]['topic'] == 'Zero-touch provisioning for customer routers'
    assert all(x['topic'] != 'Product education' for x in topics)

def test_deterministic_and_database_compatible():
    a = make_plan(BUSINESS, RESEARCH, 2026, 11, ['LinkedIn','Instagram'], 3)
    assert a == make_plan(BUSINESS, RESEARCH, 2026, 11, ['LinkedIn','Instagram'], 3)
    assert len(a) == 14
    assert 'Zero-touch provisioning' in a[0]['title']
    assert 'How It Works' in a[0]['title']
    assert all(set(p) == {'scheduled_date','scheduled_time','platform','content_type','content_pillar','category','title','caption','hashtags','cta','graphic_prompt','content_brief','status'} for p in a)
    assert all('Editorial review' in p['caption'] for p in a)

def test_business_only_still_works():
    a = make_plan(BUSINESS, None, 2026, 2, ['Facebook'], 2)
    assert 'TR-069' in a[0]['title']

def test_no_generic_filler_when_evidence_missing():
    with pytest.raises(ValueError, match='No specific product'):
        make_plan({'name':'Example','industry':'Software'}, {'suggestions':{'content_pillars':'Product education\nPractical tips'}}, 2026, 11, ['LinkedIn'])

def test_unsupported_platform():
    with pytest.raises(ValueError):
        make_plan(BUSINESS, RESEARCH, 2026, 11, ['TikTok'])
