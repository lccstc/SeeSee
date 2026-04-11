"""Demo v2: Compact quote card with brand grouping."""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class QuoteLineItem:
    face_range: str
    multiplier: str
    cny_price: float
    ngn_price: float


@dataclass
class QuoteSubSection:
    """A region/currency within a brand."""
    region: str
    items: list[QuoteLineItem] = field(default_factory=list)


@dataclass
class QuoteBrandGroup:
    """All regions under one brand."""
    brand: str
    subsections: list[QuoteSubSection] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(len(s.items) for s in self.subsections)


@dataclass
class QuoteCard:
    ngn_rate: float
    date_str: str
    brand_groups: list[QuoteBrandGroup] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
_SECTION_RE = re.compile(r"^\[(.+)\]$")
_PRICE_RE = re.compile(r"^([\w\d/\-~]+)\s+(?:(\d+)[Xx]\s+)?([\d.]+)$")


def parse_quote_text(text: str, ngn_rate: float) -> QuoteCard:
    card = QuoteCard(ngn_rate=ngn_rate, date_str=date.today().isoformat())
    groups: OrderedDict[str, QuoteBrandGroup] = OrderedDict()
    current_sub: QuoteSubSection | None = None

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = _SECTION_RE.match(line)
        if m:
            parts = m.group(1).rsplit(None, 1)
            brand = parts[0] if len(parts) == 2 else m.group(1)
            region = parts[1] if len(parts) == 2 else ""
            if brand not in groups:
                groups[brand] = QuoteBrandGroup(brand=brand)
            current_sub = QuoteSubSection(region=region)
            groups[brand].subsections.append(current_sub)
            continue

        m = _PRICE_RE.match(line)
        if m and current_sub is not None:
            cny = float(m.group(3))
            current_sub.items.append(
                QuoteLineItem(
                    face_range=m.group(1),
                    multiplier=f"{m.group(2)}X" if m.group(2) else "",
                    cny_price=cny,
                    ngn_price=round(cny * ngn_rate, 2),
                )
            )

    card.brand_groups = list(groups.values())
    return card


# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------
BRAND_COLORS = {
    "Apple": ("#007AFF", "#E8F2FF"),
    "Steam": ("#1B2838", "#E8EDF2"),
    "Razer": ("#00B020", "#E6F9EC"),
    "Xbox": ("#107C10", "#E6F5E6"),
    "Google": ("#4285F4", "#E8F0FE"),
    "PSN": ("#003087", "#E6ECF5"),
}


def _brand_colors(brand: str) -> tuple[str, str]:
    """Return (primary, light_bg) colors for a brand."""
    for key, colors in BRAND_COLORS.items():
        if key.lower() in brand.lower():
            return colors
    return ("#333333", "#F0F0F0")


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------
CARD_WIDTH = 1080
MARGIN_X = 40
CONTENT_W = CARD_WIDTH - 2 * MARGIN_X

# Layout sizes
HEADER_H = 170
BRAND_HDR_H = 48
SUB_HDR_H = 32
COL_HDR_H = 34
ROW_H = 38
BRAND_GAP = 20
FOOTER_H = 70

# Column positions (relative to left edge of content area)
COL_RANGE_X = 16
COL_QTY_X = 260
COL_CNY_X = 440
COL_NGN_X = 660
COL_NGN_END_X = CONTENT_W - 16


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _right_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: str, font: ImageFont.FreeTypeFont):
    """Draw right-aligned text where xy is (right_edge, top)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((xy[0] - w, xy[1]), text, fill=fill, font=font)


def _calc_height(card: QuoteCard) -> int:
    h = HEADER_H + FOOTER_H + 20
    for bg in card.brand_groups:
        h += BRAND_GAP + BRAND_HDR_H + COL_HDR_H
        for sub in bg.subsections:
            h += SUB_HDR_H
            h += len(sub.items) * ROW_H
    return h


def render_quote_card(card: QuoteCard, output_path: str) -> str:
    height = _calc_height(card)
    img = Image.new("RGB", (CARD_WIDTH, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    f_title = _find_font(38)
    f_sub = _find_font(22)
    f_brand = _find_font(24)
    f_region = _find_font(20)
    f_col = _find_font(17)
    f_row = _find_font(20)
    f_footer = _find_font(16)

    # ---- Header ----
    draw.rectangle([(0, 0), (CARD_WIDTH, HEADER_H)], fill="#1A1A2E")
    draw.text((MARGIN_X, 28), "SeeSee Gift Cards", fill="#FFFFFF", font=f_title)
    draw.text((MARGIN_X, 82), f"Date:  {card.date_str}", fill="#AAAACC", font=f_sub)
    draw.text((MARGIN_X, 118), f"NGN Rate:  ¥1 = ₦{card.ngn_rate:g}", fill="#FF6B6B", font=f_sub)
    # accent line
    draw.rectangle([(MARGIN_X, HEADER_H - 4), (CARD_WIDTH - MARGIN_X, HEADER_H)], fill="#E94560")

    y = HEADER_H

    # ---- Brand groups ----
    for bg in card.brand_groups:
        primary, light_bg = _brand_colors(bg.brand)
        y += BRAND_GAP

        # Brand header bar
        draw.rounded_rectangle(
            [(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y + BRAND_HDR_H)],
            radius=8,
            fill=primary,
        )
        draw.text((MARGIN_X + 20, y + 10), bg.brand, fill="#FFFFFF", font=f_brand)
        y += BRAND_HDR_H

        # Column header
        draw.rectangle([(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y + COL_HDR_H)], fill="#EEEEF2")
        lx = MARGIN_X
        draw.text((lx + COL_RANGE_X, y + 7), "Range", fill="#888888", font=f_col)
        draw.text((lx + COL_QTY_X, y + 7), "Qty", fill="#888888", font=f_col)
        draw.text((lx + COL_CNY_X, y + 7), "CNY (¥)", fill="#888888", font=f_col)
        draw.text((lx + COL_NGN_X, y + 7), "NGN (₦)", fill="#888888", font=f_col)
        y += COL_HDR_H

        row_idx = 0
        for sub in bg.subsections:
            # Region sub-header
            draw.rectangle([(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y + SUB_HDR_H)], fill=light_bg)
            draw.text((MARGIN_X + 16, y + 5), f"▸ {sub.region}", fill=primary, font=f_region)
            y += SUB_HDR_H

            for item in sub.items:
                row_bg = "#FFFFFF" if row_idx % 2 == 0 else "#F8F9FB"
                draw.rectangle([(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y + ROW_H)], fill=row_bg)
                lx = MARGIN_X
                draw.text((lx + COL_RANGE_X, y + 8), item.face_range, fill="#333333", font=f_row)
                draw.text((lx + COL_QTY_X, y + 8), item.multiplier, fill="#888888", font=f_row)
                draw.text((lx + COL_CNY_X, y + 8), f"¥{item.cny_price:g}", fill="#333333", font=f_row)
                _right_text(draw, (MARGIN_X + COL_NGN_END_X, y + 8), f"₦{item.ngn_price:,.2f}", fill="#E94560", font=f_row)
                y += ROW_H
                row_idx += 1

        # Bottom line
        draw.line([(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y)], fill="#DDDDDD", width=1)

    # ---- Footer ----
    y += 16
    draw.line([(MARGIN_X, y), (CARD_WIDTH - MARGIN_X, y)], fill="#E0E0E0", width=1)
    y += 10
    draw.text((MARGIN_X, y), "WeChat: Button-Leo    WhatsApp: +852 57006866", fill="#AAAAAA", font=f_footer)
    y += 24
    draw.text((MARGIN_X, y), "Recommend friends to add transactions and receive rewards", fill="#AAAAAA", font=f_footer)

    img.save(output_path, "PNG", optimize=True)
    return output_path


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_text = """
[Apple USA]
100/150 50X 5.57
200-450 50X 5.62
300/400 100X 5.62
500/500 500X 5.62
10-495 5X 5.2

[Apple CAD]
100-150 50X 3.7
200-500 50X 3.7
20-495 5X 3.6

[Apple AUD]
100-500 50X 3.3
10-495 5X 3.2

[Apple UK]
100-200 50X 5.7
10-495 5X 5.35

[Apple DE]
100-200 50X 5.03
10-495 5X 4.95

[Steam USD]
10-200 4.85

[Steam EUR]
10-200 5.72

[Steam GBP]
10-200 6.5

[Steam CHF]
10-200 6.22

[Steam CAD]
10-200 3.45

[Steam AUD]
10-200 3.32

[Steam NZD]
10-200 2.8

[Steam PLN]
10-200 1.26

[Razer USD]
10-500 5.55

[Razer EUR]
10-500 5.2

[Razer UK]
10-500 5.2

[Razer BRA]
10-500 0.9

[Razer SGD]
10-500 4.3

[Razer AUD]
10-500 3.65

[Razer CAD]
10-500 3.2

[Xbox USA]
photo 5.05

[Xbox GBP]
photo 5.9

[Xbox EUR]
photo 5.15
"""

    card = parse_quote_text(sample_text, ngn_rate=196.2)
    out = render_quote_card(card, "/Users/newlcc/SeeSee/repo/demo_quote_card.png")
    print(f"Demo saved: {out}")
    for bg in card.brand_groups:
        regions = ", ".join(f"{s.region}({len(s.items)})" for s in bg.subsections)
        print(f"  {bg.brand}: {regions}")
