#UI
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLayout, QHBoxLayout, QWidget, QVBoxLayout, QListWidget, QMenu, QLabel
from PySide6.QtCore import Qt

import config

from pathlib import Path

aplicacion = QApplication()


class Ventana_base(QMainWindow):

    def __init__(self):
        super().__init__()

        self.proceso_shader = None

        self.setWindowTitle("Visualizador de shaders")

        # ------- LAYOUT Y MENÚ -------

        layoutHoriz = QHBoxLayout()
        layoutDch = QVBoxLayout()
        layoutIzq = QVBoxLayout()

        menu = self.menuBar()
        menu_archivos = menu.addMenu("Archivos")
        menu_ayuda = menu.addMenu("Ayuda")

        # ------- BOTONES Y WIDGETS -------

        self.botonEjecutar = QPushButton("Ejecutar")
        self.botonEjecutar.clicked.connect(self.ejecutar_shader)
        layoutIzq.addWidget(self.botonEjecutar)

        self.labelCentral = QLabel("Escuchimizar")

        self.listaShaders = QListWidget()
        self.listaShaders.addItems(self.buscar_shaders())
        layoutDch.addWidget(self.listaShaders)

        # ------- CONTENEDOR Y PREPARAR LAYOUTS -------

        layoutHoriz.addLayout(layoutIzq)
        layoutHoriz.addWidget(self.labelCentral)
        layoutHoriz.addLayout(layoutDch)
        contenedor = QWidget()
        contenedor.setLayout(layoutHoriz)


        self.setCentralWidget(contenedor)

    def buscar_shaders(self):
        shaders = []

        ruta_shaders = Path(config.CARPETA_SHADERS)
        for archivo in ruta_shaders.glob('**/*.glsl'):
            shaders.append(str(archivo))

        return shaders

    def ejecutar_shader(self):
        shaderActual = self.listaShaders.currentItem()

        if not shaderActual:
            print("Nah primero selecciona uno")
            return

        ruta_glsl = shaderActual.text()
        print(f"preparando para ejecutar {ruta_glsl}")

        import sys #Lanzo main en un proceso independiente
        import subprocess
        import os

        ruta_base = os.path.dirname(os.path.abspath(config.__file__))
        ruta_main_real = os.path.join(ruta_base, "main.py")

        if self.proceso_shader is not None and self.proceso_shader.poll() is None:
            self.proceso_shader.terminate()   # mata el anterior si seguía vivo

        self.proceso_shader = subprocess.Popen([sys.executable, ruta_main_real, ruta_glsl])

    def closeEvent(self, evento):
        if self.proceso_shader is not None and self.proceso_shader.poll() is None:
            self.proceso_shader.terminate()
        evento.accept()
        
ventana = Ventana_base()

ventana.show()
aplicacion.exec()