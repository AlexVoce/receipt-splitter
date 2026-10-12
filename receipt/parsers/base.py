import re
from decimal import Decimal, InvalidOperation

from receipt.layout import ReceiptLine


# A price at the end of the text: "Card    £14.15", "- £1    .35"
PRICE_PATTERN = re.compile(
    r"(?P<sign>-)?\s*(?P<symbol>£)?\s*(?P<pounds>\d+)\s*\.\s*(?P<pence>\d{2})\s*$"
)

# A price at the start of the text followed by a handwritten mark,
# e.g. someone ticking off items: "£1.90A", "£2.65/2", "-£0.75 / 25".
# At most one letter may follow, so "2.25L PEPSI" isn't a price.
MARKED_PRICE_PATTERN = re.compile(
    r"^(?P<sign>-)?\s*(?P<symbol>£)?\s*(?P<pounds>\d+)\s*\.\s*(?P<pence>\d{2})"
    r"[^A-Za-z]*[A-Za-z]?[^A-Za-z]*$"
)

QUANTITY_PATTERN = re.compile(r"^(?P<quantity>\d+)\s+(?P<description>.+)$")

WEIGHT_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?\s*kg\s*@",
    re.IGNORECASE,
)

EACH_PATTERN = re.compile(
    r"^£?\s*\d+(?:\.\d+)?\s+each$",
    re.IGNORECASE,
)

# "2 @ £1.00", "2 x £1.00" (but not "4 X 330ML COKE")
MULTIBUY_PATTERN = re.compile(
    r"^(?P<quantity>\d+)\s*(?:@\s*£?|[xX]\s*£)\s*\d",
)


def normalise_label(text: str) -> str:
    return re.sub(r"[\s:]+", "", text).lower()

def normalise_price_text(text: str) -> str:
    text = text.strip()

    # Letter O misread for zero inside a number:
    # EO.65 -> E0.65
    text = re.sub(r"(?<=[£€EC\d])O(?=\s*[\d.])", "0", text)

    # Common OCR confusions for the £ symbol, only at the
    # beginning of a monetary value:
    # €2.20 -> £2.20
    # E32.30 -> £32.30
    # -C0.52 -> -£0.52
    text = text.replace("€", "£")
    text = re.sub(r"(?<![A-Za-z])[EC](?=\d)", "£", text)

    # Remove spaces OCR sometimes inserts around decimal points.
    # £0. 55 -> £0.55
    text = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)

    return text

def is_detail_line(text: str) -> bool:
    # Weight, per-unit and multibuy information about an item.
    text = normalise_price_text(text)

    return bool(
        WEIGHT_PATTERN.match(text)
        or EACH_PATTERN.match(text)
        or MULTIBUY_PATTERN.match(text)
    )

def parse_price(
    text: str,
    symbol_always_printed: bool = False,
) -> Decimal | None:
    cleaned = normalise_price_text(text)

    match = PRICE_PATTERN.search(cleaned) or MARKED_PRICE_PATTERN.match(cleaned)

    if not match:
        return None

    sign = -1 if match.group("sign") else 1
    pounds = match.group("pounds")

    # Stores like Tesco always print the £ symbol. When it's missing
    # and the value has a multi-digit pound part, OCR has almost
    # certainly read the £ as a digit:
    # 84.25 -> £4.25
    # -00.30 -> -£0.30
    if symbol_always_printed and not match.group("symbol") and len(pounds) > 1:
        pounds = pounds[1:]

    try:
        value = Decimal(f"{pounds}.{match.group('pence')}")
    except InvalidOperation:
        return None

    return value * sign


def split_description_and_price(
    text: str,
    symbol_always_printed: bool = False,
) -> tuple[str, Decimal | None]:
    parts = re.split(r"\s{2,}", text.strip())

    if len(parts) < 2:
        return text.strip(), None

    possible_price = parse_price(parts[-1], symbol_always_printed)

    if possible_price is None:
        return text.strip(), None

    description = " ".join(parts[:-1]).strip()

    return description, possible_price


def parse_quantity(description: str) -> tuple[int, str]:
    # OCR sometimes puts the description on the following line,
    # leaving only the quantity.
    if description.isdigit():
        return int(description), ""

    match = QUANTITY_PATTERN.match(description)

    if not match:
        return 1, description

    return (
        int(match.group("quantity")),
        match.group("description").strip(),
    )

def get_standalone_price(
    text: str,
    symbol_always_printed: bool = False,
) -> Decimal | None:
    # A line containing only a price, with no description.
    _, price = split_description_and_price(text, symbol_always_printed)

    if price is not None:
        return None

    return parse_price(text, symbol_always_printed)

def get_summary_price(
    lines: list[ReceiptLine],
    index: int,
    symbol_always_printed: bool = False,
) -> tuple[Decimal | None, int]:

    # Try the current line first.
    _, price = split_description_and_price(
        lines[index].text,
        symbol_always_printed,
    )

    if price is not None:
        return price, 1

    # Otherwise try the next physical line.
    if index + 1 < len(lines):
        next_price = parse_price(lines[index + 1].text, symbol_always_printed)

        if next_price is not None:
            return next_price, 2

    return None, 1
