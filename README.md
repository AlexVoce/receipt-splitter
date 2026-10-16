# Receipt Splitter

Are you sick of losing track of who owes what when you go shopping with friends? Does simple addition become very hard when its on a receipt? Do you hate how Tesco puts the full item price and has a subtitle for the sale money off? Look no further, friend. 

All I ask is that you take a nice picture of the receipt and upload it. name the poor souls involved in the shop and assign their items. 

## How it works

1. **Upload a photo** of the receipt.
2. **Check the items.** Fix any names or prices the scanner got wrong.
3. **Add people.** Add the names of everyone involved in the shop.
4. **Assign items.** Everyone shares every item by default. Tap a name to exclude that person from an item.
5. **See the totals** for each person.

## Supported receipts

Dedicated parsers handle **Tesco**, **Sainsbury's** and **Waitrose** receipts, including Clubcard and Nectar discounts and multibuy deals. Receipts from other shops go through a generic parser, which may need more fixing by hand. Cant promise itll work for every receipt, but she's a strong lass who should be able to handle most of them. (It now works for heic files and updated to try to work better with crumpled receipts but she's not perfect).

## Requirements

- **macOS.** Text recognition uses Apple's Vision framework, so the app won't run on Linux or Windows. This is basically just for my friends so I didnt do the extra work.
- Python 3.12+

## Running it

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn jinja2 python-multipart pillow pillow-heif \
    pyobjc-framework-Vision pyobjc-framework-Quartz pytest

uvicorn app.server:app --reload
```

Then open http://localhost:8000.

To use it from your phone, either open your Mac's local IP address on the same Wi-Fi, or put it behind a tunnel such as Cloudflare Tunnel.

## Testing

Check the parsers against the sample receipts in `example_receipts/`:

```bash
python main.py
```

A ✓ means the parsed item prices add up to the total printed on the receipt.

Run the unit tests:

```bash
pytest
```

## Project layout

```
app/        FastAPI server, HTML templates, CSS and JS
receipt/    OCR (vision.py), line reconstruction and store parsers
splitter/   Bill-splitting logic
tests/      Unit tests
```
