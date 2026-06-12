"""
Бот для автоматизации готовки
"""

import sys
import random
import time
from typing import List, Tuple, Optional

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit, QGridLayout,
                             QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.coordinates import cooking_coordinate
from components.config_manager import config
from components.styles import FRAME_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES, GROUPBOX_STYLES


class CookingWorker(BaseWorker):
    """Рабочий поток для готовки"""
    
    cycle_completed = BaseWorker.action_completed
    
    def __init__(self, sequence: List[Tuple[str, Tuple[int, int]]], cycles: int, resolution_mode: str = "FullHD"):
        super().__init__()
        self._sequence = sequence
        self._cycles = cycles
        self._resolution_mode = resolution_mode
        self._cells = cooking_coordinate.get(resolution_mode, cooking_coordinate["FullHD"])
    
    def run(self) -> None:
        """Основной метод потока"""
        self.log_message.emit("Начинаем готовку...")
        self.status_updated.emit("Начинаем готовку...")
        time.sleep(2)
        
        try:
            for cycle in range(self._cycles):
                if not self.is_running:
                    break
                
                self.status_updated.emit(f"Цикл {cycle + 1}/{self._cycles}")
                
                # Проверка паузы
                while self._paused and self.is_running:
                    self.msleep(500)
                
                if not self.is_running:
                    break
                
                # Выполнение последовательности
                for action, coords in self._sequence:
                    if not self.is_running:
                        break
                    
                    while self._paused and self.is_running:
                        self.msleep(500)
                    
                    if not self.is_running:
                        break
                    
                    self._perform_click(coords)
                
                if not self.is_running:
                    break
                
                # Кнопка готовки
                if "start_cooking" in self._cells:
                    self._perform_click(self._cells["start_cooking"], left_click=True)
                    time.sleep(1.0)
                
                self.cycle_completed.emit()
                
                # Пауза между циклами
                if cycle < self._cycles - 1 and self.is_running:
                    sleep_time = random.uniform(6.0, 7.0)
                    self.safe_sleep(sleep_time)
            
            if not self.is_running:
                self.status_updated.emit("Готовка остановлена")
            else:
                self.status_updated.emit(f"Готовка завершена! Циклов: {self._cycles}")
        
        except Exception as e:
            self.error_occurred.emit(str(e))
        
        self.finished_signal.emit()
        self.log_message.emit("Поток готовки остановлен")
    
    def _perform_click(self, coords: Tuple[int, int], left_click: bool = False) -> None:
        """Выполняет клик с случайным смещением"""
        try:
            import pyautogui
            
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            x = coords[0] + offset_x
            y = coords[1] + offset_y
            
            pyautogui.moveTo(x, y, duration=random.uniform(0.2, 0.4))
            pyautogui.click(button='left' if left_click else 'right')
            time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            self.log_message.emit(f"Ошибка при клике: {e}")


class CookingBotApp(BaseBotApp):
    """Приложение для автоматизации готовки"""
    
    def __init__(self):
        super().__init__(
            title="Готовка",
            window_width=800,
            window_height=880,
            has_resolution=True,
            has_delay=False,
            has_log=False,
            has_counter=True
        )
        self._sequence: List[Tuple[str, Tuple[int, int]]] = []
        self._cycles_entry: Optional[QLineEdit] = None
        self._sequence_label: Optional[QLabel] = None
        self._start_stop_btn: Optional[QPushButton] = None
    
    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет настройки готовки"""
        # Фрейм настроек
        settings_frame = QFrame()
        settings_frame.setStyleSheet(FRAME_STYLES["frame"])
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        
        # Количество циклов
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel("Количество циклов:")
        cycles_label.setStyleSheet(LABEL_STYLES["secondary"])
        cycles_layout.addWidget(cycles_label)
        
        self._cycles_entry = QLineEdit("1")
        self._cycles_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self._cycles_entry.setMaximumWidth(80)
        cycles_layout.addWidget(self._cycles_entry)
        cycles_layout.addStretch()
        settings_layout.addLayout(cycles_layout)
        
        parent_layout.addWidget(settings_frame)
        
        # Фрейм инструментов
        tools_frame = QFrame()
        tools_frame.setStyleSheet(FRAME_STYLES["frame"])
        tools_layout = QVBoxLayout(tools_frame)
        tools_layout.setContentsMargins(15, 10, 15, 10)
        
        # Инструменты
        tools_label = QLabel("Инструменты:")
        tools_label.setStyleSheet(LABEL_STYLES["secondary"])
        tools_layout.addWidget(tools_label)
        
        tools_buttons = QHBoxLayout()
        for text, action in [("Нож", "knife"), ("Венчик", "whisk"), ("Огонь", "fire")]:
            btn = QPushButton(text)
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, a=action: self._record_action(a))
            tools_buttons.addWidget(btn)
        tools_layout.addLayout(tools_buttons)
        
        # Ячейки
        cells_label = QLabel("Ячейки:")
        cells_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 10px;")
        tools_layout.addWidget(cells_label)
        
        cells_grid = QGridLayout()
        cells_grid.setSpacing(5)
        
        # Вода
        water_btn = QPushButton("Вода")
        water_btn.setStyleSheet(BUTTON_STYLES["primary_small"])
        water_btn.clicked.connect(lambda: self._record_action("water"))
        cells_grid.addWidget(water_btn, 0, 0)
        
        # Ячейки 1-2
        for i in range(1, 3):
            btn = QPushButton(f"Ячейка {i}")
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, c=f"cell_{i}": self._record_cell_action(c))
            cells_grid.addWidget(btn, 0, i)
        
        # Ячейки 3-20
        for i in range(3, 21):
            row = ((i - 3) // 3) + 1
            col = (i - 3) % 3
            btn = QPushButton(f"Ячейка {i}")
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, c=f"cell_{i}": self._record_cell_action(c))
            cells_grid.addWidget(btn, row, col)
        
        tools_layout.addLayout(cells_grid)
        parent_layout.addWidget(tools_frame)
        
        # Фрейм управления
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        # Последовательность
        seq_group = QGroupBox("Записанная последовательность:")
        seq_group.setStyleSheet(GROUPBOX_STYLES["standard"])
        seq_layout = QVBoxLayout()
        
        self._sequence_label = QLabel("Пусто")
        self._sequence_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                padding: 5px;
                background-color: #2b2b2b;
                border-radius: 3px;
            }
        """)
        self._sequence_label.setWordWrap(True)
        seq_layout.addWidget(self._sequence_label)
        seq_group.setLayout(seq_layout)
        control_layout.addWidget(seq_group, 2)
        
        # Кнопки управления
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)
        
        self._start_stop_btn = QPushButton("Запустить")
        self._start_stop_btn.setStyleSheet(BUTTON_STYLES["primary"])
        self._start_stop_btn.clicked.connect(self._toggle_cooking)
        buttons_layout.addWidget(self._start_stop_btn)
        
        # Кнопки паузы
        pause_layout = QHBoxLayout()
        pause_layout.setSpacing(5)
        
        resume_btn = QPushButton("Продолжить (F7)")
        resume_btn.setStyleSheet(BUTTON_STYLES["success"])
        resume_btn.clicked.connect(self._resume_cooking)
        pause_layout.addWidget(resume_btn)
        
        pause_btn = QPushButton("Пауза (F8)")
        pause_btn.setStyleSheet(BUTTON_STYLES["success"])
        pause_btn.clicked.connect(self._pause_cooking)
        pause_layout.addWidget(pause_btn)
        
        buttons_layout.addLayout(pause_layout)
        
        reset_btn = QPushButton("Сбросить последовательность")
        reset_btn.setStyleSheet(BUTTON_STYLES["danger_small"])
        reset_btn.clicked.connect(self._reset_sequence)
        buttons_layout.addWidget(reset_btn)
        
        control_layout.addLayout(buttons_layout, 1)
        parent_layout.addWidget(control_frame)
    
    def _get_counter_text(self) -> str:
        return "Приготовлено еды:"
    
    def _create_worker(self) -> Optional[BaseWorker]:
        return CookingWorker(self._sequence, self._get_cycles(), self._resolution_mode)
    
    def _get_cycles(self) -> int:
        try:
            return int(self._cycles_entry.text()) if self._cycles_entry else 1
        except ValueError:
            return 1
    
    def _record_action(self, action: str) -> None:
        """Запись действия"""
        cells = cooking_coordinate.get(self._resolution_mode, cooking_coordinate["FullHD"])
        if action in cells:
            self._sequence.append((action, cells[action]))
            self._update_sequence_display()
    
    def _record_cell_action(self, cell_key: str) -> None:
        """Запись ячейки"""
        cells = cooking_coordinate.get(self._resolution_mode, cooking_coordinate["FullHD"])
        if cell_key in cells:
            self._sequence.append((cell_key, cells[cell_key]))
            self._update_sequence_display()
    
    def _update_sequence_display(self) -> None:
        """Обновление отображения последовательности"""
        if self._sequence_label:
            text = ", ".join([a for a, _ in self._sequence])
            self._sequence_label.setText(text if text else "Пусто")
    
    def _reset_sequence(self) -> None:
        """Сброс последовательности"""
        self._sequence = []
        self._update_sequence_display()
        self._update_status("Последовательность сброшена")
    
    def _pause_cooking(self) -> None:
        """Пауза готовки"""
        if self._worker and hasattr(self._worker, 'pause'):
            self._worker.pause()
            self._update_status("На паузе (F7 - продолжить)")
    
    def _resume_cooking(self) -> None:
        """Продолжение готовки"""
        if self._worker and hasattr(self._worker, 'resume'):
            self._worker.resume()
            self._update_status("Активно")
    
    def _toggle_cooking(self) -> None:
        """Запуск/остановка готовки"""
        if self._running:
            self._stop_bot()
        else:
            self._start_cooking()
    
    def _start_cooking(self) -> None:
        """Запуск готовки"""
        if not self._sequence:
            QMessageBox.warning(self, "Ошибка", "Последовательность пуста!")
            return
        
        try:
            cycles = int(self._cycles_entry.text()) if self._cycles_entry else 1
            if cycles <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректное число циклов")
            return
        
        if self._counter_window:
            self._counter_window.reset_counter()
        
        self._running = True
        if self._start_stop_btn:
            self._start_stop_btn.setText("Остановить")
            self._start_stop_btn.setStyleSheet(BUTTON_STYLES["danger"])
        
        self._worker = self._create_worker()
        if self._worker:
            self._worker.cycle_completed.connect(self._increment_counter)
            self._worker.log_message.connect(self._add_log)
            self._worker.status_updated.connect(self._update_status)
            self._worker.finished_signal.connect(self._on_cooking_finished)
            self._worker.error_occurred.connect(self._on_cooking_error)
            self._worker.start()
            self._update_status("Начинаем готовку...")
    
    def _on_cooking_finished(self) -> None:
        """Обработка завершения готовки"""
        self._running = False
        if self._start_stop_btn:
            self._start_stop_btn.setText("Запустить")
            self._start_stop_btn.setStyleSheet(BUTTON_STYLES["primary"])
    
    def _on_cooking_error(self, error_msg: str) -> None:
        """Обработка ошибки готовки"""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при готовке: {error_msg}")
        self._stop_bot()
    
    def keyPressEvent(self, event) -> None:
        """Обработка горячих клавиш"""
        if event.key() == Qt.Key_F7:
            self._resume_cooking()
        elif event.key() == Qt.Key_F8:
            self._pause_cooking()
        else:
            super().keyPressEvent(event)
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._resolution_mode = config.get("cooking", "resolution_mode", "FullHD")
        cycles = config.get("cooking", "cycles", 1)
        
        if self._cycles_entry:
            self._cycles_entry.setText(str(cycles))
        
        self._set_resolution(self._resolution_mode)
        
        saved_sequence = config.load_sequence("cooking")
        if saved_sequence:
            cells = cooking_coordinate.get(self._resolution_mode, cooking_coordinate["FullHD"])
            for action in saved_sequence:
                if action in cells:
                    self._sequence.append((action, cells[action]))
            self._update_sequence_display()
        
        counter_visible = config.get("cooking", "counter_visible", False)
        if counter_visible and self._counter_window and self._counter_btn:
            self._counter_window.show()
            self._counter_btn.setText("Скрыть счётчик")
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        sequence_names = [a for a, _ in self._sequence]
        config.save_sequence("cooking", sequence_names)
        
        config.set_multiple("cooking", {
            "resolution_mode": self._resolution_mode,
            "cycles": self._get_cycles(),
            "counter_visible": self._counter_window.isVisible() if self._counter_window else False
        })


def main():
    app = QApplication(sys.argv)
    window = CookingBotApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()