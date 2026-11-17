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



def suggest_graphic_copy(post):
    """Produce concise, claim-safe graphic copy using only topic keywords."""
    title=re.sub(r'\s+', ' ', str(post.get('title') or '').strip())
    lower=title.lower()
    # The rules change the *presentation*, not the underlying product claims.
    phrases=[
        (('comprehensive isp management','isp management suite'), 'One Platform. Connected ISP Operations.', 'Bring ISP workflows into focus.'),
        (('tr-069','remote provisioning','zero-touch'), 'Simplify Remote Device Management', 'Provision, configure and support devices remotely.'),
        (('fiber fault','fiber network'), 'Make Fiber Networks Easier to Manage', 'Visibility across routes, assets and incidents.'),
        (('billing','revenue'), 'Make Every Billing Step Count', 'Connect the operational and financial picture.'),
        (('network automation','network monitoring'), 'See Network Issues Earlier', 'From monitoring to more proactive operations.'),
        (('helpdesk','support ticket'), 'Make Support Work Smarter', 'Keep tickets, owners and follow-ups connected.'),
        (('timesheet','resource allocation'), 'Turn Work Data into Clarity', 'Connect effort, capacity and decisions.'),
    ]
    for keys,head,sub in phrases:
        if any(key in lower for key in keys): return head,sub
    # Remove template filler and preserve substantive words rather than inventing facts.
    title=re.sub(r'(?i)^(how|why|explain|understanding|getting started with)\s+', '', title)
    title=re.sub(r'(?i)\s*[:—-]\s*a practical guide.*$', '', title)
    title=re.sub(r'(?i)\s+connects? to the priorities of the intended audience.*$', '', title)
    title=re.sub(r'(?i)\s+for (isp owners and founders|the intended audience).*$', '', title)
    words=title.split()
    if len(words)>9: title=' '.join(words[:9]).rstrip(',:;')
    return title or 'Business Insights', 'A closer look at the topic that matters.'


def _text_block(draw, text, xy, width, height, preferred, min_size, fill, max_lines=4):
    x,y=xy
    for size in range(preferred,min_size-1,-2):
        font=_font(size,True)
        lines=_wrap(draw,text,font,width,max_lines)
        line_h=int(size*1.27)
        if len(lines)*line_h<=height and all(draw.textbbox((0,0),line,font=font)[2]<=width for line in lines):
            break
    else:
        size=min_size; font=_font(size,True); lines=_wrap(draw,text,font,width,max_lines); line_h=int(size*1.27)
    for line in lines:
        draw.text((x,y),line,font=font,fill=fill)
        y+=line_h
    return y


def _visual_story(draw,rect,primary,accent,theme):
    x0,y0,x1,y1=map(int,rect)
    if x1-x0<120 or y1-y0<120: return
    _rounded(draw,(x0,y0,x1,y1),'#EFF4FB',34)
    W=x1-x0; H=y1-y0
    if theme=='network':
        # Distinct connected network devices, central management dashboard, labelled flow.
        cy=y0+H*.53
        _rounded(draw,(x0+W*.34,y0+H*.22,x0+W*.66,y0+H*.77),'#FFFFFF',20,primary,5)
        draw.rectangle((x0+W*.38,y0+H*.29,x0+W*.62,y0+H*.55),fill='#DFE9F8')
        for i in range(3):
            draw.rounded_rectangle((x0+W*.4,y0+H*(.32+i*.07),x0+W*.6,y0+H*(.35+i*.07)),radius=5,fill=primary if i<2 else accent)
        for side in (-1,1):
            xx=x0+W*(.14 if side<0 else .86)
            for offset in (-.18,.18):
                yy=cy+H*offset
                draw.line((xx,yy,x0+W*(.34 if side<0 else .66),cy),fill=primary,width=6)
                _rounded(draw,(xx-W*.065,yy-H*.07,xx+W*.065,yy+H*.07),'#FFFFFF',14,primary,4)
                draw.ellipse((xx-7,yy-7,xx+7,yy+7),fill=accent)
        draw.text((x0+W*.39,y0+H*.82),'CENTRAL CONTROL',font=_font(max(16,int(W*.027)),True),fill=primary)
    elif theme=='finance':
        for i,v in enumerate((.37,.55,.72,.88)):
            x=x0+W*(.15+i*.18); bottom=y0+H*.78
            _rounded(draw,(x,bottom-H*v*.63,x+W*.115,bottom),primary if i<3 else accent,12)
        draw.line((x0+W*.13,y0+H*.8,x0+W*.88,y0+H*.8),fill=primary,width=5)
        draw.text((x0+W*.18,y0+H*.12),'PERFORMANCE AT A GLANCE',font=_font(max(17,int(W*.028)),True),fill=primary)
    else:
        for i,label in enumerate(('PLAN','EXECUTE','IMPROVE')):
            x=x0+W*(.075+i*.31); y=y0+H*.29
            _rounded(draw,(x,y,x+W*.24,y+H*.38),'#FFFFFF',20,primary,4)
            draw.ellipse((x+W*.085,y+H*.07,x+W*.155,y+H*.19),fill=accent)
            draw.text((x+W*.035,y+H*.24),label,font=_font(max(16,int(W*.023)),True),fill=primary)
            if i<2:
                draw.line((x+W*.245,y+H*.19,x+W*.29,y+H*.19),fill=accent,width=7)


def render_post(business,post,template='Editorial headline',size=(1080,1080),logo_bytes=None,headline=None,subtitle=None):
    if template not in TEMPLATES: raise ValueError('Unknown design template')
    w,h=size
    if w<400 or h<400 or w>3000 or h>3000: raise ValueError('Unsupported graphic dimensions')
    primary,accent=colors_for(business)
    recommended_title,recommended_sub=suggest_graphic_copy(post)
    title=str(headline if headline is not None else recommended_title).strip() or recommended_title
    detail=str(subtitle if subtitle is not None else recommended_sub).strip()
    brand=str(business.get('name') or 'Your brand')
    theme=_theme(business,post)
    im=Image.new('RGB',(w,h),'#FFFFFF'); d=ImageDraw.Draw(im)
    m=int(w*.07); footer_y=h-max(92,int(h*.105)); landscape=h<800
    d.rectangle((0,0,w,max(18,int(h*.018))),fill=primary)
    d.rounded_rectangle((m,int(h*.064),m+int(w*.17),int(h*.073)),radius=5,fill=accent)
    if landscape:
        left=int(w*.54)
        d.text((m,70),'BUSINESS INSIGHTS',font=_font(23,True),fill=accent)
        end=_text_block(d,title,(m,115),left-m-20,270,58,36,primary,4)
        _wrap_sub(d,detail,m,end+12,left-m-35,26,primary)
        _visual_story(d,(left+14,70,w-m,footer_y-20),primary,accent,theme)
    elif template=='Feature spotlight':
        _visual_story(d,(m,int(h*.115),w-m,int(h*.55)),primary,accent,theme)
        d.text((m,int(h*.575)),'FEATURE SPOTLIGHT',font=_font(25,True),fill=accent)
        end=_text_block(d,title,(m,int(h*.625)),w-2*m,int(h*.21),75,43,primary,4)
        _wrap_sub(d,detail,m,min(end+10,footer_y-65),w-2*m,25,primary)
    elif template=='Numbered insight':
        _rounded(d,(m,int(h*.115),m+135,int(h*.115)+130),primary,25)
        d.text((m+32,int(h*.133)),'01',font=_font(75,True),fill='#FFFFFF')
        d.text((m+165,int(h*.16)),'KEY INSIGHT',font=_font(28,True),fill=accent)
        end=_text_block(d,title,(m,int(h*.31)),w-2*m,int(h*.24),82,44,primary,4)
        _visual_story(d,(m,max(end+28,int(h*.57)),w-m,footer_y-25),primary,accent,theme)
    elif template=='Problem and solution':
        d.text((m,int(h*.10)),'PROBLEM  /  SOLUTION',font=_font(27,True),fill=accent)
        end=_text_block(d,title,(m,int(h*.18)),w-2*m,int(h*.26),78,42,primary,4)
        top=max(end+25,int(h*.49)); gap=18; half=(w-2*m-gap)/2
        _rounded(d,(m,top,m+half,footer_y-25),'#FCEFED',26)
        _rounded(d,(m+half+gap,top,w-m,footer_y-25),'#EFF4FB',26)
        d.text((m+20,top+24),'THE CHALLENGE',font=_font(23,True),fill=accent)
        d.text((m+half+gap+20,top+24),'THE BETTER WAY',font=_font(23,True),fill=primary)
        d.line((m+70,top+135,m+half-70,footer_y-115),fill=accent,width=12)
        d.line((m+70,footer_y-115,m+half-70,top+135),fill=accent,width=12)
        _visual_story(d,(m+half+gap+20,top+80,w-m-20,footer_y-45),primary,accent,theme)
    else:
        d.text((m,int(h*.115)),'INDUSTRY INSIGHTS',font=_font(26,True),fill=accent)
        end=_text_block(d,title,(m,int(h*.19)),w-2*m,int(h*.28),84,44,primary,4)
        _wrap_sub(d,detail,m,end+15,w-2*m,27,primary)
        _visual_story(d,(m,max(end+100,int(h*.55)),w-m,footer_y-25),primary,accent,theme)
    _footer(im,d,brand,logo_bytes,primary,accent,w,h)
    out=BytesIO(); im.save(out,format='PNG',optimize=True); return out.getvalue()


def _wrap_sub(draw,text,x,y,width,size,color):
    f=_font(size)
    for line in _wrap(draw,text,f,width,2):
        draw.text((x,y),line,font=f,fill=color)
        y+=int(size*1.5)


def design_prompt(business,post,template,size,headline=None,subtitle=None):
    primary,accent=colors_for(business)
    suggested_title,suggested_sub=suggest_graphic_copy(post)
    title=headline if headline is not None else suggested_title
    detail=subtitle if subtitle is not None else suggested_sub
    return (f"Design a polished, flat 2D B2B social graphic for {business.get('name','the business')}.\n"
            f"Canvas: {size[0]} × {size[1]} px. Layout: {template}.\n"
            f"Exact headline: {title}\nSupporting line: {detail}\n"
            f"Brand colors: {primary} and {accent}. Audience: {business.get('audience') or 'business audience'}.\n"
            f"Original calendar topic: {post.get('title') or ''}\n"
            f"Post context: {str(post.get('caption') or '')[:550]}\n"
            f"Product context: {str(business.get('description') or '')[:400]}\n"
            f"Creative brief: {str(post.get('graphic_prompt') or '')[:500]}\n"
            "Use oversized readable typography, topic-specific vector diagrams, balanced composition, generous but purposeful whitespace, "
            "logo and brand footer. No invented statistics, glass, glow, 3D or microscopic text.")
