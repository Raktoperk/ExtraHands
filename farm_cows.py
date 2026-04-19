from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor

from components.functions import press_key, check_color
from components.colors import colors
from components.coordinates import farm_cows_coordinate

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
        COUNTER_WINDOW_STYLES, FRAME_STYLES,
        INPUT_STYLES, GROUPBOX_STYLES
    )

# Получаем абсолютный путь к папке со скриптом
if getattr(sys, 'frozen', False):
    # Если приложение упаковано в exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Если запускаем из исходников
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Добавляем недостающие цвета в colors, если их нет
if not hasattr(colors, 'color'):
    colors.color = {}

# Добавляем опасный цвет, если его нет
if 'danger' not in colors.color:
    colors.color['danger'] = (255, 105, 86)  # Оранжево-красный

# Добавляем белый цвет для коровника, если его нет
if 'white' not in colors.color:
    colors.color['white'] = (255, 255, 255)

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
        self.text_label = QLabel("Подоенно коров:")
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
        self.setFixedSize(280, 52)
        
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
        self.setWindowTitle("Логи и ошибки коровника")
        self.setFixedSize(700, 400)
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
        content_layout.addWidget(log_group, 1)
        content_layout.addWidget(error_group, 1)
        
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
    action_completed = pyqtSignal()  # Сигнал для завершения действия (опасный цвет)
    key_detected = pyqtSignal(str)   # Сигнал для обнаружения клавиши
    log_message = pyqtSignal(str)    # Сигнал для записи в лог
    status_updated = pyqtSignal(str) # Сигнал для обновления статуса
    danger_detected = pyqtSignal()   # Сигнал для обнаружения опасного цвета
    white_disappeared = pyqtSignal() # Сигнал для исчезновения белого цвета (счетчик)
    
    def __init__(self, resolution_mode, delay_between_presses, color_tolerance=15):
        super().__init__()
        self.resolution_mode = resolution_mode
        self.delay_between_presses = delay_between_presses
        self.color_tolerance = color_tolerance
        self.running = True
        self.force_pause = False
        self.white_was_present = False  # Флаг для отслеживания наличия белого цвета
        
        # Получаем координаты из общих модулей
        self.coords = farm_cows_coordinate
        
        # Цвета
        self.danger_color = colors.color["danger"]
        self.white_color = colors.color["white"]
        
        self.last_key_pressed = None  # Последняя нажатая клавиша
        
    def run(self):
        self.log_message.emit("Запуск потока коровника")
        self.status_updated.emit("Ожидание...")
        
        while self.running:
            # Проверяем наличие белого цвета
            white_present = check_color((1320, 900), (253, 253, 253), tolerance=10)
            
            # Если белый цвет был и пропал - увеличиваем счетчик
            if self.white_was_present and not white_present:
                self.white_disappeared.emit()
                self.log_message.emit("Белый цвет пропал - +1 к счетчику")
                self.white_was_present = False
            
            # Если белый цвет появился - запоминаем
            if white_present:
                self.white_was_present = True
            
            # Пока есть белый цвет - работает
            while white_present and self.running:
                # 1. Приоритетная проверка опасного цвета
                if self.check_danger_color():
                    if not self.force_pause:
                        self.force_pause = True
                        self.status_updated.emit("ПАУЗА (опасный цвет)")
                        self.log_message.emit("ВНИМАНИЕ: Обнаружен опасный цвет")
                        self.danger_detected.emit()
                    
                    # Случайная пауза от 5 до 15 секунд
                    pause_time = random.uniform(5, 15)
                    self.status_updated.emit(f"Пауза {pause_time:.1f}с (опасный цвет)")
                    
                    # Ждем с проверкой опасного цвета
                    pause_start = time.time()
                    while time.time() - pause_start < pause_time and self.running:
                        self.msleep(100)  # Проверяем каждые 100 мс
                        
                        # Если опасный цвет пропал - выходим из паузы досрочно
                        if not self.check_danger_color():
                            self.log_message.emit("Опасный цвет пропал, досрочное завершение паузы")
                            break
                    
                    # Проверяем, пропал ли опасный цвет
                    if not self.check_danger_color():
                        self.force_pause = False
                        self.status_updated.emit("Активно")
                        self.log_message.emit("Опасный цвет пропал, возобновление работы")
                    
                    # После паузы обновляем проверку белого цвета и продолжаем цикл
                    white_present = check_color((1320, 900), (253, 253, 253), tolerance=10)
                    continue
                
                # Если была пауза, но опасный цвет все еще есть, продолжаем паузу
                if self.force_pause:
                    if not self.check_danger_color():
                        self.force_pause = False
                        self.status_updated.emit("Активно")
                        self.log_message.emit("Опасный цвет пропал, возобновление работы")
                    else:
                        white_present = check_color((1320, 900), (253, 253, 253), tolerance=10)
                        continue
                
                # 2. Проверка белых цветов для клавиш A и D
                a_detected = self.check_white_color("color_a")
                d_detected = self.check_white_color("color_d")
                
                if a_detected and d_detected:
                    # Если оба цвета, делаем небольшую паузу
                    self.msleep(50)
                elif a_detected:
                    # Нажимаем A
                    press_key('a', boundary=(0.04, 0.12))
                    self.last_key_pressed = 'A'
                    self.key_detected.emit('A')
                    
                    # Задержка между нажатиями
                    delay_seconds = self.delay_between_presses / 1000
                    time.sleep(random.uniform(delay_seconds + 0.005, delay_seconds + 0.025))
                    
                elif d_detected:
                    # Нажимаем D
                    press_key('d', boundary=(0.04, 0.12))
                    self.last_key_pressed = 'D'
                    self.key_detected.emit('D')
                    
                    # Задержка между нажатиями
                    delay_seconds = self.delay_between_presses / 1000
                    time.sleep(random.uniform(delay_seconds + 0.005, delay_seconds + 0.025))
                    
                else:
                    # Ничего не обнаружено
                    self.msleep(50)  # Короткая пауза
                
                # Обновляем проверку белого цвета для следующей итерации цикла
                white_present = check_color((1320, 900), (253, 253, 253), tolerance=10)
            
            # Небольшая пауза, если белый цвет отсутствует
            self.msleep(50)
        
        self.log_message.emit("Поток коровника остановлен")
    
    def check_danger_color(self):
        """Проверяет наличие опасного цвета"""
        try:
            coords = self.coords[self.resolution_mode]["danger_color"]
            return check_color(coords, self.danger_color, self.color_tolerance)
        except Exception as e:
            self.log_message.emit(f"Ошибка при проверке опасного цвета: {e}")
            return False
    
    def check_white_color(self, coord_key):
        """Проверяет наличие белого цвета в указанных координатах"""
        try:
            coords = self.coords[self.resolution_mode][coord_key]
            return check_color(coords, self.white_color, 0)  # Белый проверяем точно
        except Exception as e:
            self.log_message.emit(f"Ошибка при проверке белого цвета: {e}")
            return False
    
    def stop(self):
        self.running = False

class FarmCowsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.resolution_mode = "FullHD"
        self.delay_between_presses = 180  # Значение по умолчанию в мс
        self.color_tolerance = 15  # Допуск цвета по умолчанию
        
        # Создаем окно счетчика (изначально скрыто)
        self.counter_window = CounterWindow()
        
        # Создаем окно логов
        self.log_window = LogWindow()
        
        self.initUI()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Ферма (коровник)")
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
        
        # Информация о цветах и координатах
        info_title = QLabel("Параметры детекции:")
        info_title.setStyleSheet(LABEL_STYLES["secondary"])
        info_title.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(info_title)
        
        # Показываем информацию о цветах и координатах
        danger_color = colors.color["danger"]
        white_color = colors.color["white"]
        coords = farm_cows_coordinate[self.resolution_mode]
        
        info_text = (f"Опасный цвет: RGB{danger_color}, Координаты: {coords['danger_color']}\n"
                     f"Белый цвет (A): {coords['color_a']}, (D): {coords['color_d']}\n"
                     f"Допуск цвета: {self.color_tolerance}")
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
        
        # Кнопка управления окном логов
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        
        self.log_btn = QPushButton("Показать логи")
        self.log_btn.setStyleSheet(BUTTON_STYLES["log_button"])
        self.log_btn.clicked.connect(self.toggle_log_window)
        log_btn_layout.addWidget(self.log_btn)
        
        main_layout.addLayout(log_btn_layout)
        
        self.setLayout(main_layout)
        
    def set_resolution(self, mode):
        """Устанавливает разрешение экрана"""
        self.resolution_mode = mode
        self.resolution_label.setText(f"Текущее: {self.resolution_mode}")
        
        # Обновляем информацию о координатах в окне
        coords = farm_cows_coordinate[self.resolution_mode]
        danger_color = colors.color["danger"]
        
        # Обновляем кнопки
        if mode == "FullHD":
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["primary_small"].replace(
                "background-color: #2196F3;", "background-color: #4CAF50;"
            ))
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
        else:
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["primary_small"].replace(
                "background-color: #2196F3;", "background-color: #4CAF50;"
            ))
        
        # Обновляем информацию в детекции
        for i in range(self.detection_label.parent().layout().count()):
            widget = self.detection_label.parent().layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget != self.detection_label and widget.text().startswith("Опасный цвет:"):
                widget.setText(f"Опасный цвет: RGB{danger_color}, Координаты: {coords['danger_color']}\n"
                              f"Белый цвет (A): {coords['color_a']}, (D): {coords['color_d']}\n"
                              f"Допуск цвета: {self.color_tolerance}")
                break
        
    def toggle_counter_window(self):
        """Показать/скрыть окно счетчика"""
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
        self.worker_thread = WorkerThread(
            self.resolution_mode, 
            self.delay_between_presses, 
            self.color_tolerance
        )
        self.worker_thread.action_completed.connect(self.increment_counter)
        self.worker_thread.key_detected.connect(self.update_detection_label)
        self.worker_thread.log_message.connect(self.add_log)
        self.worker_thread.status_updated.connect(self.update_status_label)
        # Убираем подключение danger_detected к счетчику
        # self.worker_thread.danger_detected.connect(self.increment_counter)
        self.worker_thread.white_disappeared.connect(self.increment_counter)  # Только этот сигнал для счетчика
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
        """Увеличивает счетчик в отдельном окне"""
        self.counter_window.increment_counter()
    
    def add_log(self, message):
        """Добавляет сообщение в окно логов"""
        self.log_window.add_log(message)
    
    def update_detection_label(self, key_name):
        """Обновляет метку обнаруженных клавиш"""
        if key_name in ['A', 'D']:
            self.detection_label.setText(f"Обнаружен белый цвет: нажатие клавиши {key_name}")
    
    def update_status_label(self, status_text):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {status_text}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
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
    farm_app = FarmCowsApp()
    farm_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()