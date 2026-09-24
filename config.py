import os



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
CARPETA_SHADERS = os.path.join(BASE_DIR, "Shaders")
ruta_shader = os.path.join(CARPETA_SHADERS, "Kuwahara.glsl")
 
FPS = 60
 
# Flag de SetWindowDisplayAffinity para excluir la ventana de las capturas.
WDA_EXCLUDEFROMCAPTURE = 0x00000011