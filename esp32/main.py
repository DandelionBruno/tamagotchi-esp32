# main.py - Tamagotchi personalizado para ESP32 + ST7789 240x240
# Botones: A = siguiente / Sí, B = elegir, C = anterior / volver / No
# Necesita en el ESP32: main.py, pantalla.py, sprites.py y fuente.bin

import time
import random
import json
import os
from machine import Pin, PWM
from pantalla import Pantalla, Lienzo, rgb, ancho_texto, GRANDE, CHICA
import sprites

# ================== AJUSTES ==================
VELOCIDAD = 1              # 1 = tiempo real. Para probar, ponelo en 30 y todo pasa 30 veces mas rapido
SEG_APAGAR_PANTALLA = 90   # se apaga la pantalla si no tocas nada (se sigue jugando igual)
SEG_PARA_ACTIVIDAD = 3     # segundos sin tocar botones para que se ponga a jugar o soldar
SEG_ENTRE_ACTIVIDADES = 3  # descanso entre una actividad y la siguiente
SEG_PARA_PREGUNTAR = 10    # segundos sin tocar botones para que pregunte si la queres
SEG_PARA_CONTESTAR = 10    # tiempo para contestar antes de que se ponga triste
SEG_FRASE_VISIBLE = 4      # cuanto tiempo se ve cada frase
SEG_CALLADA = (6, 14)      # cuanto tiempo se queda callada entre frase y frase
ARCHIVO = "estado.json"
SEG_GUARDAR = 30           # guarda el progreso cada 30 s (y enseguida despues de cada accion)
SEG_AVISO = 60             # si necesita algo, te avisa con un pitido cada 60 s

# ---- Buzzer ----
PIN_BUZZER = 25
BUZZER_ACTIVO = False      # False = buzzer pasivo (hace melodias). True = buzzer activo (solo pita)
SONIDO_BOTONES = True      # un clic chiquito al apretar cada boton
VOLUMEN = 15               # de 1 (re bajito) a 100 (al palo). Solo para buzzer pasivo

# Cuanto baja cada estadistica por minuto (de 0 a 100)
BAJA_DESPIERTA = {"amor": 2.5, "hambre": 1.5, "energia": 1.0}
BAJA_DORMIDA = {"amor": 0.8, "hambre": 0.5, "energia": -6.0}   # negativo = recupera
CACA_CADA_MIN = (12, 25)   # cada cuantos minutos aparece una caquita

COMIDAS = [
    # nombre, icono, efectos, lo que dice
    ("Arándanos", "arandanos", {"hambre": 50, "amor": 10}, "¡Los amo demasiado!"),   # la que mas llena
    ("Empanada", "empanada", {"hambre": 25}, "¡Qué rica empanada!"),
    ("Alfajor", "alfajor", {"hambre": 15, "amor": 5}, "Mmm, alfajorcito"),
    ("Mate", "mate", {"hambre": 10, "energia": 15, "amor": 5}, "Me gustaría compartirlo con vos"),
    ("Espresso tonic", "espresso", {"hambre": 5, "energia": 30}, "¡Espresso tonic! A mil"),
]
MENU = ["Comer", "Mimos", "Jugar", "Limpiar", "Dormir", "Estado", "Sonido"]

# ================== FRASES ==================
# Lo que dice segun su humor. Agrega o cambia las que quieras (sin emojis).
FRASES = {
    "feliz":    ["¡Hoy es un buen día!", "Te quiero mucho", "¿Jugamos un rato?",
                 "Estoy re contenta", "Me encanta estar con vos", "¡Qué lindo todo!"],
    "normal":   ["¿Qué hacemos?", "Hmm...", "Estoy aburridita", "¿Me das un mimito?"],
    "sin_amor": ["Necesito un abrazo...", "¿Ya no me querés?", "Me siento sola...",
                 "Nadie me quiere..."],
    "hambre":   ["Tengo hambre...", "¿Una empanadita?", "Me ruge la panza"],
    "sueno":    ["Tengo sueño...", "Necesito una siesta", "Se me cierran los ojos"],
    "sucio":    ["Qué olor...", "¿Limpiamos?", "Esto es un chiquero"],
    "enferma":  ["Me siento re mal...", "Estoy toda verde...", "Necesito amor...",
                 "Limpiame un poquito..."],
    "switch":   ["¡Una partidita más!", "Ya casi gano...", "¡Shh, estoy jugando!"],
    "electronica": ["Soldando cositas", "¡Prendió el LED!", "¿Dónde dejé la resistencia?"],
    "curiosa":  ["¿Qué es eso?", "Hmm, ¿y eso?", "Me pareció ver algo..."],
    "durmiendo": ["Zzz... arándano...", "Zzz...", "Zzz... cinco minutos más..."],
}
PREGUNTAS = ["¿Me querés?", "¿Me amás?", "¿Todavía me querés?", "¿Me querés mucho?"]
RESP_SI = ["¡Yo también te quiero!", "¡Sabía!", "Awww, sos lo más", "¡Yo más!"]
RESP_NO = ["...ah. Bueno.", "Me rompiste el corazón", "¿En serio? :(", "Ok... chau."]
RESP_NADA = ["¿Hola? ¿Estás ahí?", "Me ignoraste...", "Bueno, no me contestes..."]

# ================== COLORES ==================
FONDO = rgb(56, 60, 80)          # gris azulado oscuro
FONDO_NOCHE = rgb(26, 28, 44)
BARRA = rgb(28, 30, 44)
BARRA_NOCHE = rgb(12, 13, 22)
TEXTO = rgb(234, 236, 246)
TEXTO_NOCHE = rgb(165, 172, 215)
ACENTO = rgb(150, 178, 238)      # azul hielo
VACIO = rgb(82, 88, 112)
VACIO_NOCHE = rgb(42, 45, 66)
ROJO = rgb(215, 55, 70)          # corazones
GLOBO = rgb(88, 94, 122)         # globito de dialogo
GLOBO_NOCHE = rgb(40, 43, 64)
GLOBO_PREGUNTA = rgb(120, 60, 82)

# ================== POSICIONES ==================
SPR_X, SPR_Y, SPR_ESC = 56, 72, 4     # personaje 128x128
LADO_W, LADO_H = 56, 128              # columnas a los costados del personaje

# ================== ICONOS (pixel art chiquito) ==================
ICONOS = {
    "corazon": ([".XX.XX.",
                 "XXXXXXX",
                 "XXXXXXX",
                 ".XXXXX.",
                 "..XXX..",
                 "...X..."], {"X": ROJO}),
    "empanada": (["..XXXXX..",
                  ".XYYYYYX.",
                  "XYYYYYYYX",
                  "XYYYYYYYX",
                  ".XXXXXXX."], {"X": rgb(185, 115, 45), "Y": rgb(245, 190, 95)}),
    "rayo": (["...XXX",
              "..XXX.",
              ".XXX..",
              "XXXXXX",
              "...XX.",
              "..XX..",
              ".XX...",
              "XX...."], {"X": rgb(240, 150, 30)}),
    "burbuja": (["...X...",
                 "..XXX..",
                 ".XXXXX.",
                 "XXXXXXX",
                 "XWXXXXX",
                 "XWXXXXX",
                 ".XXXXX."], {"X": rgb(100, 160, 230), "W": rgb(235, 245, 255)}),
    "caca": (["....X....",
              "...XXX...",
              "..XXXXX..",
              "..XWXWX..",
              ".XXXXXXX.",
              "XXXXXXXXX",
              "XXXXXXXXX",
              ".XXXXXXX."], {"X": rgb(140, 92, 56), "W": rgb(255, 255, 255)}),
    "mosca": (["W.W",
               ".X."], {"W": rgb(200, 215, 230), "X": rgb(30, 30, 30)}),
    "mate": ([".....S.",
              "....S..",
              ".XXSXX.",
              "XGGGGGX",
              "XMMMMMX",
              "XMMMMMX",
              "XMMMMMX",
              ".XMMMX.",
              "..XXX.."], {"S": rgb(205, 205, 215), "X": rgb(90, 55, 35),
                           "G": rgb(110, 165, 60), "M": rgb(165, 108, 62)}),
    "alfajor": ([".XXXXXXX.",
                 "XXXXXXXXX",
                 "WWWWWWWWW",
                 "XXXXXXXXX",
                 ".XXXXXXX."], {"X": rgb(92, 52, 36), "W": rgb(232, 182, 112)}),
    "arandanos": (["...UU....",
                   "..UNNU...",
                   "..UUUU...",
                   ".UUUU.UU.",
                   "UNNU.UNNU",
                   "UUUU.UUUU",
                   ".UU...UU."], {"U": rgb(100, 140, 222), "N": rgb(50, 60, 120)}),
    "espresso": (["G.....G",
                  "GCCCCCG",
                  "GCWWCCG",
                  "GDWWDDG",
                  "GTTTTTG",
                  "GTTTTTG",
                  "GTTTTTG",
                  ".GGGGG."], {"G": rgb(200, 215, 228), "C": rgb(110, 65, 40), "D": rgb(175, 130, 85),
                               "W": rgb(240, 250, 255), "T": rgb(225, 220, 175)}),
    "brillo": (["..X..",
                ".XXX.",
                "XXWXX",
                ".XXX.",
                "..X.."], {"X": rgb(250, 210, 70), "W": rgb(255, 255, 255)}),
}
ICONO_STAT = [("amor", "corazon"), ("hambre", "empanada"), ("energia", "rayo"), ("higiene", "burbuja")]


def lim(v):
    return 0 if v < 0 else (100 if v > 100 else v)


def pips(v):
    """Pasa de 0-100 a 0-4 cuadraditos."""
    return 0 if v <= 0 else min(4, (int(v) + 24) // 25)


def ya(ahora, t):
    return time.ticks_diff(ahora, t) >= 0


class Botones:
    def __init__(self):
        self.pins = {"A": Pin(13, Pin.IN, Pin.PULL_UP),
                     "B": Pin(14, Pin.IN, Pin.PULL_UP),
                     "C": Pin(27, Pin.IN, Pin.PULL_UP)}
        self.estado = {k: 1 for k in self.pins}
        self.cambio = {k: 0 for k in self.pins}

    def leer(self, ahora):
        eventos = []
        for k, p in self.pins.items():
            v = p.value()
            if v != self.estado[k] and time.ticks_diff(ahora, self.cambio[k]) > 40:
                self.estado[k] = v
                self.cambio[k] = ahora
                if v == 0:
                    eventos.append(k)
        return eventos


# ================== SONIDOS ==================
# Cada sonido es una lista de (frecuencia en Hz, duracion en ms). Frecuencia 0 = silencio.
DO, RE, MI, FA, SOL, LA, SI = 523, 587, 659, 698, 784, 880, 988
DO2, MI2, SOL2, DO3 = 1047, 1319, 1568, 2093
MELODIAS = {
    "inicio":    [(DO, 90), (MI, 90), (SOL, 90), (DO2, 220)],
    "boton":     [(2400, 15)],
    "pregunta":  [(LA, 110), (0, 50), (1175, 200)],
    "si":        [(DO2, 90), (MI2, 90), (SOL2, 90), (DO3, 240)],
    "no":        [(SOL, 220), (MI, 220), (DO, 450)],
    "nada":      [(440, 300), (0, 100), (415, 450)],
    "comer":     [(600, 50), (0, 60), (600, 50), (0, 60), (650, 70)],
    "arandanos": [(600, 50), (0, 50), (650, 50), (0, 50), (DO2, 90), (MI2, 90), (SOL2, 90), (MI2, 90), (SOL2, 260)],
    "mimos":     [(SOL2, 80), (DO3, 140)],
    "limpiar":   [(1000, 40), (1300, 40), (1600, 40), (2000, 90)],
    "caca":      [(220, 120), (160, 220)],
    "dormir":    [(SOL, 220), (MI, 220), (DO, 380)],
    "despertar": [(DO, 120), (MI, 120), (SOL, 240)],
    "enferma":   [(300, 220), (0, 120), (300, 220), (0, 120), (250, 400)],
    "curada":    [(DO, 100), (MI, 100), (SOL, 100), (DO2, 100), (SOL, 100), (DO2, 300)],
    "aviso":     [(1800, 80), (0, 80), (1800, 80)],
    "acierto":   [(MI2, 70), (SOL2, 140)],
    "fallo":     [(300, 220)],
    "ganar":     [(SOL, 100), (SOL, 100), (SOL, 100), (MI2, 350)],
    "perder":    [(LA, 150), (FA, 300)],
}


class Buzzer:
    """Toca melodias sin frenar el juego: se actualiza en cada vuelta del bucle."""

    def __init__(self):
        if BUZZER_ACTIVO:
            self.pin = Pin(PIN_BUZZER, Pin.OUT, value=0)
        else:
            self.pwm = PWM(Pin(PIN_BUZZER))
            self.pwm.freq(1000)
            self.pwm.duty_u16(0)
        self.cola = []
        self.hasta = 0
        self.sonando = False

    def _nota(self, f):
        if BUZZER_ACTIVO:
            self.pin.value(1 if f else 0)
        elif f:
            self.pwm.freq(f)
            self.pwm.duty_u16(max(150, min(32768, VOLUMEN * VOLUMEN * 3)))
        else:
            self.pwm.duty_u16(0)
        self.sonando = bool(f)

    def tocar(self, melodia):
        self.cola = list(melodia)
        self.hasta = time.ticks_ms()

    def actualizar(self, ahora):
        if not ya(ahora, self.hasta):
            return
        if self.cola:
            f, ms = self.cola.pop(0)
            self._nota(f)
            self.hasta = time.ticks_add(ahora, ms)
        elif self.sonando:
            self._nota(0)


CAMPOS = ("amor", "hambre", "energia", "cacas", "enferma", "dormida", "edad", "prox_caca", "sonido")


class Juego:
    def __init__(self):
        self.p = Pantalla()
        self.botones = Botones()
        self.banda = Lienzo(240, 40)          # barra de arriba / abajo / globito / panel
        self.lado = Lienzo(LADO_W, LADO_H)    # columnas a los costados

        # estado que se guarda
        self.amor = 80
        self.hambre = 80
        self.energia = 80
        self.cacas = 0
        self.enferma = False
        self.dormida = False
        self.edad = 0
        self.prox_caca = random.randint(*CACA_CADA_MIN) * 60
        self.sonido = True
        self.cargar()
        self.buzzer = Buzzer()

        ahora = time.ticks_ms()
        self.modo = "casa"
        self.menu_i = 0
        self.comida_i = 0
        self.anim = None          # (sprite, espejo, hasta)
        self.efecto = None        # (tipo, inicio, hasta, dato)
        self.actividad = None     # (sprite, espejo, hasta)
        self.dicho = None         # frase de un evento: (texto, hasta)
        self.frase = ""           # frase de humor actual
        self.frase_humor = None
        self.frase_hasta = ahora  # hasta cuando se ve la frase
        self.prox_frase = time.ticks_add(ahora, 1500)
        self.pregunta = None      # (texto, hasta)
        self.prox_pregunta = time.ticks_add(ahora, SEG_PARA_PREGUNTAR * 1000)
        self.ultimo_boton = ahora
        self.prox_actividad = ahora
        self.prox_parpadeo = time.ticks_add(ahora, 3000)
        self.parpadeo_hasta = ahora
        self.pantalla_on = True
        self.sucio = False
        self.ultimo_guardado = ahora
        self.jg = {}              # estado del minijuego
        self.prox_aviso = time.ticks_add(ahora, SEG_AVISO * 1000)
        self.p.brillo(30 if self.dormida else 100)
        self.forzar_redibujo()
        self.sonar("inicio")

    def sonar(self, nombre):
        if self.sonido:
            self.buzzer.tocar(MELODIAS[nombre])

    # ---------- guardar / cargar ----------
    def cargar(self):
        # si se corto la luz justo mientras guardaba, usa la copia temporal
        for nombre in (ARCHIVO, ARCHIVO + ".tmp"):
            try:
                with open(nombre) as f:
                    d = json.load(f)
                for k in CAMPOS:
                    if k in d:
                        setattr(self, k, d[k])
                return
            except (OSError, ValueError):
                pass

    def guardar(self):
        # primero escribe una copia y despues la renombra: si se corta la luz
        # en el medio, el archivo bueno nunca queda roto
        tmp = ARCHIVO + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump({k: getattr(self, k) for k in CAMPOS}, f)
            try:
                os.rename(tmp, ARCHIVO)
            except OSError:
                os.remove(ARCHIVO)
                os.rename(tmp, ARCHIVO)
        except OSError:
            pass
        self.sucio = False
        self.ultimo_guardado = time.ticks_ms()

    def autoguardar(self, ahora):
        t = time.ticks_diff(ahora, self.ultimo_guardado)
        if (self.sucio and t > 1500) or t > SEG_GUARDAR * 1000:
            self.guardar()

    # ---------- estadisticas ----------
    @property
    def higiene(self):
        return max(0, 100 - 25 * self.cacas)

    def valor(self, nombre):
        return getattr(self, nombre)

    def alerta(self):
        return self.amor < 25 or self.hambre < 25 or self.energia < 25 or self.cacas >= 3

    def tick(self, dt_real):
        dt = dt_real * VELOCIDAD
        self.edad += dt
        m = dt / 60
        tabla = BAJA_DORMIDA if self.dormida else BAJA_DESPIERTA
        f = 1.5 if self.enferma else 1
        self.amor = lim(self.amor - tabla["amor"] * m * f)
        self.hambre = lim(self.hambre - tabla["hambre"] * m * f)
        self.energia = lim(self.energia - tabla["energia"] * m)

        if not self.dormida:
            self.prox_caca -= dt
            if self.prox_caca <= 0:
                if self.cacas < 4:
                    self.cacas += 1
                    self.sucio = True
                    self.sonar("caca")
                self.prox_caca = random.randint(*CACA_CADA_MIN) * 60
            if self.energia <= 0:
                self.dormir()
                self.decir("Me dormí...")
        elif self.energia >= 100:
            self.despertar()

        if not self.enferma and (self.amor <= 0 or self.hambre <= 0 or self.cacas >= 4):
            self.enferma = True
            self.actividad = None
            self.sucio = True
            self.sonar("enferma")
        elif self.enferma and self.cacas == 0 and self.amor >= 50 and self.hambre >= 25:
            self.enferma = False
            self.animar("feliz", 2500)
            self.decir("¡Ya me curé!")
            self.sonar("curada")
            self.sucio = True

    # ---------- humor y frases ----------
    def humor(self):
        if self.dormida:
            return "durmiendo"
        if self.enferma:
            return "enferma"
        if self.actividad:
            return "curiosa" if self.actividad[0].startswith("curiosa") else self.actividad[0]
        if self.amor < 25:
            return "sin_amor"
        if self.hambre < 25:
            return "hambre"
        if self.energia < 25:
            return "sueno"
        if self.cacas >= 2:
            return "sucio"
        return "feliz" if self.amor >= 60 else "normal"

    def elegir_frase(self, ahora):
        h = self.humor()
        opciones = FRASES[h]
        nueva = random.choice(opciones)
        if len(opciones) > 1:
            while nueva == self.frase:
                nueva = random.choice(opciones)
        self.frase = nueva
        self.frase_humor = h
        self.frase_hasta = time.ticks_add(ahora, SEG_FRASE_VISIBLE * 1000)
        self.prox_frase = time.ticks_add(ahora, (SEG_FRASE_VISIBLE + random.randint(*SEG_CALLADA)) * 1000)

    def decir(self, texto, ms=3500):
        self.dicho = (texto, time.ticks_add(time.ticks_ms(), ms))

    def texto_globo(self):
        if self.pregunta:
            return self.pregunta[0]
        if self.dicho:
            return self.dicho[0]
        if not ya(time.ticks_ms(), self.frase_hasta):
            return self.frase
        return ""                             # callada: no hay globito

    # ---------- pregunta de amor ----------
    def preguntar(self, ahora):
        self.pregunta = (random.choice(PREGUNTAS), time.ticks_add(ahora, SEG_PARA_CONTESTAR * 1000))
        self.actividad = None
        self.sonar("pregunta")
        if not self.pantalla_on:              # se prende la pantalla para preguntarte
            self.pantalla_on = True
            self.p.brillo(100)
            self.forzar_redibujo()

    def responder(self, respuesta, ahora):
        self.pregunta = None
        self.prox_pregunta = time.ticks_add(ahora, SEG_PARA_PREGUNTAR * 1000)
        if respuesta == "si":                 # el amor se mantiene
            self.animar("feliz", 2500)
            self.efecto_nuevo("corazones", 2500)
            self.decir(random.choice(RESP_SI))
            self.sonar("si")
        elif respuesta == "no":               # el amor baja a 0
            self.amor = 0
            self.animar("triste", 3500)
            self.decir(random.choice(RESP_NO))
            self.sonar("no")
        else:                                 # no contestaste: baja a la mitad
            self.amor = self.amor / 2
            self.animar("triste", 3000)
            self.decir(random.choice(RESP_NADA))
            self.sonar("nada")
        self.sucio = True

    # ---------- acciones ----------
    def animar(self, sprite, ms, espejo=False):
        self.anim = (sprite, espejo, time.ticks_add(time.ticks_ms(), ms))

    def efecto_nuevo(self, tipo, ms, dato=None):
        ahora = time.ticks_ms()
        self.efecto = (tipo, ahora, time.ticks_add(ahora, ms), dato)

    def comer(self, i):
        nombre, icono, efectos, frase = COMIDAS[i]
        if self.hambre >= 95 and "energia" not in efectos:
            self.decir("¡Estoy llena!")
            return
        for k, v in efectos.items():
            setattr(self, k, lim(getattr(self, k) + v))
        self.animar("comiendo", 2500)
        self.sonar("arandanos" if icono == "arandanos" else "comer")
        self.efecto_nuevo("comida", 2500, icono)
        self.decir(frase, 3000)
        self.prox_caca = min(self.prox_caca, random.randint(3, 6) * 60)
        self.sucio = True

    def mimos(self):
        self.amor = lim(self.amor + (15 if self.enferma else 25))
        self.animar("feliz", 3000)
        self.efecto_nuevo("corazones", 3000)
        self.decir(random.choice(["¡Más mimos!", "Awww", "Te quiero mucho"]), 3000)
        self.sonar("mimos")
        self.sucio = True

    def limpiar(self):
        if self.cacas == 0:
            self.decir("¡Ya está limpio!")
            return
        self.cacas = 0
        self.animar("feliz", 1500)
        self.efecto_nuevo("brillos", 1500)
        self.decir("¡Ahora sí!", 2000)
        self.sonar("limpiar")
        self.sucio = True

    def dormir(self):
        self.dormida = True
        self.actividad = None
        self.anim = None
        self.efecto = None
        self.pregunta = None
        self.modo = "casa"
        self.p.brillo(30)
        self.decir("Buenas noches...", 2500)
        self.sonar("dormir")
        self.sucio = True

    def despertar(self):
        self.dormida = False
        self.p.brillo(100)
        self.animar("feliz", 1500)
        self.decir("¡Buen día!", 2500)
        self.sonar("despertar")
        self.prox_pregunta = time.ticks_add(time.ticks_ms(), SEG_PARA_PREGUNTAR * 1000)
        self.sucio = True

    def empezar_juego(self):
        if self.enferma:
            self.decir("Me siento mal...")
        elif self.energia < 15:
            self.decir("Muy cansada...")
        else:
            self.modo = "jugar"
            self.jg = {"ronda": 1, "puntos": 0, "fase": "elegir", "hasta": 0, "texto": ""}
            self.decir("¡A ver si adivinás!", 2500)

    def terminar_juego(self):
        pts = self.jg["puntos"]
        self.energia = lim(self.energia - 10)
        self.hambre = lim(self.hambre - 5)
        if pts >= 3:
            self.amor = lim(self.amor + 25)
            self.animar("feliz", 2500)
            self.efecto_nuevo("corazones", 2500)
            self.decir("¡Ganaste! %d/5" % pts, 3000)
            self.sonar("ganar")
        else:
            self.amor = lim(self.amor + 10)
            self.decir("%d/5 ¡otra vez!" % pts, 3000)
            self.sonar("perder")
        self.modo = "casa"
        self.prox_pregunta = time.ticks_add(time.ticks_ms(), SEG_PARA_PREGUNTAR * 1000)
        self.sucio = True

    # ---------- botones ----------
    def boton(self, b, ahora):
        self.ultimo_boton = ahora
        if SONIDO_BOTONES:
            self.sonar("boton")
        if not self.pantalla_on:
            self.pantalla_on = True
            self.p.brillo(30 if self.dormida else 100)
            self.forzar_redibujo()
            return
        if self.pregunta:                      # A = si, C = no
            if b == "A":
                self.responder("si", ahora)
            elif b == "C":
                self.responder("no", ahora)
            return
        if self.actividad:                     # la interrumpiste: te mira feliz
            self.actividad = None
            self.prox_actividad = time.ticks_add(ahora, SEG_ENTRE_ACTIVIDADES * 1000)
            self.animar("feliz", 1500)

        if self.dormida:
            if b == "B":
                self.despertar()
            return

        if self.modo == "casa":
            if b == "A":
                self.menu_i = (self.menu_i + 1) % len(MENU)
            elif b == "C":
                self.menu_i = (self.menu_i - 1) % len(MENU)
            elif b == "B":
                op = MENU[self.menu_i]
                if op == "Comer":
                    self.modo = "comer"
                elif op == "Mimos":
                    self.mimos()
                elif op == "Jugar":
                    self.empezar_juego()
                elif op == "Limpiar":
                    self.limpiar()
                elif op == "Dormir":
                    self.dormir()
                elif op == "Estado":
                    self.modo = "estado"
                elif op == "Sonido":
                    self.sonido = not self.sonido
                    self.sucio = True
                    self.decir("Sonido activado" if self.sonido else "Shh... sin sonido", 2000)
                    self.sonar("mimos")
        elif self.modo == "comer":
            if b == "A":
                self.comida_i = (self.comida_i + 1) % len(COMIDAS)
            elif b == "B":
                self.modo = "casa"
                self.comer(self.comida_i)
            elif b == "C":
                self.modo = "casa"
        elif self.modo == "estado":
            self.modo = "casa"
        elif self.modo == "jugar":
            if self.jg["fase"] == "elegir" and b in ("A", "C"):
                eleccion = "izq" if b == "A" else "der"
                mira = random.choice(("izq", "der"))
                acierto = eleccion == mira
                if acierto:
                    self.jg["puntos"] += 1
                self.sonar("acierto" if acierto else "fallo")
                self.jg["fase"] = "mostrar"
                self.jg["hasta"] = time.ticks_add(ahora, 1500)
                self.jg["texto"] = "¡Bien!" if acierto else "Uy, no..."
                self.anim = ("curiosa_izq" if mira == "izq" else "curiosa", False, self.jg["hasta"])
            elif b == "B" and self.jg["fase"] == "elegir":
                self.modo = "casa"               # B sale del juego

    # ---------- logica de tiempo ----------
    def actualizar(self, ahora):
        if self.anim and ya(ahora, self.anim[2]):
            self.anim = None
        if self.efecto and ya(ahora, self.efecto[2]):
            self.efecto = None
        if self.dicho and ya(ahora, self.dicho[1]):
            self.dicho = None
        if self.actividad and ya(ahora, self.actividad[2]):
            self.actividad = None
            self.prox_actividad = time.ticks_add(ahora, SEG_ENTRE_ACTIVIDADES * 1000)

        quieta = time.ticks_diff(ahora, self.ultimo_boton)

        # pregunta de amor: solo si hace 10 s que no tocas ningun boton
        if self.pregunta and ya(ahora, self.pregunta[1]):
            self.responder("nada", ahora)
        elif (not self.pregunta and not self.dormida and self.modo == "casa"
              and quieta >= SEG_PARA_PREGUNTAR * 1000 and ya(ahora, self.prox_pregunta)):
            self.preguntar(ahora)

        if self.modo == "jugar" and self.jg["fase"] == "mostrar" and ya(ahora, self.jg["hasta"]):
            self.jg["ronda"] += 1
            if self.jg["ronda"] > 5:
                self.terminar_juego()
            else:
                self.jg["fase"] = "elegir"

        if (not self.actividad and not self.anim and not self.dormida and not self.enferma
                and not self.pregunta and self.modo == "casa" and not self.alerta()
                and quieta > SEG_PARA_ACTIVIDAD * 1000 and ya(ahora, self.prox_actividad)):
            sprite = random.choice(("switch", "electronica", "curiosa", "curiosa_izq"))
            self.actividad = (sprite, False, time.ticks_add(ahora, random.randint(6, 12) * 1000))

        # cambia de frase cada tanto, o enseguida si cambio su humor
        if ya(ahora, self.prox_frase) or self.humor() != self.frase_humor:
            self.elegir_frase(ahora)

        if ya(ahora, self.prox_aviso):
            if self.alerta() and not self.dormida and not self.pregunta:
                self.sonar("aviso")
            self.prox_aviso = time.ticks_add(ahora, SEG_AVISO * 1000)

        if ya(ahora, self.prox_parpadeo):
            self.parpadeo_hasta = time.ticks_add(ahora, 150)
            self.prox_parpadeo = time.ticks_add(ahora, random.randint(2500, 6000))

        if (self.pantalla_on and quieta > SEG_APAGAR_PANTALLA * 1000
                and not self.efecto and not self.pregunta):
            self.pantalla_on = False
            self.p.brillo(0)

    def sprite_actual(self, ahora):
        if self.dormida:
            return ("durmiendo", False)
        if self.anim:
            return (self.anim[0], self.anim[1])
        if self.enferma:
            return ("enferma", False)
        if self.pregunta:
            return ("curiosa", False)
        if self.actividad:
            return (self.actividad[0], self.actividad[1])
        if self.alerta():
            return ("triste", False)
        if not ya(ahora, self.parpadeo_hasta):
            return ("parpadeo", False)
        return ("normal", False)

    # ---------- dibujo ----------
    def forzar_redibujo(self):
        self.k_sup = self.k_inf = self.k_mascota = self.k_lados = self.k_globo = None
        self.k_fondo = None

    def colores(self):
        if self.dormida:
            return FONDO_NOCHE, BARRA_NOCHE, TEXTO_NOCHE, VACIO_NOCHE
        return FONDO, BARRA, TEXTO, VACIO

    def dibujar(self, ahora):
        fondo, barra, texto, vacio = self.colores()
        if self.k_fondo != fondo:
            self.p.rect(0, 0, 240, 240, fondo)
            self.k_fondo = fondo
            self.k_sup = self.k_inf = self.k_mascota = self.k_lados = self.k_globo = None

        # barra de arriba
        parpadeo_alerta = (ahora // 500) % 2
        valores = [pips(self.higiene if n == "higiene" else self.valor(n)) for n, _ in ICONO_STAT]
        k = (tuple(valores), parpadeo_alerta, fondo)
        if k != self.k_sup:
            self.k_sup = k
            self.barra_superior(valores, parpadeo_alerta, barra, vacio)

        # barra de abajo
        l1, l2 = self.textos_inferiores(ahora)
        k = (l1, l2, fondo)
        if k != self.k_inf:
            self.k_inf = k
            self.barra_inferior(l1, l2, barra, texto)

        # centro
        if self.modo == "estado":
            k = ("estado", tuple(valores), int(self.edad // 60), self.enferma)
            if k != self.k_mascota:
                self.k_mascota = k
                self.k_lados = self.k_globo = None
                self.panel_estado(fondo, texto, vacio)
            return

        g = self.texto_globo()
        k = (g, bool(self.pregunta), fondo)
        if k != self.k_globo:
            self.k_globo = k
            self.globo(g, fondo, texto)

        sp = self.sprite_actual(ahora)
        k = (sp, fondo)
        if k != self.k_mascota:
            self.k_mascota = k
            nombre, espejo = sp
            pal = sprites.PALETA_ENFERMA if nombre in sprites.ENFERMOS else sprites.PALETA
            self.p.sprite(sprites.SPRITES[nombre], pal, SPR_X, SPR_Y, SPR_ESC, fondo, espejo)

        k = self.clave_lados(ahora, fondo)
        if k != self.k_lados:
            self.k_lados = k
            for lado, x in (("izq", 0), ("der", 240 - LADO_W)):
                self.dibujar_lado(lado, ahora, fondo)
                self.p.mostrar(self.lado, x, SPR_Y)

    def textos_inferiores(self, ahora):
        if self.pregunta:
            quedan = max(0, time.ticks_diff(self.pregunta[1], ahora) // 1000 + 1)
            return ("A: Sí      C: No", "tenés %ds para contestar" % quedan)
        if self.dormida:
            return ("Zzz...", "B: despertar")
        if self.modo == "comer":
            return ("< %s >" % COMIDAS[self.comida_i][0], "A: otra   B: comer   C: volver")
        if self.modo == "estado":
            return ("Estado", "cualquier botón: volver")
        if self.modo == "jugar":
            if self.jg["fase"] == "mostrar":
                return (self.jg["texto"], "Ronda %d/5" % self.jg["ronda"])
            return ("¿Para dónde mira?", "A: izq   C: der   B: salir  (%d/5)" % self.jg["ronda"])
        op = MENU[self.menu_i]
        if op == "Sonido":
            op = "Sonido: " + ("sí" if self.sonido else "no")
        return ("< %s >" % op, "A: sig.    B: elegir    C: ant.")

    def barra_superior(self, valores, parp, barra, vacio):
        b = self.banda
        b.llenar(barra)
        for i, (nombre, icono) in enumerate(ICONO_STAT):
            x = i * 60
            v = valores[i]
            filas = ICONOS[icono][0]
            if not (v <= 1 and parp):            # el icono titila si esta bajo
                b.icono(ICONOS[icono], x + 4 + (14 - len(filas[0]) * 2) // 2, 20 - len(filas), 2)
            for j in range(4):
                b.rect(x + 22 + j * 9, 16, 7, 8, ACENTO if j < v else vacio)
        self.p.mostrar(b, 0, 0)

    def barra_inferior(self, l1, l2, barra, texto):
        b = self.banda
        b.llenar(barra)
        f1 = GRANDE if ancho_texto(l1, GRANDE) <= 232 else CHICA
        if l2:
            b.texto_centrado(l1, 3, texto, f1)
            b.texto_centrado(l2, 25, texto, CHICA)
        else:
            b.texto_centrado(l1, (40 - f1["alto"]) // 2, texto, f1)
        self.p.mostrar(b, 0, 200)

    def globo(self, texto_globo, fondo, texto):
        """Globito de dialogo de 32 px de alto, arriba del personaje."""
        b = self.banda
        b.llenar(fondo)
        if texto_globo:
            if self.pregunta:
                color = GLOBO_PREGUNTA
            else:
                color = GLOBO_NOCHE if self.dormida else GLOBO
            f = GRANDE if ancho_texto(texto_globo, GRANDE) <= 214 else CHICA
            w = min(240, ancho_texto(texto_globo, f) + 16)
            x0 = (240 - w) // 2
            b.rect(x0 + 2, 1, w - 4, 26, color)          # globo con esquinas redondeadas
            b.rect(x0, 3, w, 22, color)
            b.rect(x0 + 1, 2, w - 2, 24, color)
            for i in range(4):                           # colita hacia abajo
                b.rect(116 + i, 27 + i, 8 - 2 * i, 1, color)
            b.texto_centrado(texto_globo, 1 + (26 - f["alto"]) // 2, texto, f)
        self.p.mostrar(b, 0, 40, 32)

    def panel_estado(self, fondo, texto, vacio):
        d = int(self.edad // 86400)
        h = int(self.edad % 86400 // 3600)
        mi = int(self.edad % 3600 // 60)
        filas = [("Edad", "%dd %dh %dm" % (d, h, mi))]
        for n, et in (("amor", "Amor"), ("hambre", "Hambre"), ("energia", "Energía"), ("higiene", "Higiene")):
            filas.append((et, self.higiene if n == "higiene" else self.valor(n)))
        filas.append(("Salud", "Enferma :(" if self.enferma else "Bien :)"))
        b = self.banda
        for banda in range(4):
            y0 = banda * 40
            b.llenar(fondo)
            for i, (et, val) in enumerate(filas):
                y = 4 + i * 26 - y0
                if y < -24 or y > 40:
                    continue
                b.texto(et, 12, y, texto, GRANDE)
                if isinstance(val, str):
                    b.texto(val, 120, y + 3, texto, CHICA)
                else:
                    b.rect(120, y + 5, 104, 10, vacio)
                    b.rect(120, y + 5, int(val * 104 // 100), 10, ACENTO)
            self.p.mostrar(b, 0, 40 + y0)

    def clave_lados(self, ahora, fondo):
        k = [fondo, self.cacas, self.dormida]
        if self.enferma and self.cacas:
            k.append(ahora // 300)
        if self.efecto:
            k.append(self.efecto[0])
            k.append(ahora // 150)
        if self.dormida:
            k.append(ahora // 700)
        return tuple(k)

    def dibujar_lado(self, lado, ahora, fondo):
        L = self.lado
        L.llenar(fondo)
        # caquitas: 1 der abajo, 2 izq abajo, 3 der medio, 4 izq medio
        posiciones = [("der", 100), ("izq", 100), ("der", 64), ("izq", 64)]
        for i in range(self.cacas):
            s, y = posiciones[i]
            if s == lado:
                L.icono(ICONOS["caca"], 14, y, 3)
                if self.enferma:
                    for _ in range(2):
                        L.icono(ICONOS["mosca"], random.randint(4, 46), y - random.randint(4, 18), 2)

        if self.efecto:
            tipo, inicio, hasta, dato = self.efecto
            t = time.ticks_diff(ahora, inicio)
            if tipo == "corazones":
                for k in range(2):
                    y = 60 - ((t // 25 + k * 30) % 60)
                    x = 6 if (lado == "izq") == (k == 0) else 28
                    L.icono(ICONOS["corazon"], x, y, 3)
            elif tipo == "comida" and lado == "izq":
                esc = 4 if len(ICONOS[dato][0][0]) <= 7 else 3
                L.icono(ICONOS[dato], (LADO_W - len(ICONOS[dato][0][0]) * esc) // 2, 8, esc)
            elif tipo == "brillos":
                for _ in range(3):
                    L.icono(ICONOS["brillo"], random.randint(0, 44), random.randint(0, 118), 2)

        if self.dormida and lado == "der":
            fase = (ahora // 700) % 3
            L.texto("z", 14, 50, TEXTO_NOCHE, CHICA)
            if fase >= 1:
                L.texto("Z", 24, 30, TEXTO_NOCHE, CHICA)
            if fase >= 2:
                L.texto("Z", 16, 6, TEXTO_NOCHE, GRANDE)

    # ---------- bucle principal ----------
    def correr(self):
        ultimo = time.ticks_ms()
        while True:
            ahora = time.ticks_ms()
            for b in self.botones.leer(ahora):
                self.boton(b, ahora)
            dt = time.ticks_diff(ahora, ultimo)
            if dt >= 1000:
                self.tick(dt / 1000)
                ultimo = ahora
            self.actualizar(ahora)
            self.buzzer.actualizar(ahora)
            if self.pantalla_on:
                self.dibujar(ahora)
            self.autoguardar(ahora)
            time.sleep_ms(20)


Juego().correr()
