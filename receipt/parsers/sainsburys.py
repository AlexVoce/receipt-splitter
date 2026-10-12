from receipt.layout import ReceiptLine
from receipt.models import Receipt
from receipt.parsers.generic import StoreFormat, parse_generic_receipt


SAINSBURYS = StoreFormat(
    store="Sainsbury's",
    symbol_always_printed=True,
)


def parse_sainsburys_receipt(lines: list[ReceiptLine]) -> Receipt:
    return parse_generic_receipt(lines, SAINSBURYS)
