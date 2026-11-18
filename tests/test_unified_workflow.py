from modules.unified_workflow import production_guidance, research_lineage

def test_lineage():
    assert research_lineage({'content_type':'Carousel','content_brief':{'product':'Example','source_url':'https://example.com'}})['product']=='Example'

def test_formats():
    assert 'slide' in production_guidance('Carousel')
    assert 'video' in production_guidance('Short video / Reel')
