from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QScreen, QGuiApplication
import os

class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proyección")
        
        # Configurar ventana sin bordes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Label para mostrar la imagen
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Detectar monitores
        screens = QGuiApplication.screens()
        
        if len(screens) > 1:
            # Usar monitor secundario en fullscreen
            screen_geometry = screens[1].geometry()
            self.setGeometry(screen_geometry)
            self.showFullScreen()
        else:
            # Usar ventana 800x600 en monitor principal
            self.resize(800, 600)
            self.setStyleSheet("background-color: black;")
    
    def show_image(self, image_path):
        if not os.path.exists(image_path):
            return
            
        pixmap = QPixmap(image_path)
        
        # Ajustar imagen al tamaño de la ventana
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setGeometry(0, 0, self.width(), self.height()) 