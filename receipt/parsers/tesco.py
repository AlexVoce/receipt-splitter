import re
from functools import partial

from receipt.layout import ReceiptLine
from receipt.models import PriceAdjustment, Receipt, ReceiptItem
from receipt.parsers import base
from receipt.parsers.base import is_detail_line, normalise_label, parse_quantity


# Tesco prints £ on every price, so a missing symbol means OCR misread it.
parse_price = partial(base.parse_price, symbol_always_printed=True)
split_description_and_price = partial(
    base.split_description_and_price,
    symbol_always_printed=True,
)
get_standalone_price = partial(
    base.get_standalone_price,
    symbol_always_printed=True,
)
get_summary_price = partial(base.get_summary_price, symbol_always_printed=True)

CLUBCARD_PATTERN = re.compile(
    r"^[Cc][CcOo]\s*[£€E]?\s*\d",
    re.IGNORECASE,
)


def parse_tesco_receipt(lines: list[ReceiptLine]) -> Receipt:
    receipt = Receipt(store="Tesco")

    current_item: ReceiptItem | None = None
    in_items_section = False
    in_summary_section = False

    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        text = line.text.strip()
        label = normalise_label(text.split()[0]) if text.split() else ""

        if not text:
            continue

        # We consider the item section to have started once we see
        # the first line containing both a description and a price.
        description, price = split_description_and_price(text)

        if not in_items_section and description and price is not None:
            in_items_section = True

        if not in_items_section:
            continue

        # Receipt summary marks the end of products.
        if label == "subtotal":
            receipt.subtotal, consumed = get_summary_price(lines, index - 1)
            index += consumed - 1
            current_item = None
            in_summary_section = True
            continue

        if label == "savings":
            receipt.savings, consumed = get_summary_price(lines, index - 1)
            index += consumed - 1
            in_summary_section = True
            continue

        if label in {"coupons/vouchers", "coupons", "vouchers"}:
            receipt.coupons, consumed = get_summary_price(lines, index - 1)
            index += consumed - 1
            current_item = None
            in_summary_section = True
            continue

        if label == "total":
            receipt.total, _ = get_summary_price(lines, index - 1)
            break

        # Promotions and anything else in the summary aren't items.
        if in_summary_section or label == "promotions":
            continue

        # Tesco Clubcard offer line.
        # Example:
        # "CC £2.80    -£0.70"
        #
        # The right-hand value is the saving. The Clubcard price
        # on the left is useful metadata, not another item.
        if CLUBCARD_PATTERN.match(text):
            if current_item is not None and price is not None:
                current_item.adjustments.append(
                    PriceAdjustment(
                        amount=price,
                        description="Clubcard discount",
                    )
                )

                current_item.details.append(description)

            continue

        # Weight / per-unit information belongs to the current item.
        if is_detail_line(text):
            if current_item is not None:
                current_item.details.append(text)

            continue

        # A described negative price is a discount on the current item.
        # Example: "Meal Deal    -£0.30", "Reduced To Clear    -£3.00"
        if description and price is not None and price < 0:
            if current_item is not None:
                current_item.adjustments.append(
                    PriceAdjustment(amount=price, description=description)
                )

            continue

        # A line containing a description and price starts a new item.
        if description and price is not None:
            quantity, description = parse_quantity(description)

            current_item = ReceiptItem(
                description=description,
                price=price,
                quantity=quantity,
            )

            receipt.items.append(current_item)
            continue

        standalone_price = parse_price(text)

        if standalone_price is not None:

            # Negative standalone prices are discounts applied
            # to the preceding item.
            if standalone_price < 0:
                if current_item is not None:
                    current_item.adjustments.append(
                        PriceAdjustment(amount=standalone_price)
                    )

            # Positive standalone prices are suspicious.
            # They may belong to an item whose description OCR missed.
            else:
                current_item = ReceiptItem(
                    description="Unrecognised item",
                    price=standalone_price,
                )

                receipt.items.append(current_item)

            continue

        # A discount label whose price OCR placed on the next line.
        # Example: "Reduced To Clear" followed by "-£1.30"
        if index < len(lines) and current_item is not None:
            next_price = get_standalone_price(lines[index].text)

            if next_price is not None and next_price < 0:
                current_item.adjustments.append(
                    PriceAdjustment(amount=next_price, description=text)
                )
                index += 1
                continue

        # Otherwise assume this is a continuation of the item's description.
        if current_item is not None:
            current_item.description = (
                f"{current_item.description} {text}".strip()
            )

    return receipt
