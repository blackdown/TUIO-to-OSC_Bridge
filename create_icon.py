"""
create_icon.py — one-time helper to generate assets/icon.ico for TUIO Bridge.

Requires Pillow:  pip install Pillow
Run once:         python create_icon.py
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Pillow is required: pip install Pillow")


def draw_icon(size: int) -> "Image.Image":
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size
    cx, cy = s // 2, s // 2

    # Background circle — dark navy
    bg_margin = max(1, s // 20)
    draw.ellipse(
        [bg_margin, bg_margin, s - bg_margin - 1, s - bg_margin - 1],
        fill=(22, 22, 38, 255),
    )

    # Outer teal ring
    ring_outer = s // 2 - bg_margin - max(1, s // 16)
    ring_thick = max(2, s // 7)
    ring_inner = ring_outer - ring_thick
    draw.ellipse(
        [cx - ring_outer, cy - ring_outer, cx + ring_outer, cy + ring_outer],
        fill=(0, 200, 188, 255),
    )
    draw.ellipse(
        [cx - ring_inner, cy - ring_inner, cx + ring_inner, cy + ring_inner],
        fill=(22, 22, 38, 255),
    )

    # Second (smaller) ring — lighter teal, roughly 60 % radius
    r2_outer = max(ring_inner - max(1, s // 12), 2)
    r2_thick = max(1, s // 10)
    r2_inner = r2_outer - r2_thick
    if r2_inner > 0:
        draw.ellipse(
            [cx - r2_outer, cy - r2_outer, cx + r2_outer, cy + r2_outer],
            fill=(0, 230, 210, 255),
        )
        draw.ellipse(
            [cx - r2_inner, cy - r2_inner, cx + r2_inner, cy + r2_inner],
            fill=(22, 22, 38, 255),
        )

    # Centre dot — white
    dot_r = max(1, s // 9)
    draw.ellipse(
        [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
        fill=(255, 255, 255, 255),
    )

    return img


def main() -> None:
    sizes = [256, 48, 32, 16]
    images = [draw_icon(s) for s in sizes]

    out = Path("assets/icon.ico")
    out.parent.mkdir(exist_ok=True)

    # PIL saves multi-size ICO when append_images is given
    images[0].save(
        str(out),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icon written: {out}")


if __name__ == "__main__":
    main()
