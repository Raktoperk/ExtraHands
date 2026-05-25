from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor

from components.functions import press_key, detect_image, check_color
from components.colors import colors
from components.coordinates import builder_coordinate
from components.config_manager import config

import sys
import time
import random
import os
from datetime import datetime

try:
    from components.styles import *
except ImportError:
    # Запасные значения если файл стилей не найден
    from components.styles import (
        COLORS, WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, 
        CHECKBOX_STYLES, COUNTER_WINDOW_STYLES, FRAME_STYLES,
        INPUT_STYLES, GROUPBOX_STYLES
    )

# Получаем абсолютный путь к папке со скриптом
if getattr(sys, 'frozen', False):
    # Если приложение упаковано в exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Если запускаем из исходников
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Импортируем функции после определения BASE_DIR

class CounterWindow(QWidget):
    """Маленькое окно счетчика поверх всех окон"""
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.is_hidden = True  # Изначально скрыт
        self.initUI()
        
        
    def initUI(self):
        # Окно поверх всех, без рамки
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        
        # Прозрачный фон
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основной фрейм с закругленными углами
        main_frame = QFrame(self)
        main_frame.setStyleSheet(COUNTER_WINDOW_STYLES["frame"])
        
        # Горизонтальный layout для текста и счетчика
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Текст
        self.text_label = QLabel("Выполнено действий:")
        self.text_label.setStyleSheet(COUNTER_WINDOW_STYLES["text"])
        layout.addWidget(self.text_label)
        
        # Счетчик
        self.counter_label = QLabel("0")
        self.counter_label.setStyleSheet(COUNTER_WINDOW_STYLES["counter"])
        layout.addWidget(self.counter_label)
        
        # Добавляем растягивающий элемент
        layout.addStretch()
        
        # Устанавливаем layout для основного виджета
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # Устанавливаем фиксированный размер окна
        self.setFixedSize(250, 52)
        
        # Позиционируем в правом верхнем углу
        self.move_to_top_right()
        
    def paintEvent(self, event):
        """Переопределяем paintEvent для рисования закругленных углов"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(43, 43, 43)))
        painter.setPen(Qt.NoPen)
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 8, 8)
        
    def resizeEvent(self, event):
        """Обновляем при изменении размера"""
        super().resizeEvent(event)
        self.update()
        
    def move_to_top_right(self):
        """Помещает окно в правый верхний угол"""
        screen_geometry = QApplication.desktop().availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = 10
        self.move(x, y)
        
    def increment_counter(self):
        """Увеличивает счетчик на 1 (работает даже если окно скрыто)"""
        self.counter += 1
        self.update_counter_display()
        
    def update_counter_display(self):
        """Обновляет отображение счетчика (работает независимо от видимости)"""
        self.counter_label.setText(str(self.counter))
        
    def reset_counter(self):
        """Сбрасывает счетчик"""
        self.counter = 0
        self.update_counter_display()
        
    def mousePressEvent(self, event):
        """Позволяет перемещать окно"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Перемещение окна"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def toggle_visibility(self):
        """Переключает видимость окна"""
        if self.is_hidden:
            self.show()
            self.is_hidden = False
        else:
            self.hide()
            self.is_hidden = True

class LogWindow(QWidget):
    """Окно для отображения логов и ошибок"""
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Окно поверх всех - убираем Qt.Tool и добавляем нужные флаги
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        # Убираем кнопку закрытия
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        # Настройка окна
        self.setWindowTitle("Логи и ошибки стройки")
        self.setFixedSize(700, 400)  # Увеличили размер окна
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Верхняя панель с кнопками управления
        top_panel = QHBoxLayout()
        
        # Кнопка очистки всех логов
        clear_all_btn = QPushButton("Очистить всё")
        clear_all_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
        clear_all_btn.clicked.connect(self.clear_all_logs)
        top_panel.addWidget(clear_all_btn)
        
        # Кнопка очистки только ошибок
        clear_errors_btn = QPushButton("Очистить ошибки")
        clear_errors_btn.setStyleSheet(BUTTON_STYLES["danger_small"])
        clear_errors_btn.clicked.connect(self.clear_errors)
        top_panel.addWidget(clear_errors_btn)
        
        top_panel.addStretch()
        main_layout.addLayout(top_panel)
        
        # Горизонтальный layout для двух текстовых полей
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Левая часть: обычные логи
        log_group = QGroupBox("Логи")
        log_group.setStyleSheet(GROUPBOX_STYLES["standard"])
        
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(INPUT_STYLES["text_edit"])
        log_layout.addWidget(self.log_text)
        
        # Правая часть: ошибки
        error_group = QGroupBox("Ошибки")
        error_group.setStyleSheet(GROUPBOX_STYLES["error"])
        
        error_layout = QVBoxLayout(error_group)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setStyleSheet(INPUT_STYLES["text_edit_error"])
        error_layout.addWidget(self.error_text)
        
        # Распределяем пространство между двумя группами
        content_layout.addWidget(log_group, 1)  # Коэффициент 1
        content_layout.addWidget(error_group, 1)  # Коэффициент 1
        
        main_layout.addLayout(content_layout)
        
        # Панель статистики внизу
        stats_layout = QHBoxLayout()
        
        self.log_count_label = QLabel("Логов: 0")
        self.log_count_label.setStyleSheet(LABEL_STYLES["status"])
        stats_layout.addWidget(self.log_count_label)
        
        self.error_count_label = QLabel("Ошибок: 0")
        self.error_count_label.setStyleSheet(LABEL_STYLES["status_error"])
        stats_layout.addWidget(self.error_count_label)
        
        stats_layout.addStretch()
        
        # Кнопка копирования ошибок в буфер обмена
        copy_errors_btn = QPushButton("Копировать ошибки")
        copy_errors_btn.setStyleSheet(BUTTON_STYLES["primary_small"])
        copy_errors_btn.clicked.connect(self.copy_errors_to_clipboard)
        stats_layout.addWidget(copy_errors_btn)
        
        main_layout.addLayout(stats_layout)
        
        self.setLayout(main_layout)
        
        # Счетчики
        self.log_count = 0
        self.error_count = 0
        
    def add_log(self, message):
        """Добавляет сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Прокручиваем до конца
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
        # Обновляем счетчик
        self.log_count += 1
        self.log_count_label.setText(f"Логов: {self.log_count}")
        
        # Проверяем, является ли сообщение ошибкой
        if any(error_keyword in message.upper() for error_keyword in ['ОШИБКА', 'ERROR', 'EXCEPTION', 'FAIL', 'FAILED', 'КРИТИЧЕСКАЯ', 'WARNING', 'ВНИМАНИЕ']):
            self.add_error(message)
    
    def add_error(self, message):
        """Добавляет сообщение об ошибке в отдельный блок"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_entry = f"[{timestamp}] {message}"
        self.error_text.append(error_entry)
        
        # Прокручиваем до конца
        self.error_text.verticalScrollBar().setValue(
            self.error_text.verticalScrollBar().maximum()
        )
        
        # Обновляем счетчик ошибок
        self.error_count += 1
        self.error_count_label.setText(f"Ошибок: {self.error_count}")
        
    def clear_all_logs(self):
        """Очищает все логи и ошибки"""
        self.log_text.clear()
        self.error_text.clear()
        self.log_count = 0
        self.error_count = 0
        self.log_count_label.setText("Логов: 0")
        self.error_count_label.setText("Ошибок: 0")
        
    def clear_errors(self):
        """Очищает только ошибки"""
        self.error_text.clear()
        self.error_count = 0
        self.error_count_label.setText("Ошибок: 0")
        
    def copy_errors_to_clipboard(self):
        """Копирует все ошибки в буфер обмена"""
        errors = self.error_text.toPlainText()
        if errors:
            clipboard = QApplication.clipboard()
            clipboard.setText(errors)
            
            # Временно меняем текст кнопки для подтверждения
            btn = self.sender()
            if btn:
                original_text = btn.text()
                btn.setText("Скопировано!")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1500, lambda: btn.setText(original_text))

class WorkerThread(QThread):
    action_completed = pyqtSignal()  # Сигнал для завершения действия
    key_detected = pyqtSignal(str)   # Сигнал для обнаружения клавиши
    log_message = pyqtSignal(str)    # Сигнал для записи в лог
    status_updated = pyqtSignal(str) # Сигнал для обновления статуса
    
    def __init__(self, resolution_mode, delay_between_presses, color_tolerance=10):
        super().__init__()
        self.resolution_mode = resolution_mode
        self.delay_between_presses = delay_between_presses
        self.color_tolerance = color_tolerance
        self.running = True
        
        # Получаем координаты из общих модулей
        self.builder_coords = {
            "FullHD": builder_coordinate["FullHD"].get("builder_marker", (765, 496)),
            "QuadHD": builder_coordinate["QuadHD"].get("builder_marker", (1084, 674))
        }
        
        self.target_color = colors.color["light_green"]
        self.detected_key = None  # Запомненная клавиша
        self.action_in_progress = False  # Флаг выполнения действия
        
    def run(self):
        self.log_message.emit("Запуск потока строительства")
        self.status_updated.emit("Ожидание зеленого цвета...")
        
        while self.running:
            # Проверяем наличие зеленого цвета в координатах builder_marker
            if self.check_color_with_tolerance():
                if not self.action_in_progress:
                    # Зеленый цвет появился, начинаем новое действие
                    self.action_in_progress = True
                    self.status_updated.emit("Обнаружен зеленый цвет, определяю клавишу...")
                    self.process_building_action()
            else:
                if self.action_in_progress:
                    # Зеленый цвет пропал - завершаем действие
                    self.action_in_progress = False
                    self.detected_key = None
                    self.action_completed.emit()
                    self.status_updated.emit("Действие завершено, жду новый цвет")
                    self.log_message.emit("Зеленый цвет пропал, действие завершено")
                else:
                    # Ожидаем зеленый цвет
                    self.msleep(50)
                    continue
                
            self.msleep(10)  # Небольшая пауза между проверками
        
        self.log_message.emit("Поток строительства остановлен")
    
    def check_color_with_tolerance(self):
        """Проверяет наличие целевого цвета в заданных координатах с допуском"""
        x, y = self.builder_coords[self.resolution_mode]
        
        try:
            return check_color((x, y), self.target_color, self.color_tolerance)
        except Exception:
            return False
    
    def detect_which_key(self):
        """Определяет, какую клавишу нужно нажимать (E, F или H)"""
        keys_dir = os.path.join(BASE_DIR, 'assets', 'keys')
        image_keys = ['e', 'f', 'h']
        
        for key in image_keys:
            image_path = os.path.join(keys_dir, f'{key}.png')
            
            if not os.path.exists(image_path):
                self.log_message.emit(f"Файл не найден: {image_path}")
                continue
            
            # Ищем изображение на экране
            result = detect_image(image_path, threshold=0.9)
            
            if result is not None:
                self.log_message.emit(f"Обнаружено изображение: {key}.png")
                return key
        
        return None
    
    def process_building_action(self):
        """Обрабатывает действие строительства"""
        # Шаг 1: Определяем клавишу
        if self.detected_key is None:
            self.detected_key = self.detect_which_key()
            
        if self.detected_key is None:
            self.status_updated.emit("Клавиша не определена")
            self.log_message.emit("ОШИБКА: Не удалось определить клавишу для нажатия")
            self.action_in_progress = False
            return
        
        self.key_detected.emit(self.detected_key)
        self.status_updated.emit(f"Нажимаю клавишу: {self.detected_key.upper()}")
        
        # Шаг 2: Нажимаем клавишу пока виден зеленый цвет
        action_start_time = time.time()
        action_timeout = 15  # Максимальное время выполнения одного действия (секунд)
        
        while self.running and self.check_color_with_tolerance():
            # Проверяем не превышено ли время выполнения
            if time.time() - action_start_time > action_timeout:
                self.status_updated.emit("Превышено время выполнения действия")
                self.log_message.emit("ВНИМАНИЕ: Превышено время выполнения действия")
                break
            
            # Нажимаем определенную клавишу
            press_key(self.detected_key, boundary=(0.04, 0.12))
            
            # Задержка с небольшим случайным отклонением
            delay_seconds = self.delay_between_presses / 1000
            time.sleep(random.uniform(delay_seconds + 0.005, delay_seconds + 0.025))
            
            # Небольшая пауза перед следующей проверкой
            time.sleep(0.01)
        
        # Если зеленый цвет пропал во время цикла, завершаем действие
        if not self.check_color_with_tolerance():
            self.action_in_progress = False
            self.detected_key = None
    
    def stop(self):
        self.running = False

class BuilderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.resolution_mode = "FullHD"
        self.delay_between_presses = 120  # Значение по умолчанию в мс
        self.color_tolerance = 10  # Допуск цвета по умолчанию
        
        # Создаем окно счетчика (изначально скрыто)
        self.counter_window = CounterWindow()
        
        # Создаем окно логов
        self.log_window = LogWindow()
        
        self.initUI()

        self.load_settings()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Стройка")
        self.setFixedSize(550, 510)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Строка состояния
        self.status_label = QLabel("Состояние: не активно")
        self.status_label.setStyleSheet(LABEL_STYLES["primary"])
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Фрейм для разрешения экрана
        resolution_frame = QFrame()
        resolution_frame.setStyleSheet(FRAME_STYLES["frame"])
        resolution_layout = QVBoxLayout(resolution_frame)
        resolution_layout.setContentsMargins(15, 10, 15, 10)
        resolution_layout.setSpacing(5)
        
        # Заголовок
        resolution_title = QLabel("Разрешение экрана:")
        resolution_title.setStyleSheet(LABEL_STYLES["secondary"])
        resolution_title.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(resolution_title)
        
        # Фрейм для кнопок разрешения
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet(FRAME_STYLES["frame_inner"])
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(10, 5, 10, 5)
        
        # Кнопка FullHD
        self.fullhd_button = QPushButton("FullHD")
        self.fullhd_button.setStyleSheet(BUTTON_STYLES["primary_small"])
        self.fullhd_button.clicked.connect(lambda: self.set_resolution("FullHD"))
        buttons_layout.addWidget(self.fullhd_button)
        
        # Кнопка QuadHD
        self.quadhd_button = QPushButton("QuadHD")
        self.quadhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
        self.quadhd_button.clicked.connect(lambda: self.set_resolution("QuadHD"))
        buttons_layout.addWidget(self.quadhd_button)
        
        resolution_layout.addWidget(buttons_frame)
        
        # Метка текущего разрешения
        self.resolution_label = QLabel(f"Текущее: {self.resolution_mode}")
        self.resolution_label.setStyleSheet(LABEL_STYLES["muted"])
        self.resolution_label.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(self.resolution_label)
        
        main_layout.addWidget(resolution_frame)
        
        # Фрейм для поля ввода задержки
        delay_frame = QFrame()
        delay_frame.setStyleSheet(FRAME_STYLES["frame"])
        delay_layout = QHBoxLayout(delay_frame)
        delay_layout.setContentsMargins(20, 10, 20, 10)
        delay_layout.setSpacing(10)
        
        # Метка для поля ввода
        delay_label = QLabel("Задержка между нажатиями (мс):")
        delay_label.setStyleSheet(LABEL_STYLES["secondary"])
        delay_layout.addWidget(delay_label)
        
        # Поле ввода задержки
        self.delay_entry = QLineEdit()
        self.delay_entry.setText(str(self.delay_between_presses))
        self.delay_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self.delay_entry.setMaximumWidth(80)
        delay_layout.addWidget(self.delay_entry)
        
        # Добавляем растягивающий элемент
        delay_layout.addStretch()
        
        main_layout.addWidget(delay_frame)
        
        # Фрейм для информации о детекции
        detection_frame = QFrame()
        detection_frame.setStyleSheet(FRAME_STYLES["frame"])
        detection_layout = QVBoxLayout(detection_frame)
        detection_layout.setContentsMargins(15, 10, 15, 10)
        detection_layout.setSpacing(5)
        
        # Метка для отображения обнаруженных клавиш
        self.detection_label = QLabel("Обнаружено: ничего")
        self.detection_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 8px;
                background-color: #3c3c3c;
                border-radius: 8px;
                min-height: 25px;
                font-weight: bold;
            }
        """)
        self.detection_label.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(self.detection_label)
        
        # Информация о проверяемых изображениях
        images_title = QLabel("Проверяемые изображения:")
        images_title.setStyleSheet(LABEL_STYLES["secondary"])
        images_title.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(images_title)
        
        # Показываем информацию о цвете и координатах
        target_color = colors.color["light_green"]
        coords = builder_coordinate[self.resolution_mode]["builder_marker"]
        info_text = f"Цвет: RGB{target_color}, Координаты: {coords}"
        images_info = QLabel(info_text)
        images_info.setStyleSheet(LABEL_STYLES["muted"])
        images_info.setAlignment(Qt.AlignCenter)
        images_info.setWordWrap(True)
        detection_layout.addWidget(images_info)
        
        main_layout.addWidget(detection_frame)
        
        # Добавляем растягивающий элемент перед кнопками управления
        main_layout.addStretch(1)
        
        # Фрейм для кнопок управления
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 10, 20, 10)
        control_layout.setSpacing(20)
        
        # Кнопка Запустить/Остановить
        self.toggle_button = QPushButton("Запустить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_button.clicked.connect(self.toggle_bot)
        control_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)

        # Кнопка управления окном счетчика
        self.counter_btn = QPushButton("Показать счётчик")
        self.counter_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
        self.counter_btn.clicked.connect(self.toggle_counter_window)
        main_layout.addWidget(self.counter_btn, alignment=Qt.AlignCenter)
        
        # Кнопка управления окном логов (в правом нижнем углу)
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        
        self.log_btn = QPushButton("Показать логи")
        self.log_btn.setStyleSheet(BUTTON_STYLES["log_button"])
        self.log_btn.clicked.connect(self.toggle_log_window)
        log_btn_layout.addWidget(self.log_btn)
        
        main_layout.addLayout(log_btn_layout)
        
        self.setLayout(main_layout)
        
        # Проверяем существование папки keys и файлов
        self.check_keys_folder()
        
    def set_resolution(self, mode):
        """Устанавливает разрешение экрана"""
        self.resolution_mode = mode
        self.resolution_label.setText(f"Текущее: {self.resolution_mode}")
        
        # Обновляем стили кнопок
        if mode == "FullHD":
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["primary_small"].replace(
                "background-color: #2196F3;", "background-color: #4CAF50;"
            ).replace(
                "QPushButton:hover {", "QPushButton:hover { background-color: #45a049;"
            ))
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
        else:
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["primary_small"].replace(
                "background-color: #2196F3;", "background-color: #4CAF50;"
            ).replace(
                "QPushButton:hover {", "QPushButton:hover { background-color: #45a049;"
            ))
        
    def check_keys_folder(self):
        """Проверяет наличие папки keys и необходимых файлов"""
        keys_dir = os.path.join(BASE_DIR, 'assets', 'keys')
        
        if not os.path.exists(keys_dir):
            error_msg = "ОШИБКА: Папка 'keys' не найдена!"
            self.status_label.setText(error_msg)
            self.add_log(f"ВНИМАНИЕ: {error_msg}")
            return False
            
        required_files = ['e.png', 'f.png', 'h.png']
        missing_files = []
        
        for file in required_files:
            file_path = os.path.join(keys_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
                
        if missing_files:
            error_msg = f"ОШИБКА: Отсутствуют файлы: {', '.join(missing_files)}"
            self.status_label.setText(error_msg)
            self.add_log(f"ВНИМАНИЕ: {error_msg}")
            return False
            
        success_msg = f"Все файлы найдены в папке: {keys_dir}"
        self.add_log(success_msg)
        return True
        
    def toggle_counter_window(self):
        """Показать/скрыть окно счетчика (работает во время работы скрипта)"""
        if self.counter_window.isVisible():
            self.counter_window.hide()
            self.counter_btn.setText("Показать счётчик")
            self.add_log("Счётчик скрыт (продолжает считать)")
        else:
            self.counter_window.show()
            self.counter_window.move_to_top_right()
            self.counter_btn.setText("Скрыть счётчик")
            self.add_log("Счётчик показан")
    
    def toggle_log_window(self):
        """Показать/скрыть окно логов"""
        if self.log_window.isVisible():
            self.log_window.hide()
            self.log_btn.setText("Показать логи")
        else:
            self.log_window.show()
            # Позиционируем окно логов в правом нижнем углу
            screen_geometry = QApplication.desktop().availableGeometry()
            x = screen_geometry.width() - self.log_window.width() - 20
            y = screen_geometry.height() - self.log_window.height() - 20
            self.log_window.move(x, y)
            self.log_btn.setText("Скрыть логи")
    
    def toggle_bot(self):
        if self.running:
            self.stop_bot()
        else:
            self.start_bot()
    
    def start_bot(self):
        """Запускает бота"""
        # Проверяем наличие файлов перед запуском
        if not self.check_keys_folder():
            return
            
        try:
            # Получаем задержку из поля ввода
            self.delay_between_presses = int(self.delay_entry.text())
            if self.delay_between_presses < 0:
                raise ValueError("Задержка не может быть отрицательной")
        except ValueError as e:
            error_msg = f"Ошибка: {str(e)}"
            self.status_label.setText(error_msg)
            self.add_log(f"ОШИБКА: {error_msg}")
            return
            
        self.running = True
        self.toggle_button.setText("Остановить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
        self.status_label.setText("Состояние: Запуск...")
        self.detection_label.setText("Обнаружено: ничего")
        
        # Сбрасываем счетчик при запуске скрипта
        self.counter_window.reset_counter()
        self.add_log("Счётчик сброшен (начало нового цикла)")
        
        # Создаем и запускаем рабочий поток
        self.worker_thread = WorkerThread(self.resolution_mode, self.delay_between_presses, self.color_tolerance)
        self.worker_thread.action_completed.connect(self.increment_counter)
        self.worker_thread.key_detected.connect(self.update_detection_label)
        self.worker_thread.log_message.connect(self.add_log)
        self.worker_thread.status_updated.connect(self.update_status_label)
        self.worker_thread.start()
        
        self.add_log(f"Бот запущен. Задержка: {self.delay_between_presses} мс, Разрешение: {self.resolution_mode}")
    
    def stop_bot(self):
        """Останавливает бота"""
        self.running = False
        self.toggle_button.setText("Запустить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.status_label.setText("Состояние: Не активно")
        
        # Останавливаем рабочий поток
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
            
        self.add_log("Бот остановлен")
    
    def increment_counter(self):
        """Увеличивает счетчик в отдельном окне (работает даже если окно скрыто)"""
        self.counter_window.increment_counter()
    
    def add_log(self, message):
        """Добавляет сообщение в окно логов"""
        self.log_window.add_log(message)
    
    def update_detection_label(self, key_name):
        """Обновляет метку обнаруженных клавиш"""
        self.detection_label.setText(f"Обнаружено: {key_name.upper()}.png (нажатие клавиши {key_name.upper()})")
    
    def update_status_label(self, status_text):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {status_text}")
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        self.resolution_mode = config.get("builder", "resolution_mode", "FullHD")
        self.delay_between_presses = config.get("builder", "delay_between_presses", 120)
        self.color_tolerance = config.get("builder", "color_tolerance", 10)
        
        # Устанавливаем значения в поля
        self.delay_entry.setText(str(self.delay_between_presses))
        self.set_resolution(self.resolution_mode)
        
        # Загружаем состояние счетчика
        counter_visible = config.get("builder", "counter_visible", False)
        if counter_visible:
            self.counter_window.show()
            self.counter_btn.setText("Скрыть счётчик")
        else:
            self.counter_window.hide()
            self.counter_btn.setText("Показать счётчик")

    def save_settings(self):
        """Сохраняет текущие настройки"""
        # Получаем текущее значение из поля ввода
        try:
            self.delay_between_presses = int(self.delay_entry.text())
        except ValueError:
            self.delay_between_presses = 120
        
        config.set_multiple("builder", {
            "resolution_mode": self.resolution_mode,
            "delay_between_presses": self.delay_between_presses,
            "color_tolerance": self.color_tolerance,
            "counter_visible": self.counter_window.isVisible()
        })

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        self.save_settings()
        # Гарантируем остановку потока при закрытии окна
        if self.running:
            self.stop_bot()
        # Закрываем окно счетчика
        self.counter_window.close()
        # Закрываем окно логов
        self.log_window.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    builder_app = BuilderApp()
    builder_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()