"""
Constantes de configuración del proyecto.
"""
import os

 
ANCHO_INICIAL = 800
ALTO_INICIAL = 300
ESCALA_ZOOM = 20        # cuánto crece/decrece la ventana con la rueda
ANCHO_MINIMO = 300

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
CARPETA_SHADERS = os.path.join(BASE_DIR, "Shaders")
RUTA_SHADER = os.path.join(CARPETA_SHADERS, "Kuwahara.glsl")
 
FPS = 60
 
# Flag de SetWindowDisplayAffinity para excluir la ventana de las capturas.
WDA_EXCLUDEFROMCAPTURE = 0x00000011