"""
Бот для автоматизации фермы (коровник)
"""

import sys
import time
import random
from typing import Optional

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QFrame, QWidget, QLineEdit
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.functions import press_key, check_color
from components.colors import colors
from components.coordinates import farm_cows_coordinate
from components.config_manager import config
from components.styles import FRAME_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES
from components.constants import (
    PRESS_KEY_A_D, COLOR_WHITE_MARKER, COLOR_TOLERANCE_HIGH,
    DEFAULT_DELAY_FARM_COWS, COLOR_DANGER, COLOR_WHITE
)


class FarmCowsWorker(BaseWorker):
    """Рабочий поток для коровника"""
    
    def __init__(self, resolution_mode: str, delay_between_presses: int, color_tolerance: int = 15):
        super().__init__()
        self._resolution_mode = resolution_mode
        self._delay_between_presses = delay_between_presses / 1000.0
        self._color_tolerance = color_tolerance
        
        self._coords = farm_cows_coordinate
        self._danger_color = COLOR_DANGER
        self._white_color = COLOR_WHITE
        self._marker_color = COLOR_WHITE_MARKER
        
        self._force_pause = False
        self._white_was_present = False
        self._last_key_pressed = None
    
    def run(self) -> None:
        """Основной цикл потока"""
        self.log_message.emit("Запуск потока коровника")
        self.status_updated.emit("Ожидание...")
        
        # Получаем координаты маркера коровы из настроек (исправлено!)
        marker_coords = self._coords[self._resolution_mode].get("cow_marker")
        if not marker_coords:
            self.log_message.emit("ОШИБКА: Не найдены координаты cow_marker в конфигурации")
            self.status_updated.emit("Ошибка: координаты не найдены")
            return
        
        self.log_message.emit(f"Координаты маркера: {marker_coords}")
    
        while self.is_running:
            # Используем координаты из настроек вместо жестко закодированных
            white_present = check_color(marker_coords, self._marker_color, tolerance=10)
            
            # Если белый цвет был и пропал - увеличиваем счетчик
            if self._white_was_present and not white_present:
                self.action_completed.emit()
                self.log_message.emit("Белый цвет пропал - +1 к счетчику")
                self._white_was_present = False
            
            if white_present:
                self._white_was_present = True
            
            # Пока есть белый цвет - работаем
            while white_present and self.is_running:
                # Приоритетная проверка опасного цвета
                if self._check_danger_color():
                    if not self._force_pause:
                        self._force_pause = True
                        self.status_updated.emit("ПАУЗА (опасный цвет)")
                        self.log_message.emit("ВНИМАНИЕ: Обнаружен опасный цвет")
                    
                    pause_time = random.uniform(5, 15)
                    self.status_updated.emit(f"Пауза {pause_time:.1f}с (опасный цвет)")
                    
                    pause_start = time.time()
                    while time.time() - pause_start < pause_time and self.is_running:
                        self.msleep(100)
                        if not self._check_danger_color():
                            self.log_message.emit("Опасный цвет пропал, досрочное завершение паузы")
                            break
                    
                    if not self._check_danger_color():
                        self._force_pause = False
                        self.status_updated.emit("Активно")
                        self.log_message.emit("Опасный цвет пропал, возобновление работы")
                    
                    white_present = check_color(marker_coords, self._marker_color, tolerance=10)
                    continue
                
                # Если была пауза, но опасный цвет все еще есть
                if self._force_pause:
                    if not self._check_danger_color():
                        self._force_pause = False
                        self.status_updated.emit("Активно")
                        self.log_message.emit("Опасный цвет пропал, возобновление работы")
                    else:
                        white_present = check_color(marker_coords, self._marker_color, tolerance=10)
                        continue
                
                # Проверка белых цветов для клавиш A и D
                a_detected = self._check_white_color("color_a")
                d_detected = self._check_white_color("color_d")
                
                if a_detected and d_detected:
                    self.msleep(50)
                elif a_detected:
                    press_key('a', boundary=PRESS_KEY_A_D)
                    self._last_key_pressed = 'A'
                    self.status_updated.emit("Нажата клавиша A")
                    time.sleep(self._delay_between_presses + random.uniform(0.005, 0.025))
                elif d_detected:
                    press_key('d', boundary=PRESS_KEY_A_D)
                    self._last_key_pressed = 'D'
                    self.status_updated.emit("Нажата клавиша D")
                    time.sleep(self._delay_between_presses + random.uniform(0.005, 0.025))
                else:
                    self.msleep(50)
                
                white_present = check_color(marker_coords, self._marker_color, tolerance=10)
            
            self.msleep(50)
        
        self.log_message.emit("Поток коровника остановлен")
    
    def _check_danger_color(self) -> bool:
        """Проверяет наличие опасного цвета"""
        try:
            coords = self._coords[self._resolution_mode].get("danger_color")
            if not coords:
                self.log_message.emit("ВНИМАНИЕ: Не найдены координаты danger_color")
                return False
            return check_color(coords, self._danger_color, self._color_tolerance)
        except Exception as e:
            self.log_message.emit(f"Ошибка при проверке опасного цвета: {e}")
            return False
    
    def _check_white_color(self, coord_key: str) -> bool:
        """Проверяет наличие белого цвета в указанных координатах"""
        try:
            coords = self._coords[self._resolution_mode].get(coord_key)
            if not coords:
                return False
            return check_color(coords, self._white_color, COLOR_TOLERANCE_HIGH)
        except Exception as e:
            self.log_message.emit(f"Ошибка при проверке белого цвета: {e}")
            return False


class FarmCowsApp(BaseBotApp):
    """Приложение для автоматизации коровника"""
    
    def __init__(self):
        self._color_tolerance = COLOR_TOLERANCE_HIGH
        self._detection_label: Optional[QLabel] = None
        self._info_label: Optional[QLabel] = None
    
        super().__init__(
            title="Ферма (коровник)",
            window_width=550,
            window_height=520,
            has_resolution=True,
            has_delay=True,
            has_log=True,
            has_counter=True
        )

    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет фрейм с информацией о детекции"""
        detection_frame = QFrame()
        detection_frame.setStyleSheet(FRAME_STYLES["frame"])
        detection_layout = QVBoxLayout(detection_frame)
        detection_layout.setContentsMargins(15, 10, 15, 10)
        
        self._detection_label = QLabel("Обнаружено: ничего")
        self._detection_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 8px;
                background-color: #3c3c3c;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        self._detection_label.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(self._detection_label)
        
        info_title = QLabel("Параметры детекции:")
        info_title.setStyleSheet(LABEL_STYLES["secondary"])
        info_title.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(info_title)
        
        danger_color = COLOR_DANGER
        white_color = COLOR_WHITE
        coords = farm_cows_coordinate["FullHD"]
        
        self._info_label = QLabel(
            f"Опасный цвет: RGB{danger_color}, Координаты: {coords['danger_color']}\n"
            f"Белый цвет (A): {coords['color_a']}, (D): {coords['color_d']}"
            # f"Допуск цвета: {self._color_tolerance}"
        )
        self._info_label.setStyleSheet(LABEL_STYLES["muted"])
        self._info_label.setAlignment(Qt.AlignCenter)
        self._info_label.setWordWrap(True)
        detection_layout.addWidget(self._info_label)
        
        parent_layout.addWidget(detection_frame)
    
    def _get_counter_text(self) -> str:
        return "Подоенно коров:"
    
    def _create_worker(self) -> Optional[BaseWorker]:
        return FarmCowsWorker(self._resolution_mode, self._get_delay(), self._color_tolerance)
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        try:
            delay = int(self._delay_entry.text()) if self._delay_entry else DEFAULT_DELAY_FARM_COWS
            if delay < 0:
                raise ValueError("Задержка не может быть отрицательной")
        except ValueError as e:
            self._update_status(f"Ошибка: {e}")
            return
        
        super()._start_bot()
        
        if self._detection_label:
            self._detection_label.setText("Обнаружено: ничего")
        
        self._worker = self._create_worker()
        if self._worker:
            self._worker.action_completed.connect(self._increment_counter)
            self._worker.log_message.connect(self._add_log)
            self._worker.status_updated.connect(self._update_status)
            self._worker.start()
            self._add_log(f"Бот запущен. Задержка: {delay} мс, Разрешение: {self._resolution_mode}")
    
    def _set_resolution(self, mode: str) -> None:
        """Устанавливает разрешение и обновляет информацию"""
        super()._set_resolution(mode)
        if self._info_label:
            coords = farm_cows_coordinate[mode]
            danger_color = COLOR_DANGER
            self._info_label.setText(
                f"Опасный цвет: RGB{danger_color}, Координаты: {coords['danger_color']}\n"
                f"Белый цвет (A): {coords['color_a']}, (D): {coords['color_d']}"
                # f"Допуск цвета: {self._color_tolerance}"
            )
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._resolution_mode = config.get("farm_cows", "resolution_mode", "FullHD")
        delay = config.get("farm_cows", "delay_between_presses", DEFAULT_DELAY_FARM_COWS)
        self._color_tolerance = config.get("farm_cows", "color_tolerance", COLOR_TOLERANCE_HIGH)
        
        if self._delay_entry:
            self._delay_entry.setText(str(delay))
        
        self._set_resolution(self._resolution_mode)
        
        counter_visible = config.get("farm_cows", "counter_visible", False)
        if counter_visible and self._counter_window and self._counter_btn:
            self._counter_window.show()
            self._counter_btn.setText("Скрыть счётчик")
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        config.set_multiple("farm_cows", {
            "resolution_mode": self._resolution_mode,
            "delay_between_presses": self._get_delay(),
            "color_tolerance": self._color_tolerance,
            "counter_visible": self._counter_window.isVisible() if self._counter_window else False
        })


def main():
    app = QApplication(sys.argv)
    window = FarmCowsApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()