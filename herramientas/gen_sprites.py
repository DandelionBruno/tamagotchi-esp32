# Sprites 32x32 estilo kawaii (cuerpo entero, cabezota redonda, contorno suave)
# Genera esp32/sprites.py y la vista previa docs/sprites.png
import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta del repo
from PIL import Image, ImageDraw, ImageFont
import math

PAL = {
    '.': (0, 0, 0),         # 0 transparente
    'K': (34, 28, 40),      # pelo
    'B': (200, 200, 215),   # plateado (hebilla, piercing)
    'S': (252, 222, 204),   # piel
    'G': (96, 84, 104),     # anteojos
    'E': (70, 50, 58),      # contorno / ojos
    'C': (250, 160, 170),   # cachetes
    'M': (140, 70, 62),     # boca / patitas peluche
    'P': (250, 120, 145),   # lengua / corazones
    'J': (250, 248, 244),   # medias blancas / brillo ojos
    'N': (64, 68, 112),     # tapado azul marino
    'n': (38, 38, 64),      # remera, pollera, botones
    'U': (104, 146, 228),   # azul (arandano, lagrimas, joycon)
    'R': (240, 70, 70),     # rojo
    'V': (60, 160, 95),     # verde
    'Y': (252, 214, 80),    # amarillo
}
ORDEN = list(PAL.keys())
PAL_ENFERMA = dict(PAL)
PAL_ENFERMA['S'] = (196, 222, 168)
PAL_ENFERMA['C'] = (170, 205, 140)

N = 32

def nuevo():
    return [['.'] * N for _ in range(N)]

def elipse(g, cx, cy, rx, ry, ch):
    for y in range(N):
        for x in range(N):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                g[y][x] = ch

def anillo(g, cx, cy, r0, r1, ch):
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r0 <= d <= r1:
                g[y][x] = ch

def poner(g, fila, col, filas):
    for dy, s in enumerate(filas):
        for dx, ch in enumerate(s):
            if ch != '_':
                g[fila + dy][col + dx] = ch

def contorno(g):
    marcar = []
    for y in range(N):
        for x in range(N):
            if g[y][x] == '.':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < N and 0 <= yy < N and g[yy][xx] not in '.E':
                        marcar.append((y, x)); break
    for y, x in marcar:
        g[y][x] = 'E'

ESPIRAL = ["_KKK_",
           "K___K",
           "K_K_K",
           "K_KK_",
           "_K___"]
HUECOS_ESPIRAL = [(1, 9), (1, 10), (1, 11), (2, 9), (2, 11), (3, 9)]

def cuerpo(pijama=False):
    g = nuevo()
    elipse(g, 16, 17.5, 12.2, 9.5, 'K')        # pelo largo atras
    if not pijama:
        elipse(g, 16, 25.0, 7.4, 4.2, 'N')     # tapado largo
        poner(g, 21, 13, ["nnnnnn", "_nnnn_", "__nn__", "__nn__", "__nn__",
                          "_nnnn_", "_nnnn_", "__KK__"])   # remera, pollera, medias negras
        for y in (23, 25, 27):                  # botones cruzados
            g[y][12] = 'n'; g[y][19] = 'n'
        elipse(g, 8.6, 24.4, 2.0, 2.6, 'N')    # bracitos
        elipse(g, 23.4, 24.4, 2.0, 2.6, 'N')
        elipse(g, 8.6, 26.8, 1.4, 1.2, 'S')    # manitos
        elipse(g, 23.4, 26.8, 1.4, 1.2, 'S')
        poner(g, 29, 12, ["JJ____JJ"])         # medias blancas
        poner(g, 30, 11, ["KKK____KKK"])       # guillerminas
    else:
        poner(g, 21, 7, ["___nnnnnnnnnnnn___",   # remera oversize negra (pijama)
                         "_nnnnnnnnnnnnnnnn_",
                         "nnnnnnnnnnnnnnnnnn",
                         "nnnnnnnnnnnnnnnnnn",
                         "__nnnnnnnnnnnnnn__",
                         "__nnnnnnnnnnnnnn__",
                         "__nnnnnnnnnnnnnn__",
                         "__nnnnnnnnnnnnnn__",
                         "__nnnnnnnnnnnnnn__"])
        poner(g, 29, 12, ["SS____SS"])         # piernitas
        poner(g, 30, 11, ["SSS____SSS"])       # patitas descalzas
        elipse(g, 16, 26.4, 4.4, 3.6, 'U')     # peluche de arandano
        poner(g, 22, 13, ["N_NN_N", "_NNNN_"]) # coronita del arandano
        poner(g, 26, 14, ["E__E"])             # ojitos del peluche
        poner(g, 27, 15, ["EE"])               # sonrisita del peluche
        poner(g, 26, 10, ["M", "M"])           # bracitos del peluche
        poner(g, 26, 21, ["M", "M"])
        poner(g, 29, 13, ["MM__MM"])           # patitas del peluche
        poner(g, 24, 10, ["SS", "S"])          # manitos abrazando
        poner(g, 24, 20, ["SS", "_S"])
    elipse(g, 16, 13.3, 12.0, 9.4, 'K')        # cabeza (pelo)
    poner(g, 0, 8, ESPIRAL)                     # firulete espiral
    elipse(g, 16, 14.6, 9.6, 7.6, 'S')         # carita
    poner(g, 7, 11, ["___KKKKKKKKKKKKK",       # flequillo de costado
                     "_____KKKKKKKKKKK",
                     "_________KKKKKKK",
                     "____________KKKK"])
    poner(g, 4, 10, ["KK"])                     # rellenar hueco entre espiral y pelo
    g[7][13] = 'K'
    poner(g, 5, 22, ["_BB", "BB_"])            # hebillita
    for x0 in (9, 17):                          # anteojos cuadrados
        poner(g, 12, x0, ["GGGGGG", "G____G", "G____G", "G____G", "GGGGGG"])
    poner(g, 13, 15, ["GG"])                   # puente
    poner(g, 19, 7, ["CCC"])                   # cachetes
    poner(g, 19, 22, ["CCC"])
    return g

OJOS = {   # 4x3, se pone en col 10 y col 18, fila 13
    'abiertos': ["SJES", "SEES", "SEES"],
    'parpadeo': ["SSSS", "SSSS", "SEES"],
    'felices':  ["SSSS", "SEES", "ESSE"],
    'dormidos': ["SSSS", "ESSE", "SEES"],
    'abajo':    ["SSSS", "SJES", "SEES"],
    'costado':  ["SSJE", "SSEE", "SSEE"],
    'costado_izq': ["JESS", "EESS", "EESS"],
    'mareados': ["ESSE", "SEES", "ESSE"],
}
BOCAS = {  # 6x3, en col 13, fila 18
    'sonrisa': ["SESSES", "SSEESS", "SSSSSS"],
    'lengua':  ["SEEEES", "SSPPSS", "SSSSSS"],
    'abierta': ["SSEESS", "SEMMES", "SSEESS"],
    'triste':  ["SSEESS", "SESSES", "SSSSSS"],
    'ondulada':["SSSSSS", "SESESE", "ESESES"],
    'chiquita':["SSSSSS", "SSEESS", "SSSSSS"],
}

LAGRIMAS = [(17, 11, ["U", "UU", "U", "U"]), (17, 20, ["U", "UU", "U", "U"])]
SUDOR = [(8, 23, ["U", "U"])]
SWITCH = [(23, 9, ["_RRKKKKKKKKUU_", "SRRKVVYYVVKUUS", "_RRKKKKKKKKUU_"])]
ELECTRONICA = [(23, 10, ["_VVVVVVVVVR_", "SVKKKVVYVVVS", "SVKKKVVVYVVS", "_VVVVVVVVVV_"]),
               (19, 26, ["__B", "_B_", "Y__"])]

def armar(ojos, boca, extras=(), pijama=False):
    g = cuerpo(pijama)
    for c in (10, 18):
        poner(g, 13, c, OJOS[ojos])
    poner(g, 18, 13, BOCAS[boca])
    for (f, c, filas) in extras:
        poner(g, f, c, filas)
    contorno(g)
    for (y, x) in HUECOS_ESPIRAL:
        g[y][x] = '.'
    return ["".join(r) for r in g]

SPRITES = {
    'normal':      (armar('abiertos', 'sonrisa'), PAL),
    'parpadeo':    (armar('parpadeo', 'sonrisa'), PAL),
    'feliz':       (armar('felices', 'lengua'), PAL),
    'comiendo':    (armar('felices', 'abierta'), PAL),
    'triste':      (armar('abiertos', 'triste', LAGRIMAS), PAL),
    'enferma':     (armar('mareados', 'ondulada', SUDOR), PAL_ENFERMA),
    'durmiendo':   (armar('dormidos', 'chiquita', pijama=True), PAL),
    'switch':      (armar('abajo', 'lengua', SWITCH), PAL),
    'electronica': (armar('abajo', 'chiquita', ELECTRONICA), PAL),
    'curiosa':     (armar('costado', 'lengua'), PAL),
    'curiosa_izq': (armar('costado_izq', 'lengua'), PAL),
}

if __name__ == "__main__":
    ESC, COLS = 6, 5
    CELDA = N * ESC
    filas = (len(SPRITES) + COLS - 1) // COLS
    img = Image.new("RGB", (COLS * (CELDA + 20) + 20, filas * (CELDA + 50) + 20), (255, 247, 240))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for i, (nombre, (grid, pal)) in enumerate(SPRITES.items()):
        cx = 20 + (i % COLS) * (CELDA + 20)
        cy = 20 + (i // COLS) * (CELDA + 50)
        d.rectangle([cx, cy, cx + CELDA - 1, cy + CELDA - 1], fill=(255, 228, 236))
        for y, fila in enumerate(grid):
            for x, ch in enumerate(fila):
                if ch != '.':
                    d.rectangle([cx + x * ESC, cy + y * ESC, cx + x * ESC + ESC - 1, cy + y * ESC + ESC - 1], fill=pal[ch])
        d.text((cx + CELDA // 2, cy + CELDA + 22), nombre, fill=(90, 60, 70), font=font, anchor="mm")
    img.save(os.path.join(RAIZ, "docs", "sprites.png"))

    def rgb565(c):
        r, g, b = c
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    with open(os.path.join(RAIZ, "esp32", "sprites.py"), "w") as f:
        f.write("# Sprites 32x32, 4 bits por pixel (2 pixeles por byte). Generado automaticamente.\n")
        f.write("# Indice 0 = transparente (se pinta con el color de fondo).\n\n")
        f.write("PALETA = (" + ", ".join("0x%04X" % rgb565(PAL[k]) for k in ORDEN) + ")\n")
        f.write("PALETA_ENFERMA = (" + ", ".join("0x%04X" % rgb565(PAL_ENFERMA[k]) for k in ORDEN) + ")\n\n")
        f.write("SPRITES = {\n")
        for nombre, (grid, pal) in SPRITES.items():
            data = bytearray()
            for fila in grid:
                idx = [ORDEN.index(ch) for ch in fila]
                for a, b in zip(idx[0::2], idx[1::2]):
                    data.append((a << 4) | b)
            f.write("    %r: %r,\n" % (nombre, bytes(data)))
        f.write("}\n\nENFERMOS = ('enferma',)  # usan PALETA_ENFERMA\n")
    print("ok")
