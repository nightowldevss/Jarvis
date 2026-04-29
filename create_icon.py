from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        cx  = size // 2

        # Sfondo cerchio scuro
        d.ellipse([2, 2, size-2, size-2], fill=(7, 8, 15, 255))

        # Anello esterno cyan
        d.ellipse([2, 2, size-2, size-2], outline=(0, 212, 255, 255), width=max(1, size//20))

        # Cerchio interno
        m = size // 5
        d.ellipse([m, m, size-m, size-m], fill=(0, 212, 255, 180))

        # Punto centrale bianco
        c = size // 2
        r = max(2, size // 10)
        d.ellipse([c-r, c-r, c+r, c+r], fill=(255, 255, 255, 255))

        # Linee decorative (raggi)
        for angle_deg in [0, 60, 120, 180, 240, 300]:
            import math
            a  = math.radians(angle_deg)
            r1 = size // 3
            r2 = size // 2 - 3
            x1 = int(cx + r1 * math.cos(a))
            y1 = int(cx + r1 * math.sin(a))
            x2 = int(cx + r2 * math.cos(a))
            y2 = int(cx + r2 * math.sin(a))
            d.line([x1, y1, x2, y2], fill=(0, 212, 255, 200), width=max(1, size//32))

        images.append(img)

    out = os.path.join(os.path.dirname(__file__), "jarvis.ico")
    images[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"Icona creata: {out}")
    return out

if __name__ == "__main__":
    create_icon()
