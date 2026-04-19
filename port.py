from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QGroupBox, QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPainterPath, QRegion, QPainter, QBrush, QColor
import sys
import ctypes
import time
import keyboard  # Добавляем импорт keyboard
from ctypes import wintypes
from components.functions import check_color, press_key
from components.colors import colors
from components.coordinates import port_coordinate
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

# Константы для виртуальных клавиш (оставляем только нужные)
VK_ESCAPE = 0x1B

# Структуры и функции Windows API (оставляем только для GetAsyncKeyState)
user32 = ctypes.WinDLL('user32', use_last_error=True)

def is_key_pressed(vk_code):
    """Проверяет, нажата ли клавиша (используем для ESC)"""
    return user32.GetAsyncKeyState(vk_code) & 0x8000 != 0

class CounterWindow(QWidget):
    """Окно счетчика с информацией об автобеге"""
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.is_hidden = True
        self.auto_run_status = False
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
        
        # Горизонтальный layout - все элементы в одну линию
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(15)
        
        # Блок "Автобег" - Горизонтальное расположение
        auto_run_widget = QWidget()
        auto_run_widget.setStyleSheet("background: transparent;")
        auto_run_layout = QHBoxLayout(auto_run_widget)
        auto_run_layout.setContentsMargins(0, 0, 0, 0)
        auto_run_layout.setSpacing(8)
        
        # Текст "Автобег:"
        auto_run_text = QLabel("Автобег:")
        auto_run_text.setStyleSheet(f"""
            {COUNTER_WINDOW_STYLES["text"]}
            font-size: 16px;
            font-weight: bold;
            color: #CCCCCC;
        """)
        auto_run_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        auto_run_layout.addWidget(auto_run_text)
        
        # Статус автобега
        self.auto_run_status_label = QLabel("выкл")
        self.auto_run_status_label.setStyleSheet(f"""
            {COUNTER_WINDOW_STYLES["text"]}
            font-size: 18px;
            font-weight: bold;
            color: {COLORS["danger"]};
            min-width: 50px;
        """)
        self.auto_run_status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        auto_run_layout.addWidget(self.auto_run_status_label)
        
        layout.addWidget(auto_run_widget)
        
        # Разделитель
        separator = QLabel("│")
        separator.setStyleSheet(f"""
            {COUNTER_WINDOW_STYLES["text"]}
            font-size: 28px;
            font-weight: normal;
            color: #555555;
            padding: 0 10px;
        """)
        layout.addWidget(separator)
        
        # Блок "Счетчик" - Горизонтальное расположение
        counter_widget = QWidget()
        counter_widget.setStyleSheet("background: transparent;")
        counter_layout = QHBoxLayout(counter_widget)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(8)
        
        # Текст "Отнесено коробок:"
        counter_text = QLabel("Коробок:")
        counter_text.setStyleSheet(f"""
            {COUNTER_WINDOW_STYLES["text"]}
            font-size: 16px;
            font-weight: bold;
            color: #CCCCCC;
        """)
        counter_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        counter_layout.addWidget(counter_text)
        
        # Счетчик
        self.counter_label = QLabel("0")
        self.counter_label.setStyleSheet(f"""
            {COUNTER_WINDOW_STYLES["counter"]}
            font-size: 26px;
            font-weight: bold;
            color: {COLORS["primary"]};
            min-width: 50px;
        """)
        self.counter_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        counter_layout.addWidget(self.counter_label)
        
        layout.addWidget(counter_widget)
        
        # Добавляем растягивающий элемент в конце
        layout.addStretch()
        
        # Устанавливаем layout для основного виджета
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Устанавливаем размер окна
        self.setFixedSize(380, 52)
        
        # Позиционируем в правом верхнем углу
        self.move_to_top_right()
        
    def paintEvent(self, event):
        """Переопределяем paintEvent для рисования закругленных углов"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Используем цвет из стилей
        painter.setBrush(QBrush(QColor(COLORS["bg_medium"])))
        painter.setPen(Qt.NoPen)
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)
        
        # Добавляем тонкую рамку
        painter.setPen(QColor(COLORS["border"]))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 10, 10)
        
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
        
    def update_auto_run_status(self, is_running):
        """Обновляет статус автобега"""
        self.auto_run_status = is_running
        if is_running:
            self.auto_run_status_label.setText("  вкл")
            self.auto_run_status_label.setStyleSheet(f"""
                {COUNTER_WINDOW_STYLES["text"]}
                font-size: 18px;
                font-weight: bold;
                color: {COLORS["success"]};
            """)
        else:
            self.auto_run_status_label.setText("выкл")
            self.auto_run_status_label.setStyleSheet(f"""
                {COUNTER_WINDOW_STYLES["text"]}
                font-size: 18px;
                font-weight: bold;
                color: {COLORS["danger"]};
            """)
        
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
        # Окно поверх всех
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        # Убираем кнопку закрытия
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        # Настройка окна
        self.setWindowTitle("Логи порта")
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
        log_group = QGroupBox("Логи порта")
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

class AutoRunManager:
    """Менеджер автобега с использованием keyboard библиотеки"""
    
    def __init__(self, checkbox=None, counter_window=None):
        self.is_running = False
        self.log_callback = None
        self.checkbox = checkbox
        self.counter_window = counter_window
        self.hotkey_id = None
        
    def start(self, log_callback=None):
        """Запускает менеджер автобега"""
        self.log_callback = log_callback
        
        # Регистрируем горячую клавишу F7
        try:
            keyboard.remove_hotkey('f7')  # Удаляем предыдущий, если был
        except:
            pass
            
        self.hotkey_id = keyboard.add_hotkey('f7', self.toggle_auto_run)
        
        if self.log_callback:
            self.log_callback("Автобег инициализирован (F7 - вкл/выкл)")
    
    def toggle_auto_run(self):
        """Включает/выключает автобег"""
        if self.is_running:
            self.stop_auto_run()
        else:
            self.start_auto_run()
            
        # Обновляем чекбокс
        if self.checkbox:
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(self.is_running)
            self.checkbox.blockSignals(False)
            
        # Обновляем статус в окне счетчика
        if self.counter_window:
            self.counter_window.update_auto_run_status(self.is_running)
    
    def start_auto_run(self):
        """Запускает автобег - зажимает Shift + W"""
        try:
            # Зажимаем клавиши через keyboard
            keyboard.press('shift')
            time.sleep(0.05)
            keyboard.press('w')
            
            self.is_running = True
            if self.log_callback:
                self.log_callback("Автобег включен (Shift + W зажаты)")
                
            # Обновляем статус в окне счетчика
            if self.counter_window:
                self.counter_window.update_auto_run_status(True)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка при запуске автобега: {str(e)}")
    
    def stop_auto_run(self):
        """Останавливает автобег - отпускает Shift + W"""
        try:
            # Отпускаем клавиши через keyboard
            keyboard.release('w')
            time.sleep(0.05)
            keyboard.release('shift')
            
            self.is_running = False
            if self.log_callback:
                self.log_callback("Автобег выключен (Shift + W отпущены)")
                
            # Обновляем статус в окне счетчика
            if self.counter_window:
                self.counter_window.update_auto_run_status(False)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка при остановке автобега: {str(e)}")
    
    def set_state(self, state):
        """Устанавливает состояние автобега (True/False)"""
        if state and not self.is_running:
            self.start_auto_run()
        elif not state and self.is_running:
            self.stop_auto_run()
            
        # Обновляем статус в окне счетчика
        if self.counter_window:
            self.counter_window.update_auto_run_status(state)
    
    def cleanup(self):
        """Очистка при завершении"""
        if self.is_running:
            self.stop_auto_run()
        
        # Удаляем горячую клавишу
        try:
            keyboard.remove_hotkey('f7')
        except:
            pass

class WorkerThread(QThread):
    status_update = pyqtSignal(str)
    box_completed = pyqtSignal()
    log_message = pyqtSignal(str)
    
    def __init__(self, active_resolution):
        super().__init__()
        self.active_resolution = active_resolution
        self.running = True
        self.green_color = colors.color["light_green"]
        
    def run(self):
        while self.running:
            try:
                # Получаем координаты для активного разрешения из coordinates.py
                if self.active_resolution in port_coordinate:
                    coords = port_coordinate[self.active_resolution].get("port_marker")
                    if coords:
                        if check_color(coordinates=coords, color=self.green_color):
                            press_key("e", boundary=(0.06, 0.14))
                            success_message = "Нажата клавиша E (обнаружен зелёный цвет)"
                            print(success_message)
                            self.status_update.emit(success_message)
                            self.log_message.emit(success_message)
                            self.box_completed.emit()
                        else:
                            # Логируем, что зелёный цвет не обнаружен
                            self.log_message.emit("Зелёный цвет не обнаружен в координатах порта")
                    else:
                        self.log_message.emit(f"ВНИМАНИЕ: Координаты 'port_marker' не найдены для разрешения {self.active_resolution}")
                else:
                    self.log_message.emit(f"ОШИБКА: Разрешение {self.active_resolution} не найдено в конфигурации координат")
                    
            except Exception as e:
                error_message = f"ОШИБКА В РАБОЧЕМ ПОТОКЕ: {str(e)}"
                self.log_message.emit(error_message)
                
            self.msleep(10)  # Проверка каждые 10 мс
    
    def stop(self):
        self.running = False
        self.log_message.emit("Рабочий поток остановлен")

class PortApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.active_resolution = "FullHD"
        
        # Инициализируем окна
        self.counter_window = CounterWindow()
        self.log_window = LogWindow()
        
        self.initUI()
        
        # Создаем и запускаем менеджер автобега после инициализации UI
        self.auto_run_manager = AutoRunManager(
            checkbox=self.auto_run_checkbox,
            counter_window=self.counter_window
        )
        self.auto_run_manager.start(log_callback=self.add_log)
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Порт")
        self.setFixedSize(550, 500)
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
        self.resolution_label = QLabel(f"Текущее: {self.active_resolution}")
        self.resolution_label.setStyleSheet(LABEL_STYLES["muted"])
        self.resolution_label.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(self.resolution_label)
        
        main_layout.addWidget(resolution_frame)
        
        # Фрейм для автобега
        auto_run_frame = QFrame()
        auto_run_frame.setStyleSheet(FRAME_STYLES["frame"])
        auto_run_layout = QHBoxLayout(auto_run_frame)
        auto_run_layout.setContentsMargins(15, 10, 15, 10)
        auto_run_layout.setSpacing(10)
        
        # Чекбокс для автобега
        self.auto_run_checkbox = QCheckBox("Автобег (Shift+W)")
        self.auto_run_checkbox.setStyleSheet(CHECKBOX_STYLES["standard"])
        self.auto_run_checkbox.stateChanged.connect(self.toggle_auto_run)
        auto_run_layout.addWidget(self.auto_run_checkbox)
        
        # Подпись для горячей клавиши
        hotkey_label = QLabel("(Вкл/Выкл: F7)")
        hotkey_label.setStyleSheet(LABEL_STYLES["muted"])
        auto_run_layout.addWidget(hotkey_label)
        
        auto_run_layout.addStretch()
        main_layout.addWidget(auto_run_frame)

        # Фрейм для кнопок управления
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 10, 20, 10)
        control_layout.setSpacing(20)
        
        # Кнопка Запустить/Остановить
        self.toggle_button = QPushButton("Запустить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_button.clicked.connect(self.toggle_task)
        control_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)

        info_label = QLabel("Бот будет нажимать E при обнаружении зелёного цвета в указанных координатах")
        info_label.setStyleSheet(LABEL_STYLES["muted"])
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

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
        
    def toggle_auto_run(self, state):
        """Включает/выключает автобег через чекбокс"""
        self.auto_run_manager.set_state(state == Qt.Checked)
        
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
    
    def toggle_task(self):
        if self.running:
            self.stop_task()
        else:
            self.start_task()
    
    def start_task(self):
        self.running = True
        self.toggle_button.setText("Остановить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
        self.status_label.setText("Состояние: Активно")
        
        # Сбрасываем счетчик при запуске
        self.counter_window.reset_counter()
        
        # Добавляем запись в лог о начале работы
        self.add_log(f"Запуск работы порта. Разрешение: {self.active_resolution}")
        
        # Создаем и запускаем рабочий поток
        self.worker_thread = WorkerThread(self.active_resolution)
        self.worker_thread.status_update.connect(self.update_status)
        self.worker_thread.box_completed.connect(self.increment_counter)
        self.worker_thread.log_message.connect(self.add_log)
        self.worker_thread.start()
    
    def stop_task(self):
        self.running = False
        self.toggle_button.setText("Запустить")
        self.toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.status_label.setText("Состояние: Не активно")
        
        # Добавляем запись в лог об остановке
        self.add_log("Остановка работы порта")
        
        # Останавливаем рабочий поток
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
    
    def increment_counter(self):
        """Увеличивает счетчик в отдельном окне"""
        self.counter_window.increment_counter()
        # Добавляем запись в лог о счетчике
        current_count = self.counter_window.counter
        self.add_log(f"Счётчик коробок: {current_count}")
    
    def set_resolution(self, resolution):
        self.active_resolution = resolution
        
        # Обновляем состояние кнопок
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
        
        self.resolution_label.setText(f"Текущее: {resolution}")
        
        # Добавляем запись в лог об изменении разрешения
        self.add_log(f"Изменено разрешение на: {resolution}")
        
        # Если поток запущен, обновляем разрешение в нем
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.active_resolution = resolution
    
    def update_status(self, message):
        """Обновляет статус (может использоваться для отладки)"""
        pass
    
    def add_log(self, message):
        """Добавляет сообщение в окно логов"""
        self.log_window.add_log(message)
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Гарантируем остановку потока при закрытии окна
        if self.running:
            self.stop_task()
        
        # Останавливаем автобег при закрытии
        if hasattr(self, 'auto_run_manager'):
            self.auto_run_manager.cleanup()
        
        # Закрываем окно счетчика
        self.counter_window.close()
        
        # Закрываем окно логов
        self.log_window.close()
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    port_app = PortApp()
    port_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()