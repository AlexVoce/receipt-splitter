from collections.abc import Callable

from receipt.layout import ReceiptLine
from receipt.models import Receipt
from receipt.parsers.generic import parse_generic_receipt
from receipt.parsers.sainsburys import parse_sainsburys_receipt
from receipt.parsers.tesco import parse_tesco_receipt
from receipt.parsers.waitrose import parse_waitrose_receipt


STORE_PARSERS: dict[str, Callable[[list[ReceiptLine]], Receipt]] = {
    "tesco": parse_tesco_receipt,
    "sainsbury": parse_sainsburys_receipt,
    "waitrose": parse_waitrose_receipt,
}


def detect_store(lines: list[ReceiptLine]) -> str | None:
    # The store name nearest the top wins; footers can mention
    # other sites ("waitrosehaveyoursay.com").
    for line in lines:
        text = line.text.lower()

        for store in STORE_PARSERS:
            if store in text:
                return store

    return None


def parse_receipt(lines: list[ReceiptLine]) -> Receipt:
    store = detect_store(lines)

    if store is None:
        return parse_generic_receipt(lines)

    return STORE_PARSERS[store](lines)
