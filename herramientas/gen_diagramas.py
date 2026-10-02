# Genera conexiones.png (esquema de cableado) y placa.png (ubicacion en la placa perforada 6x4)
import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta del repo
from PIL import Image, ImageDraw, ImageFont
from itertools import permutations

B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def F(s, bold=True):
    return ImageFont.truetype(B if bold else R, s)


BG = (250, 248, 243)
INK = (40, 40, 48)
GRIS = (120, 124, 138)
PLACA = (34, 38, 54)
ORO = (214, 170, 60)
C = {
    "GND": (30, 30, 34), "3V3": (214, 39, 40), "5V": (255, 127, 14), "BAT": (214, 39, 40),
    "SCL": (31, 119, 180), "SDA": (44, 160, 44), "RES": (148, 103, 189), "DC": (140, 86, 75),
    "BLK": (23, 170, 190), "A": (184, 134, 11), "B": (214, 39, 154), "C": (107, 142, 35),
    "BUZ": (74, 90, 120),
}


def wire(d, pts, color, w=8):
    d.line(pts, fill=color, width=w, joint="curve")
    for x, y in pts:
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=color)


def dot(d, x, y, color, r=11):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(255, 255, 255), width=3)


def caja(d, x0, y0, x1, y1, fill=(255, 255, 255), outline=INK, r=14, w=4):
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=w)


# =====================================================================
#  1) ESQUEMA DE CONEXIONES
# =====================================================================
W, H = 2000, 1800
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.text((60, 36), "Tamagotchi: conexiones", fill=INK, font=F(56))
d.text((60, 110), "Guiate por el NOMBRE impreso al lado de cada pin de tu placa, no por la posición.",
       fill=GRIS, font=F(28, False))
d.text((60, 148), "Cada cable tiene el mismo color en las dos puntas.", fill=GRIS, font=F(28, False))

# ---------- ESP32 ----------
EX0, EX1, EY0, EY1 = 800, 1200, 340, 1120
IZQ = ["EN", "VP", "VN", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
DER = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
USO_IZQ = {"D25": "BUZ", "D27": "C", "D14": "B", "D13": "A", "GND": "GND"}
USO_DER = {"D23": "SDA", "D22": "BLK", "D21": "DC", "D18": "SCL", "D4": "RES", "GND": "GND", "3V3": "3V3"}


def py(i):
    return 380 + 50 * i


d.rectangle([900, 290, 1100, 345], fill=(60, 66, 88))          # antena
d.text((1000, 316), "antena", fill=(200, 205, 220), font=F(20, False), anchor="mm")
caja(d, EX0, EY0, EX1, EY1, fill=PLACA, outline=(15, 16, 24), r=18)
d.rounded_rectangle([930, 370, 1070, 560], radius=8, fill=(150, 154, 166))   # modulo metalico
d.text((1000, 465), "ESP32", fill=(60, 62, 72), font=F(30), anchor="mm")
d.text((1000, 640), "ESP32", fill=(235, 236, 246), font=F(40), anchor="mm")
d.text((1000, 685), "DevKit", fill=(165, 170, 190), font=F(26, False), anchor="mm")
d.rectangle([950, 1085, 1050, 1140], fill=(190, 194, 204), outline=(90, 92, 100), width=3)
d.text((1070, 1162), "USB", fill=GRIS, font=F(24), anchor="lm")

for i, n in enumerate(IZQ):
    usado = n in USO_IZQ
    d.text((822, py(i)), n, fill=(255, 255, 255) if usado else (105, 110, 132),
           font=F(26 if usado else 22, usado), anchor="lm")
    d.ellipse([EX0 - 8, py(i) - 8, EX0 + 8, py(i) + 8], fill=ORO if usado else (95, 98, 112))
for i, n in enumerate(DER):
    usado = n in USO_DER
    d.text((1178, py(i)), n, fill=(255, 255, 255) if usado else (105, 110, 132),
           font=F(26 if usado else 22, usado), anchor="rm")
    d.ellipse([EX1 - 8, py(i) - 8, EX1 + 8, py(i) + 8], fill=ORO if usado else (95, 98, 112))

# ---------- Pantalla ----------
PX = 1560
d.text((1740, 372), "Pantalla IPS 240×240", fill=INK, font=F(30), anchor="mm")
caja(d, PX, 400, 1920, 860, fill=PLACA, outline=(15, 16, 24))
d.rounded_rectangle([1690, 470, 1895, 790], radius=10, fill=(8, 9, 14))
d.text((1792, 630), "pantalla", fill=(120, 126, 150), font=F(24, False), anchor="mm")
PANT = ["GND", "VCC", "SCL", "SDA", "RES", "DC", "BLK"]
PY = {n: 450 + 60 * k for k, n in enumerate(PANT)}
for n in PANT:
    d.text((PX + 22, PY[n]), n, fill=(255, 255, 255), font=F(26), anchor="lm")

# cables ESP32 -> pantalla, eligiendo el orden de canales con menos cruces
cables = [("SDA", py(DER.index("D23")), PY["SDA"]), ("BLK", py(DER.index("D22")), PY["BLK"]),
          ("DC", py(DER.index("D21")), PY["DC"]), ("SCL", py(DER.index("D18")), PY["SCL"]),
          ("RES", py(DER.index("D4")), PY["RES"]), ("GND", py(13), PY["GND"]), ("3V3", py(14), PY["VCC"])]
canales = [1250 + 40 * k for k in range(7)]


def cruces(orden):
    n = 0
    for i in range(7):
        for j in range(7):
            if i == j:
                continue
            _, ye, yd = cables[i]
            _, ye2, yd2 = cables[j]
            lo, hi = min(ye2, yd2), max(ye2, yd2)
            if orden[j] < orden[i] and lo < ye < hi:      # tramo izquierdo de i cruza el vertical de j
                n += 1
            if orden[j] > orden[i] and lo < yd < hi:      # tramo derecho de i cruza el vertical de j
                n += 1
    return n


mejor = min(permutations(range(7)), key=cruces)
for (nombre, ye, yd), k in zip(cables, mejor):
    xc = canales[k]
    wire(d, [(EX1, ye), (xc, ye), (xc, yd), (PX, yd)], C[nombre])
for nombre, ye, yd in cables:
    dot(d, EX1, ye, C[nombre])
    dot(d, PX, yd, C[nombre])

# ---------- Botones y buzzer ----------
CX0, CX1 = 230, 400
comp = [("Buzzer", "BUZ", 610, "D25", 700), ("Botón C", "C", 740, "D27", 640),
        ("Botón B", "B", 870, "D14", 580), ("Botón A", "A", 1000, "D13", 520)]
RAIL = 150
wire(d, [(RAIL, 610), (RAIL, 1140), (640, 1140)], C["GND"])
for titulo, col, cy, pin, xc in comp:
    yp = py(IZQ.index(pin))
    wire(d, [(CX1, cy), (xc, cy), (xc, yp), (EX0, yp)], C[col])
    wire(d, [(CX0, cy), (RAIL, cy)], C["GND"])
    caja(d, CX0, cy - 36, CX1, cy + 36)
    d.text(((CX0 + CX1) // 2, cy), titulo, fill=INK, font=F(26), anchor="mm")
    dot(d, CX1, cy, C[col])
    dot(d, CX0, cy, C["GND"])
    dot(d, EX0, yp, C[col])
    d.ellipse([RAIL - 9, cy - 9, RAIL + 9, cy + 9], fill=C["GND"])
d.text((CX1 + 10, 610 - 34), "+", fill=INK, font=F(28), anchor="lm")
d.text((CX0 - 12, 610 - 34), "−", fill=INK, font=F(28), anchor="rm")
d.text((170, 1172), "GND común", fill=INK, font=F(24), anchor="lm")
d.text((60, 470), "Cada botón: una pata", fill=GRIS, font=F(22, False))
d.text((60, 498), "al pin y la otra a GND", fill=GRIS, font=F(22, False))

# ---------- Alimentacion: solo USB ----------
wire(d, [(EX0, py(13)), (640, py(13)), (640, 1140)], C["GND"])
dot(d, EX0, py(13), C["GND"])
wire(d, [(1000, 1140), (1000, 1250)], (150, 154, 166), 14)
caja(d, 760, 1250, 1240, 1340, fill=(226, 232, 244))
d.text((1000, 1295), "Cable USB: cargador o compu", fill=INK, font=F(26), anchor="mm")

# ---------- Notas ----------
d.rounded_rectangle([60, 1400, 1940, 1520], radius=16, fill=(255, 240, 214), outline=(214, 150, 40), width=3)
notas = ["1.  Soldá con el USB desenchufado.",
         "2.  VCC de la pantalla va a 3V3, nunca a VIN ni a 5V."]
for k, t in enumerate(notas):
    d.text((90, 1420 + 44 * k), t, fill=INK, font=F(27, k == 1))
img = img.crop((0, 0, W, 1570))
img.save(os.path.join(RAIZ, "docs", "conexiones.png"))

# =====================================================================
#  2) UBICACION EN LA PLACA PERFORADA 6x4
# =====================================================================
W, H = 2000, 1620
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.text((60, 36), "Placa perforada 6×4 cm", fill=INK, font=F(56))
d.text((60, 110), "Probá todo apoyado y sin soldar primero: las medidas cambian un poco según el modelo.",
       fill=GRIS, font=F(28, False))

P = 50                                    # 1 agujero = 2.54 mm = 50 px
X0, Y0 = 150, 300
BW, BH = 787, 1181
HX, HY = X0 + 68, Y0 + 115


def hole(c, r):
    return HX + c * P, HY + r * P


d.text((X0 + BW // 2, 222), "FRENTE (lo que se ve)", fill=INK, font=F(32), anchor="mm")
d.text((X0 + BW // 2, 270), "4 cm", fill=GRIS, font=F(24, False), anchor="mm")
d.text((X0 - 60, Y0 + BH // 2), "6 cm", fill=GRIS, font=F(24, False), anchor="mm")
caja(d, X0, Y0, X0 + BW, Y0 + BH, fill=(196, 160, 96), outline=(120, 92, 48), r=16)
for r in range(20):
    for c in range(14):
        x, y = hole(c, r)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(226, 196, 130), outline=(150, 118, 64), width=2)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(90, 70, 40))

# pantalla (modulo de 1.3": aprox. 28 x 39 mm)
cx = hole(6, 0)[0]
mx0, my0, mx1, my1 = cx - 276, HY - 45, cx + 276, HY + 723
d.rounded_rectangle([mx0, my0, mx1, my1], radius=12, fill=PLACA, outline=(15, 16, 24), width=4)
d.rounded_rectangle([cx - 232, HY + 150, cx + 232, HY + 614], radius=10, fill=(8, 9, 14))
d.text((cx, HY + 382), "PANTALLA", fill=(120, 126, 150), font=F(34), anchor="mm")
for k, n in enumerate(PANT):
    x, y = hole(3 + k, 0)
    d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=ORO, outline=(120, 90, 20), width=2)
    d.text((x, y + 34), n, fill=(255, 255, 255), font=F(17), anchor="mm")
d.text((cx, HY + 84), "7 pines soldados en la fila de arriba", fill=(170, 176, 198), font=F(20, False), anchor="mm")

# botones
for nombre, c0, col, pin in (("A", 0, "A", "D13"), ("B", 5, "B", "D14"), ("C", 10, "C", "D27")):
    x0, y0 = hole(c0, 16)
    x1, y1 = hole(c0 + 3, 18)
    bx, by = (x0 + x1) // 2, (y0 + y1) // 2
    for (lx, ly) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        d.ellipse([lx - 11, ly - 11, lx + 11, ly + 11], fill=(200, 204, 214), outline=(90, 92, 100), width=2)
    gx, gy = hole(c0, 19)
    wire(d, [(x0, y1), (gx, gy)], C["GND"], 9)
    d.rounded_rectangle([bx - 62, by - 62, bx + 62, by + 62], radius=12, fill=(52, 56, 72), outline=(20, 20, 28), width=4)
    d.ellipse([bx - 40, by - 40, bx + 40, by + 40], fill=(22, 24, 32))
    d.text((bx, by), nombre, fill=(255, 255, 255), font=F(34), anchor="mm")
    dot(d, x1, y0, C[col], 12)
    dot(d, x0, y1, C["GND"], 12)
wire(d, [hole(0, 19), hole(13, 19)], C["GND"], 9)

# referencias debajo de la placa
yb = Y0 + BH + 30
d.line([(X0 + 20, yb + 14), (X0 + 80, yb + 14)], fill=C["GND"], width=9)
d.text((X0 + 95, yb + 14), "tira de GND: une una pata de cada botón (por atrás)", fill=INK, font=F(24, False), anchor="lm")
for k, (n, col, pin) in enumerate((("A", "A", "D13"), ("B", "B", "D14"), ("C", "C", "D27"))):
    x = X0 + 50 + k * 250
    dot(d, x, yb + 62, C[col], 12)
    d.text((x + 24, yb + 62), "%s → %s" % (n, pin), fill=INK, font=F(24), anchor="lm")

# ---------- vista de costado ----------
SX = 1070
d.text((1520, 222), "DE COSTADO (cómo van las capas)", fill=INK, font=F(32), anchor="mm")
d.text((SX + 30, 282), "adelante", fill=GRIS, font=F(22, False), anchor="mm")
d.text((SX + 300, 282), "atrás", fill=GRIS, font=F(22, False), anchor="mm")
d.line([(SX + 95, 282), (SX + 240, 282)], fill=GRIS, width=3)
d.polygon([(SX + 240, 273), (SX + 258, 282), (SX + 240, 291)], fill=GRIS)

TOP = 390
capas = []
# 1 pantalla y botones
d.rounded_rectangle([SX, TOP + 30, SX + 34, TOP + 610], radius=6, fill=PLACA)
d.rectangle([SX + 34, TOP + 40, SX + 60, TOP + 62], fill=ORO)                     # tira de pines
for yy in (TOP + 700, TOP + 760, TOP + 820):
    d.rounded_rectangle([SX - 4, yy, SX + 60, yy + 40], radius=6, fill=(52, 56, 72))
# 2 placa perforada
d.rectangle([SX + 60, TOP, SX + 84, TOP + 900], fill=(196, 160, 96), outline=(120, 92, 48), width=3)
# 3 aislante
d.rectangle([SX + 112, TOP + 40, SX + 128, TOP + 860], fill=(120, 190, 150))
# 4 ESP32
d.rectangle([SX + 156, TOP + 90, SX + 180, TOP + 860], fill=PLACA)
d.rectangle([SX + 180, TOP + 110, SX + 215, TOP + 300], fill=(150, 154, 166))     # modulo metalico
d.rectangle([SX + 180, TOP + 800, SX + 214, TOP + 880], fill=(190, 194, 204), outline=(90, 92, 100), width=2)
for yy in range(TOP + 340, TOP + 780, 40):
    d.rectangle([SX + 180, yy, SX + 236, yy + 10], fill=ORO)                       # pines
LX = 1400
etiquetas = [
    (SX + 17, "Pantalla y botones", "soldados al frente de la placa"),
    (SX + 72, "Placa perforada", "atrás van las soldaduras y el buzzer"),
    (SX + 120, "Aislante", "cartón, goma eva o cinta gruesa"),
    (SX + 190, "ESP32", "con cinta doble faz, USB hacia abajo"),
]
for k, (mx, t1, t2) in enumerate(etiquetas):
    n = str(k + 1)
    d.ellipse([mx - 19, TOP - 54, mx + 19, TOP - 16], fill=INK)
    d.text((mx, TOP - 35), n, fill=(255, 255, 255), font=F(22), anchor="mm")
    ty = TOP + 40 + k * 130
    d.ellipse([LX - 19, ty - 3, LX + 19, ty + 35], fill=INK)
    d.text((LX, ty + 16), n, fill=(255, 255, 255), font=F(22), anchor="mm")
    d.text((LX + 34, ty), t1, fill=INK, font=F(27))
    d.text((LX + 34, ty + 38), t2, fill=GRIS, font=F(21, False))

d.text((SX + 192, TOP + 915), "USB", fill=GRIS, font=F(20), anchor="mm")
d.text((SX + 192, TOP + 940), "alimentación", fill=GRIS, font=F(18, False), anchor="mm")

d.rounded_rectangle([1050, 1400, 1950, 1590], radius=16, fill=(255, 240, 214), outline=(214, 150, 40), width=3)
for k, t in enumerate(["El ESP32 no entra en la misma cara que la pantalla:",
                       "ocupa casi toda la placa. Por eso va atrás, unido con cables.",
                       "Dejá el conector USB del ESP32 asomando por abajo,",
                       "así podés enchufarlo y reprogramarlo cuando quieras."]):
    d.text((1080, 1416 + 42 * k), t, fill=INK, font=F(26, k in (0, 2)))
img.save(os.path.join(RAIZ, "docs", "placa.png"))
print("ok, cruces pantalla:", cruces(mejor))
