from components.functions import press_key, toMS

import random
import time
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QWaitCondition, QMutex
from PyQt5.QtGui import QFont

# Импорт стилей
try:
    from components.styles import *
except ImportError:
    # Запасные значения если файл стилей не найден
    from components.styles import (
        COLORS, WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, 
        CHECKBOX_STYLES, COUNTER_WINDOW_STYLES
    )

keys = ['w', 'a', 's', 'd']
time_between_keys = (toMS(300), toMS(450))
time_between_cycles = (60, 180)
clamping_time = {
    'fast': (toMS(30), toMS(60)),
    'standard': (toMS(900), 1)
}

class BotThread(QThread):
    """Поток для работы бота с безопасной остановкой"""
    state_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.fast_mode = False
        self.condition = QWaitCondition()
        self.mutex = QMutex()
        self.paused = False
        
    def run(self):
        self.state_changed.emit("активно")
        time.sleep(3)  # Время на открытие окна с игрой

        while self.running:
            for _ in range(random.randint(1, 6)):
                if not self.running:
                    break
                    
                # Выбор скорости зажатия в зависимости от режима
                mode = 'fast' if self.fast_mode else 'standard'
                press_key(random.choice(keys), clamping_time[mode])
                
                # Ожидание с проверкой остановки
                wait_time = random.uniform(*time_between_keys)
                if not self.sleep_with_check(wait_time):
                    break
            
            if not self.running:
                break
                
            # Ожидание между циклами с проверкой остановки
            wait_time = random.uniform(*time_between_cycles)
            if not self.sleep_with_check(wait_time):
                break
        
        self.state_changed.emit("не активно")
    
    def sleep_with_check(self, seconds):
        """Безопасный sleep с проверкой флага остановки"""
        end_time = time.time() + seconds
        while time.time() < end_time and self.running:
            # Проверка каждые 0.1 секунды для быстрой реакции на остановку
            sleep_time = min(0.1, end_time - time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)
        return self.running
    
    def start_bot(self):
        self.running = True
        if not self.isRunning():
            self.start()
    
    def stop_bot(self):
        """Остановка бота с немедленным завершением"""
        self.running = False
        # Сигнал выхода из ожиданий
        self.condition.wakeAll()
        self.wait(1000)  # Ожидание до 1 секунды для завершения
    
    def set_fast_mode(self, enabled):
        """Установить режим быстрого зажатия"""
        self.fast_mode = enabled

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.bot_thread = BotThread()
        self.bot_active = False
        self.init_ui()
        self.bot_thread.state_changed.connect(self.update_state_label)
    
    def init_ui(self):
        # Настройки окна
        self.setWindowTitle('AFK+')
        self.move(150, 150)
        self.setFixedSize(400, 200)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Заголовок
        title_label = QLabel("AFK+")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(WINDOW_STYLES["title"])

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        main_layout.addWidget(title_label)
        
        # Сетка для состояния
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(10)
        grid_widget.setLayout(grid_layout)
        
        # Метка состояния
        label_state = QLabel("Текущее состояние:")
        label_state.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_state.setStyleSheet(LABEL_STYLES["secondary"])
        
        self.label_status = QLabel("не активно")
        self.label_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_status.setStyleSheet(LABEL_STYLES["primary"])
        
        grid_layout.addWidget(label_state, 0, 0)
        grid_layout.addWidget(self.label_status, 0, 1)
        
        # Добавляем метку состояния
        main_layout.addWidget(grid_widget)
        
        # Контейнер для центрирования чек-бокса
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 20, 0, 0)
        checkbox_container.setLayout(checkbox_layout)
        
        # Чек-бокс быстрого режима
        self.fast_mode_checkbox = QCheckBox("Быстрое зажатие клавиш")
        self.fast_mode_checkbox.setStyleSheet(CHECKBOX_STYLES["small"])
        self.fast_mode_checkbox.stateChanged.connect(self.toggle_fast_mode)
        
        # Центрирование чек-бокса
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.fast_mode_checkbox)
        checkbox_layout.addStretch()
        
        main_layout.addWidget(checkbox_container)
        
        # Контейнер для кнопки
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_container.setLayout(button_layout)
        
        # Переключаемая кнопка
        self.toggle_btn = QPushButton("Включить")
        self.toggle_btn.setFixedWidth(120)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.setStyleSheet(BUTTON_STYLES["primary"])
        self.toggle_btn.clicked.connect(self.toggle_bot)
        
        # Центрирование кнопки
        button_layout.addStretch()
        button_layout.addWidget(self.toggle_btn)
        button_layout.addStretch()
        
        main_layout.addWidget(button_container)
        
        # Растяжку снизу
        main_layout.addStretch()
    
    def toggle_fast_mode(self, state):
        """Переключение режима быстрого зажатия"""
        enabled = state == Qt.Checked
        self.bot_thread.set_fast_mode(enabled)
    
    def toggle_bot(self):
        if not self.bot_active:
            # Включение бота
            self.bot_thread.start_bot()
            self.toggle_btn.setText("Выключить")
            self.toggle_btn.setStyleSheet(BUTTON_STYLES["danger"])
            self.bot_active = True
        else:
            # Выключение бота
            self.bot_thread.stop_bot()
            self.toggle_btn.setText("Включить")
            self.toggle_btn.setStyleSheet(BUTTON_STYLES["primary"])
            self.bot_active = False
    
    def closeEvent(self, event):
        """Обработчик закрытия окна - останавливаем поток"""
        if self.bot_active:
            self.bot_thread.stop_bot()
        event.accept()
    
    @pyqtSlot(str)
    def update_state_label(self, text):
        """Обновить текст метки состояния"""
        self.label_status.setText(text)

def main():
    # Приложение
    app = QApplication(sys.argv)
    
    # Показ окна
    window = MainWindow()
    window.show()
    
    # Запуск главного цикла
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()