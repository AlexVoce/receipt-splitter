from decimal import Decimal

from receipt.layout import ReceiptLine, reconstruct_lines
from receipt.models import Receipt
from receipt.parsers import parse_receipt
from receipt.vision import extract_text


# Angles (degrees, anticlockwise) to retry when a scan doesn't add up.
RETRY_ANGLES = [-1, 1, -2, 2, -3, 3, -4, 4]

# Once the best whole-degree angle is known, also try either side of it.
REFINE_STEP = 0.5


def _scan_at(image_path: str, rotation: float) -> tuple[Receipt, list[ReceiptLine]]:
    lines = reconstruct_lines(extract_text(image_path, rotation))
    return parse_receipt(lines), lines


def _score(receipt: Receipt) -> tuple:
    # Higher is better: found a total, then items add up to it,
    # then how close they get, then more items (fewer rows merged together).
    if receipt.total is None:
        return (False, False, Decimal("-Infinity"), len(receipt.items))

    difference = abs(receipt.calculated_total - receipt.total)
    return (True, difference == 0, -difference, len(receipt.items))


def scan_receipt(image_path: str) -> tuple[Receipt, list[ReceiptLine]]:
    receipt, lines = _scan_at(image_path, 0)

    if receipt.total is not None and receipt.calculated_total == receipt.total:
        return receipt, lines

    # Line reconstruction groups text by height on the page, so on a tilted
    # or crumpled receipt prices drift onto the line above or below their
    # item. Rotating the photo slightly can level it, so try a few angles
    # and keep whichever reads best.
    results = {0: (receipt, lines)}

    for angle in RETRY_ANGLES:
        results[angle] = _scan_at(image_path, angle)

    best_angle = max(results, key=lambda angle: _score(results[angle][0]))

    if best_angle != 0:
        for angle in (best_angle - REFINE_STEP, best_angle + REFINE_STEP):
            results[angle] = _scan_at(image_path, angle)

    # Ties go to the smallest rotation.
    best_angle = max(
        results,
        key=lambda angle: (_score(results[angle][0]), -abs(angle)),
    )

    return results[best_angle]
