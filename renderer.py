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

    def _crear_textura(self):
        self.textura = self.ctx.texture((self.ancho, self.alto), 4)

    # ------------------------------------------------------------------

    def renderizar(self, captura, tiempo): #Renderizo 
        if self.prog == None: #Blindo
            return

        if "u_resolution" in self.prog:
            self.prog["u_resolution"] = (
                self.ancho,
                self.alto
            )

        if "u_time" in self.prog:
            self.prog["u_time"] = tiempo

        self.textura.write(captura.tobytes())

        self.textura.use(0)

        if "u_screen_texture" in self.prog:
            self.prog["u_screen_texture"] = 0

        self.ctx.clear()
        self.vao.render()
