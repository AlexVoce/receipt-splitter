import re
from dataclasses import dataclass

from receipt.layout import ReceiptLine
from receipt.models import PriceAdjustment, Receipt, ReceiptItem
from receipt.parsers.base import (
    MULTIBUY_PATTERN,
    get_summary_price,
    is_detail_line,
    normalise_label,
    normalise_price_text,
    parse_price,
    split_description_and_price,
)


@dataclass(frozen=True)
class StoreFormat:
    store: str | None = None

    # Whether every item price is printed with a £ symbol. If so, a
    # missing symbol means OCR has misread it as a digit.
    symbol_always_printed: bool = False

    subtotal_labels: tuple[str, ...] = ("subtotal",)
    total_labels: tuple[str, ...] = ("balancedue", "total", "amountdue")


def get_label(description: str) -> str:
    # Drop a leading item count: "8 BALANCE DUE" -> "balancedue"
    return normalise_label(re.sub(r"^\d+\s+", "", description))


def parse_generic_receipt(
    lines: list[ReceiptLine],
    store_format: StoreFormat = StoreFormat(),
) -> Receipt:
    """Parse receipts that print one item per line with the price on
    the right, and only wrap onto a second line for weight or
    multibuy details. Sainsbury's and Waitrose work like this.
    """
    symbol_always_printed = store_format.symbol_always_printed

    receipt = Receipt(store=store_format.store)

    current_item: ReceiptItem | None = None
    # A description whose price is on the following detail line, e.g.
    # "LOOSE BANANAS" then "0.95 kg @ £0.80/kg    £0.76".
    pending_description: str | None = None
    in_items_section = False
    in_summary_section = False

    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        text = line.text.strip()

        if not text:
            continue

        description, price = split_description_and_price(
            text,
            symbol_always_printed,
        )

        # The item section starts at the first line containing both
        # a description and a price.
        if not in_items_section and description and price is not None:
            in_items_section = True

        if not in_items_section:
            continue

        label = get_label(description)

        if label.startswith(store_format.subtotal_labels):
            receipt.subtotal, consumed = get_summary_price(
                lines,
                index - 1,
                symbol_always_printed,
            )
            index += consumed - 1
            in_summary_section = True
            continue

        if label.startswith(store_format.total_labels):
            receipt.total, _ = get_summary_price(
                lines,
                index - 1,
                symbol_always_printed,
            )
            break

        if in_summary_section:
            continue

        # Weight / per-unit / multibuy information.
        if is_detail_line(description):
            if pending_description is not None and price is not None:
                multibuy = MULTIBUY_PATTERN.match(
                    normalise_price_text(description)
                )

                current_item = ReceiptItem(
                    description=pending_description,
                    price=price,
                    quantity=int(multibuy.group("quantity")) if multibuy else 1,
                    details=[description],
                )
                receipt.items.append(current_item)
                pending_description = None

            elif current_item is not None:
                current_item.details.append(text)

            continue

        if price is None:
            price = parse_price(text, symbol_always_printed)
            description = ""

        if price is None:
            # No price on this line, so it's probably an item whose
            # price is on the next line.
            pending_description = text.lstrip("*").strip()
            continue

        pending_description = None

        # Negative prices are discounts on the preceding item.
        # Example: "Nectar Price Saving    -£0.75"
        if price < 0:
            if current_item is not None:
                current_item.adjustments.append(
                    PriceAdjustment(
                        amount=price,
                        description=description or "discount",
                    )
                )

            continue

        # Sainsbury's marks Nectar-priced items with a leading "*".
        current_item = ReceiptItem(
            description=description.lstrip("*").strip() or "Unrecognised item",
            price=price,
        )
        receipt.items.append(current_item)

    return receipt
