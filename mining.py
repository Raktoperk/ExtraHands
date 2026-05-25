import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor

# Импортируем общие модули
from components.colors import colors
from components.coordinates import mining_coordinate
from components.functions import press_key, toMS
from components.config_manager import config

import time
import random
import pyautogui

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

class CounterWindow(QWidget):
    """Маленькое окно счетчика поверх всех окон"""
    def __init__(self):
        super().__init__()
        self.counter = 0
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
        text_label = QLabel("Отнесено камней:")
        text_label.setStyleSheet(COUNTER_WINDOW_STYLES["text"])
        layout.addWidget(text_label)
        
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
        """Увеличивает счетчик на 1"""
        self.counter += 1
        self.counter_label.setText(str(self.counter))
        
    def reset_counter(self):
        """Сбрасывает счетчик"""
        self.counter = 0
        self.counter_label.setText("0")
        
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

class WorkerThread(QThread):
    action_completed = pyqtSignal()  # Сигнал для завершения действия
    status_updated = pyqtSignal(str)  # Сигнал для обновления статуса
    
    def __init__(self, resolution_mode, delay_between_presses, color_tolerance=10):
        super().__init__()
        self.resolution_mode = resolution_mode
        self.delay_between_presses = delay_between_presses
        self.color_tolerance = color_tolerance
        self.running = True
        
        # Получаем координаты и цвет из общих модулей
        self.target_coords = {
            "FullHD": mining_coordinate["FullHD"].get("mining_marker", (960, 495)),
            "QuadHD": mining_coordinate["QuadHD"].get("mining_marker", (1276, 671))
        }
        
        # Добавляем координаты в общий модуль, если их нет
        if "mining_marker" not in mining_coordinate["FullHD"]:
            mining_coordinate["FullHD"]["mining_marker"] = (960, 495)
        if "mining_marker" not in mining_coordinate["QuadHD"]:
            mining_coordinate["QuadHD"]["mining_marker"] = (1276, 671)
            
        self.target_color = colors.color["light_green"]
        self.action_in_progress = False  # Флаг, что действие выполняется
        
    def run(self):
        while self.running:
            # Проверяем цвет в целевых координатах
            if self.check_color_with_tolerance():
                if not self.action_in_progress:
                    # Начинаем новое действие
                    self.action_in_progress = True
                    self.status_updated.emit("Активно: обнаружен зеленый цвет")
                    self.press_key_e()
            else:
                if self.action_in_progress:
                    # Зеленый цвет пропал - завершаем действие
                    self.action_in_progress = False
                    self.action_completed.emit()
                    self.status_updated.emit("Действие завершено")
                else:
                    self.status_updated.emit("Ожидание: зеленый цвет не обнаружен")
                
            self.msleep(10)  # Небольшая пауза между проверками
    
    def check_color_with_tolerance(self):
        """Проверяет наличие целевого цвета в заданных координатах с допуском"""
        x, y = self.target_coords[self.resolution_mode]
        
        try:
            # Получаем текущий цвет пикселя
            current_color = pyautogui.pixel(x, y)
            
            # Проверяем каждый канал RGB с допуском
            for i in range(3):
                if abs(current_color[i] - self.target_color[i]) > self.color_tolerance:
                    return False
            return True
        except Exception:
            return False
    
    def press_key_e(self):
        """Нажимает клавишу E пока виден зеленый цвет"""
        action_start_time = time.time()
        action_timeout = 15  # Максимальное время выполнения одного действия (секунд)
        
        while self.running and self.check_color_with_tolerance():
            # Проверяем не превышено ли время выполнения
            if time.time() - action_start_time > action_timeout:
                self.status_updated.emit("Превышено время выполнения действия")
                break
            
            # Нажимаем клавишу E
            press_key('e', boundary=(toMS(40), toMS(120)))
            print(f'Вижу зеленый цвет, нажимаю E')
            
            # Задержка с небольшим случайным отклонением
            delay_seconds = self.delay_between_presses / 1000
            time.sleep(random.uniform(delay_seconds + 0.005, delay_seconds + 0.015))
            
            # Небольшая пауза перед следующей проверкой
            time.sleep(0.01)
    
    def stop(self):
        self.running = False

class MiningBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.resolution_mode = "FullHD"
        self.delay_between_presses = 120  # Значение по умолчанию в мс
        self.color_tolerance = 10  # Допуск цвета по умолчанию
        
        # Создаем окно счетчика
        self.counter_window = CounterWindow()
        
        self.initUI()

        self.load_settings()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Шахта")
        self.setFixedSize(550, 450)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Строка состояния
        self.status_label = QLabel("Состояние: Не активно")
        self.status_label.setStyleSheet(LABEL_STYLES["primary"])
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
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
        
        # Убрал кнопку сброса счетчика - теперь счетчик сбрасывается при запуске бота
        
        self.setLayout(main_layout)
        
        # Счетчик теперь изначально скрыт
        # self.counter_window.hide() - НЕ ПОКАЗЫВАЕМ при запуске
        
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
        
    def toggle_counter_window(self):
        """Показать/скрыть окно счетчика"""
        if self.counter_window.isVisible():
            self.counter_window.hide()
            self.counter_btn.setText("Показать счётчик")
        else:
            self.counter_window.show()
            self.counter_window.move_to_top_right()
            self.counter_btn.setText("Скрыть счётчик")
    
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
            
            # Получаем допуск цвета
            self.color_tolerance = 10
            if self.color_tolerance < 0 or self.color_tolerance > 255:
                raise ValueError("Допуск цвета должен быть в диапазоне 0-255")
                
        except ValueError as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            return
            
        self.running = True
        self.toggle_button.setText("Остановить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
        self.status_label.setText("Состояние: Запуск...")
        
        # Сбрасываем счетчик при запуске бота
        self.counter_window.reset_counter()
        
        # Создаем и запускаем рабочий поток
        self.worker_thread = WorkerThread(self.resolution_mode, 
                                         self.delay_between_presses,
                                         self.color_tolerance)
        self.worker_thread.action_completed.connect(self.increment_counter)
        self.worker_thread.status_updated.connect(self.update_status_label)
        self.worker_thread.start()
    
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
    
    def increment_counter(self):
        """Увеличивает счетчик в отдельном окне"""
        # Счетчик увеличивается всегда, даже если окно скрыто
        self.counter_window.increment_counter()
    
    def update_status_label(self, status_text):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {status_text}")
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        self.resolution_mode = config.get("mining", "resolution_mode", "FullHD")
        self.delay_between_presses = config.get("mining", "delay_between_presses", 120)
        self.color_tolerance = config.get("mining", "color_tolerance", 10)
        
        # Устанавливаем значения в поля
        self.delay_entry.setText(str(self.delay_between_presses))
        self.set_resolution(self.resolution_mode)
        
        # Загружаем состояние счетчика
        counter_visible = config.get("mining", "counter_visible", False)
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
        
        config.set_multiple("mining", {
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
        event.accept()

def main():
    app = QApplication(sys.argv)
    mining_app = MiningBotApp()
    mining_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()