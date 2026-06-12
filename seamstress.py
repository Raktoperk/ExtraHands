"""
Бот для автоматизации швеи (последовательный кликер)
Работает только на основе общего времени выполнения
"""

import sys
import time
import random
import os
from typing import Optional, Dict, Tuple

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.config_manager import config
from components.styles import FRAME_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGES_FOLDER = os.path.join(BASE_DIR, "assets", "seamstress")


class SeamstressWorker(BaseWorker):
    """Рабочий поток для швеи"""
    
    action_updated = BaseWorker.status_updated
    
    def __init__(self, total_time_sec: int):
        """
        Args:
            total_time_sec: Общее время работы бота в секундах
        """
        super().__init__()
        self._total_time_sec = total_time_sec
        self._pyautogui = None
        self._coordinates: Dict[str, Tuple[int, int]] = {}
        self._delay_between_clicks = 0.1  # Базовая задержка, будет пересчитана
    
    def _calculate_delays(self, cycles_count: int) -> None:
        """
        Рассчитывает задержки на основе общего времени выполнения
        
        Args:
            cycles_count: Количество циклов, которые планируется выполнить
        """
        if cycles_count <= 0:
            return
        
        # В одном цикле:
        # - 1 клик по 1.png
        # - 18 двойных кликов (2-19.png)
        # - 1 клик по 20.png
        # Итого: 20 действий
        
        actions_per_cycle = 20
        total_actions = cycles_count * actions_per_cycle
        
        # Общее время на все действия (без учета времени поиска)
        search_time_per_cycle = 1.5
        available_time = max(1, self._total_time_sec - (cycles_count * search_time_per_cycle))
        
        if available_time <= 0:
            self._delay_between_clicks = 0.05
        else:
            # Время на одно действие
            self._delay_between_clicks = available_time / total_actions
            # Ограничиваем разумными пределами
            self._delay_between_clicks = max(0.05, min(0.5, self._delay_between_clicks))
        
        self.log_message.emit(
            f"Расчет задержек: {cycles_count} циклов, {total_actions} действий, "
            f"{available_time:.1f}с доступно → {self._delay_between_clicks:.3f}с на действие"
        )
    
    def _get_click_delay(self) -> float:
        """
        Возвращает задержку с погрешностью ±5-10 мс
        
        Базовая задержка рассчитывается из общего времени выполнения,
        а погрешность добавляется в миллисекундах для естественности
        """
        if self._delay_between_clicks <= 0:
            return 0.05
        
        # Погрешность в миллисекундах (конвертируем в секунды)
        ms_variation = random.uniform(5, 15) / 1000  # 5-15 мс
        
        # Добавляем или вычитаем случайное значение
        if random.choice([True, False]):
            delay = self._delay_between_clicks + ms_variation
        else:
            delay = self._delay_between_clicks - ms_variation
        
        # Ограничиваем разумными пределами
        return max(0.04, min(0.5, delay))
    
    def _init_pyautogui(self) -> None:
        """Ленивая инициализация pyautogui"""
        if self._pyautogui is None:
            import pyautogui
            self._pyautogui = pyautogui
            self._pyautogui.PAUSE = 0
            self._pyautogui.FAILSAFE = False
    
    def _find_image(self, image_name: str) -> Optional[Tuple[int, int, float]]:
        """Ищет изображение на экране"""
        try:
            filepath = os.path.join(IMAGES_FOLDER, image_name)
            if not os.path.exists(filepath):
                return None
            
            for confidence in [0.9, 0.85, 0.8, 0.75]:
                try:
                    location = self._pyautogui.locateOnScreen(filepath, confidence=confidence)
                    if location:
                        x = location.left + location.width // 2
                        y = location.top + location.height // 2
                        return (x, y, confidence)
                except Exception:
                    continue
        except Exception as e:
            self.log_message.emit(f"Ошибка поиска {image_name}: {e}")
        return None
    
    def _click_at(self, x: int, y: int, click_type: str = "left") -> bool:
        """Выполняет клик с рассчитанной задержкой"""
        try:
            move_duration = random.uniform(0.05, 0.1)
            self._pyautogui.moveTo(x, y, duration=move_duration)
            time.sleep(0.01)
            
            if click_type == "double":
                self._pyautogui.doubleClick()
                delay = self._get_click_delay() + 0.01
            else:
                self._pyautogui.click(button='left')
                delay = self._get_click_delay()
            
            time.sleep(delay)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка клика: {e}")
            return False
    
    def _execute_click_sequence(self) -> None:
        """Выполняет последовательность кликов"""
        self.log_message.emit(f"Выполняю последовательность (базовая задержка: {self._delay_between_clicks:.3f}с)...")
        
        # Клик по 1.png
        if "1.png" in self._coordinates:
            x, y = self._coordinates["1.png"]
            self.status_updated.emit("Клик по 1.png")
            self._click_at(x, y, "left")
        
        # Двойные клики по 2-19.png
        for i in range(2, 20):
            if not self.is_running:
                break
            
            filename = f"{i}.png"
            if filename in self._coordinates:
                self.status_updated.emit(f"Двойной клик по {filename}")
                x, y = self._coordinates[filename]
                self._click_at(x, y, "double")
        
        # Клик по 20.png
        if "20.png" in self._coordinates:
            x, y = self._coordinates["20.png"]
            self.status_updated.emit("Клик по 20.png")
            self._click_at(x, y, "left")
    
    def run(self) -> None:
        """Основной цикл потока"""
        self._init_pyautogui()
        self.log_message.emit(f"Запуск потока швеи. Общее время: {self._total_time_sec} сек")
        
        cycle_count = 0
        start_time = time.time()
        
        # Первоначальная оценка количества возможных циклов
        estimated_cycles = max(1, self._total_time_sec // 3)
        self._calculate_delays(estimated_cycles)
        
        while self.is_running:
            # Проверка времени выполнения
            elapsed = time.time() - start_time
            if elapsed >= self._total_time_sec:
                self.log_message.emit(f"Достигнуто время выполнения ({self._total_time_sec} сек)")
                break
            
            cycle_count += 1
            self.log_message.emit(f"Цикл #{cycle_count}")
            
            # Ожидание 1.png
            found_1 = False
            while self.is_running and not found_1:
                if time.time() - start_time >= self._total_time_sec:
                    break
                
                self.status_updated.emit("Поиск 1.png...")
                result = self._find_image("1.png")
                
                if result:
                    x, y, confidence = result
                    self.log_message.emit(f"✓ Найдено: 1.png ({confidence:.2f})")
                    found_1 = True
                    self._coordinates = {"1.png": (x, y)}
                    break
                
                time.sleep(0.1)
            
            if not self.is_running:
                break
            
            if time.time() - start_time >= self._total_time_sec:
                break
            
            # Поиск остальных изображений
            found_count = 1
            for i in range(2, 21):
                if not self.is_running:
                    break
                
                if time.time() - start_time >= self._total_time_sec:
                    break
                
                filename = f"{i}.png"
                self.status_updated.emit(f"Поиск {filename}...")
                result = self._find_image(filename)
                
                if result:
                    x, y, confidence = result
                    self.log_message.emit(f"✓ Найдено: {filename} ({confidence:.2f})")
                    self._coordinates[filename] = (x, y)
                    found_count += 1
                    time.sleep(0.02)
            
            self.log_message.emit(f"Найдено: {found_count}/20")
            
            if found_count >= 2:
                # Корректируем задержки на основе реального прогресса
                elapsed = time.time() - start_time
                remaining_time = max(1, self._total_time_sec - elapsed)
                remaining_cycles_estimate = max(1, remaining_time // 2)
                self._calculate_delays(cycle_count + remaining_cycles_estimate)
                
                self._execute_click_sequence()
                self.status_updated.emit(f"Цикл #{cycle_count} завершен")
            else:
                self.log_message.emit("Недостаточно изображений. Пропускаю цикл.")
                time.sleep(0.3)
        
        elapsed_total = time.time() - start_time
        self.log_message.emit(f"Поток швеи остановлен. Выполнено циклов: {cycle_count} за {elapsed_total:.1f} сек")
        self.status_updated.emit("Работа завершена")


class SeamstressApp(BaseBotApp):
    """Приложение для автоматизации швеи"""
    
    def __init__(self):
        # Инициализируем атрибуты ПЕРЕД вызовом super().__init__()
        self._total_time_sec = 35
        self._time_entry: Optional[QLineEdit] = None
        self._action_label: Optional[QLabel] = None
        
        # Вызываем родительский __init__
        super().__init__(
            title="Швея",
            window_width=550,
            window_height=380,
            has_resolution=False,
            has_delay=False,
            has_log=True,
            has_counter=False
        )
        
        # Создаем папку если нужно
        if not os.path.exists(IMAGES_FOLDER):
            os.makedirs(IMAGES_FOLDER)
        
        # Загружаем настройки
        self._load_settings()
    
    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет настройки"""
        # Текущее действие
        self._action_label = QLabel("Текущее действие: ожидание")
        self._action_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                padding: 8px;
                background-color: #3c3c3c;
                border-radius: 8px;
            }
        """)
        self._action_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(self._action_label)
        
        # Фрейм настроек
        settings_frame = QFrame()
        settings_frame.setStyleSheet(FRAME_STYLES["frame"])
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        
        # Время выполнения
        time_layout = QHBoxLayout()
        time_label = QLabel("Время выполнения (сек):")
        time_label.setStyleSheet(LABEL_STYLES["secondary"])
        time_layout.addWidget(time_label)
        
        self._time_entry = QLineEdit(str(self._total_time_sec))
        self._time_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self._time_entry.setMaximumWidth(100)
        time_layout.addWidget(self._time_entry)
        time_layout.addStretch()
        settings_layout.addLayout(time_layout)
        
        # Информация о папке
        images_info = QLabel(f"📁 Папка с шаблонами: {IMAGES_FOLDER}")
        images_info.setStyleSheet(LABEL_STYLES["muted"])
        images_info.setWordWrap(True)
        settings_layout.addWidget(images_info)
        
        parent_layout.addWidget(settings_frame)
        
        self._check_images_folder()
    
    def _check_images_folder(self) -> bool:
        """Проверяет наличие изображений"""
        if not os.path.exists(IMAGES_FOLDER):
            self._add_log("ВНИМАНИЕ: Папка с изображениями не найдена!")
            return False
        
        missing = [f"{i}.png" for i in range(1, 21)
                  if not os.path.exists(os.path.join(IMAGES_FOLDER, f"{i}.png"))]
        
        if missing:
            self._add_log(f"ВНИМАНИЕ: Отсутствуют файлы: {missing[:3]}...")
            return False
        
        self._add_log(f"✅ Все 20 файлов найдены: {IMAGES_FOLDER}")
        return True
    
    def _create_worker(self) -> Optional[BaseWorker]:
        if not self._check_images_folder():
            return None
        
        try:
            total_time = int(self._time_entry.text()) if self._time_entry else self._total_time_sec
            
            if total_time < 1:
                raise ValueError("Время выполнения должно быть не менее 1 секунды")
            if total_time > 3600:
                raise ValueError("Время выполнения не должно превышать 3600 секунд (1 час)")
            
            return SeamstressWorker(total_time)
        except ValueError as e:
            self._update_status(f"Ошибка: {e}")
            return None
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        self._worker = self._create_worker()
        if not self._worker:
            return
        
        super()._start_bot()
        
        self._worker.status_updated.connect(self._update_action)
        self._worker.log_message.connect(self._add_log)
        self._worker.start()
        
        total_time = int(self._time_entry.text()) if self._time_entry else self._total_time_sec
        self._add_log(f"Бот запущен. Время работы: {total_time} сек")
    
    def _update_action(self, action_text: str) -> None:
        """Обновляет текст текущего действия"""
        if self._action_label:
            self._action_label.setText(f"Текущее действие: {action_text}")
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._total_time_sec = config.get("seamstress", "total_time_sec", 35)
        
        if self._time_entry:
            self._time_entry.setText(str(self._total_time_sec))
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        total_time = self._total_time_sec
        
        if self._time_entry:
            try:
                total_time = int(self._time_entry.text())
            except ValueError:
                pass
        
        config.set("seamstress", "total_time_sec", total_time)


def main():
    app = QApplication(sys.argv)
    window = SeamstressApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()