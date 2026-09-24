"""
Todo lo relacionado con la API nativa de Windows (ctypes) vive aquí:
- Poner la ventana "siempre al frente" (topmost).
- Hacer la ventana "click-through" (que ignore el ratón).
- Ocultar la ventana de capturas de pantalla/grabaciones.
- Leer la posición absoluta del ratón (para poder arrastrar la ventana).
"""

import ctypes
from ctypes import wintypes

from config import WDA_EXCLUDEFROMCAPTURE

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attrib", ctypes.c_int),
                ("pvData", ctypes.c_void_p),
                ("cbData", ctypes.c_size_t),
            ]

class VentanaNativa():

    # --- Constantes de SetWindowPos ---
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    SWP_FRAMECHANGED = 0x0020

    # --- Constantes de estilos extendidos ---
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TRANSPARENT = 0x00000020   # <-- esta es la que hace que ignore el ratón
    LWA_ALPHA = 0x00000002

    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    def obtener_resolucion_pantalla(self):
        ancho = self._user32.GetSystemMetrics(self.SM_CXSCREEN)
        alto = self._user32.GetSystemMetrics(self.SM_CYSCREEN)
        return ancho, alto

    def __init__(self, hwnd):
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._declarar_tipos()

        self.hwnd = hwnd
        self.bloqueada = False
        self.click_through = False
        self.aplicar_display_affinity()

    def _declarar_tipos(self):
        """
        Declara explícitamente los tipos de cada función de user32.dll.
        Sin esto, en Python de 64 bits los HWND especiales como
        HWND_TOPMOST (-1) se corrompen y las llamadas fallan en silencio.
        """
        u = self._user32

        u.SetWindowPos.restype = wintypes.BOOL
        u.SetWindowPos.argtypes = [
            wintypes.HWND, wintypes.HWND,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.UINT,
        ]

        u.GetSystemMetrics.restype = ctypes.c_int
        u.GetSystemMetrics.argtypes = [ctypes.c_int]

        u.GetCursorPos.restype = wintypes.BOOL
        u.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]

        u.SetWindowDisplayAffinity.restype = wintypes.BOOL
        u.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]

        # En Python de 64 bits hay que usar las versiones "Ptr". En 32 bits
        # esas no existen, así que caemos a las normales.
        self._get_long = getattr(u, "GetWindowLongPtrW", u.GetWindowLongW)
        self._set_long = getattr(u, "SetWindowLongPtrW", u.SetWindowLongW)

        self._get_long.restype = ctypes.c_longlong
        self._get_long.argtypes = [wintypes.HWND, ctypes.c_int]

        self._set_long.restype = ctypes.c_longlong
        self._set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

        u.SetLayeredWindowAttributes.restype = wintypes.BOOL
        u.SetLayeredWindowAttributes.argtypes = [
            wintypes.HWND, wintypes.COLORREF, ctypes.c_ubyte, wintypes.DWORD
        ]
        u.SystemParametersInfoW.restype = wintypes.BOOL
        u.SystemParametersInfoW.argtypes = [
            wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT
        ]

    # ------------------------------------------------------------------
    # Gestión del HWND
    # ------------------------------------------------------------------

    def actualizar_hwnd(self, nuevo_hwnd):
        """
        Llama a esto cada vez que pygame.display.set_mode() te dé un HWND
        nuevo (al redimensionar). Reaplica todos los estados activos.
        """
        self.hwnd = nuevo_hwnd
        self.aplicar_display_affinity()
        if self.bloqueada:
            self.aplicar_frente(True)
        if self.click_through:
            self.establecer_click_through(True)

        self.excluir_de_duplicacion()

    def aplicar_display_affinity(self):
        self._user32.SetWindowDisplayAffinity(
            wintypes.HWND(self.hwnd), WDA_EXCLUDEFROMCAPTURE
        )
        self.excluir_de_duplicacion()

    # ------------------------------------------------------------------
    # Siempre al frente
    # ------------------------------------------------------------------

    def alternar_bloqueo(self):
        """Cambia entre 'siempre al frente' y normal. Devuelve el nuevo estado."""
        self.bloqueada = not self.bloqueada
        self.aplicar_frente(self.bloqueada)
        return self.bloqueada

    def aplicar_frente(self, bloquear):
        if not self.hwnd:
            return
        try:
            HWND_TOPMOST = wintypes.HWND(-1)
            HWND_NOTOPMOST = wintypes.HWND(-2)

            z_order = HWND_TOPMOST if bloquear else HWND_NOTOPMOST

            ok = self._user32.SetWindowPos(
                wintypes.HWND(self.hwnd), z_order, 0, 0, 0, 0,
                self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE
            )
            if not ok:
                print(f"SetWindowPos falló. Código de error: {ctypes.get_last_error()}")
        except Exception as e:
            print(f"Error nativo al fijar ventana: {e}")

    # ------------------------------------------------------------------
    # Click-through (la ventana ignora el ratón)
    # ------------------------------------------------------------------

    def establecer_click_through(self, activar):
        """
        Hace que los clics "atraviesen" la ventana y lleguen a lo que hay
        debajo. La clave es el estilo extendido WS_EX_TRANSPARENT.

        WS_EX_LAYERED es obligatorio para que WS_EX_TRANSPARENT funcione de
        verdad. Y al activar LAYERED, Windows deja la ventana invisible
        hasta que le dices su opacidad, por eso llamamos después a
        SetLayeredWindowAttributes con alpha=255 (totalmente opaca).
        """
        if not self.hwnd:
            return

        hwnd = wintypes.HWND(self.hwnd)
        estilo = self._get_long(hwnd, self.GWL_EXSTYLE)

        if activar:
            estilo |= self.WS_EX_LAYERED | self.WS_EX_TRANSPARENT | self.WS_EX_NOACTIVATE
        else:
            estilo &= ~self.WS_EX_TRANSPARENT
            estilo &= ~self.WS_EX_NOACTIVATE   # quitamos solo TRANSPARENT

        self._set_long(hwnd, self.GWL_EXSTYLE, estilo)

        if activar:
            self._user32.SetLayeredWindowAttributes(hwnd, 0, 255, self.LWA_ALPHA)

        self.click_through = activar

    # ------------------------------------------------------------------
    # Ratón
    # ------------------------------------------------------------------

    def obtener_mouse_absoluto(self):
        pt = wintypes.POINT()
        self._user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    WCA_EXCLUDED_FROM_DDA = 24
        
    def excluir_de_duplicacion(self):
        valor = ctypes.c_int(1)  # BOOL: TRUE
        datos = WINDOWCOMPOSITIONATTRIBDATA(
            Attrib=self.WCA_EXCLUDED_FROM_DDA,
            pvData=ctypes.cast(ctypes.byref(valor), ctypes.c_void_p),
            cbData=ctypes.sizeof(valor),
        )
        self._user32.SetWindowCompositionAttribute(wintypes.HWND(self.hwnd), ctypes.byref(datos))

    SPI_GETWORKAREA = 0x0030

    def obtener_area_trabajo(self):
        rect = wintypes.RECT()
        self._user32.SystemParametersInfoW(
            self.SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
        )
        ancho = rect.right - rect.left
        alto = rect.bottom - rect.top
        return rect.left, rect.top, ancho, alto