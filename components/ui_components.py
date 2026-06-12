"""
Общие UI компоненты для всех ботов
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QGroupBox, QPushButton, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor
from datetime import datetime

from components.styles import COLORS, COUNTER_WINDOW_STYLES, WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES, GROUPBOX_STYLES, FRAME_STYLES


class CounterWindow(QWidget):
    """
    Маленькое окно счетчика поверх всех окон
    Может быть скрыто, но продолжает подсчет
    """
    
    def __init__(self, text: str = "Выполнено действий:", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._counter = 0
        self._text = text
        self._is_hidden = True
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Инициализирует интерфейс окна счетчика"""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основной фрейм
        main_frame = QFrame(self)
        main_frame.setStyleSheet(COUNTER_WINDOW_STYLES["frame"])
        
        # Layout
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Текст
        self._text_label = QLabel(self._text)
        self._text_label.setStyleSheet(COUNTER_WINDOW_STYLES["text"])
        self._text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self._text_label)
        
        # Счетчик
        self._counter_label = QLabel("0")
        self._counter_label.setStyleSheet(COUNTER_WINDOW_STYLES["counter"])
        self._counter_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self._counter_label)
        
        layout.addStretch()
        
        # Устанавливаем layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Размер окна
        self.setFixedSize(280, 48)
        self.move_to_top_right()
        
        # Изначально скрыто
        self.hide()
    
    def paintEvent(self, event) -> None:
        """Отрисовка закругленных углов"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(COLORS["bg_medium"])))
        painter.setPen(Qt.NoPen)
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)
        
        # Рамка
        painter.setPen(QColor(COLORS["border"]))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 10, 10)
    
    def move_to_top_right(self) -> None:
        """Помещает окно в правый верхний угол"""
        screen = QApplication.desktop().availableGeometry()
        x = screen.width() - self.width() - 20
        y = 10
        self.move(x, y)
    
    def increment_counter(self) -> None:
        """Увеличивает счетчик на 1"""
        self._counter += 1
        self._update_display()
    
    def reset_counter(self) -> None:
        """Сбрасывает счетчик"""
        self._counter = 0
        self._update_display()
    
    def set_counter(self, value: int) -> None:
        """Устанавливает значение счетчика"""
        self._counter = value
        self._update_display()
    
    def get_counter(self) -> int:
        """Возвращает текущее значение счетчика"""
        return self._counter
    
    def _update_display(self) -> None:
        """Обновляет отображение счетчика"""
        self._counter_label.setText(str(self._counter))
    
    def mousePressEvent(self, event) -> None:
        """Обработка перемещения окна"""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event) -> None:
        """Перемещение окна"""
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_position'):
            self.move(event.globalPos() - self._drag_position)
            event.accept()


class LogWindow(QWidget):
    """
    Окно для отображения логов и ошибок
    Поддерживает разделение на обычные логи и ошибки
    """
    
    def __init__(self, title: str = "Логи", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._title = title
        self._log_count = 0
        self._error_count = 0
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Инициализирует интерфейс окна логов"""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        self.setWindowTitle(self._title)
        self.setFixedSize(700, 400)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Верхняя панель
        top_panel = QHBoxLayout()
        
        clear_all_btn = QPushButton("Очистить всё")
        clear_all_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
        clear_all_btn.clicked.connect(self.clear_all_logs)
        top_panel.addWidget(clear_all_btn)
        
        clear_errors_btn = QPushButton("Очистить ошибки")
        clear_errors_btn.setStyleSheet(BUTTON_STYLES["danger_small"])
        clear_errors_btn.clicked.connect(self.clear_errors)
        top_panel.addWidget(clear_errors_btn)
        
        top_panel.addStretch()
        main_layout.addLayout(top_panel)
        
        # Основное содержимое (логи и ошибки)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Логи
        log_group = QGroupBox("Логи")
        log_group.setStyleSheet(GROUPBOX_STYLES["standard"])
        log_layout = QVBoxLayout(log_group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(INPUT_STYLES["text_edit"])
        log_layout.addWidget(self._log_text)
        
        # Ошибки
        error_group = QGroupBox("Ошибки")
        error_group.setStyleSheet(GROUPBOX_STYLES["error"])
        error_layout = QVBoxLayout(error_group)
        
        self._error_text = QTextEdit()
        self._error_text.setReadOnly(True)
        self._error_text.setStyleSheet(INPUT_STYLES["text_edit_error"])
        error_layout.addWidget(self._error_text)
        
        content_layout.addWidget(log_group, 1)
        content_layout.addWidget(error_group, 1)
        main_layout.addLayout(content_layout)
        
        # Статистика
        stats_layout = QHBoxLayout()
        
        self._log_count_label = QLabel("Логов: 0")
        self._log_count_label.setStyleSheet(LABEL_STYLES["status"])
        stats_layout.addWidget(self._log_count_label)
        
        self._error_count_label = QLabel("Ошибок: 0")
        self._error_count_label.setStyleSheet(LABEL_STYLES["status_error"])
        stats_layout.addWidget(self._error_count_label)
        
        stats_layout.addStretch()
        
        copy_errors_btn = QPushButton("Копировать ошибки")
        copy_errors_btn.setStyleSheet(BUTTON_STYLES["primary_small"])
        copy_errors_btn.clicked.connect(self._copy_errors_to_clipboard)
        stats_layout.addWidget(copy_errors_btn)
        
        main_layout.addLayout(stats_layout)
        self.setLayout(main_layout)
    
    def move_to_bottom_right(self) -> None:
        """Помещает окно в правый нижний угол"""
        screen = QApplication.desktop().availableGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 20
        self.move(x, y)
    
    def add_log(self, message: str) -> None:
        """Добавляет сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._log_text.append(log_entry)
        self._scroll_to_bottom(self._log_text)
        
        self._log_count += 1
        self._log_count_label.setText(f"Логов: {self._log_count}")
        
        # Проверяем, является ли сообщение ошибкой
        if self._is_error_message(message):
            self._add_error(message)
    
    def add_error(self, message: str) -> None:
        """Добавляет сообщение об ошибке"""
        self._add_error(message)
    
    def _add_error(self, message: str) -> None:
        """Внутренний метод добавления ошибки"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_entry = f"[{timestamp}] {message}"
        self._error_text.append(error_entry)
        self._scroll_to_bottom(self._error_text)
        
        self._error_count += 1
        self._error_count_label.setText(f"Ошибок: {self._error_count}")
    
    def clear_all_logs(self) -> None:
        """Очищает все логи и ошибки"""
        self._log_text.clear()
        self._error_text.clear()
        self._log_count = 0
        self._error_count = 0
        self._log_count_label.setText("Логов: 0")
        self._error_count_label.setText("Ошибок: 0")
    
    def clear_errors(self) -> None:
        """Очищает только ошибки"""
        self._error_text.clear()
        self._error_count = 0
        self._error_count_label.setText("Ошибок: 0")
    
    def get_logs(self) -> str:
        """Возвращает все логи"""
        return self._log_text.toPlainText()
    
    def get_errors(self) -> str:
        """Возвращает все ошибки"""
        return self._error_text.toPlainText()
    
    @staticmethod
    def _is_error_message(message: str) -> bool:
        """Проверяет, является ли сообщение ошибкой"""
        error_keywords = ['ОШИБКА', 'ERROR', 'EXCEPTION', 'FAIL', 'FAILED', 
                         'КРИТИЧЕСКАЯ', 'WARNING', 'ВНИМАНИЕ']
        return any(keyword in message.upper() for keyword in error_keywords)
    
    @staticmethod
    def _scroll_to_bottom(text_edit: QTextEdit) -> None:
        """Прокручивает текстовое поле до конца"""
        scrollbar = text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _copy_errors_to_clipboard(self) -> None:
        """Копирует ошибки в буфер обмена"""
        errors = self._error_text.toPlainText()
        if errors:
            clipboard = QApplication.clipboard()
            clipboard.setText(errors)
            
            # Визуальное подтверждение
            btn = self.sender()
            if btn:
                original_text = btn.text()
                btn.setText("Скопировано!")
                QTimer.singleShot(1500, lambda: btn.setText(original_text))