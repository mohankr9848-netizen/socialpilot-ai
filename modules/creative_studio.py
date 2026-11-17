"""Offline, brand-aware 2D social graphics rendered with Pillow; no external APIs."""
from io import BytesIO
import re
from PIL import Image, ImageDraw, ImageFont

SIZES = {'Square (1080 × 1080)': (1080,1080), 'Portrait (1080 × 1350)': (1080,1350), 'Story (1080 × 1920)': (1080,1920), 'Landscape (1200 × 628)': (1200,628)}
TEMPLATES = ('Editorial headline', 'Feature spotlight', 'Numbered insight', 'Problem and solution')
FONT_REGULAR='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def colors_for(business):
    supplied=business.get('colors') or []
    if isinstance(supplied,str): supplied=[x.strip() for x in supplied.split(',')]
    good=[x.upper() for x in supplied if isinstance(x,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',x)]
    return (good+['#24468F','#C62229'])[:2]

def _font(n,bold=False):
    try: return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR,max(10,int(n)))
    except OSError: return ImageFont.load_default()

def _wrap(draw,text,font,max_width,max_lines=5):
    words=str(text or '').strip().split()
    lines=[]; current=''
    for word in words:
        proposal=(current+' '+word).strip()
        if draw.textbbox((0,0),proposal,font=font)[2]<=max_width:
            current=proposal
        else:
            if current: lines.append(current)
            current=word
    if current: lines.append(current)
    if len(lines)>max_lines:
        lines=lines[:max_lines]
        while lines[-1] and draw.textbbox((0,0),lines[-1]+'…',font=font)[2]>max_width:
            lines[-1]=lines[-1][:-1]
        lines[-1]=lines[-1].rstrip()+'…'
    return lines

def _headline(draw,text,x,y,width,height,preferred=76,minimum=33,color='#18336B',max_lines=5):
    chosen=None
    for size in range(preferred,minimum-1,-2):
        f=_font(size,True); lines=_wrap(draw,text,f,width,max_lines)
        spacing=int(size*1.26)
        if len(lines)*spacing<=height:
            chosen=(f,lines,spacing); break
    if chosen is None:
        f=_font(minimum,True); lines=_wrap(draw,text,f,width,max_lines); chosen=(f,lines,int(minimum*1.26))
    f,lines,spacing=chosen
    for i,line in enumerate(lines): draw.text((x,y+i*spacing),line,font=f,fill=color)
    return y+len(lines)*spacing

def _rounded(draw,rect,fill,r=24,outline=None,width=3):
    draw.rounded_rectangle(tuple(map(int,rect)),radius=int(r),fill=fill,outline=outline,width=width)

def _logo(canvas,logo_bytes,box):
    if not logo_bytes: return False
    try:
        im=Image.open(BytesIO(logo_bytes)).convert('RGBA')
        im.thumbnail((int(box[2]),int(box[3])),Image.Resampling.LANCZOS)
        canvas.paste(im,(int(box[0]),int(box[1]+(box[3]-im.height)/2)),im)
        return True
    except (OSError,ValueError): return False

def _footer(canvas,draw,brand,logo_bytes,primary,accent,w,h):
    footer_h=min(125,max(76,int(h*.11)))
    y=h-footer_h
    draw.line((65,y, w-65,y),fill='#DCE5F1',width=3)
    if not _logo(canvas,logo_bytes,(72,y+13,min(300,w*.38),footer_h-23)):
        draw.text((75,y+26),brand[:35],font=_font(26,True),fill=primary)
    draw.ellipse((w-107,y+29,w-82,y+54),fill=accent)
    draw.ellipse((w-72,y+29,w-47,y+54),fill=primary)
    return y

def _device(draw,x,y,s,primary,accent):
    _rounded(draw,(x,y,x+s*1.05,y+s*.7),'#FFFFFF',22,primary,5)
    _rounded(draw,(x+18,y+20,x+s*1.05-18,y+s*.7-40),'#EDF4FC',12)
    draw.line((x+s*.13,y+s*.53,x+s*.33,y+s*.38,x+s*.52,y+s*.45,x+s*.79,y+s*.25),fill=accent,width=max(5,int(s*.024)),joint='curve')
    draw.line((x+s*.37,y+s*.7,x+s*.37,y+s*.82),fill=primary,width=9)
    draw.line((x+s*.68,y+s*.7,x+s*.68,y+s*.82),fill=primary,width=9)
    draw.line((x+s*.24,y+s*.82,x+s*.81,y+s*.82),fill=primary,width=9)

def _network(draw,cx,cy,r,primary,accent):
    pts=[(cx,cy-r*.8),(cx-r*.85,cy-r*.12),(cx+r*.85,cy-r*.12),(cx-r*.65,cy+r*.72),(cx+r*.65,cy+r*.72)]
    for px,py in pts[1:]: draw.line((cx,cy,px,py),fill=primary,width=7)
    for i,(px,py) in enumerate(pts):
        radius=r*.22 if i==0 else r*.17
        draw.ellipse((px-radius,py-radius,px+radius,py+radius),fill=accent if i==0 else '#FFFFFF',outline=primary,width=7)
        if i: draw.ellipse((px-8,py-8,px+8,py+8),fill=primary)

def _graphic_label(draw,text,x,y,accent):
    draw.text((x,y),text.upper()[:34],font=_font(22,True),fill=accent)

def _theme(business,post):
    content=' '.join(str(post.get(k) or '') for k in ('title','caption','graphic_prompt','content_pillar')).lower()
    if any(x in content for x in ('network','isp','fiber','router','olt','device','wifi','wi-fi','tr-069','provision','monitor','radius')):
        return 'network'
    if any(x in content for x in ('billing','revenue','payment','sales','profit','finance')):
        return 'finance'
    return 'workflow'

def _visual(draw,rect,primary,accent,theme):
    x0,y0,x1,y1=map(int,rect); width=x1-x0; height=y1-y0
    if width<100 or height<100: return
    _rounded(draw,(x0,y0,x1,y1),'#EEF4FC',32)
    cx=(x0+x1)//2; cy=(y0+y1)//2
    if theme=='network':
        _network(draw,cx,cy,min(width,height)*.34,primary,accent)
    elif theme=='finance':
        base=y0+height*.79; bw=width*.13
        for i,frac in enumerate((.35,.58,.82)):
            bx=x0+width*(.23+i*.22)
            _rounded(draw,(bx,base-height*frac*.62,bx+bw,base),accent if i==2 else primary,10)
        draw.line((x0+width*.18,base+10,x0+width*.83,base+10),fill=primary,width=5)
    else:
        r=min(width,height)*.16
        for i in range(3):
            xx=x0+width*(.13+i*.30); yy=cy-r
            _rounded(draw,(xx,yy,xx+r*1.35,yy+r*2), '#FFFFFF',18,primary,5)
            draw.ellipse((xx+r*.42,yy+r*.35,xx+r*.9,yy+r*.83),fill=accent)
            draw.line((xx+r*.28,yy+r*1.25,xx+r*1.08,yy+r*1.25),fill=primary,width=5)
            if i<2: draw.line((xx+r*1.4,cy,xx+r*1.72,cy),fill=accent,width=7)

def render_post(business,post,template='Editorial headline',size=(1080,1080),logo_bytes=None,headline=None,subtitle=None):
    if template not in TEMPLATES: raise ValueError('Unknown design template')
    w,h=size
    if w<400 or h<400 or w>3000 or h>3000: raise ValueError('Unsupported graphic dimensions')
    primary,accent=colors_for(business)
    title=str(headline if headline is not None else post.get('title') or '').strip() or 'Your headline'
    detail=str(subtitle if subtitle is not None else post.get('content_pillar') or post.get('category') or '').strip()
    brand=str(business.get('name') or 'Your brand')
    theme=_theme(business,post)
    canvas=Image.new('RGB',(w,h),'#FFFFFF'); d=ImageDraw.Draw(canvas)
    landscape=h<800
    margin=int(w*.068)
    footer_top=h-min(125,max(76,int(h*.11)))
    d.rectangle((0,0,w,20 if not landscape else 14),fill=primary)
    if landscape:
        left_width=int(w*.51)
        _graphic_label(d,detail or 'INSIGHTS',margin,60,accent)
        _headline(d,title,margin,113,left_width-margin-22,footer_top-150,preferred=59,minimum=28,color=primary,max_lines=6)
        _visual(d,(left_width+22,75,w-margin,footer_top-26),primary,accent,theme)
    elif template=='Editorial headline':
        _graphic_label(d,detail or 'INSIGHTS',margin,85,accent)
        headline_end=_headline(d,title,margin,145,w-2*margin,int(h*.34),preferred=76,minimum=38,color=primary)
        top=max(headline_end+28,int(h*.48))
        _visual(d,(margin,top,w-margin,footer_top-30),primary,accent,theme)
    elif template=='Feature spotlight':
        _graphic_label(d,'FEATURE SPOTLIGHT',margin,85,accent)
        _visual(d,(margin,145,w-margin,int(h*.52)),primary,accent,theme)
        _headline(d,title,margin,int(h*.55),w-2*margin,footer_top-int(h*.55)-20,preferred=70,minimum=35,color=primary)
    elif template=='Numbered insight':
        _rounded(d,(margin,95,margin+170,265),primary,28)
        d.text((margin+40,133),'01',font=_font(80,True),fill='#FFFFFF')
        _graphic_label(d,detail or 'KEY INSIGHT',margin+205,166,accent)
        end=_headline(d,title,margin,305,w-2*margin,int(h*.31),preferred=75,minimum=35,color=primary)
        _visual(d,(margin,max(end+25,int(h*.62)),w-margin,footer_top-28),primary,accent,theme)
    else:
        _graphic_label(d,'PROBLEM → SOLUTION',margin,80,accent)
        end=_headline(d,title,margin,145,w-2*margin,int(h*.28),preferred=70,minimum=34,color=primary)
        top=max(end+26,int(h*.47))
        gap=18; half=(w-2*margin-gap)/2
        _rounded(d,(margin,top,margin+half,footer_top-30),'#FFF3F1',26)
        _rounded(d,(margin+half+gap,top,w-margin,footer_top-30),'#EEF4FC',26)
        d.text((margin+25,top+22),'CHALLENGE',font=_font(23,True),fill=accent)
        d.text((margin+half+gap+25,top+22),'BETTER WAY',font=_font(23,True),fill=primary)
        d.line((margin+45,top+125,margin+half-45,footer_top-85),fill=accent,width=13)
        d.line((margin+45,footer_top-85,margin+half-45,top+125),fill=accent,width=13)
        _network(d,margin+half+gap+half/2,top+(footer_top-top)*.62,min(half,footer_top-top)*.23,primary,accent)
    _footer(canvas,d,brand,logo_bytes,primary,accent,w,h)
    output=BytesIO(); canvas.save(output,format='PNG',optimize=True)
    return output.getvalue()

def design_prompt(business,post,template,size,headline=None,subtitle=None):
    primary,accent=colors_for(business)
    title=headline if headline is not None else post.get('title','')
    detail=subtitle if subtitle is not None else (post.get('content_pillar') or post.get('category') or '')
    original=post.get('graphic_prompt') or ''
    return (f"Create a polished flat 2D social media design for {business.get('name','the business')}.\n"
            f"Canvas: {size[0]} × {size[1]} pixels. Layout: {template}.\n"
            f"Exact headline: {title}\nSupporting text: {detail}\n"
            f"Primary color: {primary}; accent: {accent}; light background.\n"
            f"Audience: {business.get('audience') or 'the business target audience'}.\n"
            f"Business context: {(business.get('product_description') or business.get('description') or '')[:550]}\n"
            f"Post context: {(post.get('caption') or '')[:550]}\n"
            f"Original creative brief: {original[:650]}\n"
            "Design for legibility at mobile size: bold headline, meaningful topic-specific flat vector diagram or illustration, "
            "balanced composition, restrained shapes and professional spacing. Use the supplied official logo only. "
            "No invented claims, 3D, gradients, glow, glass or unreadably small text.")
