"""Brand colours and fonts, matching the Figma design system."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path(__file__).parent / "fonts"

BERRY = HexColor("#C2185B")
BERRY_DARK = HexColor("#9C0F48")
BERRY_TINT = HexColor("#FCE4EE")
BERRY_WASH = HexColor("#FFF5F9")
INK = HexColor("#1C1220")
INK_MUTED = HexColor("#5E5363")
INK_SOFT = HexColor("#8A8090")
INK_LINE = HexColor("#EFEAF0")
GOLD = HexColor("#C9A24A")
GOLD_TINT = HexColor("#F7EFD9")


@dataclass(frozen=True, slots=True)
class FontSet:
    serif: str
    sans: str
    sans_bold: str


BRAND_FONTS = {
    "PTP-Serif": "DMSerifDisplay-Regular.ttf",
    "PTP-Sans": "PlusJakartaSans-Regular.ttf",
    "PTP-Sans-Bold": "PlusJakartaSans-Bold.ttf",
}
FALLBACK_FONTS = FontSet(
    serif="Times-Roman", sans="Helvetica", sans_bold="Helvetica-Bold"
)


@lru_cache(maxsize=1)
def load_fonts() -> FontSet:
    """Register the brand fonts once, falling back to built-in PDF fonts."""
    paths = {name: FONT_DIR / filename for name, filename in BRAND_FONTS.items()}
    if not all(path.is_file() for path in paths.values()):
        return FALLBACK_FONTS

    for name, path in paths.items():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    return FontSet(serif="PTP-Serif", sans="PTP-Sans", sans_bold="PTP-Sans-Bold")
