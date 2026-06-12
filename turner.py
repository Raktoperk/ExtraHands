"""
Бот для автоматизации токаря (отслеживание стамески)
"""

import sys
import os
import time
from typing import Optional

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QFrame, QWidget
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.config_manager import config
from components.styles import FRAME_STYLES, LABEL_STYLES


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHISEL_PATH = os.path.join(BASE_DIR, "assets", "turner", "chisel.png")

# Область поиска (left, top, right, bottom)
SEARCH_AREA = (635, 655, 1280, 990)


class TurnerWorker(BaseWorker):
    """Рабочий поток для отслеживания стамески"""

    def __init__(self, vertical_offset: int = 50, horizontal_offset: int = 5):
        super().__init__()
        self._vertical_offset = vertical_offset
        self._horizontal_offset = horizontal_offset
        self._cv2 = None
        self._np = None
        self._mss = None
        self._pyautogui = None
    
    def _init_imports(self) -> None:
        """Ленивая инициализация импортов"""
        if self._cv2 is None:
            import cv2
            self._cv2 = cv2
        if self._np is None:
            import numpy as np
            self._np = np
        if self._pyautogui is None:
            import pyautogui
            self._pyautogui = pyautogui
            self._pyautogui.PAUSE = 0
        if self._mss is None:
            try:
                from mss import mss
                self._mss = mss()
            except ImportError:
                self._mss = None
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        if self._mss:
            self._mss.close()
            self._mss = None
    
    def run(self) -> None:
        """Основной цикл потока"""
        self._init_imports()
        
        self.log_message.emit("Запуск потока отслеживания стамески")
        self.status_updated.emit("Поиск стамески...")
        
        # Загрузка шаблона
        template = self._cv2.imread(CHISEL_PATH, self._cv2.IMREAD_GRAYSCALE)
        if template is None:
            self.log_message.emit(f"ОШИБКА: Не удалось загрузить {CHISEL_PATH}")
            self.status_updated.emit("Ошибка загрузки шаблона")
            return
        
        h, w = template.shape
        half_w, half_h = w // 2, h // 2
        
        self.log_message.emit(f"Шаблон: {w}x{h} пикселей")
        self.log_message.emit(f"Область поиска: {SEARCH_AREA[2]-SEARCH_AREA[0]}x{SEARCH_AREA[3]-SEARCH_AREA[1]}")
        
        left, top, right, bottom = SEARCH_AREA
        width, height = right - left, bottom - top
        
        # Кэш для плавности
        pos_cache = []
        cache_size = 3
        last_position = None
        
        # Статистика
        start_time = time.time()
        frame_count = 0
        detection_count = 0
        last_stats_time = start_time
        
        try:
            while self.is_running:
                frame_count += 1
                
                # Захват области
                if self._mss:
                    monitor = {"left": left, "top": top, "width": width, "height": height}
                    screenshot = self._mss.grab(monitor)
                    frame = self._np.array(screenshot)
                    gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGRA2GRAY)
                else:
                    screenshot = self._pyautogui.screenshot(region=(left, top, width, height))
                    frame = self._np.array(screenshot)
                    gray = self._cv2.cvtColor(frame, self._cv2.COLOR_RGB2GRAY)
                
                # Поиск шаблона
                result = self._cv2.matchTemplate(gray, template, self._cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = self._cv2.minMaxLoc(result)
                
                if max_val > 0.8:
                    detection_count += 1
                    
                    local_x = max_loc[0] + half_w
                    local_y = max_loc[1] + half_h
                    
                    global_x = left + local_x + self._horizontal_offset
                    global_y = top + local_y + self._vertical_offset
                    
                    pos_cache.append((global_x, global_y))
                    if len(pos_cache) > cache_size:
                        pos_cache.pop(0)
                    
                    if len(pos_cache) >= 2:
                        xs = [p[0] for p in pos_cache]
                        ys = [p[1] for p in pos_cache]
                        filtered_x = int(self._np.median(xs))
                        filtered_y = int(self._np.median(ys))
                    else:
                        filtered_x, filtered_y = global_x, global_y
                    
                    if last_position != (filtered_x, filtered_y):
                        self._pyautogui.moveTo(filtered_x, filtered_y, duration=0)
                        last_position = (filtered_x, filtered_y)
                        self.status_updated.emit(f"Стамеска найдена: ({filtered_x}, {filtered_y})")
                
                # Статистика
                current_time = time.time()
                if current_time - last_stats_time >= 1.0:
                    elapsed = current_time - start_time
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    detection_rate = (detection_count / frame_count * 100) if frame_count > 0 else 0
                    
                    if last_position:
                        status = f"FPS: {fps:.0f} | Обнаружение: {detection_rate:.1f}% | Позиция: ({last_position[0]}, {last_position[1]})"
                    else:
                        status = f"FPS: {fps:.0f} | Обнаружение: {detection_rate:.1f}% | Поиск..."
                    
                    self.status_updated.emit(status)
                    last_stats_time = current_time
                
                self.msleep(10)
        
        except Exception as e:
            self.log_message.emit(f"ОШИБКА: {e}")
            self.status_updated.emit(f"Ошибка: {str(e)}")
        
        finally:
            self.cleanup()
            
            total_time = time.time() - start_time
            self.log_message.emit(f"Всего кадров: {frame_count:,}")
            self.log_message.emit(f"Средний FPS: {frame_count/total_time:.1f}" if total_time > 0 else "N/A")
            self.log_message.emit("Поток отслеживания остановлен")
            self.status_updated.emit("Отслеживание остановлено")


class TurnerApp(BaseBotApp):
    """Приложение для автоматизации токаря"""
    
    def __init__(self):
        # Инициализируем атрибуты ПЕРЕД вызовом super().__init__()
        self._vertical_offset = 50
        self._horizontal_offset = 5
        
        super().__init__(
            title="Токарь",
            window_width=500,
            window_height=250,
            has_resolution=False,
            has_delay=False,
            has_log=False,
            has_counter=False
        )
    
    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет информацию о настройках"""
        info_frame = QFrame()
        info_frame.setStyleSheet(FRAME_STYLES["frame"])
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)
        
        area_info = QLabel(f"Область поиска: {SEARCH_AREA[2]-SEARCH_AREA[0]}x{SEARCH_AREA[3]-SEARCH_AREA[1]} пикселей")
        area_info.setStyleSheet(LABEL_STYLES["secondary"])
        info_layout.addWidget(area_info)
        
        # Теперь self._horizontal_offset и self._vertical_offset уже существуют
        offset_info = QLabel(f"Смещение курсора: +{self._horizontal_offset}px вправо, +{self._vertical_offset}px вниз")
        offset_info.setStyleSheet(LABEL_STYLES["secondary"])
        info_layout.addWidget(offset_info)
        
        file_info = QLabel("Файл шаблона: chisel.png")
        file_info.setStyleSheet(LABEL_STYLES["secondary"])
        info_layout.addWidget(file_info)
        
        parent_layout.addWidget(info_frame)
    
    def _create_worker(self) -> Optional[BaseWorker]:
        if not os.path.exists(CHISEL_PATH):
            self._update_status("ОШИБКА: chisel.png не найден")
            return None
        
        return TurnerWorker(self._vertical_offset, self._horizontal_offset)
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        if not os.path.exists(CHISEL_PATH):
            self._update_status("ОШИБКА: chisel.png не найден")
            return
        
        super()._start_bot()
        
        self._worker = self._create_worker()
        if self._worker:
            self._worker.log_message.connect(self._add_log)
            self._worker.status_updated.connect(self._update_status)
            self._worker.start()
            
            print("\n" + "=" * 60)
            print("ЗАПУСК ОТСЛЕЖИВАНИЯ СТАМЕСКИ")
            print(f"Смещение курсора: +{self._horizontal_offset} вправо, +{self._vertical_offset} вниз")
            print("=" * 60)
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._vertical_offset = config.get("turner", "vertical_offset", 50)
        self._horizontal_offset = config.get("turner", "horizontal_offset", 5)
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        config.set_multiple("turner", {
            "vertical_offset": self._vertical_offset,
            "horizontal_offset": self._horizontal_offset
        })


def main():
    app = QApplication(sys.argv)
    window = TurnerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()