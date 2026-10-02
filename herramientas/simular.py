# Simulador en PC: emula machine, framebuf, ST7789 y el reloj de MicroPython
import sys, types, time as _t, os
from PIL import Image, ImageFont, ImageDraw

SIM = {"ms": 0, "pins": {}, "pulsado": set()}
PANT = Image.new("RGB", (240, 240), (0, 0, 0))
PX = PANT.load()

# ---- reloj ----
import time
time.ticks_ms = lambda: SIM["ms"]
time.ticks_diff = lambda a, b: a - b
time.ticks_add = lambda a, b: a + b
def _sleep_ms(ms): SIM["ms"] += ms
time.sleep_ms = _sleep_ms

# ---- machine ----
machine = types.ModuleType("machine")
class Pin:
    IN, OUT, PULL_UP = 0, 1, 2
    def __init__(self, n, mode=None, pull=None, value=None):
        self.n = n; self.v = 1; SIM["pins"][n] = self
    def value(self, v=None):
        if v is None:
            return 0 if self.n in SIM["pulsado"] else self.v
        self.v = v
class PWM:
    def __init__(self, pin, freq=1000, duty_u16=0): self.pin = pin.n; self.f = freq
    def freq(self, f=None): self.f = f
    def duty_u16(self, d):
        if self.pin == 25:
            SIM.setdefault("notas", []).append((SIM["ms"], self.f if d else 0))
        else:
            SIM["brillo"] = d
class SPI:
    def __init__(self, *a, **k):
        self.cmd = None; self.args = []; self.win = (0, 0, 239, 239); self.pos = 0
    def write(self, data):
        dc = SIM["pins"][21].v
        if dc == 0:
            self.cmd = data[0]; self.args = []
            if self.cmd == 0x2C:
                self.pos = 0
            return
        if self.cmd in (0x2A, 0x2B):
            self.args += list(data)
            if len(self.args) == 4:
                a = (self.args[0] << 8) | self.args[1]; b = (self.args[2] << 8) | self.args[3]
                x0, y0, x1, y1 = self.win
                self.win = (a, y0, b, y1) if self.cmd == 0x2A else (x0, a, x1, b)
        elif self.cmd == 0x2C:
            x0, y0, x1, y1 = self.win
            w = x1 - x0 + 1
            for i in range(0, len(data), 2):
                c = (data[i] << 8) | data[i + 1]
                x = x0 + self.pos % w; y = y0 + self.pos // w
                if 0 <= x < 240 and 0 <= y < 240:
                    PX[x, y] = (((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)
                self.pos += 1
machine.Pin, machine.PWM, machine.SPI = Pin, PWM, SPI
sys.modules["machine"] = machine

# ---- framebuf ----
fb = types.ModuleType("framebuf")
fb.RGB565, fb.MONO_HLSB = 1, 2
FONT = ImageFont.load_default()
_glyph = {}
def glyph(ch):
    if ch not in _glyph:
        im = Image.new("1", (8, 8), 0)
        ImageDraw.Draw(im).text((1, -2), ch, fill=1, font=FONT)
        _glyph[ch] = im
    return _glyph[ch]
class FrameBuffer:
    def __init__(self, buf, w, h, fmt):
        self.buf, self.w, self.h, self.fmt = buf, w, h, fmt
    def pixel(self, x, y, c=None):
        if not (0 <= x < self.w and 0 <= y < self.h): return 0
        if self.fmt == fb.MONO_HLSB:
            stride = (self.w + 7) // 8
            i = y * stride + x // 8; bit = 7 - x % 8
            if c is None: return (self.buf[i] >> bit) & 1
            if c: self.buf[i] |= 1 << bit
            else: self.buf[i] &= ~(1 << bit)
        else:
            i = (y * self.w + x) * 2
            if c is None: return self.buf[i] | (self.buf[i + 1] << 8)
            self.buf[i] = c & 0xFF; self.buf[i + 1] = c >> 8
    def fill_rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.pixel(xx, yy, c)
    def fill(self, c): self.fill_rect(0, 0, self.w, self.h, c)
    def hline(self, x, y, w, c): self.fill_rect(x, y, w, 1, c)
    def rect(self, x, y, w, h, c):
        self.fill_rect(x, y, w, 1, c); self.fill_rect(x, y + h - 1, w, 1, c)
        self.fill_rect(x, y, 1, h, c); self.fill_rect(x + w - 1, y, 1, h, c)
    def text(self, s, x, y, c):
        for k, ch in enumerate(s):
            g = glyph(ch).load()
            for py in range(8):
                for px in range(8):
                    if g[px, py]: self.pixel(x + k * 8 + px, y + py, c)
fb.FrameBuffer = FrameBuffer
sys.modules["framebuf"] = fb

# ---- cargar el juego sin arrancar el bucle infinito ----
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(RAIZ, "esp32"))
sys.path.insert(0, ".")
if os.path.exists("estado.json"): os.remove("estado.json")
src = open("main.py").read().replace("Juego().correr()", "")
ns = {"__name__": "juego"}
exec(compile(src, "main.py", "exec"), ns)
J = ns["Juego"]()

def paso(n=1, botones=()):
    for _ in range(n):
        ahora = time.ticks_ms()
        for b in botones:
            J.boton(b, ahora)
        botones = ()
        if not hasattr(J, "_ult"): J._ult = ahora
        dt = time.ticks_diff(ahora, J._ult)
        if dt >= 1000:
            J.tick(dt / 1000); J._ult = ahora
        J.actualizar(ahora)
        if J.pantalla_on: J.dibujar(ahora)
        J.autoguardar(ahora)
        time.sleep_ms(20)

capturas = []
def foto(nombre):
    capturas.append((nombre, PANT.copy()))
def esperar(seg):
    paso(int(seg * 1000 / 20))

esperar(0.3); foto("inicio (frase de humor)")
esperar(10); foto("pregunta cada 10s")
paso(1, "A"); esperar(0.6); foto("respondes: Sí")
esperar(10.5); paso(1, "C"); esperar(0.6); foto("respondes: No")
esperar(4); foto("después del No")
J.amor = 80; J.enferma = False; J.cacas = 0; J.hambre = 80
esperar(7); foto("otra pregunta")
esperar(10.3); foto("no contestas en 10s")
J.amor = 90; J.prox_pregunta = SIM["ms"] + 10**9; esperar(4)
J.ultimo_boton = SIM["ms"] - 6000; J.prox_actividad = 0
J.actividad = ("switch", False, SIM["ms"] + 30000); esperar(0.3); foto("sola: switch")
J.actividad = ("electronica", False, SIM["ms"] + 30000); esperar(0.3); foto("sola: electrónica")
J.actividad = None; J.ultimo_boton = SIM["ms"]
J.hambre = 15; esperar(0.3); foto("con hambre")
J.hambre = 80; J.cacas = 4; J.amor = 0; esperar(1.5); foto("enferma")
J.cacas = 0; J.amor = 90; J.enferma = False; esperar(0.3)
J.menu_i = 1; paso(1, "B"); esperar(0.5); foto("mimos")
esperar(3); J.hambre = 40; J.menu_i = 0; paso(1, "B"); paso(1, "B"); esperar(0.5); foto("arándanos")
esperar(3); J.menu_i = 0; paso(1, "B"); J.comida_i = 3; paso(1); esperar(0.1); foto("menú: mate")
paso(1, "B"); esperar(0.5); foto("tomando mate")
esperar(3); J.menu_i = 0; paso(1, "B"); J.comida_i = 4; paso(1); esperar(0.1); foto("menú: espresso tonic")
paso(1, "B"); esperar(0.5); foto("espresso tonic")
esperar(5); J.prox_pregunta = SIM["ms"] + 10**9; esperar(5); foto("callada (sin globito)")
esperar(3); J.menu_i = 4; paso(1, "B"); esperar(1.5); foto("durmiendo")
# Mosaico
W = 240; esc = 2
cols = 4; filas = (len(capturas) + cols - 1) // cols
mos = Image.new("RGB", (cols * (W * esc + 20) + 20, filas * (W * esc + 50) + 20), (40, 40, 48))
d = ImageDraw.Draw(mos)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except OSError:
    f = ImageFont.load_default()
for i, (n, im) in enumerate(capturas):
    x = 20 + (i % cols) * (W * esc + 20); y = 20 + (i // cols) * (W * esc + 50)
    mos.paste(im.resize((W * esc, W * esc), Image.NEAREST), (x, y))
    d.text((x + W * esc // 2, y + W * esc + 24), n, fill=(240, 240, 240), font=f, anchor="mm")
mos.save(os.path.join(RAIZ, "docs", "capturas_juego.png"))

# GIF animado para el README: cada captura al doble de tamaño
cuadros = [im.resize((480, 480), Image.NEAREST).convert("P", palette=Image.ADAPTIVE, colors=64) for _, im in capturas]
cuadros[0].save(os.path.join(RAIZ, "docs", "demo.gif"), save_all=True, append_images=cuadros[1:],
                duration=1300, loop=0, optimize=True)
print("capturas:", len(capturas), "tiempo sim ms:", SIM["ms"])
for f in ("estado.json", "estado.json.tmp"):
    if os.path.exists(f): os.remove(f)

# control de anchos de todas las frases
from pantalla import ancho_texto, CHICA, GRANDE
todas = sum(ns["FRASES"].values(), []) + ns["PREGUNTAS"] + ns["RESP_SI"] + ns["RESP_NO"] + ns["RESP_NADA"] + [c[3] for c in ns["COMIDAS"]]
for t in todas:
    g = ancho_texto(t, GRANDE); c = ancho_texto(t, CHICA)
    if g > 214:
        print(("OK chica " if c <= 234 else "NO ENTRA ") + str(c), t)
print("frases revisadas:", len(todas))
