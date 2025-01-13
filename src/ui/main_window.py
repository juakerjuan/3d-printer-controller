from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QComboBox, QMessageBox, QLabel, 
                            QGroupBox, QSpinBox, QDoubleSpinBox, QFileDialog,
                            QFormLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from pymata4 import pymata4
import serial.tools.list_ports
import os
import time
from datetime import datetime
from .projection_window import ProjectionWindow
from .languages import TRANSLATIONS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inicializar idioma
        self.current_language = "Español"
        self.translations = TRANSLATIONS[self.current_language]
        
        self.setWindowTitle(self.translations["window_title"])
        self.board = None
        self.selected_folder = None
        self.setMinimumSize(1000, 700)
        
        # Agregar selector de idioma
        self.language_selector = QComboBox()
        self.language_selector.addItems([
            "Español", "English", "Русский", "Deutsch", 
            "Français", "中文", "हिंदी", "日本語", 
            "한국어", "Português"
        ])
        self.language_selector.currentTextChanged.connect(self.change_language)
        
        # Widget y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Layout para el selector de idioma
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("Idioma:"))
        language_layout.addWidget(self.language_selector)
        language_layout.addStretch()
        main_layout.addLayout(language_layout)
        
        # Layout para los paneles principales
        panels_layout = QHBoxLayout()
        main_layout.addLayout(panels_layout)
        
        # Panel izquierdo - Conexión y estado
        left_panel = QGroupBox(self.translations["connection"])
        left_panel.setObjectName("connection")
        left_layout = QVBoxLayout()
        
        self.status_label = QLabel("Estado: Desconectado")
        self.port_selector = QComboBox()
        self.refresh_ports()
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_arduino)
        
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(QLabel("Puerto:"))
        left_layout.addWidget(self.port_selector)
        left_layout.addWidget(self.connect_button)
        
        # Agregar sección de Ajustes CNC
        cnc_group = QGroupBox(self.translations["cnc_settings"])
        cnc_group.setObjectName("cnc_settings")
        cnc_layout = QFormLayout()
        
        # Pasos por milímetro
        self.steps_per_mm = QDoubleSpinBox()
        self.steps_per_mm.setRange(1, 1000)
        self.steps_per_mm.setValue(80)  # Valor típico para muchos motores
        self.steps_per_mm.setSuffix(" pasos/mm")
        
        # Pines Arduino
        self.pin_step = QSpinBox()
        self.pin_step.setRange(2, 13)
        self.pin_step.setValue(2)
        
        self.pin_dir = QSpinBox()
        self.pin_dir.setRange(2, 13)
        self.pin_dir.setValue(3)
        
        self.pin_home = QSpinBox()
        self.pin_home.setRange(2, 13)
        self.pin_home.setValue(4)
        
        self.pin_end = QSpinBox()
        self.pin_end.setRange(2, 13)
        self.pin_end.setValue(5)
        
        self.pin_uv = QSpinBox()
        self.pin_uv.setRange(2, 13)
        self.pin_uv.setValue(6)
        
        # Agregar campos al layout CNC
        cnc_layout.addRow("Pasos por mm:", self.steps_per_mm)
        cnc_layout.addRow("Pin STEP:", self.pin_step)
        cnc_layout.addRow("Pin DIR:", self.pin_dir)
        cnc_layout.addRow("Pin HOME:", self.pin_home)
        cnc_layout.addRow("Pin END:", self.pin_end)
        cnc_layout.addRow("Pin UV:", self.pin_uv)
        
        cnc_group.setLayout(cnc_layout)
        left_layout.addWidget(cnc_group)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Panel central - Controles de Impresión
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 1. Sección de Controles CNC
        cnc_control_group = QGroupBox(self.translations["cnc_controls"])
        cnc_control_group.setObjectName("cnc_controls")
        cnc_control_layout = QVBoxLayout()
        
        # Control de distancia
        distance_layout = QHBoxLayout()
        distance_layout.addWidget(QLabel("Distancia a mover:"))
        self.distance_control = QDoubleSpinBox()
        self.distance_control.setRange(0.1, 50)
        self.distance_control.setValue(1.0)
        self.distance_control.setSingleStep(0.1)
        self.distance_control.setSuffix(" mm")
        distance_layout.addWidget(self.distance_control)
        distance_layout.addStretch()
        
        # Botones de control Z
        z_buttons_layout = QHBoxLayout()
        self.btn_z_up = QPushButton("⬆ Subir Z")
        self.btn_z_down = QPushButton("⬇ Bajar Z")
        self.btn_z_home = QPushButton("🏠 Home")
        self.btn_z_end = QPushButton("⏫ Final")
        self.btn_stop = QPushButton("⏹ STOP")
        self.btn_uv = QPushButton("💡 UV")
        
        # Estilo para el botón de stop
        self.btn_stop.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        
        # Conectar señales
        self.btn_z_up.clicked.connect(lambda: self.move_z("up"))
        self.btn_z_down.clicked.connect(lambda: self.move_z("down"))
        self.btn_z_home.clicked.connect(self.go_home)
        self.btn_z_end.clicked.connect(self.go_end)
        self.btn_stop.clicked.connect(self.emergency_stop)
        self.btn_uv.clicked.connect(self.toggle_uv)
        
        # UV LED estado
        self.uv_state = False
        
        # Agregar botones al layout
        z_buttons_layout.addWidget(self.btn_z_up)
        z_buttons_layout.addWidget(self.btn_z_down)
        z_buttons_layout.addWidget(self.btn_z_home)
        z_buttons_layout.addWidget(self.btn_z_end)
        
        # Layout para Stop y UV
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.addWidget(self.btn_stop)
        control_buttons_layout.addWidget(self.btn_uv)
        
        # Agregar todos los controles al grupo CNC
        cnc_control_layout.addLayout(distance_layout)
        cnc_control_layout.addLayout(z_buttons_layout)
        cnc_control_layout.addLayout(control_buttons_layout)
        cnc_control_group.setLayout(cnc_control_layout)
        
        # 2. Sección de Parámetros de Impresión
        print_params_group = QGroupBox(self.translations["print_params"])
        print_params_group.setObjectName("print_params")
        self.print_params_layout = QFormLayout()
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No se ha seleccionado carpeta")
        self.folder_button = QPushButton("Seleccionar Carpeta")
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        
        # Parámetros de impresión
        self.layer_height = QDoubleSpinBox()
        self.layer_height.setRange(0.01, 0.2)
        self.layer_height.setSingleStep(0.01)
        self.layer_height.setValue(0.05)
        self.layer_height.setSuffix(" mm")
        
        self.primary_layers = QSpinBox()
        self.primary_layers.setRange(1, 10)
        self.primary_layers.setValue(3)
        
        self.primary_time = QDoubleSpinBox()
        self.primary_time.setRange(1, 120)
        self.primary_time.setValue(30)
        self.primary_time.setSuffix(" s")
        
        self.normal_time = QDoubleSpinBox()
        self.normal_time.setRange(1, 60)
        self.normal_time.setValue(8)
        self.normal_time.setSuffix(" s")
        
        self.lift_distance = QDoubleSpinBox()
        self.lift_distance.setRange(1, 50)
        self.lift_distance.setValue(30)
        self.lift_distance.setSuffix(" mm")
        
        # Agregar widgets al layout de parámetros
        self.print_params_layout.addRow("Carpeta de slices:", QWidget())
        self.print_params_layout.addRow(folder_layout)
        self.print_params_layout.addRow("Altura de capa:", self.layer_height)
        self.print_params_layout.addRow("Número de capas primarias:", self.primary_layers)
        self.print_params_layout.addRow("Tiempo capas primarias:", self.primary_time)
        self.print_params_layout.addRow("Tiempo capas normales:", self.normal_time)
        self.print_params_layout.addRow("Distancia de elevación:", self.lift_distance)
        
        # Botón de inicio
        self.start_button = QPushButton("Iniciar Impresión")
        self.start_button.setEnabled(False)
        self.print_params_layout.addRow(self.start_button)
        
        print_params_group.setLayout(self.print_params_layout)
        
        # Agregar ambos grupos al layout central
        center_layout.addWidget(cnc_control_group)
        center_layout.addWidget(print_params_group)
        
        # Panel derecho - Estado de Impresión
        right_panel = QGroupBox(self.translations["print_status"])
        right_panel.setObjectName("print_status")
        right_layout = QVBoxLayout()
        
        # Estado de impresión
        self.current_layer_label = QLabel("Capa actual: -")
        self.remaining_layers_label = QLabel("Capas restantes: -")
        self.elapsed_time_label = QLabel("Tiempo transcurrido: 00:00:00")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        
        right_layout.addWidget(self.current_layer_label)
        right_layout.addWidget(self.remaining_layers_label)
        right_layout.addWidget(self.elapsed_time_label)
        right_layout.addWidget(self.progress_bar)
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        
        # Variables de impresión
        self.projection_window = None
        self.print_timer = QTimer()
        self.print_timer.timeout.connect(self.update_elapsed_time)
        self.start_time = None
        self.current_layer = 0
        self.total_layers = 0
        self.is_printing = False
        
        # Conectar botón de inicio
        self.start_button.clicked.connect(self.start_print)
        
        # Agregar paneles al layout principal
        panels_layout.addWidget(left_panel, 1)
        panels_layout.addWidget(center_panel, 2)
        panels_layout.addWidget(right_panel, 1)

        # Agregar variables de estado para los límites
        self.home_limit_active = False
        self.end_limit_active = False

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Slices",
            ""
        )
        if folder:
            self.selected_folder = folder
            folder_name = os.path.basename(folder)
            self.folder_label.setText(f"Carpeta: {folder_name}")
            
            # Obtener solo archivos de imagen
            all_files = os.listdir(folder)
            image_files = []
            
            # Filtrar solo archivos de imagen y extraer números
            for file in all_files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        # Extraer número del nombre del archivo
                        num = int(''.join(filter(str.isdigit, file)))
                        image_files.append((num, file))
                    except ValueError:
                        continue
            
            # Ordenar por número y verificar secuencia
            image_files.sort(key=lambda x: x[0])
            valid_sequence = []
            
            # Verificar que la secuencia empiece en 1 y sea continua
            if image_files and image_files[0][0] == 1:
                valid_sequence.append(image_files[0][1])
                expected_num = 2
                
                for num, file in image_files[1:]:
                    if num == expected_num:
                        valid_sequence.append(file)
                        expected_num += 1
                    else:
                        break
            
            if valid_sequence:
                self.start_button.setEnabled(True)
                self.status_label.setText(f"Estado: {len(valid_sequence)} slices en secuencia")
            else:
                self.start_button.setEnabled(False)
                self.status_label.setText("Error: No se encontró secuencia válida de imágenes")

    def refresh_ports(self):
        self.port_selector.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_selector.addItems(ports)

    def connect_arduino(self):
        try:
            port = self.port_selector.currentText()
            self.status_label.setText("Estado: Conectando...")
            self.board = pymata4.Pymata4(arduino_instance_id=1, com_port=port)
            
            # Guardar los valores de configuración CNC
            self.saved_steps_per_mm = self.steps_per_mm.value()
            self.saved_pin_step = self.pin_step.value()
            self.saved_pin_dir = self.pin_dir.value()
            self.saved_pin_home = self.pin_home.value()
            self.saved_pin_end = self.pin_end.value()
            self.saved_pin_uv = self.pin_uv.value()
            
            # Configurar pines
            self.board.set_pin_mode_digital_output(self.saved_pin_step)
            self.board.set_pin_mode_digital_output(self.saved_pin_dir)
            # Configurar pines de sensores con pull-up
            self.board.set_pin_mode_digital_input_pullup(self.saved_pin_home)
            self.board.set_pin_mode_digital_input_pullup(self.saved_pin_end)
            self.board.set_pin_mode_digital_output(self.saved_pin_uv)
            
            # Deshabilitar ajustes CNC
            self.steps_per_mm.setEnabled(False)
            self.pin_step.setEnabled(False)
            self.pin_dir.setEnabled(False)
            self.pin_home.setEnabled(False)
            self.pin_end.setEnabled(False)
            self.pin_uv.setEnabled(False)
            
            self.status_label.setText("Estado: Conectado")
            self.connect_button.setEnabled(False)
            
        except Exception as e:
            self.status_label.setText("Estado: Error de conexión")
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")
            print(f"Error al conectar: {e}")

    def closeEvent(self, event):
        if self.board:
            try:
                self.board.shutdown()
            except:
                pass
        super().closeEvent(event)

    def move_z(self, direction):
        if not self.board:
            return
            
        try:
            distance_mm = self.distance_control.value()
            steps = int(distance_mm * self.saved_steps_per_mm)
            
            # Verificar sensor según dirección
            if direction == "up":
                # Si el sensor END está presionado, no permite subir
                if self.board.digital_read(self.saved_pin_end)[0] == 0:
                    print("No se puede subir más")
                    return
                self.board.digital_write(self.saved_pin_dir, 1)
            else:
                # Si el sensor HOME está presionado, no permite bajar
                if self.board.digital_read(self.saved_pin_home)[0] == 0:
                    print("No se puede bajar más")
                    return
                self.board.digital_write(self.saved_pin_dir, 0)
                    
            # Generar pulsos para los pasos
            for step in range(steps):
                # Verificar sensor durante el movimiento
                if step % 10 == 0:
                    if direction == "up" and self.board.digital_read(self.saved_pin_end)[0] == 0:
                        print("Límite superior alcanzado")
                        break
                    if direction == "down" and self.board.digital_read(self.saved_pin_home)[0] == 0:
                        print("Límite inferior alcanzado")
                        break
                    
                self.board.digital_write(self.saved_pin_step, 1)
                time.sleep(0.0001)
                self.board.digital_write(self.saved_pin_step, 0)
                time.sleep(0.0001)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al mover eje Z: {str(e)}")

    def go_home(self):
        if not self.board:
            return
        try:
            # Si ya está presionado el sensor HOME, no hace nada
            if self.board.digital_read(self.saved_pin_home)[0] == 0:
                print("Ya está en home")
                return
                
            self.board.digital_write(self.saved_pin_dir, 0)
            
            while True:
                if self.board.digital_read(self.saved_pin_home)[0] == 0:
                    print("Home encontrado")
                    break
                
                self.board.digital_write(self.saved_pin_step, 1)
                time.sleep(0.0001)
                self.board.digital_write(self.saved_pin_step, 0)
                time.sleep(0.0001)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al buscar home: {str(e)}")

    def go_end(self):
        if not self.board:
            return
        try:
            # Si ya está presionado el sensor END, no hace nada
            if self.board.digital_read(self.saved_pin_end)[0] == 0:
                print("Ya está en final")
                return
                
            self.board.digital_write(self.saved_pin_dir, 1)
            
            while True:
                if self.board.digital_read(self.saved_pin_end)[0] == 0:
                    print("Final encontrado")
                    break
                
                self.board.digital_write(self.saved_pin_step, 1)
                time.sleep(0.0001)
                self.board.digital_write(self.saved_pin_step, 0)
                time.sleep(0.0001)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al buscar final: {str(e)}")

    def emergency_stop(self):
        if not self.board:
            return
        try:
            # Detener todos los movimientos
            # Apagar UV
            self.uv_state = False
            self.btn_uv.setStyleSheet("")
            self.board.digital_write(self.saved_pin_uv, 0)
            print("Movimiento detenido")
            
        except Exception as e:
            print(f"Error al detener: {str(e)}")

    def toggle_uv(self):
        if not self.board:
            return
        try:
            self.uv_state = not self.uv_state
            self.board.digital_write(self.saved_pin_uv, 1 if self.uv_state else 0)
            # Cambiar estilo del botón según estado
            self.btn_uv.setStyleSheet(
                "background-color: #44ff44;" if self.uv_state else ""
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al controlar UV: {str(e)}")

    def start_print(self):
        if not self.validate_print_settings():
            return
            
        try:
            # Deshabilitar controles
            self.disable_controls()
            
            # Habilitar botón cancelar
            self.cancel_button = QPushButton("Cancelar Impresión")
            self.cancel_button.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
            self.cancel_button.clicked.connect(self.cancel_print)
            self.print_params_layout.addRow(self.cancel_button)
            
            # Resto del código de inicio de impresión...
            self.is_printing = True
            self.current_layer = 0
            self.start_time = datetime.now()
            
            # Obtener lista de imágenes en secuencia
            all_files = os.listdir(self.selected_folder)
            image_files = []
            
            for file in all_files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        num = int(''.join(filter(str.isdigit, file)))
                        image_files.append((num, file))
                    except ValueError:
                        continue
            
            # Ordenar y verificar secuencia
            image_files.sort(key=lambda x: x[0])
            self.image_files = []
            
            if image_files and image_files[0][0] == 1:
                self.image_files.append(image_files[0][1])
                expected_num = 2
                
                for num, file in image_files[1:]:
                    if num == expected_num:
                        self.image_files.append(file)
                        expected_num += 1
                    else:
                        break
            
            self.total_layers = len(self.image_files)
            
            if self.total_layers == 0:
                raise Exception("No se encontró secuencia válida de imágenes")
            
            # Crear ventana de proyección
            self.projection_window = ProjectionWindow()
            self.projection_window.show()
            
            # Ir a home
            self.go_home()
            
            # Iniciar timer
            self.print_timer.start(1000)  # Actualizar cada segundo
            
            # Iniciar proceso de impresión
            self.process_next_layer()
            
        except Exception as e:
            self.enable_controls()
            QMessageBox.critical(self, "Error", f"Error al iniciar impresión: {str(e)}")
            self.stop_print()
    
    def process_next_layer(self):
        if not self.is_printing or self.current_layer >= self.total_layers:
            self.finish_print()
            return
            
        try:
            # Mostrar imagen actual
            image_path = os.path.join(self.selected_folder, self.image_files[self.current_layer])
            self.projection_window.show_image(image_path)
            
            # Actualizar estado
            self.current_layer_label.setText(f"Capa actual: {self.current_layer + 1}")
            self.remaining_layers_label.setText(f"Capas restantes: {self.total_layers - self.current_layer - 1}")
            self.progress_bar.setValue(int((self.current_layer + 1) * 100 / self.total_layers))
            
            # Encender UV
            self.board.digital_write(self.saved_pin_uv, 1)
            
            # Determinar tiempo de exposición
            if self.current_layer < self.primary_layers.value():
                exposure_time = int(self.primary_time.value() * 1000)  # convertir a ms entero
            else:
                exposure_time = int(self.normal_time.value() * 1000)  # convertir a ms entero
            
            # Programar siguiente paso
            QTimer.singleShot(exposure_time, self.after_exposure)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en capa {self.current_layer + 1}: {str(e)}")
            self.stop_print()
    
    def after_exposure(self):
        # Apagar UV
        self.board.digital_write(self.saved_pin_uv, 0)
        
        # Subir plataforma
        self.move_z_distance(self.lift_distance.value())
        
        # Bajar plataforma menos el ancho de capa
        down_distance = self.lift_distance.value() - self.layer_height.value()
        self.move_z_distance(-down_distance)
        
        # Siguiente capa
        self.current_layer += 1
        self.process_next_layer()
    
    def move_z_distance(self, distance):
        steps = int(abs(distance) * self.saved_steps_per_mm)
        direction = 1 if distance > 0 else 0
        
        self.board.digital_write(self.saved_pin_dir, direction)
        
        for _ in range(steps):
            self.board.digital_write(self.saved_pin_step, 1)
            time.sleep(0.0001)
            self.board.digital_write(self.saved_pin_step, 0)
            time.sleep(0.0001)
    
    def finish_print(self):
        # Ir a posición final
        self.go_end()
        
        # Limpiar
        self.is_printing = False
        self.print_timer.stop()
        if self.projection_window:
            self.projection_window.close()
            self.projection_window = None
        
        QMessageBox.information(self, "Impresión Completada", 
                              "El proceso de impresión ha finalizado correctamente.")
    
    def stop_print(self):
        self.is_printing = False
        self.print_timer.stop()
        self.board.digital_write(self.saved_pin_uv, 0)
        if self.projection_window:
            self.projection_window.close()
            self.projection_window = None
    
    def update_elapsed_time(self):
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.elapsed_time_label.setText(
                f"Tiempo transcurrido: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
    
    def validate_print_settings(self):
        if not self.selected_folder:
            QMessageBox.warning(self, "Error", "Seleccione una carpeta de imágenes")
            return False
            
        if not self.board:
            QMessageBox.warning(self, "Error", "Conecte el Arduino primero")
            return False
            
        return True

    def disable_controls(self):
        # Deshabilitar controles CNC
        self.btn_z_up.setEnabled(False)
        self.btn_z_down.setEnabled(False)
        self.btn_z_home.setEnabled(False)
        self.btn_z_end.setEnabled(False)
        self.btn_uv.setEnabled(False)
        self.distance_control.setEnabled(False)
        
        # Deshabilitar ajustes de impresión
        self.layer_height.setEnabled(False)
        self.primary_layers.setEnabled(False)
        self.primary_time.setEnabled(False)
        self.normal_time.setEnabled(False)
        self.lift_distance.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.start_button.setEnabled(False)

    def enable_controls(self):
        # Habilitar controles CNC
        self.btn_z_up.setEnabled(True)
        self.btn_z_down.setEnabled(True)
        self.btn_z_home.setEnabled(True)
        self.btn_z_end.setEnabled(True)
        self.btn_uv.setEnabled(True)
        self.distance_control.setEnabled(True)
        
        # Habilitar ajustes de impresión
        self.layer_height.setEnabled(True)
        self.primary_layers.setEnabled(True)
        self.primary_time.setEnabled(True)
        self.normal_time.setEnabled(True)
        self.lift_distance.setEnabled(True)
        self.folder_button.setEnabled(True)
        self.start_button.setEnabled(True)
        
        # Remover botón cancelar si existe
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setParent(None)
            self.cancel_button = None

    def cancel_print(self):
        try:
            # Detener el proceso
            self.is_printing = False
            self.print_timer.stop()
            
            # Apagar UV
            self.board.digital_write(self.saved_pin_uv, 0)
            
            # Cerrar ventana de proyección
            if self.projection_window:
                self.projection_window.close()
                self.projection_window = None
            
            # Habilitar controles
            self.enable_controls()
            
            QMessageBox.information(self, "Impresión Cancelada", 
                                  "El proceso de impresión ha sido cancelado")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cancelar: {str(e)}")

    def change_language(self, language):
        self.current_language = language
        self.translations = TRANSLATIONS[language]
        
        # Actualizar título de la ventana
        self.setWindowTitle(self.translations["window_title"])
        
        # Actualizar panel de conexión
        self.status_label.setText(self.translations["status"] + 
            (self.translations["connected"] if self.board else self.translations["disconnected"]))
        self.connect_button.setText(self.translations["connect"])
        
        # Actualizar grupo de ajustes CNC
        self.findChild(QGroupBox, "cnc_settings").setTitle(self.translations["cnc_settings"])
        
        # Actualizar controles CNC
        self.findChild(QGroupBox, "cnc_controls").setTitle(self.translations["cnc_controls"])
        self.btn_z_up.setText(self.translations["up"])
        self.btn_z_down.setText(self.translations["down"])
        self.btn_z_home.setText(self.translations["home"])
        self.btn_z_end.setText(self.translations["end"])
        self.btn_stop.setText(self.translations["stop"])
        self.btn_uv.setText(self.translations["uv_light"])
        
        # Actualizar parámetros de impresión
        self.findChild(QGroupBox, "print_params").setTitle(self.translations["print_params"])
        self.folder_button.setText(self.translations["select_folder"])
        self.start_button.setText(self.translations["start_print"])
        
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setText(self.translations["cancel_print"])
        
        # Actualizar estado de impresión
        self.findChild(QGroupBox, "print_status").setTitle(self.translations["print_status"])
        self.current_layer_label.setText(self.translations["current_layer"] + 
            str(self.current_layer if self.is_printing else "-"))
        self.remaining_layers_label.setText(self.translations["remaining_layers"] + 
            str(self.total_layers - self.current_layer if self.is_printing else "-"))
        
        # Actualizar tiempo transcurrido
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.elapsed_time_label.setText(
                f"{self.translations['elapsed_time']} {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
        else:
            self.elapsed_time_label.setText(f"{self.translations['elapsed_time']} 00:00:00")
        
        # Actualizar etiqueta de carpeta
        if self.selected_folder:
            folder_name = os.path.basename(self.selected_folder)
            self.folder_label.setText(f"{self.translations['select_folder']}: {folder_name}")
        else:
            self.folder_label.setText(self.translations["no_folder"])