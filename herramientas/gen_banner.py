# Genera docs/banner.png: la portada del README, con los colores y la letra del juego
import os
import sys
import random
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta del repo
sys.path.insert(0, os.path.join(RAIZ, "esp32"))
import sprites

FONDO = (28, 30, 44)
PANEL = (56, 60, 80)
TEXTO = (234, 236, 246)
ACENTO = (150, 178, 238)
ROJO = (215, 55, 70)
TENUE = (82, 88, 112)


def rgb565(c):
    return ((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)


def cargar_fuentes():
    d = open(os.path.join(RAIZ, "esp32", "fuente.bin"), "rb").read()
    fuentes, i = [], 0
    while i < len(d):
        alto, n = d[i], d[i + 1] | (d[i + 2] << 8)
        i += 3
        g = {}
        for _ in range(n):
            cp, adv, nr = d[i] | (d[i + 1] << 8), d[i + 2], d[i + 3] * 3
            i += 4
            g[chr(cp)] = (adv, d[i:i + nr])
            i += nr
        fuentes.append({"alto": alto, "g": g})
    return fuentes


GRANDE, CHICA = cargar_fuentes()


def ancho(s, f, esc):
    return (sum(f["g"][ch][0] + 1 for ch in s) - 1) * esc


def texto(d, s, x, y, f, esc, color):
    for ch in s:
        adv, runs = f["g"][ch]
        for k in range(0, len(runs), 3):
            x0, y0 = x + runs[k + 1] * esc, y + runs[k] * esc
            d.rectangle([x0, y0, x0 + runs[k + 2] * esc - 1, y0 + esc - 1], fill=color)
        x += (adv + 1) * esc


def sprite(img, nombre, x, y, esc):
    datos = sprites.SPRITES[nombre]
    pal = sprites.PALETA_ENFERMA if nombre in sprites.ENFERMOS else sprites.PALETA
    d = ImageDraw.Draw(img)
    for r in range(32):
        for b in range(16):
            v = datos[r * 16 + b]
            for k, idx in enumerate((v >> 4, v & 15)):
                if idx:
                    px, py = x + (b * 2 + k) * esc, y + r * esc
                    d.rectangle([px, py, px + esc - 1, py + esc - 1], fill=rgb565(pal[idx]))


CORAZON = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]


def corazon(d, x, y, esc, color):
    for r, fila in enumerate(CORAZON):
        for c, ch in enumerate(fila):
            if ch == "X":
                d.rectangle([x + c * esc, y + r * esc, x + (c + 1) * esc - 1, y + (r + 1) * esc - 1], fill=color)


W, H = 1600, 600
img = Image.new("RGB", (W, H), FONDO)
d = ImageDraw.Draw(img)

random.seed(7)                                   # estrellitas de pixel
for _ in range(90):
    x, y = random.randrange(0, W, 8), random.randrange(0, H, 8)
    d.rectangle([x, y, x + 3, y + 3], fill=TENUE if random.random() < 0.8 else ACENTO)

titulo = "tamagotchi esp32"
esc = 5
tx = (W - ancho(titulo, GRANDE, esc)) // 2
texto(d, titulo, tx, 56, GRANDE, esc, TEXTO)
corazon(d, tx - 96, 78, 9, ROJO)
corazon(d, tx + ancho(titulo, GRANDE, esc) + 34, 78, 9, ROJO)

sub = "una mascota que necesita amor, arándanos y un soldador"
texto(d, sub, (W - ancho(sub, CHICA, 2)) // 2, 186, CHICA, 2, ACENTO)

# franja con el personaje en distintos estados
d.rounded_rectangle([60, 262, W - 60, 540], radius=28, fill=PANEL)
estados = ["normal", "feliz", "switch", "electronica", "comiendo", "enferma", "durmiendo"]
E = 6
paso = (W - 120) // len(estados)
for k, nombre in enumerate(estados):
    sprite(img, nombre, 60 + k * paso + (paso - 32 * E) // 2, 300, E)

img.save(os.path.join(RAIZ, "docs", "banner.png"))
print("ok")
