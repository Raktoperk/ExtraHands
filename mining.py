"""
Бот для автоматизации шахты
"""

import sys
import time
import random
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.functions import press_key, check_color
from components.colors import colors
from components.coordinates import mining_coordinate
from components.config_manager import config
from components.constants import (
    PRESS_KEY_DURATION,
    ACTION_TIMEOUT,
    DEFAULT_DELAY_MINING,
    COLOR_TOLERANCE_NORMAL,
    COLOR_LIGHT_GREEN
)


class MiningWorker(BaseWorker):
    """Рабочий поток для шахты"""
    
    def __init__(self, resolution_mode: str, delay_between_presses: int, color_tolerance: int = COLOR_TOLERANCE_NORMAL):
        super().__init__()
        self._resolution_mode = resolution_mode
        self._delay_between_presses = delay_between_presses / 1000.0
        self._color_tolerance = color_tolerance
        
        self._target_coords = {
            "FullHD": mining_coordinate["FullHD"].get("mining_marker", (960, 495)),
            "QuadHD": mining_coordinate["QuadHD"].get("mining_marker", (1276, 671))
        }
        
        self._target_color = COLOR_LIGHT_GREEN
        self._is_processing = False
        self._action_start_time = 0
    
    def run(self) -> None:
        """Основной цикл потока"""
        self.log_message.emit("Запуск потока шахты")
        self.status_updated.emit("Ожидание зеленого цвета...")
        
        while self.is_running:
            green_detected = self._check_green_color()
            
            if green_detected:
                # Зеленый цвет обнаружен
                if not self._is_processing:
                    # Начинаем новое действие
                    self._is_processing = True
                    self._action_start_time = time.time()
                    self.status_updated.emit("Обнаружен зеленый цвет, начинаю копать...")
                    self.log_message.emit("Зеленый цвет обнаружен, начинаю нажатия E")
                
                # Нажимаем клавишу E с задержкой
                press_key('e', boundary=PRESS_KEY_DURATION)
                
                # Задержка между нажатиями + случайная погрешность
                delay = self._delay_between_presses + random.uniform(0.005, 0.015)
                time.sleep(delay)
                
                # Проверка таймаута (защита от бесконечного цикла)
                if time.time() - self._action_start_time > ACTION_TIMEOUT:
                    self.log_message.emit(f"ВНИМАНИЕ: Превышено время выполнения ({ACTION_TIMEOUT} сек)")
                    self.status_updated.emit("Таймаут, прерываю действие")
                    self._is_processing = False
                    continue
            
            else:
                # Зеленый цвет пропал
                if self._is_processing:
                    # Действие завершено - увеличиваем счетчик
                    self._is_processing = False
                    self.action_completed.emit()
                    self.status_updated.emit("Зеленый цвет пропал, действие завершено")
                    self.log_message.emit("Зеленый цвет пропал, +1 к счетчику")
                else:
                    # Небольшая пауза для снижения нагрузки CPU
                    self.msleep(50)
            
            # Небольшая пауза между итерациями цикла
            self.msleep(10)
        
        self.log_message.emit("Поток шахты остановлен")
    
    def _check_green_color(self) -> bool:
        """Проверяет наличие зеленого цвета"""
        x, y = self._target_coords[self._resolution_mode]
        return check_color((x, y), self._target_color, self._color_tolerance)


class MiningBotApp(BaseBotApp):
    """Приложение для автоматизации шахты"""
    
    def __init__(self):
        super().__init__(
            title="Шахта",
            window_width=550,
            window_height=450,
            has_resolution=True,
            has_delay=True,
            has_log=True,
            has_counter=True
        )
        self._color_tolerance = COLOR_TOLERANCE_NORMAL
    
    def _get_counter_text(self) -> str:
        return "Отнесено камней:"
    
    def _create_worker(self) -> Optional[BaseWorker]:
        return MiningWorker(self._resolution_mode, self._get_delay(), self._color_tolerance)
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        try:
            delay = int(self._delay_entry.text()) if self._delay_entry else DEFAULT_DELAY_MINING
            if delay < 0:
                raise ValueError("Задержка не может быть отрицательной")
        except ValueError as e:
            self._update_status(f"Ошибка: {e}")
            return
        
        super()._start_bot()
        
        self._worker = self._create_worker()
        if self._worker:
            self._worker.action_completed.connect(self._increment_counter)
            self._worker.log_message.connect(self._add_log)
            self._worker.status_updated.connect(self._update_status)
            self._worker.start()
            self._add_log(f"Бот запущен. Задержка: {delay} мс, Разрешение: {self._resolution_mode}")
            self._add_log(f"Координаты маркера: {mining_coordinate[self._resolution_mode].get('mining_marker')}")
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._resolution_mode = config.get("mining", "resolution_mode", "FullHD")
        delay = config.get("mining", "delay_between_presses", DEFAULT_DELAY_MINING)
        self._color_tolerance = config.get("mining", "color_tolerance", COLOR_TOLERANCE_NORMAL)
        
        if self._delay_entry:
            self._delay_entry.setText(str(delay))
        
        self._set_resolution(self._resolution_mode)
        
        counter_visible = config.get("mining", "counter_visible", False)
        if counter_visible and self._counter_window and self._counter_btn:
            self._counter_window.show()
            self._counter_btn.setText("Скрыть счётчик")
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        config.set_multiple("mining", {
            "resolution_mode": self._resolution_mode,
            "delay_between_presses": self._get_delay(),
            "color_tolerance": self._color_tolerance,
            "counter_visible": self._counter_window.isVisible() if self._counter_window else False
        })


def main():
    app = QApplication(sys.argv)
    window = MiningBotApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()