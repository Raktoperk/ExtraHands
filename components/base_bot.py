"""
Базовые классы для всех ботов ExtraHands
Обеспечивают единую структуру и устраняют дублирование кода
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import sys
import os

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from components.config_manager import config
from components.ui_components import CounterWindow, LogWindow
from components.styles import WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, FRAME_STYLES, INPUT_STYLES


class BaseWorker(QThread):
    """
    Базовый класс для всех рабочих потоков ботов
    Предоставляет стандартные сигналы и методы управления
    """
    
    # Стандартные сигналы
    log_message = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    action_completed = pyqtSignal()
    finished_signal = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._running = True
        self._paused = False
        self._stop_requested = False
        
    @property
    def is_running(self) -> bool:
        """Возвращает True, если поток должен продолжать работу"""
        return self._running and not self._stop_requested
    
    def pause(self) -> None:
        """Приостанавливает выполнение"""
        self._paused = True
        self.log_message.emit("Работа приостановлена")
    
    def resume(self) -> None:
        """Возобновляет выполнение"""
        self._paused = False
        self.log_message.emit("Работа возобновлена")
    
    def stop(self) -> None:
        """Останавливает выполнение"""
        self._stop_requested = True
        self.log_message.emit("Получена команда остановки")
    
    def safe_sleep(self, seconds: float, check_interval: float = 0.1) -> bool:
        """
        Безопасный сон с проверкой флага остановки
        Возвращает True, если сон завершился нормально, False если была остановка
        """
        elapsed = 0.0
        while elapsed < seconds and self.is_running:
            sleep_time = min(check_interval, seconds - elapsed)
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))
            elapsed += check_interval
        return self.is_running
    
    def run(self) -> None:
        """Основной метод потока (должен быть переопределен)"""
        raise NotImplementedError
    
    def cleanup(self) -> None:
        """Очистка ресурсов (переопределяется при необходимости)"""
        pass


class BaseBotApp(QWidget):
    """
    Базовый класс для всех окон ботов
    Предоставляет стандартные компоненты UI и методы управления
    """
    
    def __init__(self, 
                 title: str, 
                 window_width: int = 550, 
                 window_height: int = 450,
                 has_resolution: bool = True,
                 has_delay: bool = False,
                 has_log: bool = True,
                 has_counter: bool = True):
        super().__init__()
        
        self._title = title
        self._window_width = window_width
        self._window_height = window_height
        self._has_resolution = has_resolution
        self._has_delay = has_delay
        self._has_log = has_log
        self._has_counter = has_counter
        
        self._running = False
        self._worker: Optional[BaseWorker] = None
        self._resolution_mode: str = "FullHD"
        
        # Инициализация компонентов UI
        self._status_label: Optional[QLabel] = None
        self._toggle_button: Optional[QPushButton] = None
        self._resolution_label: Optional[QLabel] = None
        self._fullhd_button: Optional[QPushButton] = None
        self._quadhd_button: Optional[QPushButton] = None
        self._delay_entry: Optional[QLineEdit] = None
        self._counter_window: Optional[CounterWindow] = None
        self._log_window: Optional[LogWindow] = None
        self._counter_btn: Optional[QPushButton] = None
        self._log_btn: Optional[QPushButton] = None
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Инициализирует пользовательский интерфейс"""
        self.setWindowTitle(self._title)
        self.setFixedSize(self._window_width, self._window_height)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Строка состояния
        self._status_label = QLabel("Состояние: не активно")
        self._status_label.setStyleSheet(LABEL_STYLES["primary"])
        self._status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._status_label)
        
        # Фрейм разрешения экрана (если нужен)
        if self._has_resolution:
            self._add_resolution_frame(main_layout)
        
        # Фрейм задержки (если нужен)
        if self._has_delay:
            self._add_delay_frame(main_layout)
        
        # Дополнительные настройки (переопределяется в дочерних классах)
        self._add_custom_settings(main_layout)
        
        # Растяжка
        main_layout.addStretch(1)
        
        # Кнопка управления
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 10, 20, 10)
        
        self._toggle_button = QPushButton("Запустить")
        self._toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        self._toggle_button.clicked.connect(self._toggle_bot)
        control_layout.addWidget(self._toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)
        
        # Кнопка счетчика (если нужна)
        if self._has_counter:
            self._counter_window = CounterWindow(self._get_counter_text())
            self._counter_btn = QPushButton("Показать счётчик")
            self._counter_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
            self._counter_btn.clicked.connect(self._toggle_counter_window)
            main_layout.addWidget(self._counter_btn, alignment=Qt.AlignCenter)
        
        # Кнопка логов (если нужна)
        if self._has_log:
            log_layout = QHBoxLayout()
            log_layout.addStretch()
            
            self._log_window = LogWindow(f"{self._title} - Логи")
            self._log_btn = QPushButton("Показать логи")
            self._log_btn.setStyleSheet(BUTTON_STYLES["log_button"])
            self._log_btn.clicked.connect(self._toggle_log_window)
            log_layout.addWidget(self._log_btn)
            
            main_layout.addLayout(log_layout)
        
        self.setLayout(main_layout)
    
    def _add_resolution_frame(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет фрейм выбора разрешения экрана"""
        resolution_frame = QFrame()
        resolution_frame.setStyleSheet(FRAME_STYLES["frame"])
        resolution_layout = QVBoxLayout(resolution_frame)
        resolution_layout.setContentsMargins(15, 10, 15, 10)
        
        resolution_title = QLabel("Разрешение экрана:")
        resolution_title.setStyleSheet(LABEL_STYLES["secondary"])
        resolution_title.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(resolution_title)
        
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet(FRAME_STYLES["frame_inner"])
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(10, 5, 10, 5)
        
        self._fullhd_button = QPushButton("FullHD")
        self._fullhd_button.setStyleSheet(BUTTON_STYLES["primary_small"])
        self._fullhd_button.clicked.connect(lambda: self._set_resolution("FullHD"))
        buttons_layout.addWidget(self._fullhd_button)
        
        self._quadhd_button = QPushButton("QuadHD")
        self._quadhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
        self._quadhd_button.clicked.connect(lambda: self._set_resolution("QuadHD"))
        buttons_layout.addWidget(self._quadhd_button)
        
        resolution_layout.addWidget(buttons_frame)
        
        self._resolution_label = QLabel(f"Текущее: {self._resolution_mode}")
        self._resolution_label.setStyleSheet(LABEL_STYLES["muted"])
        self._resolution_label.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(self._resolution_label)
        
        parent_layout.addWidget(resolution_frame)
    
    def _add_delay_frame(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет фрейм ввода задержки"""
        delay_frame = QFrame()
        delay_frame.setStyleSheet(FRAME_STYLES["frame"])
        delay_layout = QHBoxLayout(delay_frame)
        delay_layout.setContentsMargins(20, 10, 20, 10)
        
        delay_label = QLabel("Задержка между нажатиями (мс):")
        delay_label.setStyleSheet(LABEL_STYLES["secondary"])
        delay_layout.addWidget(delay_label)
        
        self._delay_entry = QLineEdit()
        self._delay_entry.setText("120")
        self._delay_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self._delay_entry.setMaximumWidth(80)
        delay_layout.addWidget(self._delay_entry)
        delay_layout.addStretch()
        
        parent_layout.addWidget(delay_frame)
    
    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """
        Добавляет дополнительные настройки (переопределяется в дочерних классах)
        """
        pass
    
    def _set_resolution(self, mode: str) -> None:
        """Устанавливает разрешение экрана"""
        self._resolution_mode = mode
        if self._resolution_label:
            self._resolution_label.setText(f"Текущее: {self._resolution_mode}")
        
        # Обновляем стили кнопок
        active_style = self._get_active_resolution_style()
        if mode == "FullHD":
            if self._fullhd_button:
                self._fullhd_button.setStyleSheet(active_style)
            if self._quadhd_button:
                self._quadhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
        else:
            if self._fullhd_button:
                self._fullhd_button.setStyleSheet(BUTTON_STYLES["secondary_small"])
            if self._quadhd_button:
                self._quadhd_button.setStyleSheet(active_style)
    
    def _get_active_resolution_style(self) -> str:
        """Возвращает стиль для активной кнопки разрешения"""
        return BUTTON_STYLES["primary_small"].replace(
            "background-color: #2196F3;", "background-color: #4CAF50;"
        ).replace(
            "QPushButton:hover {", "QPushButton:hover { background-color: #45a049;"
        )
    
    def _toggle_bot(self) -> None:
        """Переключает состояние бота"""
        if self._running:
            self._stop_bot()
        else:
            self._start_bot()
    
    def _start_bot(self) -> None:
        """Запускает бота (переопределяется в дочерних классах)"""
        self._running = True
        if self._toggle_button:
            self._toggle_button.setText("Остановить")
            self._toggle_button.setStyleSheet(BUTTON_STYLES["danger"])
        
        if self._counter_window:
            self._counter_window.reset_counter()
            self._add_log("Счётчик сброшен")
    
    def _stop_bot(self) -> None:
        """Останавливает бота"""
        self._running = False
        if self._toggle_button:
            self._toggle_button.setText("Запустить")
            self._toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        
        if self._worker:
            self._worker.stop()
            self._worker.wait()
            self._worker = None
    
    def _toggle_counter_window(self) -> None:
        """Показывает/скрывает окно счетчика"""
        if not self._counter_window:
            return
            
        if self._counter_window.isVisible():
            self._counter_window.hide()
            if self._counter_btn:
                self._counter_btn.setText("Показать счётчик")
        else:
            self._counter_window.show()
            self._counter_window.move_to_top_right()
            if self._counter_btn:
                self._counter_btn.setText("Скрыть счётчик")
    
    def _toggle_log_window(self) -> None:
        """Показывает/скрывает окно логов"""
        if not self._log_window:
            return
            
        if self._log_window.isVisible():
            self._log_window.hide()
            if self._log_btn:
                self._log_btn.setText("Показать логи")
        else:
            self._log_window.show()
            self._log_window.move_to_bottom_right()
            if self._log_btn:
                self._log_btn.setText("Скрыть логи")
    
    def _add_log(self, message: str) -> None:
        """Добавляет сообщение в лог"""
        if self._log_window:
            self._log_window.add_log(message)
        else:
            print(f"[LOG] {message}")
    
    def _update_status(self, status: str) -> None:
        """Обновляет текст статуса"""
        if self._status_label:
            self._status_label.setText(f"Состояние: {status}")
    
    def _increment_counter(self) -> None:
        """Увеличивает счетчик"""
        if self._counter_window:
            self._counter_window.increment_counter()
    
    def _get_counter_text(self) -> str:
        """Возвращает текст для счетчика (переопределяется)"""
        return "Выполнено действий:"
    
    def _get_delay(self) -> int:
        """Возвращает значение задержки из поля ввода"""
        if self._delay_entry:
            try:
                return int(self._delay_entry.text())
            except ValueError:
                return 120
        return 120
    
    def _create_worker(self) -> Optional[BaseWorker]:
        """
        Создает рабочий поток (должен быть переопределен в дочерних классах)
        
        Returns:
            Экземпляр BaseWorker или None
        """
        return None
    
    def _load_settings(self) -> None:
        """Загружает настройки (переопределяется в дочерних классах)"""
        pass
    
    def _save_settings(self) -> None:
        """Сохраняет настройки (переопределяется в дочерних классах)"""
        pass
    
    def closeEvent(self, event) -> None:
        """Обработчик закрытия окна"""
        self._save_settings()
        if self._running:
            self._stop_bot()
        if self._counter_window:
            self._counter_window.close()
        if self._log_window:
            self._log_window.close()
        event.accept()