"""Подготовка иконки и логотипа из исходных изображений."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "resources"
DOCS = ROOT / "docs"
RES.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

ICON_SRC = Path(
    r"C:\Users\Russska\.dsh\attachments\v1\objects\32"
    r"\32e94944999a89167b67dce9790af7d5cb0b0a8ad2651c3159d6ff7f71a3f36f"
)
BANNER_SRC = Path(
    r"C:\Users\Russska\.dsh\attachments\v1\objects\54"
    r"\5456b0c7a786bde08be0421968ec694f559196da5ba81a7f5bd2ab7170867762"
)


def content_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    """Границы тёмной иконки: фон у исходника светлый (≈200), иконка тёмная."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    px = rgb.load()
    left, top, right, bottom = width, height, 0, 0
    for y in range(0, height):
        for x in range(0, width):
            r, g, b = px[x, y]
            if 0.299 * r + 0.587 * g + 0.114 * b < 140:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    return left, top, right + 1, bottom + 1


def rounded_icon(image: Image.Image, size: int) -> Image.Image:
    image = image.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(size * 0.22)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(image, (0, 0), mask)
    return result


def bright_bbox(image: Image.Image, threshold: float = 110) -> tuple[int, int, int, int]:
    """Границы яркого содержимого (логотип на тёмном фоне)."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    px = rgb.load()
    left, top, right, bottom = width, height, 0, 0
    for y in range(height):
        for x in range(width):
            r, g, b = px[x, y]
            if 0.299 * r + 0.587 * g + 0.114 * b > threshold:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    return left, top, right + 1, bottom + 1


def main() -> None:
    icon = Image.open(ICON_SRC)
    box = content_bbox(icon)
    print("bbox иконки:", box)
    icon = icon.crop(box)

    big = rounded_icon(icon, 256)
    big.save(RES / "icon.png")
    big.save(RES / "logo.png")

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    big.save(RES / "icon.ico", sizes=sizes)

    banner = Image.open(BANNER_SRC).convert("RGB")
    banner.resize((1200, 670), Image.LANCZOS).save(DOCS / "banner.png")

    # Горизонтальный логотип «TT + TextTalk» для заголовка окна.
    mark = bright_bbox(banner)
    print("bbox логотипа:", mark)
    wordmark = banner.crop(mark)
    wordmark.resize((wordmark.width * 96 // wordmark.height, 96), Image.LANCZOS).save(
        RES / "logo_wordmark.png"
    )
    print("готово: icon.png, logo.png, icon.ico, logo_wordmark.png, docs/banner.png")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
