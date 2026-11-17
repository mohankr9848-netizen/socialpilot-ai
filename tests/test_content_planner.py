from modules.content_planner import make_plan

def test_deterministic_and_month_bounds():
    b={'name':'Example','industry':'Software','colors':['#123456'], 'product_description':'Remote router provisioning and diagnostics'}
    a=make_plan(b,{},2026,2,['LinkedIn','Instagram'],3)
    assert a == make_plan(b,{},2026,2,['LinkedIn','Instagram'],3)
    assert len(a)==12
    assert all(x['scheduled_date'].startswith('2026-02-') for x in a)
    assert all(x['status']=='draft' for x in a)

def test_approved_research_pillars():
    a=make_plan({'name':'Acme'}, {'suggestions':{'content_pillars':'Network monitoring\nSubscriber billing'}},2026,11,['Facebook'],2)
    assert a[0]['content_pillar']=='Network monitoring'
    assert a[1]['content_pillar']=='Subscriber billing'

def test_empty_platforms_rejected():
    import pytest
    with pytest.raises(ValueError): make_plan({}, {}, 2026, 11, [], 3)
