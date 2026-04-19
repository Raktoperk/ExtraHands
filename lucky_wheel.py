import sys
import time
from threading import Thread, Event
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime

# Импорт координат из отдельного файла
from components.coordinates import lucky_wheel_coordinate

# Импорт функций из functions.py
from components.functions import click_coordinates, press_key

try:
    from components.styles import *
except ImportError:
    # Запасные значения если файл стилей не найден
    from components.styles import (
        COLORS, WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, 
        CHECKBOX_STYLES, COUNTER_WINDOW_STYLES, FRAME_STYLES,
        INPUT_STYLES, GROUPBOX_STYLES
    )

class LuckyWheelWorkerThread(QThread):
    """Рабочий поток для выполнения колеса удачи"""
    status_updated = pyqtSignal(str)  # Сигнал для обновления статуса
    log_message = pyqtSignal(str)    # Сигнал для записи в лог
    
    def __init__(self, resolution_mode, hours, minutes):
        super().__init__()
        self.resolution_mode = resolution_mode
        self.hours = hours
        self.minutes = minutes
        self.running = True
        
    def run(self):
        try:
            # Вычисляем общее время ожидания в секундах
            total_seconds = self.hours * 3600 + self.minutes * 60 + 60
            
            # Ждем указанное время
            wait_message = f"Ожидание {self.hours}ч {self.minutes}мин перед запуском..."
            self.status_updated.emit(wait_message)
            self.log_message.emit(wait_message)
            
            end_time = time.time() + total_seconds
            while time.time() < end_time and self.running:
                time.sleep(0.1)  # Проверяем каждые 100 мс
            
            if not self.running:
                return
            
            # Получаем координаты для текущего разрешения
            coords = lucky_wheel_coordinate.get(self.resolution_mode)
            if not coords:
                error_message = f"Нет координат для разрешения {self.resolution_mode}"
                self.status_updated.emit(error_message)
                self.log_message.emit(f"ОШИБКА: {error_message}")
                return
            
            # Запускаем основной цикл
            while self.running:
                # Нажимаем F10
                press_message = "Нажимаю F10"
                self.status_updated.emit(press_message)
                self.log_message.emit(press_message)
                press_key('f10')
                time.sleep(2)
                
                if not self.running:
                    break
                    
                # Выполняем клики по координатам
                click_message = "Кликаю в магазин"
                self.status_updated.emit(click_message)
                self.log_message.emit(click_message)
                click_coordinates(coords["shop"])
                time.sleep(2)
                
                if not self.running:
                    break
                    
                click_message = "Кликаю в рулетку"
                self.status_updated.emit(click_message)
                self.log_message.emit(click_message)
                click_coordinates(coords["roulette"])
                time.sleep(2)
                
                if not self.running:
                    break
                    
                click_message = "Кликаю в колесо удачи"
                self.status_updated.emit(click_message)
                self.log_message.emit(click_message)
                click_coordinates(coords["luckywheel"])
                time.sleep(2)
                
                if not self.running:
                    break
                    
                click_message = "Кликаю в спин"
                self.status_updated.emit(click_message)
                self.log_message.emit(click_message)
                click_coordinates(coords["spin"])
                time.sleep(15)
                
                if not self.running:
                    break
                    
                # Дважды нажимаем ESC
                press_message = "Нажимаю ESC"
                self.status_updated.emit(press_message)
                self.log_message.emit(press_message)
                press_key('esc')
                time.sleep(2)
                
                if not self.running:
                    break
                    
                press_message = "Нажимаю ESC второй раз"
                self.status_updated.emit(press_message)
                self.log_message.emit(press_message)
                press_key('esc')
                
                # Ждем 4 часа 10 минут (15000 секунд) до следующего запуска
                wait_message = "Ожидание 4ч 10мин до следующего запуска..."
                self.status_updated.emit(wait_message)
                self.log_message.emit(wait_message)
                
                end_time = time.time() + 15000
                while time.time() < end_time and self.running:
                    time.sleep(0.1)
                
        except Exception as e:
            error_message = f"Ошибка в выполнении действия: {e}"
            self.status_updated.emit(error_message)
            self.log_message.emit(f"ОШИБКА: {error_message}")
            
    def stop(self):
        """Останавливает выполнение"""
        self.running = False
        self.log_message.emit("Получена команда остановки")

class LuckyWheelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.current_resolution = "FullHD"
        
        self.initUI()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Колесо удачи")
        self.setFixedSize(550, 450)
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
        
        # Фрейм для поля ввода часов
        hours_frame = QFrame()
        hours_frame.setStyleSheet(FRAME_STYLES["frame"])
        hours_layout = QHBoxLayout(hours_frame)
        hours_layout.setContentsMargins(20, 10, 20, 10)
        hours_layout.setSpacing(10)
        
        # Метка для поля ввода часов
        hours_label = QLabel("Часы (0-4):")
        hours_label.setStyleSheet(LABEL_STYLES["secondary"])
        hours_layout.addWidget(hours_label)
        
        # Поле ввода часов
        self.hours_entry = QLineEdit()
        self.hours_entry.setText("0")
        self.hours_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self.hours_entry.setMaximumWidth(80)
        hours_layout.addWidget(self.hours_entry)
        
        # Добавляем растягивающий элемент
        hours_layout.addStretch()
        
        main_layout.addWidget(hours_frame)
        
        # Фрейм для поля ввода минут
        minutes_frame = QFrame()
        minutes_frame.setStyleSheet(FRAME_STYLES["frame"])
        minutes_layout = QHBoxLayout(minutes_frame)
        minutes_layout.setContentsMargins(20, 10, 20, 10)
        minutes_layout.setSpacing(10)
        
        # Метка для поля ввода минут
        minutes_label = QLabel("Минуты (0-59):")
        minutes_label.setStyleSheet(LABEL_STYLES["secondary"])
        minutes_layout.addWidget(minutes_label)
        
        # Поле ввода минут
        self.minutes_entry = QLineEdit()
        self.minutes_entry.setText("0")
        self.minutes_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self.minutes_entry.setMaximumWidth(80)
        minutes_layout.addWidget(self.minutes_entry)
        
        # Добавляем растягивающий элемент
        minutes_layout.addStretch()
        
        main_layout.addWidget(minutes_frame)
        
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
        self.resolution_label = QLabel(f"Текущее: {self.current_resolution}")
        self.resolution_label.setStyleSheet(LABEL_STYLES["muted"])
        self.resolution_label.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(self.resolution_label)
        
        main_layout.addWidget(resolution_frame)
        
        # Добавляем растягивающий элемент
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
        
        # Информационная метка
        info_label = QLabel("Бот нажмет F10, откроет магазин, выберет колесо удачи, провернет его и закроет")
        info_label.setStyleSheet(LABEL_STYLES["muted"])
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # Кнопка управления окном логов (в правом нижнем углу, как в gym.py)
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        
        self.log_btn = QPushButton("Показать логи")
        self.log_btn.setStyleSheet(BUTTON_STYLES["log_button"])
        self.log_btn.clicked.connect(self.toggle_log_window)
        log_btn_layout.addWidget(self.log_btn)
        
        main_layout.addLayout(log_btn_layout)
        
        self.setLayout(main_layout)
        
        # Создаем окно логов (как в gym.py)
        self.log_window = self.create_log_window()
        
    def create_log_window(self):
        """Создает окно логов (упрощенная версия из gym.py)"""
        from PyQt5.QtWidgets import QTextEdit
        from datetime import datetime
        
        log_window = QWidget()
        log_window.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        # Убираем кнопку закрытия
        log_window.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        log_window.setWindowTitle("Логи колеса удачи")
        log_window.setFixedSize(500, 300)
        log_window.setStyleSheet(WINDOW_STYLES["main_window"])
        
        main_layout = QVBoxLayout(log_window)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(INPUT_STYLES["text_edit"])
        main_layout.addWidget(self.log_text)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        # Кнопка очистки логов
        clear_btn = QPushButton("Очистить логи")
        clear_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
        clear_btn.clicked.connect(self.clear_logs)
        control_layout.addWidget(clear_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        return log_window
        
    def set_resolution(self, resolution):
        """Устанавливает разрешение экрана"""
        self.current_resolution = resolution
        self.resolution_label.setText(f"Текущее: {self.current_resolution}")
        
        # Обновляем стили кнопок как в gym.py
        if resolution == "FullHD":
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
        
        # Добавляем запись в лог
        self.add_log(f"Изменено разрешение на: {resolution}")
        
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
            
    def add_log(self, message):
        """Добавляет сообщение в окно логов"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Прокручиваем до конца
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def clear_logs(self):
        """Очищает все логи"""
        self.log_text.clear()
        
    def toggle_bot(self):
        if self.running:
            self.stop_bot()
        else:
            self.start_bot()
    
    def start_bot(self):
        """Запускает бота"""
        try:
            # Проверяем введенные значения
            hours_text = self.hours_entry.text().strip()
            minutes_text = self.minutes_entry.text().strip()
            
            hours = int(hours_text) if hours_text else 0
            minutes = float(minutes_text) if minutes_text else 0
            
            if hours < 0 or hours > 4 or minutes < 0 or minutes > 59:
                self.status_label.setText("Ошибка: некорректные значения времени")
                return
            
            self.running = True
            self.toggle_button.setText("Остановить")
            self.toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
            self.status_label.setText("Состояние: Запуск...")
            
            # Деактивируем элементы управления
            self.set_controls_enabled(False)
            
            # Создаем и запускаем рабочий поток
            self.worker_thread = LuckyWheelWorkerThread(
                self.current_resolution, hours, minutes
            )
            self.worker_thread.status_updated.connect(self.update_status_label)
            self.worker_thread.log_message.connect(self.add_log)
            self.worker_thread.finished.connect(self.on_bot_finished)
            self.worker_thread.start()
            
            # Добавляем запись в лог о начале работы
            self.add_log(f"Начало работы колеса удачи. Разрешение: {self.current_resolution}, "
                        f"Ожидание: {hours}ч {minutes}мин")
            
        except ValueError:
            error_message = "Пожалуйста, введите корректные числа."
            self.status_label.setText(error_message)
            self.add_log(f"ОШИБКА: {error_message}")
            return
    
    def stop_bot(self):
        """Останавливает бота"""
        self.running = False
        self.toggle_button.setText("Остановка...")
        self.toggle_button.setEnabled(False)
        self.status_label.setText("Состояние: Остановка...")
        self.add_log("Запрошена остановка бота")
        
        # Останавливаем рабочий поток
        if self.worker_thread:
            self.worker_thread.stop()
            # Не ждем завершения потока, используем таймер для проверки статуса
            self.start_stop_timer()
    
    def start_stop_timer(self):
        """Запускает таймер для проверки остановки потока"""
        from PyQt5.QtCore import QTimer
        self.stop_timer = QTimer()
        self.stop_timer.timeout.connect(self.check_thread_stopped)
        self.stop_timer.start(100)  # Проверяем каждые 100 мс
    
    def check_thread_stopped(self):
        """Проверяет, остановился ли рабочий поток"""
        if self.worker_thread and not self.worker_thread.isRunning():
            self.stop_timer.stop()
            self.finalize_stop()
    
    def finalize_stop(self):
        """Завершает остановку бота"""
        self.worker_thread = None
        self.running = False
        
        self.toggle_button.setText("Запустить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_button.setEnabled(True)
        self.status_label.setText("Состояние: Не активно")
        self.add_log("Бот остановлен")
        
        # Активируем элементы управления
        self.set_controls_enabled(True)
    
    def set_controls_enabled(self, enabled):
        """Активирует или деактивирует элементы управления"""
        self.hours_entry.setEnabled(enabled)
        self.minutes_entry.setEnabled(enabled)
        self.fullhd_button.setEnabled(enabled)
        self.quadhd_button.setEnabled(enabled)
    
    def on_bot_finished(self):
        """Обработчик завершения работы бота"""
        if self.running:  # Если бот завершился сам, а не по остановке
            self.finalize_stop()
    
    def update_status_label(self, message):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {message}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Гарантируем остановку потока при закрытии окна
        if self.running:
            self.stop_bot()
            # Даем время на корректную остановку
            import time
            for _ in range(10):  # Максимум 1 секунда ожидания
                if not self.running:
                    break
                time.sleep(0.1)
                QApplication.processEvents()
        
        # Закрываем окно логов
        self.log_window.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = LuckyWheelApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()