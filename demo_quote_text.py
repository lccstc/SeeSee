"""Demo: Generate clean WhatsApp text quote formats."""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date


@dataclass
class QuoteLineItem:
    face_range: str
    multiplier: str
    cny_price: float
    ngn_price: float


@dataclass
class QuoteSubSection:
    region: str
    items: list[QuoteLineItem] = field(default_factory=list)


@dataclass
class QuoteBrandGroup:
    brand: str
    subsections: list[QuoteSubSection] = field(default_factory=list)


@dataclass
class QuoteCard:
    ngn_rate: float
    date_str: str
    brand_groups: list[QuoteBrandGroup] = field(default_factory=list)


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


def _ngn_fmt(v: float) -> str:
    """Format NGN price: drop decimals if .00"""
    if v == int(v):
        return f"{int(v):,}"
    return f"{v:,.2f}"


# =====================================================================
# Format A: Clean structured — bold headers + aligned rows
# =====================================================================
def format_a(card: QuoteCard) -> str:
    lines: list[str] = []
    lines.append(f"*SeeSee Gift Cards*")
    lines.append(f"{card.date_str}  |  ¥1 = ₦{card.ngn_rate:g}")
    lines.append("━" * 32)

    for bg in card.brand_groups:
        # Check if brand is "compact" (every subsection has exactly 1 item)
        is_compact = all(len(s.items) == 1 for s in bg.subsections)

        if is_compact:
            lines.append("")
            lines.append(f"*{bg.brand}*")
            for sub in bg.subsections:
                item = sub.items[0]
                rng = f"{item.face_range}" if item.face_range != "photo" else "photo"
                lines.append(
                    f"{sub.region:<4} {rng:<8} ¥{item.cny_price:<6g} ₦{_ngn_fmt(item.ngn_price)}"
                )
        else:
            for sub in bg.subsections:
                lines.append("")
                lines.append(f"*{bg.brand} {sub.region}*")
                for item in sub.items:
                    qty = f" {item.multiplier}" if item.multiplier else ""
                    lines.append(
                        f"  {item.face_range:<8}{qty:<6} ¥{item.cny_price:<6g} ₦{_ngn_fmt(item.ngn_price)}"
                    )

    lines.append("")
    lines.append("━" * 32)
    lines.append("WeChat: Button-Leo")
    lines.append("WhatsApp: +852 57006866")

    return "\n".join(lines)


# =====================================================================
# Format B: Monospace block for perfect alignment
# =====================================================================
def format_b(card: QuoteCard) -> str:
    lines: list[str] = []
    lines.append(f"*SeeSee Gift Cards*")
    lines.append(f"{card.date_str}  ¥1 = ₦{card.ngn_rate:g}")
    lines.append("")
    lines.append("```")

    for bg in card.brand_groups:
        is_compact = all(len(s.items) == 1 for s in bg.subsections)

        if is_compact:
            lines.append(f"[ {bg.brand} ]")
            for sub in bg.subsections:
                item = sub.items[0]
                rng = item.face_range
                lines.append(
                    f" {sub.region:<4} {rng:<7} ¥{item.cny_price:<5g}  ₦{_ngn_fmt(item.ngn_price):>8}"
                )
            lines.append("")
        else:
            for sub in bg.subsections:
                lines.append(f"[ {bg.brand} {sub.region} ]")
                for item in sub.items:
                    qty = item.multiplier if item.multiplier else "   "
                    lines.append(
                        f" {item.face_range:<8} {qty:<5} ¥{item.cny_price:<5g}  ₦{_ngn_fmt(item.ngn_price):>8}"
                    )
                lines.append("")

    lines.append("```")
    lines.append("WeChat: Button-Leo | WA: +852 57006866")

    return "\n".join(lines)


# =====================================================================
# Format C: Minimal — pipe-separated, very clean
# =====================================================================
def format_c(card: QuoteCard) -> str:
    lines: list[str] = []
    lines.append(f"*SeeSee*  {card.date_str}")
    lines.append(f"Rate ¥1 = ₦{card.ngn_rate:g}")
    lines.append("─" * 30)

    for bg in card.brand_groups:
        is_compact = all(len(s.items) == 1 for s in bg.subsections)
        lines.append("")
        lines.append(f"▎*{bg.brand}*")

        if is_compact:
            for sub in bg.subsections:
                item = sub.items[0]
                lines.append(f"  {sub.region} {item.face_range} │ ¥{item.cny_price:g} │ ₦{_ngn_fmt(item.ngn_price)}")
        else:
            for sub in bg.subsections:
                lines.append(f"  *{sub.region}*")
                for item in sub.items:
                    qty = f"({item.multiplier})" if item.multiplier else ""
                    lines.append(f"  {item.face_range}{qty} │ ¥{item.cny_price:g} │ ₦{_ngn_fmt(item.ngn_price)}")

    lines.append("")
    lines.append("─" * 30)
    lines.append("Leo | WA +852 57006866")

    return "\n".join(lines)


# =====================================================================
SAMPLE = """
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

if __name__ == "__main__":
    card = parse_quote_text(SAMPLE, ngn_rate=196.2)

    print("=" * 50)
    print("FORMAT A — Bold headers + smart compact")
    print("=" * 50)
    print(format_a(card))

    print("\n\n")
    print("=" * 50)
    print("FORMAT B — Monospace block (perfect alignment)")
    print("=" * 50)
    print(format_b(card))

    print("\n\n")
    print("=" * 50)
    print("FORMAT C — Minimal pipe-separated")
    print("=" * 50)
    print(format_c(card))
