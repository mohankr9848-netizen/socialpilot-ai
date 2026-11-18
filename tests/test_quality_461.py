import pytest
from modules.content_planner import make_plan, topic_sources


def test_rejects_navigation_and_vague_website_slogans():
    b = {'name': 'ISP', 'audience': 'ISP owners'}
    r = {'facts': {'website_headings': ['Impact we bring', 'Verticals we cater to', 'Transforming ISP Operations', 'Subscriber billing and automated payment collection']}}
    topics = topic_sources(b, r)
    assert [t['topic'] for t in topics] == ['Subscriber billing and automated payment collection']
    posts = make_plan(b, r, 2026, 11, ['LinkedIn'])
    assert all('priorities of the intended audience' not in p['title'] for p in posts)
    assert all('Impact we bring' not in p['title'] for p in posts)


def test_no_usable_source_blocks_filler():
    with pytest.raises(ValueError, match='No specific'):
        make_plan({'name':'ISP'}, {'facts':{'website_headings':['Impact we bring','Verticals we cater to']}}, 2026, 11, ['LinkedIn'])


def test_product_attribution_survives():
    product = {'name':'IconACS','url':'https://example.com/acs','approved':True,
               'facts':{'source_url':'https://example.com/acs','headings':['TR-069 remote router provisioning','Our solutions']}}
    posts = make_plan({'name':'ISP','audience':'Network operations managers'}, None, 2026, 11, ['LinkedIn'], products=[product], product_only=True)
    assert all(p['content_brief']['product']=='IconACS' for p in posts)
    assert all(p['content_brief']['source_url']=='https://example.com/acs' for p in posts)
    assert all('intended audience' not in p['title'] for p in posts)
