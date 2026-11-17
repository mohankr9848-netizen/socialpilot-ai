from modules.business_analyzer import analyze
from modules.crawler import extract_page


def test_extract_page():
    p = extract_page('https://example.com', b'<html><head><title>Sample</title></head><body><main><h1>Our Services</h1><p>We build tools.</p></main></body></html>')
    assert p['title'] == 'Sample'
    assert 'Our Services' in p['headings']


def test_analysis_separates_facts_and_suggestions():
    report = analyze({'description': 'A business'}, {'pages': [{'url': 'https://example.com', 'title': 'Sample', 'headings': ['Our Services'], 'description': 'Test'}]})
    assert report['facts']['source_urls'] == ['https://example.com']
    assert report['suggestions']['business_overview'] == 'A business'
