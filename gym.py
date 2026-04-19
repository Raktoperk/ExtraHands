from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QLineEdit, QCheckBox,
                             QGroupBox, QSpinBox, QStackedWidget, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor

from components.functions import detect_image, press_key, check_color
from components.coordinates import gym_coordinate  # Добавляем импорт координат
import components.gym_logic
import time
import random
import threading
import sys
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

class CounterWindow(QWidget):
    """Маленькое окно счетчика поверх всех окон"""
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.total_cycles = 0  # 0 означает бесконечные подходы
        self.is_hidden = False  # Флаг для отслеживания состояния видимости
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
        self.text_label = QLabel("Выполнено подходов:")
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
        
    def set_total_cycles(self, total):
        """Устанавливает общее количество подходов"""
        self.total_cycles = total
        self.update_counter_display()
        
    def increment_counter(self):
        """Увеличивает счетчик на 1 (работает даже если окно скрыто)"""
        self.counter += 1
        self.update_counter_display()
        
    def update_counter_display(self):
        """Обновляет отображение счетчика (работает независимо от видимости)"""
        if self.total_cycles > 0:
            self.counter_label.setText(f"{self.counter}/{self.total_cycles}")
        else:
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
        # Окно поверх всех - УБИРАЕМ Qt.Tool и добавляем нужные флаги
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        # Убираем кнопку закрытия
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        # Настройка окна
        self.setWindowTitle("Логи и ошибки Качалки")
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
        log_group = QGroupBox("Логи тренировки")
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
        copy_errors_btn.setStyleSheet(BUTTON_STYLES["secondary_small"])
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

class GymWorkerThread(QThread):
    """Рабочий поток для выполнения тренировки"""
    update_status = pyqtSignal(str)  # Сигнал для обновления статуса
    update_counter = pyqtSignal()    # Сигнал для увеличения счетчика
    training_finished = pyqtSignal()  # Сигнал для завершения тренировки
    log_message = pyqtSignal(str)    # Сигнал для записи в лог
    
    def __init__(self, cycles, key_with_food, espander, bind_espander, time_between_sets, miss_chance):
        super().__init__()
        self.cycles = cycles
        self.key_with_food = key_with_food
        self.espander = espander
        self.bind_espander = bind_espander
        self.time_between_sets = time_between_sets
        self.miss_chance = miss_chance
        self.running = True
        self.space_pressed_flag = False
        self.detector_thread = None
        
        # Пути к изображениям (с использованием абсолютных путей)
        self.success_path = os.path.join(BASE_DIR, 'assets', 'gym', 'gym_success.png')
        self.fail_path = os.path.join(BASE_DIR, 'assets', 'gym', 'gym_fail.png')
        self.hungry_path = os.path.join(BASE_DIR, 'assets', 'gym', 'player_hungry.png')
        self.damage_received = os.path.join(BASE_DIR, 'assets', 'gym', 'damage_received.png')
        
        # Определяем разрешение экрана для получения координат
        self.resolution = self.detect_screen_resolution()
        
    def detect_screen_resolution(self):
        """Определяет разрешение экрана"""
        screen = QApplication.desktop().screenGeometry()
        width = screen.width()
        height = screen.height()
        
        if width == 1920 and height == 1080:
            return "FullHD"
        elif width == 2560 and height == 1440:
            return "QuadHD"
        else:
            # Если разрешение не определено, используем FullHD по умолчанию
            self.log_message.emit(f"Неизвестное разрешение: {width}x{height}. Использую координаты для FullHD")
            return "FullHD"
        
    def run(self):
        try:
            # Запускаем детектор в отдельном потоке с учетом шанса промаха
            self.detector_thread = threading.Thread(
                target=components.gym_logic.run_detector,
                args=(self.on_space_pressed, self.miss_chance),
                daemon=True
            )
            self.detector_thread.start()
            
            # Даем детектору время на инициализацию
            time.sleep(5)
            
            cycle_counter = 0
            while self.running:
                # Если задано ограниченное количество циклов, проверяем
                if self.cycles > 0 and cycle_counter >= self.cycles:
                    break
                        
                # Проверка голода
                if os.path.exists(self.hungry_path):
                    try:
                        if detect_image(self.hungry_path, threshold=0.7) is not None:
                            hunger_message = f'Персонаж голоден. Нажимаю клавишу "{self.key_with_food}"'
                            self.update_status.emit(hunger_message)
                            self.log_message.emit(hunger_message)
                            press_key(self.key_with_food)
                            time.sleep(random.uniform(5, 8))
                        else:
                            no_hunger_message = "Персонаж не голоден"
                            self.update_status.emit(no_hunger_message)
                            self.log_message.emit(no_hunger_message)
                    except Exception as e:
                        error_message = f"Ошибка при проверке голода: {str(e)}"
                        self.update_status.emit(error_message)
                        self.log_message.emit(f"ОШИБКА: {error_message}")
                else:
                    file_not_found_message = f"Файл голода не найден: {self.hungry_path}"
                    self.update_status.emit(file_not_found_message)
                    self.log_message.emit(f"ВНИМАНИЕ: {file_not_found_message}")

                if self.espander:
                    key_message = f"Нажимаю {self.bind_espander}"
                    self.update_status.emit(key_message)
                    self.log_message.emit(key_message)
                    press_key(self.bind_espander)
                    # time.sleep(0.5)
                else:
                    key_message = "Нажимаю E"
                    self.update_status.emit(key_message)
                    self.log_message.emit(key_message)
                    press_key('e')
                    # time.sleep(0.5)

                
                time.sleep(0.25)
                
                # Проверка маркера тренажерного зала перед началом подхода
                marker_coords = gym_coordinate.get(self.resolution, {}).get("gym_e_marker")
                if marker_coords:
                    # Проверяем цвет (253, 255, 253) с погрешностью 5
                    if not check_color(marker_coords, color=(253, 255, 253), tolerance=5):
                        # Ждем 5-10 секунд
                        wait_time = random.uniform(5, 10)
                        
                        marker_message = f"Маркер не найден (цвет не совпадает). Ожидание {wait_time} секунд..."
                        self.update_status.emit(marker_message)
                        self.log_message.emit(marker_message)

                        time.sleep(wait_time)
                        
                        # Пропускаем этот подход без добавления к счетчику
                        skip_message = f"Подход {cycle_counter} пропущен (маркер не найден)"
                        self.update_status.emit(skip_message)
                        self.log_message.emit(skip_message)
                        continue  # Начинаем следующий подход
                else:
                    error_message = f"Координаты маркера не найдены для разрешения {self.resolution}"
                    self.update_status.emit(error_message)
                    self.log_message.emit(f"ОШИБКА: {error_message}")

                wait_message = f"Подход {cycle_counter}. Ожидание завершения упражнения..."
                self.update_status.emit(wait_message)
                self.log_message.emit(wait_message)
                
                cycle_counter += 1
                status_message = f"Подход {cycle_counter}"
                self.update_status.emit(status_message)
                self.log_message.emit(status_message)

                # Ожидание завершения упражнения (ИСПРАВЛЕНО: добавлена проверка running в цикл)
                success_detected = False
                fail_detected = False
                
                while self.running and not success_detected and not fail_detected:
                    # Проверяем флаг от детектора
                    if self.space_pressed_flag:
                        detector_message = "[Gym] Получен сигнал от детектора"
                        self.update_status.emit(detector_message)
                        self.log_message.emit(detector_message)
                        self.space_pressed_flag = False  # Сбрасываем флаг
                    
                    # Проверяем успех
                    try:
                        if detect_image(self.success_path, threshold=0.6) is not None:
                            success_detected = True
                            success_message = "Успешное завершение подхода"
                            self.log_message.emit(success_message)
                            self.update_counter.emit()
                            time.sleep(3)
                            continue
                    except Exception as e:
                        self.log_message.emit(f"Ошибка при проверке успеха: {str(e)}")
                    
                    # Проверяем неудачу
                    try:
                        if detect_image(self.fail_path, threshold=0.6) is not None:
                            fail_detected = True
                            fail_message = "Неудачное завершение подхода"
                            self.log_message.emit(fail_message)
                            time.sleep(3)
                            continue
                    except Exception as e:
                        self.log_message.emit(f"Ошибка при проверке неудачи: {str(e)}")
                    # Проверяем получение урона
                    try:
                        if detect_image(self.damage_received, threshold=0.6) is not None:
                            fail_detected = True
                            damage_message = "Получен урон. Завершение подхода"
                            self.log_message.emit(damage_message)
                            time.sleep(3)
                            continue
                    except Exception as e:
                        self.log_message.emit(f"Ошибка при проверке получения урона: {str(e)}")
                    
                    # Небольшая пауза чтобы не перегружать процессор
                    time.sleep(random.uniform(0.3, 0.7))
                
                if not self.running:
                    break
                
                finish_message = f"Подход {cycle_counter} завершен"
                self.update_status.emit(finish_message)
                self.log_message.emit(finish_message)
                
                # Если это не последний подход (или бесконечные подходы), ждем
                if self.running:
                    is_last_cycle = (self.cycles > 0 and cycle_counter >= self.cycles)
                    
                    if self.espander:
                        # Добавляем паузу для эспандера (2-7 секунд)
                        if not is_last_cycle:
                            wait_time = random.uniform(2, 7)
                            wait_message = f'Жду {wait_time:.1f} секунд (эспандер)'
                            self.update_status.emit(wait_message)
                            self.log_message.emit(wait_message)
                            # Разбиваем ожидание на небольшие интервалы для возможности прерывания
                            steps = int(wait_time * 10)
                            for i in range(steps):
                                if not self.running:
                                    break
                                time.sleep(0.1)
                        else:
                            last_cycle_message = "Последний подход - ждать не нужно, завершаю тренировку"
                            self.update_status.emit(last_cycle_message)
                            self.log_message.emit(last_cycle_message)
                    elif is_last_cycle:
                        last_cycle_message = "Последний подход - ждать не нужно, завершаю тренировку"
                        self.update_status.emit(last_cycle_message)
                        self.log_message.emit(last_cycle_message)
                    else:
                        wait_time = random.uniform(*self.time_between_sets)
                        wait_message = f'Жду {wait_time:.1f} секунд'
                        self.update_status.emit(wait_message)
                        self.log_message.emit(wait_message)
                        # Разбиваем ожидание на небольшие интервалы для возможности прерывания
                        steps = int(wait_time * 10)
                        for i in range(steps):
                            if not self.running:
                                break
                            time.sleep(0.1)
            
            finish_training_message = "Тренировка завершена"
            self.update_status.emit(finish_training_message)
            self.log_message.emit(finish_training_message)
            self.training_finished.emit()
            
        except Exception as e:
            error_message = f"Критическая ошибка: {str(e)}"
            self.update_status.emit(error_message)
            self.log_message.emit(f"КРИТИЧЕСКАЯ ОШИБКА: {error_message}")
            self.training_finished.emit()
    
    def on_space_pressed(self):
        """Колбэк, вызываемый когда детектор нажимает пробел"""
        self.space_pressed_flag = True
        self.log_message.emit("[Detector] Пробел нажат")
    
    def stop(self):
        """Останавливает выполнение тренировки"""
        self.running = False
        self.log_message.emit("Получена команда остановки")

class GymApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.stop_requested = False
        
        # Создаем окно счетчика
        self.counter_window = CounterWindow()
        
        # Создаем окно логов
        self.log_window = LogWindow()
        
        self.initUI()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Качалка")
        self.setFixedSize(550, 500)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        
        # Строка состояния
        self.status_label = QLabel("Состояние: не активно")
        self.status_label.setStyleSheet(LABEL_STYLES["primary"])
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Фрейм для настроек подходов
        cycles_frame = QFrame()
        cycles_frame.setStyleSheet(FRAME_STYLES["frame"])
        cycles_layout = QHBoxLayout(cycles_frame)
        cycles_layout.setContentsMargins(20, 8, 20, 8)
        cycles_layout.setSpacing(10)
        
        cycles_label = QLabel("Количество подходов (0 = бесконечно):")
        cycles_label.setStyleSheet(LABEL_STYLES["secondary"])
        cycles_layout.addWidget(cycles_label)
        
        self.cycles_entry = QSpinBox()
        self.cycles_entry.setRange(0, 9999)
        self.cycles_entry.setValue(0)
        self.cycles_entry.setStyleSheet(INPUT_STYLES["spin_box"])
        self.cycles_entry.setMaximumWidth(80)
        cycles_layout.addWidget(self.cycles_entry)
        
        cycles_layout.addStretch()
        main_layout.addWidget(cycles_frame)
        
        # Фрейм для настроек еды
        food_frame = QFrame()
        food_frame.setStyleSheet(FRAME_STYLES["frame"])
        food_layout = QHBoxLayout(food_frame)
        food_layout.setContentsMargins(20, 8, 20, 8)
        food_layout.setSpacing(10)
        
        food_label = QLabel("Клавиша с едой:")
        food_label.setStyleSheet(LABEL_STYLES["secondary"])
        food_layout.addWidget(food_label)
        
        self.food_entry = QLineEdit()
        self.food_entry.setText("5")
        self.food_entry.setStyleSheet(INPUT_STYLES["line_edit_small"])
        self.food_entry.setMaximumWidth(60)
        food_layout.addWidget(self.food_entry)
        
        food_layout.addStretch()
        main_layout.addWidget(food_frame)
        
        # Фрейм для шанса промаха
        miss_frame = QFrame()
        miss_frame.setStyleSheet(FRAME_STYLES["frame"])
        miss_layout = QHBoxLayout(miss_frame)
        miss_layout.setContentsMargins(20, 8, 20, 8)
        miss_layout.setSpacing(10)
        
        miss_label = QLabel("Шанс промаха (%):")
        miss_label.setStyleSheet(LABEL_STYLES["secondary"])
        miss_layout.addWidget(miss_label)
        
        self.miss_chance_entry = QSpinBox()
        self.miss_chance_entry.setRange(0, 100)
        self.miss_chance_entry.setValue(0)
        self.miss_chance_entry.setStyleSheet(INPUT_STYLES["spin_box"])
        self.miss_chance_entry.setMaximumWidth(80)
        miss_layout.addWidget(self.miss_chance_entry)
        
        # Текстовая подсказка о промахе
        miss_info_label = QLabel("(Промах: -40px к радиусу)")
        miss_info_label.setStyleSheet(LABEL_STYLES["muted"])
        # miss_layout.addWidget(miss_info_label)
        
        miss_layout.addStretch()
        main_layout.addWidget(miss_frame)
        
        # Фрейм для чекбокса эспандера
        espander_frame = QFrame()
        espander_frame.setStyleSheet(FRAME_STYLES["frame"])
        espander_layout = QHBoxLayout(espander_frame)
        espander_layout.setContentsMargins(20, 8, 20, 8)
        espander_layout.setSpacing(10)
        
        self.espander_checkbox = QCheckBox("Использовать эспандер")
        self.espander_checkbox.setStyleSheet(CHECKBOX_STYLES["standard"])
        self.espander_checkbox.stateChanged.connect(self.on_espander_changed)
        espander_layout.addWidget(self.espander_checkbox)
        
        espander_layout.addStretch()
        main_layout.addWidget(espander_frame)
        
        # StackedWidget для переключения между временем отдыха и биндом эспандера
        self.rest_stack = QStackedWidget()
        self.rest_stack.setFixedHeight(55)
        
        # Страница 1: Время отдыха между подходами (по умолчанию)
        self.rest_time_page = QWidget()
        rest_time_layout = QVBoxLayout(self.rest_time_page)
        rest_time_layout.setContentsMargins(0, 0, 0, 0)
        
        rest_time_inner_frame = QFrame()
        rest_time_inner_frame.setStyleSheet(FRAME_STYLES["frame"])
        rest_time_inner_layout = QHBoxLayout(rest_time_inner_frame)
        rest_time_inner_layout.setContentsMargins(20, 8, 20, 8)
        rest_time_inner_layout.setSpacing(10)
        
        time_label = QLabel("Время отдыха между подходами (сек):")
        time_label.setStyleSheet(LABEL_STYLES["secondary"])
        rest_time_inner_layout.addWidget(time_label)
        
        time_sub_layout = QHBoxLayout()
        time_sub_layout.setSpacing(5)
        
        self.min_time_entry = QLineEdit()
        self.min_time_entry.setText("35")
        self.min_time_entry.setStyleSheet(INPUT_STYLES["line_edit_small"])
        time_sub_layout.addWidget(self.min_time_entry)
        
        dash_label = QLabel("-")
        dash_label.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        time_sub_layout.addWidget(dash_label)
        
        self.max_time_entry = QLineEdit()
        self.max_time_entry.setText("50")
        self.max_time_entry.setStyleSheet(INPUT_STYLES["line_edit_small"])
        time_sub_layout.addWidget(self.max_time_entry)
        
        rest_time_inner_layout.addLayout(time_sub_layout)
        rest_time_inner_layout.addStretch()
        
        rest_time_layout.addWidget(rest_time_inner_frame)
        self.rest_stack.addWidget(self.rest_time_page)
        
        # Страница 2: Бинд эспандера
        self.espander_bind_page = QWidget()
        espander_bind_layout = QVBoxLayout(self.espander_bind_page)
        espander_bind_layout.setContentsMargins(0, 0, 0, 0)
        
        espander_bind_inner_frame = QFrame()
        espander_bind_inner_frame.setStyleSheet(FRAME_STYLES["frame"])
        espander_bind_inner_layout = QHBoxLayout(espander_bind_inner_frame)
        espander_bind_inner_layout.setContentsMargins(20, 8, 20, 8)
        espander_bind_inner_layout.setSpacing(10)
        
        bind_label = QLabel("Бинд эспандера:")
        bind_label.setStyleSheet(LABEL_STYLES["secondary"])
        espander_bind_inner_layout.addWidget(bind_label)
        
        self.bind_espander_entry = QLineEdit()
        self.bind_espander_entry.setText("p")
        self.bind_espander_entry.setStyleSheet(INPUT_STYLES["line_edit_small"])
        self.bind_espander_entry.setMaximumWidth(60)
        espander_bind_inner_layout.addWidget(self.bind_espander_entry)
        
        espander_bind_inner_layout.addStretch()
        espander_bind_layout.addWidget(espander_bind_inner_frame)
        self.rest_stack.addWidget(self.espander_bind_page)
        
        main_layout.addWidget(self.rest_stack)
        
        # Добавляем растягивающий элемент перед кнопками управления
        main_layout.addStretch(1)
        
        # Фрейм для кнопок управления
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 10, 20, 10)
        control_layout.setSpacing(20)
        
        self.toggle_button = QPushButton("Запустить тренировку")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_button.clicked.connect(self.toggle_training)
        control_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)
        
        # Кнопка управления окном счетчика (обновленная для работы во время тренировки)
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
           
    def on_espander_changed(self, state):
        """Обработчик изменения состояния чекбокса эспандера"""
        if state == Qt.Checked:
            self.rest_stack.setCurrentWidget(self.espander_bind_page)
        else:
            self.rest_stack.setCurrentWidget(self.rest_time_page)
        
    def toggle_counter_window(self):
        """Показать/скрыть окно счетчика (работает во время тренировки)"""
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
    
    def toggle_training(self):
        if self.running:
            self.stop_training_async()
        else:
            self.start_training()
    
    def start_training(self):
        """Запускает тренировку"""
        try:
            cycles = self.cycles_entry.value()
            key_with_food = self.food_entry.text().strip() or "5"
            espander = self.espander_checkbox.isChecked()
            bind_espander = self.bind_espander_entry.text().strip() if espander else ""
            miss_chance = self.miss_chance_entry.value()
            
            time_between_sets = (35, 50)
            if not espander:
                try:
                    min_time = float(self.min_time_entry.text())
                    max_time = float(self.max_time_entry.text())
                    if min_time < 0 or max_time < 0 or min_time > max_time:
                        raise ValueError("Некорректное время между подходами")
                    time_between_sets = (min_time, max_time)
                except ValueError:
                    self.status_label.setText("Ошибка: некорректное время между подходами")
                    return
                
            self.running = True
            self.toggle_button.setText("Остановить тренировку")
            self.toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
            self.status_label.setText("Состояние: Тренировка активна")
            
            # Активируем/деактивируем элементы управления
            self.set_controls_enabled(False)
            
            # Сбрасываем счетчик (при начале нового цикла тренировки)
            self.counter_window.reset_counter()
            self.counter_window.set_total_cycles(cycles)
            
            self.worker_thread = GymWorkerThread(
                cycles, key_with_food, espander, bind_espander, time_between_sets, miss_chance
            )
            self.worker_thread.update_status.connect(self.update_status_label)
            self.worker_thread.update_counter.connect(self.increment_counter)
            self.worker_thread.training_finished.connect(self.on_training_finished)
            self.worker_thread.log_message.connect(self.add_log)
            self.worker_thread.start()
            
            # Добавляем запись в лог о начале тренировки
            self.add_log(f"Начало тренировки. Подходов: {cycles if cycles > 0 else 'бесконечно'}, Шанс промаха: {miss_chance}%")
            
        except Exception as e:
            error_message = f"Ошибка: {str(e)}"
            self.status_label.setText(error_message)
            self.add_log(f"ОШИБКА ЗАПУСКА: {error_message}")
            self.running = False
            self.set_controls_enabled(True)
    
    def stop_training_async(self):
        """Асинхронная остановка тренировки"""
        self.stop_requested = True
        self.toggle_button.setEnabled(False)
        self.toggle_button.setText("Останавливается...")
        self.status_label.setText("Состояние: Остановка...")
        self.add_log("Запрошена остановка тренировки")
        
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
        """Завершает остановку тренировки"""
        self.worker_thread = None
        self.running = False
        self.stop_requested = False
        
        self.toggle_button.setText("Запустить тренировку")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_button.setEnabled(True)
        self.status_label.setText("Состояние: Не активно")
        self.add_log("Тренировка остановлена")
        
        # Активируем элементы управления
        self.set_controls_enabled(True)
    
    def set_controls_enabled(self, enabled):
        """Активирует или деактивирует элементы управления"""
        self.cycles_entry.setEnabled(enabled)
        self.food_entry.setEnabled(enabled)
        self.miss_chance_entry.setEnabled(enabled)
        self.espander_checkbox.setEnabled(enabled)
        self.min_time_entry.setEnabled(enabled)
        self.max_time_entry.setEnabled(enabled)
        self.bind_espander_entry.setEnabled(enabled)
    
    def on_training_finished(self):
        """Обработчик завершения тренировки"""
        if not self.stop_requested:
            # Только если остановка не была запрошена вручную
            self.finalize_stop()
    
    def increment_counter(self):
        """Увеличивает счетчик в отдельном окне (только при успехе) - работает даже если окно скрыто"""
        self.counter_window.increment_counter()
        # Добавляем запись в лог о счетчике
        current_count = self.counter_window.counter
        total = self.counter_window.total_cycles
        if total > 0:
            self.add_log(f"Счётчик: {current_count}/{total}")
        else:
            self.add_log(f"Счётчик: {current_count}")
    
    def add_log(self, message):
        """Добавляет сообщение в окно логов"""
        self.log_window.add_log(message)
    
    def update_status_label(self, message):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {message}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Гарантируем остановку потока при закрытии окна
        if self.running:
            self.stop_training_async()
            # Даем время на корректную остановку
            import time
            for _ in range(10):  # Максимум 1 секунда ожидания
                if not self.running:
                    break
                time.sleep(0.1)
                QApplication.processEvents()
        
        # Закрываем окно счетчика
        self.counter_window.close()
        # Закрываем окно логов
        self.log_window.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    gym_app = GymApp()
    gym_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()