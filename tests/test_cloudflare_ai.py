from io import BytesIO
import base64
import pytest
from PIL import Image
from modules.cloudflare_ai import build_art_prompt, compose_social_graphic, generate_artwork, ImageGenerationError

B={'name':'Example ISP','colors':['#24468F','#C62229'],'audience':'ISP operators','description':'Network monitoring software'}
P={'title':'How OLT monitoring helps ISPs','caption':'Reduce manual diagnostics','graphic_prompt':'An OLT connected to network nodes'}

def test_prompt():
    prompt=build_art_prompt(B,P)
    assert 'OLT monitoring' in prompt and 'No words' in prompt
    assert len(prompt)<=2048

def test_compose_all_sizes():
    for dims in ((1080,1080),(1080,1350),(1080,1920),(1200,628)):
        raw=compose_social_graphic(Image.new('RGB',(512,512),'#aabbcc'),B,P,dims,'Monitor Your OLTs','Network operations')
        assert Image.open(BytesIO(raw)).size==dims

def test_api_response_decode():
    buf=BytesIO();Image.new('RGB',(128,128),'blue').save(buf,'JPEG')
    class Response:
        status_code=200
        def json(self): return {'success':True,'result':{'image':base64.b64encode(buf.getvalue()).decode()}}
    class Session:
        def post(self,*a,**kw):
            assert 'Bearer secret'==kw['headers']['Authorization']
            assert kw['json']['steps']==6
            return Response()
    im=generate_artwork('a'*32,'secret','A network',session=Session())
    assert im.size==(128,128)

def test_auth_error():
    class Response:
        status_code=403
    class Session:
        def post(self,*a,**kw):return Response()
    with pytest.raises(ImageGenerationError,match='authorization'):
        generate_artwork('a'*32,'secret','A network',session=Session())
