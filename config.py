"""
Constantes de configuración del proyecto.
"""
 
ANCHO_INICIAL = 800
ALTO_INICIAL = 300
ESCALA_ZOOM = 20        # cuánto crece/decrece la ventana con la rueda
ANCHO_MINIMO = 300
 
CARPETA_SHADERS = "Shaders"
RUTA_SHADER = "Shaders/Kuwahara.glsl"
 
FPS = 60
 
# Flag de SetWindowDisplayAffinity para excluir la ventana de las capturas.
WDA_EXCLUDEFROMCAPTURE = 0x00000011