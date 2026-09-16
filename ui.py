"""
UI básica del proyecto.

OJO AL DATO IMPORTANTE:
Como la ventana está creada con pygame.OPENGL, NO puedes usar el dibujado
normal de pygame (screen.blit, pygame.draw sobre la ventana). Esa
superficie ya no existe: todo lo pinta OpenGL.

La solución (y es lo que hace casi todo el mundo) es:
  1. Dibujar la UI con pygame en una Surface aparte, en memoria.
  2. Convertir esa Surface en una textura de OpenGL.
  3. Dibujar esa textura encima de tu shader, con transparencia.

Así sigues usando las funciones de pygame que ya conoces (pygame.draw.rect,
font.render...) y OpenGL solo se encarga de pegarlo por encima.
"""

import os
import pygame

COLOR_FONDO_PANEL = (18, 18, 22, 220)   # el 4º valor es el alpha
COLOR_TEXTO = (230, 230, 235)
COLOR_SELECCION = (80, 140, 255)
COLOR_BORDE = (70, 70, 80)

MARGEN = 16
ALTO_FILA = 28


def listar_shaders(carpeta):
    """Devuelve la lista de archivos .glsl que haya en la carpeta."""
    if not os.path.isdir(carpeta):
        return []
    return sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".glsl"))


class SelectorShaders:
    """
    Menú simple para elegir shader. Funciona con flechas arriba/abajo +
    Enter, y también con el ratón.

    Uso desde main.py:
        selector.manejar_evento(evento)   -> devuelve la ruta elegida o None
        superficie = selector.dibujar(ancho, alto)
    """

    def __init__(self, carpeta_shaders):
        self.carpeta = carpeta_shaders
        self.shaders = listar_shaders(carpeta_shaders)
        self.indice = 0
        self.indice_hover = -1

        # La fuente hay que crearla después de pygame.init()
        self.fuente = pygame.font.SysFont("Consolas", 16)
        self.fuente_titulo = pygame.font.SysFont("Consolas", 18, bold=True)

    def refrescar(self):
        """Vuelve a leer la carpeta, por si añadiste un .glsl con el programa abierto."""
        self.shaders = listar_shaders(self.carpeta)
        self.indice = min(self.indice, max(0, len(self.shaders) - 1))

    # ------------------------------------------------------------------

    def _rect_fila(self, i, ancho):
        y = MARGEN + 34 + i * ALTO_FILA
        return pygame.Rect(MARGEN, y, ancho - MARGEN * 2, ALTO_FILA)

    def manejar_evento(self, evento, ancho, alto):
        """
        Procesa un evento. Devuelve la RUTA del shader si el usuario ha
        confirmado una elección, o None si todavía no ha elegido nada.
        """
        if not self.shaders:
            return None

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_DOWN:
                self.indice = (self.indice + 1) % len(self.shaders)
            elif evento.key == pygame.K_UP:
                self.indice = (self.indice - 1) % len(self.shaders)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.ruta_actual()

        elif evento.type == pygame.MOUSEMOTION:
            self.indice_hover = -1
            for i in range(len(self.shaders)):
                if self._rect_fila(i, ancho).collidepoint(evento.pos):
                    self.indice_hover = i
                    break

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i in range(len(self.shaders)):
                if self._rect_fila(i, ancho).collidepoint(evento.pos):
                    self.indice = i
                    return self.ruta_actual()

        return None

    def ruta_actual(self):
        if not self.shaders:
            return None
        return os.path.join(self.carpeta, self.shaders[self.indice])

    # ------------------------------------------------------------------

    def dibujar(self, ancho, alto):
        """
        Dibuja el panel en una Surface con canal alfa y la devuelve.
        main.py se la pasará al Renderizador para que la pinte por encima.
        """
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)

        filas = max(1, len(self.shaders))
        alto_panel = 34 + filas * ALTO_FILA + MARGEN
        panel = pygame.Rect(MARGEN // 2, MARGEN // 2,
                            ancho - MARGEN, min(alto_panel, alto - MARGEN))

        pygame.draw.rect(superficie, COLOR_FONDO_PANEL, panel, border_radius=8)
        pygame.draw.rect(superficie, COLOR_BORDE, panel, width=1, border_radius=8)

        titulo = self.fuente_titulo.render("Elegir shader  (Esc para salir)", True, COLOR_TEXTO)
        superficie.blit(titulo, (MARGEN, MARGEN))

        if not self.shaders:
            aviso = self.fuente.render("No hay archivos .glsl en la carpeta", True, COLOR_TEXTO)
            superficie.blit(aviso, (MARGEN, MARGEN + 34))
            return superficie

        for i, nombre in enumerate(self.shaders):
            rect = self._rect_fila(i, ancho)
            if rect.bottom > alto:
                break

            if i == self.indice:
                pygame.draw.rect(superficie, COLOR_SELECCION, rect, border_radius=4)
            elif i == self.indice_hover:
                pygame.draw.rect(superficie, (45, 45, 55), rect, border_radius=4)

            texto = self.fuente.render(nombre, True, COLOR_TEXTO)
            superficie.blit(texto, (rect.x + 8, rect.y + 4))

        return superficie