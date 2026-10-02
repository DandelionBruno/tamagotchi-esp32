# Genera fuente.py: dos fuentes bitmap (grande y chica) con tildes, para MicroPython
import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta del repo
from PIL import Image, ImageDraw, ImageFont

CHARS = "".join(chr(c) for c in range(32, 127)) + "áéíóúÁÉÍÓÚñÑ¿¡üÜ"
TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def generar(tam, umbral=110):
    f = ImageFont.truetype(TTF, tam)
    asc, desc = f.getmetrics()
    H = asc + desc
    glifos = {}
    top, bot = H, 0
    crudos = {}
    for ch in CHARS:
        adv = int(round(f.getlength(ch)))
        w = max(adv, 1) + 2
        im = Image.new("L", (w, H), 0)
        ImageDraw.Draw(im).text((0, asc), ch, fill=255, font=f, anchor="ls")
        px = im.load()
        filas = []
        for y in range(H):
            fila = [px[x, y] > umbral for x in range(w)]
            if any(fila):
                top = min(top, y); bot = max(bot, y)
            filas.append(fila)
        crudos[ch] = (adv, filas)
    alto = bot - top + 1
    for ch, (adv, filas) in crudos.items():
        runs = bytearray()
        for y in range(top, bot + 1):
            fila = filas[y]
            x = 0
            while x < len(fila):
                if fila[x]:
                    x0 = x
                    while x < len(fila) and fila[x]:
                        x += 1
                    runs += bytes([y - top, x0, x - x0])
                else:
                    x += 1
        glifos[ch] = (adv, bytes(runs))
    return alto, glifos


import struct
datos = bytearray()
for tam in (17, 11):                     # 1ra fuente = GRANDE, 2da = CHICA
    alto, glifos = generar(tam)
    datos += struct.pack("<BH", alto, len(glifos))
    for ch, (adv, runs) in glifos.items():
        datos += struct.pack("<HBB", ord(ch), adv, len(runs) // 3) + runs
open(os.path.join(RAIZ, "esp32", "fuente.bin"), "wb").write(datos)
print("fuente.bin:", len(datos), "bytes")
