from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

import Quartz
import Vision
from PIL import Image, ImageOps


MIN_SHORTEST_SIDE = 1000

@dataclass
class TextObservation:
    text: str
    x: float
    y: float
    width: float
    height: float
    confidence: float


def _normalise_image(image_path: str) -> str:
    path = Path(image_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    with Image.open(path) as image:
        # Physically rotate the pixels according to the photo's EXIF metadata.
        image = ImageOps.exif_transpose(image)

        # Convert to RGB so we can reliably save as JPEG.
        image = image.convert("RGB")

        # Vision struggles with small text in low-resolution photos,
        # misreading £ symbols and digits. Upscaling helps a lot.
        shortest_side = min(image.size)

        if shortest_side < MIN_SHORTEST_SIDE:
            scale = MIN_SHORTEST_SIDE / shortest_side
            image = image.resize(
                (round(image.width * scale), round(image.height * scale)),
                Image.LANCZOS,
            )

        temp_file = NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(temp_file.name, "JPEG", quality=95)

    return temp_file.name


def extract_text(image_path: str) -> list[TextObservation]:
    normalised_path = _normalise_image(image_path)

    path_bytes = normalised_path.encode("utf-8")

    image_url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None,
        path_bytes,
        len(path_bytes),
        False,
    )

    image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)

    if image_source is None:
        raise ValueError(f"Could not open image: {image_path}")

    image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    request.setRecognitionLanguages_(["en-GB"])

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        image,
        {},
    )

    success, error = handler.performRequests_error_([request], None)

    if not success:
        raise RuntimeError(f"Vision failed: {error}")

    observations = []

    for observation in request.results():
        candidates = observation.topCandidates_(1)

        if not candidates:
            continue

        candidate = candidates[0]
        box = observation.boundingBox()

        observations.append(
            TextObservation(
                text=candidate.string(),
                x=box.origin.x,
                y=box.origin.y,
                width=box.size.width,
                height=box.size.height,
                confidence=candidate.confidence(),
            )
        )

    observations.sort(key=lambda obs: (-obs.y, obs.x))

    return observations