"""
Punto de entrada. Orquesta VentanaNativa, Renderizador y la UI.

Controles:
  L        -> bloquear/desbloquear "siempre al frente"
  T        -> activar/desactivar click-through (la ventana ignora el ratón)
  TAB      -> abrir/cerrar el selector de shaders
  ESC      -> cerrar el selector, o salir si ya está cerrado
  Rueda    -> redimensionar
  Arrastrar-> mover la ventana
"""

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProclessDPIAware()

import sys
import pygame
import mss

from config import (
    ANCHO_INICIAL, ALTO_INICIAL, ESCALA_ZOOM, ANCHO_MINIMO,
    RUTA_SHADER, CARPETA_SHADERS, FPS,
)
from ventana_nativa import VentanaNativa
from renderer import Renderizador
from ui import SelectorShaders

# Los dos "modos" del programa. En vez de un await como en Godot, el bucle
# mira en qué estado está y ejecuta un camino u otro en cada frame.
MODO_RENDER = "render"
MODO_MENU = "menu"

def crear_ventana_pygame(ancho, alto):
    return pygame.display.set_mode(
        (ancho, alto),
        pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.NOFRAME,
    )




def main():
    pygame.init()
    sct = mss.mss()

    ancho, alto = ANCHO_INICIAL, ALTO_INICIAL
    crear_ventana_pygame(ancho, alto)

    hwnd = pygame.display.get_wm_info()['window']
    win_nativa = VentanaNativa(hwnd)
    render = Renderizador(RUTA_SHADER, ancho, alto)
    selector = SelectorShaders(CARPETA_SHADERS)

    reloj = pygame.time.Clock()
    ejecutando = True
    modo = MODO_RENDER
    arrastrando = False
    offset_x = offset_y = 0

    estado_ventana = None

    def aplicar_geometria(nuevo_ancho, nuevo_alto, x, y):
        nonlocal ancho, alto, hwnd

        crear_ventana_pygame(nuevo_ancho, nuevo_alto)
        hwnd = pygame.display.get_wm_info()['window']
        win_nativa.actualizar_hwnd(hwnd)
        pygame.display.set_window_position((x, y))
        render.redimensionar(nuevo_ancho, nuevo_alto)

        ancho, alto = nuevo_ancho, nuevo_alto

    while ejecutando:
        pygame.event.pump()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
                continue

            # ---------------- MODO MENÚ ----------------
            # Mientras el menú está abierto, el resto de controles
            # (arrastre, zoom) quedan "bloqueados": ni los miramos.
            if modo == MODO_MENU:
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_TAB):
                    modo = MODO_RENDER
                    continue

                ruta = selector.manejar_evento(evento, ancho, alto)
                if ruta:
                    render.cambiar_shader(ruta)
                    modo = MODO_RENDER
                continue

            # ---------------- MODO RENDER ----------------
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F11:
                    if estado_ventana is None:
                        estado_ventana = (ancho, alto, *pygame.display.get_window_position())
                        ancho_pantalla, alto_pantalla = win_nativa.obtener_resolucion_pantalla()
                        aplicar_geometria(ancho_pantalla, alto_pantalla, 0, 0)
                    else:
                        an, al, x, y = estado_ventana
                        aplicar_geometria(an, al, x, y)
                        estado_ventana = None


                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False

                elif evento.key == pygame.K_TAB:
                    selector.refrescar()
                    modo = MODO_MENU
                    arrastrando = False

                elif evento.key == pygame.K_l:
                    bloqueada = win_nativa.alternar_bloqueo()
                    print("Ventana:", "BLOQUEADA al frente" if bloqueada else "Normal")

                elif evento.key == pygame.K_t:
                    nuevo = not win_nativa.click_through
                    win_nativa.establecer_click_through(nuevo)
                    arrastrando = False
                    print("Click-through:", "ACTIVADO (ignora el ratón)" if nuevo else "desactivado")

            elif evento.type == pygame.VIDEORESIZE:
                ancho, alto = evento.w, evento.h
                render.redimensionar(ancho, alto)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                arrastrando = True
                offset_x, offset_y = pygame.mouse.get_pos()

            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                arrastrando = False

            elif evento.type == pygame.MOUSEWHEEL:
                ancho_antiguo, alto_antiguo = ancho, alto

                if evento.y > 0:
                    ancho += ESCALA_ZOOM
                elif evento.y < 0:
                    ancho = max(ANCHO_MINIMO, ancho - ESCALA_ZOOM)
                alto = ancho // 2

                if (ancho, alto) != (ancho_antiguo, alto_antiguo):
                    pos_actual = pygame.display.get_window_position()
                    x, y = pos_actual
                    aplicar_geometria(ancho, alto, x, y)

        # ---- Lógica continua (solo en modo render) ----
        if modo == MODO_RENDER and arrastrando:
            global_x, global_y = win_nativa.obtener_mouse_absoluto()
            pygame.display.set_window_position((global_x - offset_x, global_y - offset_y))

        # ---- Dibujado ----
        pos_x, pos_y = pygame.display.get_window_position()
        
        # 🛡️ VALIDACIÓN DE SEGURIDAD: Evita pasar 0 o valores negativos a mss
        if ancho > 0 and alto > 0:
            try:
                captura = sct.grab({"top": pos_y, "left": pos_x, "width": ancho, "height": alto})
            except mss.exception.ScreenShotError:
                captura = None

            if captura is not None:
                render.renderizar(captura.rgb, pygame.time.get_ticks() / 1000.0)

                if modo == MODO_MENU:
                    render.dibujar_ui(selector.dibujar(ancho, alto))

                pygame.display.flip()
            
        reloj.tick(FPS)

    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    main()