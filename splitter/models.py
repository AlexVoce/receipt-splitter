from dataclasses import dataclass


@dataclass
class Item:
    description: str
    price: float
    people: list[str]