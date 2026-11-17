from io import BytesIO
from PIL import Image
from modules.creative_studio import render_post, design_prompt, colors_for, SIZES, TEMPLATES

B = {'name': 'Example ISP', 'colors': ['#24468F', '#C62229'], 'audience': 'ISP owners', 'description': 'Network tools'}
P = {'title': 'How Remote Provisioning Helps ISP Teams', 'caption': 'A practical overview', 'content_pillar': 'Network automation'}

def test_all_templates_png():
    for template in TEMPLATES:
        raw = render_post(B, P, template, (1080, 1080))
        image = Image.open(BytesIO(raw))
        assert image.size == (1080, 1080)
        assert image.format == 'PNG'

def test_all_sizes():
    for size in SIZES.values():
        raw = render_post(B, P, size=size)
        assert Image.open(BytesIO(raw)).size == size

def test_logo_and_long_headline():
    img = Image.new('RGBA', (300, 100), 'red')
    output = BytesIO()
    img.save(output, 'PNG')
    raw = render_post(B, P, logo_bytes=output.getvalue(), headline='Remote network management ' * 25)
    assert Image.open(BytesIO(raw)).size == (1080, 1080)

def test_brand_fallback():
    assert colors_for({'colors': ['invalid']}) == ['#24468F', '#C62229']

def test_prompt_grounded():
    prompt = design_prompt(B, P, TEMPLATES[0], (1080, 1080))
    assert 'ISP owners' in prompt and P['title'] in prompt
