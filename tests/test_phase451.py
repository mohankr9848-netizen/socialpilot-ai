from pathlib import Path


def test_new_business_urls_wired():
    app = (Path(__file__).resolve().parents[1] / 'app.py').read_text()
    assert "new_business_product_urls" in app
    assert "product_entries = parse_product_lines(new_product_lines)" in app
    assert "'business_id': created['id']" in app
    assert "db.table('business_products').insert(product_records).execute()" in app
