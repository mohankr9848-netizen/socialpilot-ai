"""Offline, template-based social graphics. No network calls, AI APIs, or fonts bundled."""
from io import BytesIO
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZES = {'Square (1080 × 1080)': (1080, 1080), 'Portrait (1080 × 1350)': (1080, 1350), 'Story (1080 × 1920)': (1080, 1920), 'Landscape (1200 × 628)': (1200, 628)}
TEMPLATES = ('Editorial headline', 'Feature spotlight', 'Numbered insight', 'Problem and solution')
FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def colors_for(business):
    supplied = business.get('colors') or []
    if isinstance(supplied, str):
        supplied = [x.strip() for x in supplied.split(',')]
    good = [x.upper() for x in supplied if isinstance(x, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', x)]
    return (good + ['#24468F', '#C62229'])[:2]


def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)
    except OSError:
        return ImageFont.load_default()


def _wrap(draw, text, font, width, max_lines=5):
    words = re.sub(r'\s+', ' ', str(text or '')).strip().split(' ')
    lines, current = [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + '…', font=font)[2] > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines


def _fit_title(draw, title, width, max_height):
    for size in range(86, 29, -3):
        font = _font(size, True)
        lines = _wrap(draw, title, font, width, 6)
        step = int(size * 1.27)
        if len(lines) * step <= max_height:
            return font, lines, step
    font = _font(30, True)
    return font, _wrap(draw, title, font, width, max(2, max_height // 40)), 40


def _logo(canvas, logo_bytes, box):
    if not logo_bytes:
        return False
    try:
        logo = Image.open(BytesIO(logo_bytes)).convert('RGBA')
        logo.thumbnail((box[2], box[3]), Image.Resampling.LANCZOS)
        canvas.paste(logo, (box[0], box[1] + (box[3] - logo.height) // 2), logo)
        return True
    except (OSError, ValueError):
        return False


def render_post(business, post, template='Editorial headline', size=(1080, 1080), logo_bytes=None, headline=None, subtitle=None):
    """Return PNG bytes. All input text is user/business data; never render HTML."""
    if template not in TEMPLATES:
        raise ValueError('Unknown design template')
    w, h = size
    if w < 400 or h < 400 or w > 3000 or h > 3000:
        raise ValueError('Unsupported graphic dimensions')
    primary, accent = colors_for(business)
    canvas = Image.new('RGB', (w, h), '#FFFFFF')
    draw = ImageDraw.Draw(canvas)
    margin = int(w * .075)
    title = (headline if headline is not None else post.get('title', '')).strip() or 'Your headline'
    detail = (subtitle if subtitle is not None else post.get('content_pillar', '') or post.get('category', '')).strip()
    brand = str(business.get('name') or 'Your brand')[:80]
    # restrained brand geometry; no gradients, glass, or external image dependencies
    if template == 'Editorial headline':
        draw.rectangle((0, 0, w, int(h * .055)), fill=primary)
        draw.rectangle((margin, int(h * .26), margin + 90, int(h * .27)), fill=accent)
    elif template == 'Feature spotlight':
        draw.rectangle((int(w * .68), 0, w, h), fill=primary)
        draw.rounded_rectangle((int(w * .72), int(h * .30), int(w * .93), int(h * .58)), radius=24, fill='#FFFFFF')
        draw.line((int(w * .77), int(h * .42), int(w * .81), int(h * .46), int(w * .89), int(h * .36)), fill=accent, width=14, joint='curve')
    elif template == 'Numbered insight':
        draw.rounded_rectangle((margin, int(h * .22), margin + 150, int(h * .22) + 150), radius=25, fill=primary)
        draw.text((margin + 37, int(h * .22) + 33), '01', font=_font(66, True), fill='#FFFFFF')
    else:
        draw.rectangle((0, 0, int(w * .05), h), fill=accent)
        draw.rounded_rectangle((int(w * .70), int(h * .29), int(w * .92), int(h * .47)), radius=24, fill=primary)
        draw.text((int(w * .735), int(h * .34)), '→', font=_font(85, True), fill='#FFFFFF')
    text_width = int(w * (.56 if template in ('Feature spotlight', 'Problem and solution') else .83))
    top = int(h * (.39 if template == 'Numbered insight' else .32))
    if h < 800:
        top = int(h * .23)
    title_height = min(int(h * .40), h - top - int(h * .20))
    font, lines, step = _fit_title(draw, title, text_width, title_height)
    for i, line in enumerate(lines):
        draw.text((margin, top + i * step), line, font=font, fill=primary)
    bottom_title = top + len(lines) * step
    if detail and bottom_title + 70 < h * .82:
        detail_font = _font(28)
        for i, line in enumerate(_wrap(draw, detail, detail_font, text_width, 2)):
            draw.text((margin, bottom_title + 26 + i * 40), line, font=detail_font, fill='#555D6A')
    footer_y = int(h * .89)
    draw.line((margin, footer_y - 24, w - margin, footer_y - 24), fill='#DDE3EA', width=3)
    if not _logo(canvas, logo_bytes, (margin, footer_y, int(w * .24), int(h * .075))):
        draw.text((margin, footer_y + 4), brand, font=_font(27, True), fill=primary)
    out = BytesIO()
    canvas.save(out, format='PNG', optimize=True)
    return out.getvalue()


def design_prompt(business, post, template, size, headline=None, subtitle=None):
    primary, accent = colors_for(business)
    title = headline if headline is not None else post.get('title', '')
    detail = subtitle if subtitle is not None else (post.get('content_pillar') or post.get('category') or '')
    original = post.get('graphic_prompt') or ''
    return (f"Create a polished, flat 2D social media graphic for {business.get('name', 'the business')}.\n"
            f"Canvas: {size[0]} × {size[1]} pixels. Layout: {template}.\n"
            f"Headline (exact): {title}\nSupporting line: {detail}\n"
            f"Brand colors: primary {primary}; accent {accent}; white background.\n"
            f"Target audience: {business.get('audience') or 'the business target audience'}.\n"
            f"Business context: {(business.get('product_description') or business.get('description') or '')[:550]}\n"
            f"Post context: {(post.get('caption') or '')[:550]}\n"
            f"Original calendar creative brief: {original[:650]}\n"
            "Use clear typography, generous whitespace, a simple relevant vector illustration, and accessible contrast. "
            "Use the official logo only if supplied separately. Avoid gradients, 3D, glass, glow, invented statistics and unsupported product claims. "
            "Keep all text legible and leave space for the brand logo."
           )
