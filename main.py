from decimal import Decimal
from pathlib import Path

from receipt.layout import reconstruct_lines
from receipt.parsers import parse_receipt
from receipt.vision import extract_text


receipt_folder = Path("example_receipts")

extensions = ["jpg", "jpeg", "webp"]

image_paths = sorted(
    path
    for extension in extensions
    for path in receipt_folder.glob(f"*.{extension}")
)


def print_items(receipt):
    print("  Parsed items:")

    for item in receipt.items:
        adjustment_total = sum(
            (adjustment.amount for adjustment in item.adjustments),
            start=Decimal("0.00"),
        )

        print(
            f"    £{item.price:>6.2f}"
            f"  adjustments £{adjustment_total:>6.2f}"
            f"  final £{item.final_price:>6.2f}"
            f"  {item.description}"
        )


for image_path in image_paths:
    observations = extract_text(str(image_path))
    lines = reconstruct_lines(observations)
    receipt = parse_receipt(lines)

    if receipt.total is None:
        print(
            f"\n? {image_path.name} ({receipt.store or 'unknown store'}): "
            "couldn't find receipt total"
        )

        print("\n  Reconstructed receipt:")
        for line in lines:
            print(f"    {line.text}")

        continue

    difference = receipt.calculated_total - receipt.total

    if difference == Decimal("0.00"):
        print(
            f"✓ {image_path.name} ({receipt.store or 'unknown store'}): "
            f"£{receipt.total:.2f}"
        )

    else:
        print(
            f"\n✗ {image_path.name} ({receipt.store or 'unknown store'}): "
            f"items £{receipt.calculated_total:.2f}, "
            f"receipt £{receipt.total:.2f}, "
            f"difference £{difference:.2f}"
        )

        print_items(receipt)