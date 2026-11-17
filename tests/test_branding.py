from io import BytesIO
from PIL import Image
from modules.branding import extract_colors

def test_extract_colors():
    im = Image.new('RGB', (30, 30), (35, 70, 150))
    data = BytesIO()
    im.save(data, format='PNG')
    assert extract_colors(data.getvalue())[0].startswith('#')
