from decimal import Decimal

from receipt.layout import ReceiptLine
from receipt.parsers.tesco import parse_tesco_receipt
from receipt.vision import TextObservation


def make_line(*texts: str) -> ReceiptLine:
    observations = []

    for i, text in enumerate(texts):
        observations.append(
            TextObservation(
                text=text,
                x=i * 0.5,
                y=0.5,
                width=0.2,
                height=0.02,
                confidence=1.0,
            )
        )

    return ReceiptLine(observations)


def test_tesco_discounted_receipt():

    lines = [
        make_line("TESCO"),
        make_line("1 Chicken", "£2.25"),
        make_line("1 Crisps", "£2.50"),
        make_line("-£1.00"),
        make_line("Unrecognised item", "£0.37"),
        make_line("Subtotal:", "£5.12"),
        make_line("Savings:", "-£1.00"),
        make_line("Promotions:", "-£1.00"),
        make_line("TOTAL:", "£4.12"),
    ]

    receipt = parse_tesco_receipt(lines)

    assert len(receipt.items) == 3

    assert receipt.items[0].description == "Chicken"
    assert receipt.items[0].final_price == Decimal("2.25")

    assert receipt.items[1].description == "Crisps"
    assert receipt.items[1].price == Decimal("2.50")
    assert receipt.items[1].final_price == Decimal("1.50")

    assert receipt.items[2].price == Decimal("0.37")

    assert receipt.total == Decimal("4.12")
    assert receipt.calculated_total == Decimal("4.12")

def test_parse_price_ocr_confusions():
    from receipt.parsers.tesco import parse_price

    assert parse_price("€2.20") == Decimal("2.20")
    assert parse_price("-EO.65") == Decimal("-0.65")
    assert parse_price("-C0.52") == Decimal("-0.52")
    assert parse_price("E0. 77") == Decimal("0.77")
    assert parse_price("- £1    .35") == Decimal("-1.35")
    assert parse_price("£12.10") == Decimal("12.10")

    # £ misread as a digit.
    assert parse_price("84.25") == Decimal("4.25")
    assert parse_price("-00.30") == Decimal("-0.30")

    # Not prices.
    assert parse_price("Bread 750g q91    10") is None


def test_tesco_reduced_and_coupons():

    lines = [
        make_line("1 Candle", "£8.50"),
        make_line("Reduced To Clear", "-£3.00"),
        make_line("1 Candle", "£8.50"),
        make_line("Reduced To Clear"),
        make_line("-£1.30"),
        make_line("1 Crisps", "£1.00"),
        make_line("1.00 each"),
        make_line("Subtotal:"),
        make_line("£18.00"),
        make_line("Promotions:", "-£4.30"),
        make_line("Coupons/vouchers:", "£2.00"),
        make_line("TOTAL:", "£11.70"),
    ]

    receipt = parse_tesco_receipt(lines)

    assert len(receipt.items) == 3
    assert receipt.items[0].final_price == Decimal("5.50")
    assert receipt.items[1].description == "Candle"
    assert receipt.items[1].final_price == Decimal("7.20")
    assert receipt.items[2].details == ["1.00 each"]
    assert receipt.subtotal == Decimal("18.00")
    assert receipt.calculated_total == receipt.total == Decimal("11.70")


def test_parse_price_ignores_handwritten_marks():
    from receipt.parsers.base import parse_price

    assert parse_price("£1.15€") == Decimal("1.15")
    assert parse_price("£1.90A") == Decimal("1.90")
    assert parse_price("£2.65/г") == Decimal("2.65")
    assert parse_price("-£O. 754") == Decimal("-0.75")
    assert parse_price("-£0. 75 / 25") == Decimal("-0.75")

    # Not prices.
    assert parse_price("2.25L PEPSI") is None
    assert parse_price("1.234 kg") is None


def test_sainsburys_receipt():
    from receipt.parsers import parse_receipt

    lines = [
        make_line("Sainsbury's"),
        make_line("Vat Number : 660 4548 36"),
        make_line("JS MIXD S/LSS GRAPES", "£2.00"),
        make_line("*MILKYBAR BTTNS TUBE", "£2.00"),
        make_line("Nectar Price Saving", "-£0. 75 / 25"),
        make_line("LOOSE BANANAS"),
        make_line("0.95 kg @ £0.80/kg", "£0.76"),
        make_line("JS RED LABEL DECAF", "£1.90A"),
        make_line("4 BALANCE DUE", "£5.91"),
        make_line("PROMOTIONS", "-£0.75"),
    ]

    receipt = parse_receipt(lines)

    assert receipt.store == "Sainsbury's"
    assert [item.description for item in receipt.items] == [
        "JS MIXD S/LSS GRAPES",
        "MILKYBAR BTTNS TUBE",
        "LOOSE BANANAS",
        "JS RED LABEL DECAF",
    ]
    assert receipt.items[1].final_price == Decimal("1.25")
    assert receipt.items[2].price == Decimal("0.76")
    assert receipt.items[2].details == ["0.95 kg @ £0.80/kg"]
    assert receipt.calculated_total == receipt.total == Decimal("5.91")


def test_waitrose_receipt():
    from receipt.parsers import parse_receipt

    lines = [
        make_line("WAITROSE", "& PARTNERS"),
        make_line("£"),
        make_line("WR NB BEEF MINCE 12%", "16.00"),
        make_line("WR LINGUINE", "1.65"),
        make_line("WR ONIONS", "1.00"),
        make_line("2 @ 0.50"),
        make_line("3 items"),
        make_line("BALANCE DUE", "£18.65"),
        make_line("Total Amount", "GBP 18.65"),
        make_line("t waitrosehaveyoursay.com"),
    ]

    receipt = parse_receipt(lines)

    assert receipt.store == "Waitrose"
    # No £ on Waitrose prices, so 16.00 must not become 6.00.
    assert receipt.items[0].price == Decimal("16.00")
    assert receipt.items[2].details == ["2 @ 0.50"]
    assert receipt.calculated_total == receipt.total == Decimal("18.65")
