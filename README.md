Un visualizador de shaders en tiempo real para ponerle filtros a la pantalla.

Utiliza Dxcam para capturar la pantalla mediante la CPU, y la envía con Ctypes a un código que utiliza ModernGl para aplicarle el shader seleccionado. Además cuenta con una GUI hecha con PySide6.

Cuenta con una carpeta de shaders por defecto con varios efectos. Nota: Los shaders utilizan los colores BGRA.

A añadir en el futuro:
- Optimizar el rendimiento lo máximo posible.
- La posibilidad de editar los shaders en la interfaz y verlos en tiempo real sobre una imagen.

Actualizaciones:

  versión 0.1(Lanzamiento):
    - Resuelto un problema que gastaba mucha CPU para cambiar el color de la pantalla de BGRA a RGBA. Ahora simplemente no ocurre ese cambio. BGRA es el formato nativo de Dxcam.
    - Mejorado el rendimiento de la CPU al usar Dxcam en lugar de Mss como hacía previamente.
    - Creada la GUI
