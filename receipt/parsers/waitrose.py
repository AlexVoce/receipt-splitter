from receipt.layout import ReceiptLine
from receipt.models import Receipt
from receipt.parsers.generic import StoreFormat, parse_generic_receipt


# Waitrose prints item prices without a £ symbol ("4.10"), with a
# single "£" heading above the price column.
WAITROSE = StoreFormat(
    store="Waitrose",
    symbol_always_printed=False,
)


def parse_waitrose_receipt(lines: list[ReceiptLine]) -> Receipt:
    return parse_generic_receipt(lines, WAITROSE)
