from collections import Counter
from io import BytesIO
from PIL import Image


def extract_colors(data: bytes, count: int = 3) -> list[str]:
    image = Image.open(BytesIO(data)).convert('RGBA')
    image.thumbnail((150, 150))
    pixels = [tuple((c // 24) * 24 for c in rgb[:3]) for rgb in image.getdata() if rgb[3] > 200 and max(rgb[:3]) - min(rgb[:3]) > 25 and min(rgb[:3]) < 225]
    colors = Counter(pixels).most_common(count)
    return ['#%02X%02X%02X' % rgb for rgb, _ in colors] or ['#24468F', '#C62229']
