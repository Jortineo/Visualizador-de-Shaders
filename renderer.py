"""
Todo lo relacionado con moderngl vive aquí: compilar el shader, la
geometría, la textura de captura, el dibujado, y ahora también pegar
la UI por encima.
"""

import array
import pygame
import moderngl

VERTEX_SHADER = """
#version 330
in vec2 in_vert;
out vec2 v_texcoord;

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_texcoord = in_vert * 0.5 + 0.5;
}
"""

# Shader mínimo para pegar la UI encima, respetando la transparencia.
OVERLAY_FRAGMENT = """
#version 330
uniform sampler2D u_ui;
in vec2 v_texcoord;
out vec4 f_color;

void main() {
    f_color = texture(u_ui, v_texcoord);
}
"""

VERTICES = [
    -1.0, -1.0,   1.0, -1.0,  -1.0,  1.0,
    -1.0,  1.0,   1.0, -1.0,   1.0,  1.0,
]


class Renderizador:
    def __init__(self, ruta_fragment_shader, ancho, alto):
        self.ctx = moderngl.create_context()
        self.ancho = ancho
        self.alto = alto

        self.ctx.viewport = (0, 0, ancho, alto)

        self.vbo = self.ctx.buffer(array.array('f', VERTICES))

        self.prog = None
        self.vao = None
        self.cambiar_shader(ruta_fragment_shader)

        self.textura = None
        self._crear_textura()

        # Programa y textura dedicados a la UI
        self.prog_ui = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT,
        )
        self.vao_ui = self.ctx.vertex_array(self.prog_ui, [(self.vbo, '2f', 'in_vert')])
        self.textura_ui = None

    # ------------------------------------------------------------------

    def cambiar_shader(self, ruta_fragment_shader):
        """
        Compila (o recompila) el programa desde un .glsl distinto.
        Si el shader tiene un error de sintaxis, avisa y NO rompe el
        programa: se queda con el que ya estaba funcionando.
        """
        try:
            with open(ruta_fragment_shader, "r") as archivo:
                codigo = archivo.read()
            nuevo_prog = self.ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=codigo,
            )
        except Exception as e:
            print(f"No se pudo cargar el shader '{ruta_fragment_shader}':\n{e}")
            return False

        if self.prog is not None:
            self.prog.release()
        if self.vao is not None:
            self.vao.release()

        self.prog = nuevo_prog
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f', 'in_vert')])
        return True

    def redimensionar(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.textura.release()
        self._crear_textura()

        if self.textura_ui is not None:
            self.textura_ui.release()
            self.textura_ui = None

    def _crear_textura(self):
        self.textura = self.ctx.texture((self.ancho, self.alto), 4)

    # ------------------------------------------------------------------

    def renderizar(self, captura, tiempo): #Renderizo 
        if "u_resolution" in self.prog:
            self.prog["u_resolution"].value = (
                self.ancho,
                self.alto
            )

        if "u_time" in self.prog:
            self.prog["u_time"].value = tiempo

        alto_real = captura.shape[0]
        ancho_real = captura.shape[1]

        if (ancho_real, alto_real) != self.textura.size:
            self.redimensionar(ancho_real, alto_real)

        self.textura.write(captura.tobytes())

        self.textura.use(0)

        if "u_screen_texture" in self.prog:
            self.prog["u_screen_texture"].value = 0

        self.ctx.clear()
        self.vao.render()

    def dibujar_ui(self, superficie_pygame):
        """
        Convierte una Surface de pygame en textura y la pinta encima de lo
        que ya haya dibujado, respetando la transparencia.

        pygame.image.tostring(..., flipped=True) es necesario porque
        pygame cuenta las filas desde arriba y OpenGL desde abajo.
        """
        ancho, alto = superficie_pygame.get_size()
        datos = pygame.image.tobytes(superficie_pygame, "RGBA", True)

        if self.textura_ui is None or self.textura_ui.size != (ancho, alto):
            if self.textura_ui is not None:
                self.textura_ui.release()
            self.textura_ui = self.ctx.texture((ancho, alto), 4)

        self.textura_ui.write(datos.tobytes())
        self.textura_ui.use(location=0)
        self.prog_ui['u_ui'].value = 0

        # Mezcla alfa: lo transparente del panel deja ver el shader de debajo
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.vao_ui.render()
        self.ctx.disable(moderngl.BLEND)