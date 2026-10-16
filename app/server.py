from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from receipt.scan import scan_receipt as scan_receipt_image


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

    receipt, _ = scan_receipt_image(image_path)

    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"receipt": receipt},
    )