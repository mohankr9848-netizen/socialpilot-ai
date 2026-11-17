"""Optional free-tier Cloudflare Workers AI artwork generation.

No secrets are logged, returned to the UI, or written to disk.
"""
import base64
from io import BytesIO
import re
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from modules.creative_studio import colors_for, suggest_graphic_copy

MODEL = '@cf/black-forest-labs/flux-1-schnell'
API_ROOT = 'https://api.cloudflare.com/client/v4/accounts'

class ImageGenerationError(RuntimeError):
    pass


def build_art_prompt(business, post, visual_style='Clean editorial illustration'):
    """Describe artwork ONLY; branding/text is composited locally."""
    topic = str(post.get('title') or 'business operations').strip()[:220]
    brief = str(post.get('graphic_prompt') or '').strip()[:400]
    audience = str(business.get('audience') or 'business decision makers')[:140]
    product = str(business.get('product_description') or business.get('description') or '')[:260]
    primary, accent = colors_for(business)
    prompt = (
        f'Create a premium, professional B2B marketing editorial illustration about: {topic}. '
        f'Visual subject and creative direction: {brief}. Business context: {product}. '
        f'Intended viewers: {audience}. Style: {visual_style}. '
        f'Brand-inspired color palette {primary}, {accent}, white, soft neutral gray. '
        'Strong clear focal point, sophisticated composition, rich meaningful visual detail, '
        'clean corporate aesthetic, sharp edges, attractive balanced lighting. '
        'Full-bleed artwork, no margins. No words, no lettering, no typography, '
        'no logos, no watermarks, no fake dashboards with tiny text. '
        'Avoid generic abstract swirls, avoid unrelated symbols, avoid clutter.'
    )
    return prompt[:2048]


def generate_artwork(account_id, api_token, prompt, steps=6, timeout=90, session=None):
    """Return decoded PIL RGB image; handles Cloudflare JSON envelope and errors."""
    account_id = str(account_id or '').strip()
    api_token = str(api_token or '').strip()
    if not re.fullmatch(r'[a-fA-F0-9]{32}', account_id):
        raise ImageGenerationError('Cloudflare Account ID should be a 32-character hexadecimal value.')
    if not api_token:
        raise ImageGenerationError('Cloudflare API token is missing from Streamlit Secrets.')
    if not prompt or not prompt.strip():
        raise ImageGenerationError('Please provide a visual prompt.')
    url = f'{API_ROOT}/{account_id}/ai/run/{MODEL}'
    caller = session or requests
    try:
        response = caller.post(url, headers={'Authorization': f'Bearer {api_token}', 'Content-Type':'application/json'},
                               json={'prompt':prompt[:2048], 'steps':max(1,min(8,int(steps)))}, timeout=timeout)
    except requests.RequestException as exc:
        raise ImageGenerationError('Cloudflare could not be reached. Check your internet connection and try again.') from exc
    if response.status_code in (401,403):
        raise ImageGenerationError('Cloudflare authorization failed. Check the Account ID, API token and Workers AI permission.')
    if response.status_code == 429:
        raise ImageGenerationError('Cloudflare rate limit reached. Try later or use the free template fallback.')
    if response.status_code >= 400:
        raise ImageGenerationError(f'Cloudflare returned HTTP {response.status_code}. Check Workers AI free quota and dashboard.')
    try:
        data = response.json()
        if data.get('success') is False:
            raise ImageGenerationError('Cloudflare reported an unsuccessful generation. Check the Workers AI dashboard.')
        payload = data.get('result', data)
        encoded = payload.get('image') if isinstance(payload,dict) else None
        if not encoded:
            raise ImageGenerationError('Cloudflare returned no image. Try another prompt.')
        raw = base64.b64decode(encoded,validate=True)
        if len(raw)>18_000_000:
            raise ImageGenerationError('The generated image is too large to process.')
        im = Image.open(BytesIO(raw))
        im.load()
        if im.width<64 or im.height<64:
            raise ImageGenerationError('Cloudflare returned an unexpectedly small image.')
        return im.convert('RGB')
    except (ValueError,TypeError,KeyError,OSError,base64.binascii.Error) as exc:
        raise ImageGenerationError('Could not decode the image returned by Cloudflare.') from exc


def _font(size,bold=False):
    path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try: return ImageFont.truetype(path,int(size))
    except OSError: return ImageFont.load_default()


def _fit_lines(draw, text, width, max_height, start=78, min_size=27, max_lines=4):
    text=' '.join(str(text or '').split())
    for font_size in range(start,min_size-1,-2):
        font=_font(font_size,True)
        lines=[]; line=''
        for word in text.split():
            candidate=(line+' '+word).strip()
            if draw.textbbox((0,0),candidate,font=font)[2] <= width:
                line=candidate
            else:
                if line: lines.append(line)
                line=word
        if line: lines.append(line)
        line_height=int(font_size*1.32)
        if len(lines)<=max_lines and len(lines)*line_height<=max_height:
            return lines,font,line_height
    font=_font(min_size,True)
    words=text.split(); lines=[]; line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]<=width: line=candidate
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    if len(lines)>max_lines:
        lines=lines[:max_lines]
        while lines[-1] and draw.textbbox((0,0),lines[-1]+'…',font=font)[2]>width:
            lines[-1]=lines[-1][:-1]
        lines[-1]=lines[-1].rstrip()+'…'
    return lines,font,int(min_size*1.32)


def compose_social_graphic(artwork, business, post, size, headline=None, subtitle=None, logo_bytes=None):
    """AI artwork plus deterministic, exact text and optional original logo."""
    w,h=map(int,size)
    if w<400 or h<400 or w>3000 or h>3000: raise ValueError('Unsupported dimensions')
    primary,accent=colors_for(business)
    suggested_head,suggested_sub=suggest_graphic_copy(post)
    headline=str(headline if headline is not None else suggested_head).strip() or suggested_head
    subtitle=str(subtitle if subtitle is not None else suggested_sub).strip()
    image=Image.new('RGB',(w,h),'#FFFFFF')
    d=ImageDraw.Draw(image)
    m=int(w*.065)
    top_h=int(h*(.36 if h>=w else .59))
    footer_h=max(74,int(h*.10))
    art_top=top_h
    art_bottom=h-footer_h
    if art_bottom-art_top<120: art_top=max(140,int(h*.3))
    image.paste(ImageOps.fit(artwork.convert('RGB'),(w,art_bottom-art_top),method=Image.Resampling.LANCZOS,centering=(.5,.5)),(0,art_top))
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,w,max(13,int(h*.014))),fill=primary)
    d.rounded_rectangle((m,int(h*.052),m+int(w*.15),int(h*.059)),radius=4,fill=accent)
    d.text((m,int(h*.083)),'BUSINESS INSIGHTS',font=_font(max(16,int(w*.020)),True),fill=accent)
    title_y=int(h*.13)
    available_h=top_h-title_y-int(h*.055)
    lines,font,line_h=_fit_lines(d,headline,w-2*m,available_h,start=int(w*(.069 if h>=w else .052)),min_size=max(25,int(w*.026)))
    for line in lines:
        d.text((m,title_y),line,font=font,fill=primary)
        title_y+=line_h
    if subtitle and title_y+int(h*.045)<top_h:
        sub_font=_font(max(15,int(w*.019)))
        words=subtitle.split(); line=''
        for word in words:
            cand=(line+' '+word).strip()
            if d.textbbox((0,0),cand,font=sub_font)[2]<w-2*m: line=cand
            else: break
        if line: d.text((m,title_y+int(h*.009)),line,font=sub_font,fill='#475569')
    d.rectangle((0,art_bottom,w,h),fill='#FFFFFF')
    d.line((m,art_bottom,w-m,art_bottom),fill='#E2E8F0',width=2)
    brand=str(business.get('name') or 'Your brand')
    logo_ok=False
    if logo_bytes:
        try:
            logo=Image.open(BytesIO(logo_bytes)).convert('RGBA')
            logo.thumbnail((int(w*.36),int(footer_h*.70)),Image.Resampling.LANCZOS)
            image.paste(logo,(m,art_bottom+(footer_h-logo.height)//2),logo)
            logo_ok=True
        except (ValueError,OSError): pass
    if not logo_ok:
        d.text((m,art_bottom+footer_h*.31),brand[:35],font=_font(max(16,int(w*.025)),True),fill=primary)
    d.ellipse((w-m-34,art_bottom+footer_h*.40,w-m-8,art_bottom+footer_h*.40+26),fill=accent)
    output=BytesIO(); image.save(output,format='PNG',optimize=True)
    return output.getvalue()
