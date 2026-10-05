"""Locally served genuine fonts; embedded copies for portable exports."""
import base64
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
@lru_cache(maxsize=2)
def font_css(embed=False):
    rules=[]
    for family,stem in [('HK Grotesk','HKGrotesk'),('Metropolis','Metropolis')]:
        for suffix,weight in [('Regular',400),('Semibold',600),('Bold',700)]:
            filename=f'{stem}-{suffix}.woff2'
            path=ROOT/'static/fonts'/filename
            if path.exists():
                src=('data:font/woff2;base64,'+base64.b64encode(path.read_bytes()).decode()) if embed else '/app/static/fonts/'+filename
                rules.append(f'@font-face{{font-family:"{family}";src:url("{src}") format("woff2");font-weight:{weight};font-display:swap;}}')
    return '\n'.join(rules)
