"""
Бот для предотвращения AFK (Anti-AFK)
"""

import sys
import random
import time
from typing import List

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QLabel, QPushButton, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont

from components.base_bot import BaseWorker
from components.functions import press_key
from components.config_manager import config
from components.styles import WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, CHECKBOX_STYLES


class AntiAFKWorker(BaseWorker):
    """Рабочий поток для Anti-AFK"""
    
    state_changed = BaseWorker.status_updated
    
    def __init__(self):
        super().__init__()
        self._fast_mode = False
        
        self._keys: List[str] = ['w', 'a', 's', 'd']
        self._time_between_keys: tuple = (0.3, 0.45)
        self._time_between_cycles: tuple = (60, 180)
        self._clamping_time: dict = {
            'fast': (0.03, 0.06),
            'standard': (0.9, 1.0)
        }
    
    def set_fast_mode(self, enabled: bool) -> None:
        """Устанавливает быстрый режим"""
        self._fast_mode = enabled
    
    def run(self) -> None:
        """Основной цикл потока"""
        self.status_updated.emit("активно")
        time.sleep(3)
        
        while self.is_running:
            for _ in range(random.randint(1, 6)):
                if not self.is_running:
                    break
                
                mode = 'fast' if self._fast_mode else 'standard'
                press_key(random.choice(self._keys), self._clamping_time[mode])
                
                wait = random.uniform(*self._time_between_keys)
                self.safe_sleep(wait)
            
            if not self.is_running:
                break
            
            wait = random.uniform(*self._time_between_cycles)
            self.safe_sleep(wait)
        
        self.status_updated.emit("не активно")


class MainWindow(QMainWindow):
    """Главное окно Anti-AFK"""
    
    def __init__(self):
        super().__init__()
        self._worker = AntiAFKWorker()
        self._bot_active = False
        self._init_ui()
        self._worker.state_changed.connect(self._update_state_label)
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        self.setWindowTitle('AFK+')
        self.move(150, 150)
        self.setFixedSize(400, 200)
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        title_label = QLabel("AFK+")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(WINDOW_STYLES["title"])
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        central.setLayout(main_layout)
        main_layout.addWidget(title_label)
        
        # Статус
        grid = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid.setLayout(grid_layout)
        
        state_label = QLabel("Текущее состояние:")
        state_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        state_label.setStyleSheet(LABEL_STYLES["secondary"])
        
        self._status_label = QLabel("не активно")
        self._status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._status_label.setStyleSheet(LABEL_STYLES["primary"])
        
        grid_layout.addWidget(state_label, 0, 0)
        grid_layout.addWidget(self._status_label, 0, 1)
        main_layout.addWidget(grid)
        
        # Чекбокс быстрого режима
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 20, 0, 0)
        checkbox_container.setLayout(checkbox_layout)
        
        self._fast_mode_cb = QCheckBox("Быстрое зажатие клавиш")
        self._fast_mode_cb.setStyleSheet(CHECKBOX_STYLES["small"])
        self._fast_mode_cb.stateChanged.connect(self._toggle_fast_mode)
        
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self._fast_mode_cb)
        checkbox_layout.addStretch()
        main_layout.addWidget(checkbox_container)
        
        # Кнопка
        btn_container = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_container.setLayout(btn_layout)
        
        self._toggle_btn = QPushButton("Включить")
        self._toggle_btn.setFixedSize(120, 40)
        self._toggle_btn.setStyleSheet(BUTTON_STYLES["primary"])
        self._toggle_btn.clicked.connect(self._toggle_bot)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self._toggle_btn)
        btn_layout.addStretch()
        main_layout.addWidget(btn_container)
        main_layout.addStretch()
    
    def _toggle_fast_mode(self, state: int) -> None:
        """Переключение быстрого режима"""
        self._worker.set_fast_mode(state == Qt.Checked)
    
    def _toggle_bot(self) -> None:
        """Включение/выключение бота"""
        if not self._bot_active:
            self._worker.start()
            self._toggle_btn.setText("Выключить")
            self._toggle_btn.setStyleSheet(BUTTON_STYLES["danger"])
            self._bot_active = True
        else:
            self._worker.stop()
            self._worker.wait()
            self._toggle_btn.setText("Включить")
            self._toggle_btn.setStyleSheet(BUTTON_STYLES["primary"])
            self._bot_active = False
    
    def _load_settings(self) -> None:
        """Загрузка настроек"""
        fast_mode = config.get("antiafk", "fast_mode", False)
        self._fast_mode_cb.setChecked(fast_mode)
        self._worker.set_fast_mode(fast_mode)
    
    def _save_settings(self) -> None:
        """Сохранение настроек"""
        config.set("antiafk", "fast_mode", self._fast_mode_cb.isChecked())
    
    @pyqtSlot(str)
    def _update_state_label(self, text: str) -> None:
        """Обновление статуса"""
        self._status_label.setText(text)
    
    def closeEvent(self, event) -> None:
        """Обработчик закрытия"""
        self._save_settings()
        if self._bot_active:
            self._worker.stop()
            self._worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()