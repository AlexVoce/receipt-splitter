from splitter.models import Item


def calculate_totals(items: list[Item]) -> dict[str, float]:
    """
    for every item, calculate price per person
    for every person sharing that item, add that to their running total
    """
    totals = {}

    for item in items:
        share = item.price / len(item.people)

        for person in item.people:
            totals[person] = totals.get(person, 0) + share

    return totals