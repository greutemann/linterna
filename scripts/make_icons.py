"""Genera los íconos de la extensión (linterna proyectando un haz).

Si existe una imagen fuente (`icon-source.png` en la raíz del repo), la reescala a los
tamaños que pide Chrome. Si no, dibuja una de respaldo. Reescala con LANCZOS para bordes
suaves. Uso:  python scripts/make_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

_ROOT = Path(__file__).resolve().parents[1]
_OUT = _ROOT / "extension" / "icons"
_SOURCE = _ROOT / "icon-source.png"
_S = 512  # lienzo de trabajo
_SIZES = [16, 32, 48, 128]


def _draw() -> Image.Image:
    img = Image.new("RGBA", (_S, _S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Fondo redondeado oscuro (slate-900).
    d.rounded_rectangle([0, 0, _S, _S], radius=112, fill=(15, 23, 42, 255))

    lens = (196, 300)

    # Haz de luz: cono externo tenue + cono interno brillante (cálido).
    d.polygon([lens, (512, 96), (512, 504)], fill=(253, 230, 138, 70))
    d.polygon([lens, (512, 178), (512, 422)], fill=(253, 224, 71, 165))

    # Cuerpo de la linterna (mango gris) y aro de la lente.
    d.rounded_rectangle([64, 262, 196, 338], radius=26, fill=(148, 163, 184, 255))
    d.ellipse([176, 256, 232, 344], fill=(100, 116, 139, 255))
    # Lente encendida.
    d.ellipse([188, 268, 224, 332], fill=(255, 251, 235, 255))

    return img


def main() -> int:
    _OUT.mkdir(parents=True, exist_ok=True)
    if _SOURCE.is_file():
        base = Image.open(_SOURCE).convert("RGBA")
        origen = f"fuente {_SOURCE.name}"
    else:
        base = _draw()
        origen = "respaldo dibujado"
    for size in _SIZES:
        base.resize((size, size), Image.LANCZOS).save(_OUT / f"icon{size}.png")
    print(f"Íconos generados desde {origen}: {', '.join(f'icon{s}.png' for s in _SIZES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
