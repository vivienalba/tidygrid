"""Optional licensed, locally embedded webfonts."""

import base64
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def font_css():
    rules = []
    for family, filename, weight in [
        ('HK Grotesk','HKGrotesk-Regular.woff2',400),
        ('HK Grotesk','HKGrotesk-Semibold.woff2',600),
        ('HK Grotesk','HKGrotesk-Bold.woff2',700),
        ('Proxima Nova','ProximaNova-Regular.woff2',400),
        ('Proxima Nova','ProximaNova-Semibold.woff2',600),
        ('Proxima Nova','ProximaNova-Bold.woff2',700),
    ]:
        path = ROOT / "assets/fonts" / filename
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode()
            rules.append(
                f'@font-face{{font-family:"{family}";src:url(data:font/woff2;base64,{encoded}) format("woff2");font-weight:{weight};font-display:swap;}}'
            )
    return "\n".join(rules)
