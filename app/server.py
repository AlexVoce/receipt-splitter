from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from receipt.layout import reconstruct_lines
from receipt.parsers import parse_receipt
from receipt.vision import extract_text


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.post("/scan")
async def scan_receipt(
    request: Request,
    receipt_image: UploadFile = File(...),
):
    suffix = Path(receipt_image.filename or "receipt.jpg").suffix

    with NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as temp_file:
        contents = await receipt_image.read()
        temp_file.write(contents)
        image_path = temp_file.name

    observations = extract_text(image_path)
    lines = reconstruct_lines(observations)
    receipt = parse_receipt(lines)

    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"receipt": receipt},
    )