# pantalla.py - driver minimo para ST7789 240x240 SIN pin CS + utilidades de dibujo
# Pines: SCL=18, SDA=23, RES=4, DC=21, BLK=22

from machine import Pin, SPI, PWM
import framebuf
import time


def rgb(r, g, b):
    """Convierte RGB (0-255) a RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _sw(c):
    """framebuf guarda los colores al reves que la pantalla: los damos vuelta."""
    return ((c & 0xFF) << 8) | (c >> 8)


class Pantalla:
    def __init__(self):
        self.spi = SPI(2, baudrate=40_000_000, polarity=1, phase=1,
                       sck=Pin(18), mosi=Pin(23))
        self.dc = Pin(21, Pin.OUT)
        self.rst = Pin(4, Pin.OUT)
        self.bl = PWM(Pin(22), freq=1000)
        self.brillo(100)
        self._iniciar()

    def brillo(self, porcentaje):
        self.bl.duty_u16(int(65535 * porcentaje / 100))

    def _cmd(self, c, data=None):
        self.dc.value(0)
        self.spi.write(bytes([c]))
        if data:
            self.dc.value(1)
            self.spi.write(bytes(data))

    def _iniciar(self):
        self.rst.value(1); time.sleep_ms(50)
        self.rst.value(0); time.sleep_ms(50)
        self.rst.value(1); time.sleep_ms(150)
        self._cmd(0x01); time.sleep_ms(150)
        self._cmd(0x11); time.sleep_ms(120)
        self._cmd(0x3A, [0x55])
        self._cmd(0x36, [0x00])
        self._cmd(0x21)
        self._cmd(0x13)
        self._cmd(0x29); time.sleep_ms(50)

    def _ventana(self, x, y, w, h):
        x1, y1 = x + w - 1, y + h - 1
        self._cmd(0x2A, [x >> 8, x & 0xFF, x1 >> 8, x1 & 0xFF])
        self._cmd(0x2B, [y >> 8, y & 0xFF, y1 >> 8, y1 & 0xFF])
        self._cmd(0x2C)
        self.dc.value(1)

    def rect(self, x, y, w, h, color):
        self._ventana(x, y, w, h)
        linea = bytes([color >> 8, color & 0xFF]) * w
        for _ in range(h):
            self.spi.write(linea)

    def mostrar(self, lienzo, x, y, alto=None):
        """Manda un Lienzo a la pantalla en (x, y). Con 'alto' manda solo las primeras filas."""
        alto = lienzo.h if alto is None else alto
        self._ventana(x, y, lienzo.w, alto)
        self.spi.write(memoryview(lienzo.buf)[:lienzo.w * alto * 2])

    def sprite(self, datos, paleta, x, y, escala, fondo, espejo=False):
        """Dibuja un sprite 32x32 de 4 bits, agrandado 'escala' veces.
        El color 0 de la paleta es transparente y se pinta con 'fondo'."""
        n = 32
        paso = escala * 2
        pal = []
        for i, c in enumerate(paleta):
            if i == 0:
                c = fondo
            pal.append(bytes([c >> 8, c & 0xFF]) * escala)
        fila = bytearray(n * paso)
        self._ventana(x, y, n * escala, n * escala)
        for r in range(n):
            base = r * 16
            for b in range(16):
                v = datos[base + b]
                col = b * 2
                if espejo:
                    p1 = (n - 1 - col) * paso
                    p2 = p1 - paso
                else:
                    p1 = col * paso
                    p2 = p1 + paso
                fila[p1:p1 + paso] = pal[v >> 4]
                fila[p2:p2 + paso] = pal[v & 0x0F]
            for _ in range(escala):
                self.spi.write(fila)


class Lienzo:
    """Un pedacito de pantalla en memoria donde dibujamos antes de mandarlo."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 2)
        self.fb = framebuf.FrameBuffer(self.buf, w, h, framebuf.RGB565)

    def llenar(self, c):
        self.fb.fill(_sw(c))

    def rect(self, x, y, w, h, c, lleno=True):
        if lleno:
            self.fb.fill_rect(x, y, w, h, _sw(c))
        else:
            self.fb.rect(x, y, w, h, _sw(c))

    def texto(self, s, x, y, c, fuente):
        """Escribe con una de las fuentes de fuente.bin (GRANDE o CHICA)."""
        cc = _sw(c)
        g = fuente["g"]
        hl = self.fb.hline
        for ch in s:
            adv, runs = g.get(ch) or g["?"]
            for k in range(0, len(runs), 3):
                hl(x + runs[k + 1], y + runs[k], runs[k + 2], cc)
            x += adv + 1

    def texto_centrado(self, s, y, c, fuente, x0=0, ancho=None):
        ancho = self.w if ancho is None else ancho
        self.texto(s, x0 + (ancho - ancho_texto(s, fuente)) // 2, y, c, fuente)

    def icono(self, ico, x, y, esc=1):
        filas, colores = ico
        for py, fila in enumerate(filas):
            for px, ch in enumerate(fila):
                if ch != '.':
                    self.fb.fill_rect(x + px * esc, y + py * esc, esc, esc, _sw(colores[ch]))


def ancho_texto(s, fuente):
    g = fuente["g"]
    return sum((g.get(ch) or g["?"])[0] + 1 for ch in s) - 1


def _cargar_fuentes(ruta="fuente.bin"):
    with open(ruta, "rb") as f:
        d = f.read()
    fuentes = []
    i = 0
    while i < len(d):
        alto = d[i]
        n = d[i + 1] | (d[i + 2] << 8)
        i += 3
        g = {}
        for _ in range(n):
            cp = d[i] | (d[i + 1] << 8)
            adv = d[i + 2]
            nr = d[i + 3] * 3
            i += 4
            g[chr(cp)] = (adv, d[i:i + nr])
            i += nr
        fuentes.append({"alto": alto, "g": g})
    return fuentes


GRANDE, CHICA = _cargar_fuentes()
