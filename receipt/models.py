from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class PriceAdjustment:
    amount: Decimal
    description: str = "discount"


@dataclass
class ReceiptItem:
    description: str
    price: Decimal
    quantity: int = 1
    details: list[str] = field(default_factory=list)
    adjustments: list[PriceAdjustment] = field(default_factory=list)

    @property
    def final_price(self) -> Decimal:
        return self.price + sum(
            (adjustment.amount for adjustment in self.adjustments),
            start=Decimal("0.00"),
        )


@dataclass
class Receipt:
    store: str | None = None
    items: list[ReceiptItem] = field(default_factory=list)
    subtotal: Decimal | None = None
    total: Decimal | None = None
    savings: Decimal | None = None
    coupons: Decimal | None = None

    @property
    def calculated_total(self) -> Decimal:
        items_total = sum(
            (item.final_price for item in self.items),
            start=Decimal("0.00"),
        )

        # Coupons/vouchers apply to the whole receipt, not to an item
        # Tesco prints them as a positive amount
        if self.coupons is not None:
            items_total -= abs(self.coupons)

        return items_total