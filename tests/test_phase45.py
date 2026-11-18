import pytest
from modules.product_intelligence import parse_product_lines, extract_product_page, product_topics
from modules.format_briefs import FORMATS, make_brief
from modules.content_planner import make_plan


def test_multiple_urls_and_duplicates():
    rows = parse_product_lines('Router | https://example.com/router\nBilling | https://example.com/billing\nhttps://example.com/router')
    assert len(rows) == 2
    assert rows[0]['name'] == 'Router'


def test_reject_internal_urls():
    with pytest.raises(ValueError):
        parse_product_lines('Local | file:///etc/passwd')


def test_source_approval():
    product = {'name':'IconACS','url':'https://example.com/acs'}
    facts = extract_product_page(product, {'pages':[{'url':product['url'],'title':'TR-069 Remote Provisioning','description':'Manage customer routers remotely','headings':['Zero-touch provisioning']}], 'warnings':[]})
    assert not product_topics([{'name':'IconACS','url':product['url'],'facts':facts,'approved':False}])
    topics = product_topics([{'name':'IconACS','url':product['url'],'facts':facts,'approved':True}])
    assert any('Zero-touch' in t['topic'] for t in topics)
    assert topics[0]['source_url'] == product['url']


def test_all_formats_have_briefs():
    for fmt in FORMATS:
        brief = make_brief(fmt, 'ISP operations', 'TR-069 provisioning', 'ISP owners', 'IconACS', 'https://example.com/acs')
        assert brief['format'] == fmt
        assert len(brief) >= 6


def test_product_topics_drive_multiformat_calendar():
    product = {'name':'IconACS','url':'https://example.com/acs','approved':True,'facts':{'title':'TR-069 Remote Provisioning','headings':['Zero-touch provisioning'],'source_url':'https://example.com/acs'}}
    business = {'name':'IconWave','audience':'ISP owners'}
    posts = make_plan(business, None, 2026, 12, ['LinkedIn'], 3, products=[product], selected_formats=['Carousel','Short video / Reel','Infographic'])
    assert posts[0]['content_brief']['product'] == 'IconACS'
    assert {p['content_type'] for p in posts} == {'Carousel','Short video / Reel','Infographic'}
    assert posts[1]['content_brief']['video']['scenes']
