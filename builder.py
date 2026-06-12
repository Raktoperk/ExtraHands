"""
Бот для автоматизации строительства
"""

import os
import sys
import time
import random
from typing import Optional

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QWidget
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.functions import press_key, check_color
from components.colors import colors
from components.coordinates import builder_coordinate
from components.config_manager import config
from components.image_processor import OptimizedImageFinder
from components.styles import FRAME_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES
from components.constants import (
    PRESS_KEY_DURATION,
    ACTION_TIMEOUT,
    DEFAULT_DELAY_BUILDER,
    COLOR_TOLERANCE_NORMAL,
    IMAGE_CONFIDENCE_STRICT,
    SMOOTHING_SIZE,
    COLOR_LIGHT_GREEN
)


# Путь к папке с изображениями клавиш
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KEYS_DIR = os.path.join(BASE_DIR, 'assets', 'keys')


class BuilderWorker(BaseWorker):
    """Рабочий поток для строительства"""
    
    def __init__(self, resolution_mode: str, delay_between_presses: int, color_tolerance: int = COLOR_TOLERANCE_NORMAL):
        super().__init__()
        self._resolution_mode = resolution_mode
        self._delay_between_presses = delay_between_presses / 1000.0
        self._color_tolerance = color_tolerance
        
        self._builder_coords = {
            "FullHD": builder_coordinate["FullHD"].get("builder_marker", (765, 496)),
            "QuadHD": builder_coordinate["QuadHD"].get("builder_marker", (1084, 674))
        }
        
        self._target_color = COLOR_LIGHT_GREEN
        self._current_key: Optional[str] = None
        self._is_processing = False
        self._image_finder: Optional[OptimizedImageFinder] = None
        
        # Область поиска для клавиш (расширенная область)
        self._search_area = (700, 400, 1300, 800)  # left, top, right, bottom
        
    def run(self) -> None:
        """Основной цикл потока"""
        self.log_message.emit("Запуск потока строительства")
        self.status_updated.emit("Ожидание зеленого цвета...")
        
        # Проверяем наличие папки с изображениями
        if not os.path.exists(KEYS_DIR):
            self.log_message.emit(f"ОШИБКА: Папка с изображениями не найдена: {KEYS_DIR}")
            self.status_updated.emit("Ошибка: папка keys не найдена")
            return
        
        # Проверяем наличие файлов клавиш
        required_keys = ['e.png', 'f.png', 'h.png']
        missing_keys = []
        for key in required_keys:
            key_path = os.path.join(KEYS_DIR, key)
            if not os.path.exists(key_path):
                missing_keys.append(key)
        
        if missing_keys:
            self.log_message.emit(f"ОШИБКА: Отсутствуют файлы: {', '.join(missing_keys)}")
            self.status_updated.emit(f"Ошибка: отсутствуют {', '.join(missing_keys)}")
            return
        
        # Инициализация поисковика с областью поиска
        self._image_finder = OptimizedImageFinder(
            confidence=IMAGE_CONFIDENCE_STRICT,
            smoothing=True,
            smoothing_size=SMOOTHING_SIZE,
            search_area=self._search_area
        )
        
        self.log_message.emit(f"Поиск клавиш в области: {self._search_area}")
        
        while self.is_running:
            # Проверяем наличие зеленого цвета
            green_detected = self._check_green_color()
            
            if green_detected:
                # Если зеленый цвет есть, но мы еще не обрабатываем - начинаем обработку
                if not self._is_processing:
                    self._is_processing = True
                    self.status_updated.emit("Обнаружен зеленый цвет, определяю клавишу...")
                    self.log_message.emit("Зеленый цвет обнаружен, начинаю обработку")
                    
                    # Определяем клавишу один раз в начале действия
                    self._current_key = self._detect_which_key()
                    
                    if self._current_key is None:
                        self.status_updated.emit("Клавиша не определена - пропускаю действие")
                        self.log_message.emit("ОШИБКА: Не удалось определить клавишу")
                        self._is_processing = False
                        self.msleep(100)
                        continue
                    
                    self.log_message.emit(f"Определена клавиша: {self._current_key.upper()}")
                    self.status_updated.emit(f"Нажимаю клавишу: {self._current_key.upper()}")
                
                # Пока есть зеленый цвет - нажимаем клавишу с заданной периодичностью
                if self._current_key:
                    press_key(self._current_key, boundary=PRESS_KEY_DURATION)
                    # Задержка между нажатиями + случайная погрешность
                    delay = self._delay_between_presses + random.uniform(0.005, 0.025)
                    time.sleep(delay)
            
            else:
                # Зеленый цвет пропал
                if self._is_processing:
                    # Завершаем действие и увеличиваем счетчик
                    self._is_processing = False
                    self._current_key = None
                    self.action_completed.emit()
                    self.status_updated.emit("Зеленый цвет пропал, действие завершено")
                    self.log_message.emit("Зеленый цвет пропал, +1 к счетчику")
                else:
                    # Небольшая пауза для снижения нагрузки CPU
                    self.msleep(50)
            
            # Небольшая пауза между итерациями цикла
            self.msleep(10)
        
        self._cleanup()
        self.log_message.emit("Поток строительства остановлен")
    
    def _check_green_color(self) -> bool:
        """Проверяет наличие зеленого цвета"""
        x, y = self._builder_coords[self._resolution_mode]
        return check_color((x, y), self._target_color, self._color_tolerance)
    
    def _detect_which_key(self) -> Optional[str]:
        """Определяет, какую клавишу нужно нажимать"""
        if not self._image_finder:
            self.log_message.emit("ОШИБКА: ImageFinder не инициализирован")
            return None
        
        # Список клавиш для проверки в порядке приоритета
        keys_to_check = ['e', 'f', 'h']
        
        for key in keys_to_check:
            image_path = os.path.join(KEYS_DIR, f'{key}.png')
            if not os.path.exists(image_path):
                continue
            
            result = self._image_finder.find_image(image_path)
            
            if result:
                x, y, confidence = result
                self.log_message.emit(f"Обнаружено изображение: {key}.png (уверенность: {confidence:.2f})")
                return key
        
        # Если не нашли через image finder, пробуем альтернативный метод
        self.log_message.emit("Поиск по изображениям не дал результатов, пробую альтернативный метод...")
        alt_key = self._detect_key_by_color()
        if alt_key:
            return alt_key
        
        return None
    
    def _detect_key_by_color(self) -> Optional[str]:
        """
        Альтернативный метод определения клавиши по цвету в области
        """
        try:
            # Координаты областей для разных клавиш (относительные)
            if self._resolution_mode == "FullHD":
                key_areas = {
                    'e': (800, 540),
                    'f': (900, 540),
                    'h': (1000, 540)
                }
            else:  # QuadHD
                key_areas = {
                    'e': (1100, 720),
                    'f': (1200, 720),
                    'h': (1300, 720)
                }
            
            # Ищем белый цвет (клавиши обычно белые или светлые)
            for key, pos in key_areas.items():
                if check_color(pos, (255, 255, 255), tolerance=40):
                    self.log_message.emit(f"Альтернативное определение: клавиша {key.upper()} по цвету")
                    return key
            
            return None
        except Exception as e:
            self.log_message.emit(f"Ошибка в альтернативном определении: {e}")
            return None
    
    def _cleanup(self) -> None:
        """Очистка ресурсов"""
        if self._image_finder:
            self._image_finder.close()


class BuilderApp(BaseBotApp):
    """Приложение для автоматизации строительства"""
    
    def __init__(self):
        super().__init__(
            title="Стройка",
            window_width=550,
            window_height=525,
            has_resolution=True,
            has_delay=True,
            has_log=True,
            has_counter=True
        )
        self._color_tolerance = COLOR_TOLERANCE_NORMAL
        self._detection_label: Optional[QLabel] = None
        self._info_label: Optional[QLabel] = None
    
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
        
        target_color = COLOR_LIGHT_GREEN
        coords = builder_coordinate["FullHD"]["builder_marker"]
        self._info_label = QLabel(f"Цвет: RGB{target_color}, Координаты: {coords}\nОбласть поиска клавиш: 700-1300 x 400-800")
        self._info_label.setStyleSheet(LABEL_STYLES["muted"])
        self._info_label.setAlignment(Qt.AlignCenter)
        self._info_label.setWordWrap(True)
        detection_layout.addWidget(self._info_label)
        
        parent_layout.addWidget(detection_frame)
        self._check_keys_folder()
    
    def _check_keys_folder(self) -> bool:
        """Проверяет наличие файлов клавиш"""
        if not os.path.exists(KEYS_DIR):
            self._add_log(f"ОШИБКА: Папка 'keys' не найдена по пути: {KEYS_DIR}")
            self._update_status("Ошибка: папка keys не найдена")
            return False
        
        required = ['e.png', 'f.png', 'h.png']
        missing = [f for f in required if not os.path.exists(os.path.join(KEYS_DIR, f))]
        
        if missing:
            self._add_log(f"ОШИБКА: Отсутствуют файлы: {', '.join(missing)} в папке {KEYS_DIR}")
            self._update_status(f"Ошибка: отсутствуют {', '.join(missing)}")
            return False
        
        self._add_log(f"Все файлы найдены: {KEYS_DIR}")
        return True
    
    def _get_counter_text(self) -> str:
        return "Выполнено действий:"
    
    def _create_worker(self) -> Optional[BaseWorker]:
        if not self._check_keys_folder():
            return None
        return BuilderWorker(self._resolution_mode, self._get_delay(), self._color_tolerance)
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        super()._start_bot()
        
        if self._detection_label:
            self._detection_label.setText("Обнаружено: ничего")
        
        self._worker = self._create_worker()
        if self._worker:
            self._worker.action_completed.connect(self._increment_counter)
            self._worker.log_message.connect(self._add_log)
            self._worker.status_updated.connect(self._update_status)
            
            # Подключаем сигнал обнаружения клавиши через лог
            def on_log_message(msg: str):
                if "Обнаружено изображение:" in msg and self._detection_label:
                    key = msg.split(":")[-1].strip().replace(".png", "")
                    self._detection_label.setText(f"Обнаружено: {key.upper()}.png")
                elif "Альтернативное определение: клавиша" in msg and self._detection_label:
                    key = msg.split("клавиша")[-1].strip().upper()
                    self._detection_label.setText(f"Обнаружено: {key} (по цвету)")
            
            self._worker.log_message.connect(on_log_message)
            self._worker.start()
            self._add_log(f"Бот запущен. Задержка: {self._get_delay()} мс")
            self._add_log(f"Разрешение: {self._resolution_mode}")
    
    def _set_resolution(self, mode: str) -> None:
        """Устанавливает разрешение и обновляет информацию"""
        super()._set_resolution(mode)
        if self._info_label:
            coords = builder_coordinate[mode]["builder_marker"]
            target_color = COLOR_LIGHT_GREEN
            self._info_label.setText(f"Цвет: RGB{target_color}, Координаты: {coords}\nОбласть поиска клавиш: 700-1300 x 400-800")
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._resolution_mode = config.get("builder", "resolution_mode", "FullHD")
        self._color_tolerance = config.get("builder", "color_tolerance", COLOR_TOLERANCE_NORMAL)
        
        if self._delay_entry:
            delay = config.get("builder", "delay_between_presses", DEFAULT_DELAY_BUILDER)
            self._delay_entry.setText(str(delay))
        
        self._set_resolution(self._resolution_mode)
        
        counter_visible = config.get("builder", "counter_visible", False)
        if counter_visible and self._counter_window and self._counter_btn:
            self._counter_window.show()
            self._counter_btn.setText("Скрыть счётчик")
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        config.set_multiple("builder", {
            "resolution_mode": self._resolution_mode,
            "delay_between_presses": self._get_delay(),
            "color_tolerance": self._color_tolerance,
            "counter_visible": self._counter_window.isVisible() if self._counter_window else False
        })


def main():
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = BuilderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()