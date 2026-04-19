import os
import sys
import time
import cv2
import numpy as np
import pyautogui
from mss import mss
from functools import lru_cache
import threading

try:
    from components.styles import *
except ImportError:
    COLORS = {
        "primary": "#00adb5", "primary_hover": "#0098a0", "primary_pressed": "#01959c",
        "danger": "#ca162e", "danger_hover": "#be0f27", "danger_pressed": "#b41227",
        "bg_dark": "#2b2b2b", "bg_medium": "#3c3c3c", "bg_light": "#1e1e1e",
        "text_primary": "#ffffff", "text_secondary": "#cccccc", "border": "#555555",
    }

# Получаем абсолютный путь к папке со скриптом
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

accept_path = os.path.join(BASE_DIR, "assets", "catch_pda", "accept.png")

# ОПРЕДЕЛЕННАЯ ОБЛАСТЬ ПОИСКА (можно изменить для тестов)
SEARCH_AREA = {
    'left': 1220, 'top': 350,
    'right': 1350, 'bottom': 800
}
SEARCH_AREA['width'] = SEARCH_AREA['right'] - SEARCH_AREA['left']
SEARCH_AREA['height'] = SEARCH_AREA['bottom'] - SEARCH_AREA['top']

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class OptimizedImageFinder:
    """Оптимизированный поиск с запоминанием шаблона"""
    
    # Кэш шаблонов на уровне класса (один на все экземпляры)
    _template_cache = {}
    _template_info_cache = {}
    
    def __init__(self, confidence=0.7):
        self.confidence = confidence
        self.sct = mss()
        self.last_position = None
        self.pos_cache = []
        self.cache_size = 3
        
        # Настройка для максимальной скорости
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
        
        # Получаем информацию о мониторах
        self.all_monitors = self.sct.monitors
        self.monitor_to_use = self._find_monitor_for_search_area()
        
        # Предварительно вычисленные константы для быстрого доступа
        self.search_left = SEARCH_AREA['left']
        self.search_top = SEARCH_AREA['top']
        self.search_width = SEARCH_AREA['width']
        self.search_height = SEARCH_AREA['height']
        
        # Оптимизация: предварительно выделенный массив для скриншота
        self.screenshot_buffer = None
        
        # Статистика
        self.frame_count = 0
        
    def _find_monitor_for_search_area(self):
        """Находит монитор, в котором находится область поиска"""
        center_x = SEARCH_AREA['left'] + SEARCH_AREA['width'] // 2
        center_y = SEARCH_AREA['top'] + SEARCH_AREA['height'] // 2
        
        for i in range(1, len(self.all_monitors)):
            m = self.all_monitors[i]
            if (m['left'] <= center_x <= m['left'] + m['width'] and
                m['top'] <= center_y <= m['top'] + m['height']):
                return i
        return 1
    
    @classmethod
    def load_template_cached(cls, template_path):
        """Загружает шаблон с кэшированием"""
        # Проверяем, не загружен ли уже шаблон
        if template_path in cls._template_cache:
            return cls._template_cache[template_path], cls._template_info_cache.get(template_path, {})
        
        # Загружаем новый шаблон
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(f"Не удалось загрузить шаблон: {template_path}")
        
        # Сохраняем в кэш
        cls._template_cache[template_path] = template
        cls._template_info_cache[template_path] = {
            'h': template.shape[0],
            'w': template.shape[1],
            'path': template_path
        }
        
        return template, cls._template_info_cache[template_path]
    
    def fast_screenshot(self):
        """Быстрый захват определенной области через MSS"""
        try:
            monitor = self.all_monitors[self.monitor_to_use]
            
            # Относительные координаты (вычисляем один раз)
            relative_left = self.search_left - monitor['left']
            relative_top = self.search_top - monitor['top']
            
            # Проверка границ
            if (relative_left < 0 or relative_top < 0 or 
                relative_left + self.search_width > monitor['width'] or 
                relative_top + self.search_height > monitor['height']):
                return None
            
            # Область для захвата
            capture_area = {
                'left': monitor['left'] + relative_left,
                'top': monitor['top'] + relative_top,
                'width': self.search_width,
                'height': self.search_height
            }
            
            # Захватываем область
            screenshot = self.sct.grab(capture_area)
            
            # Конвертируем в numpy array (оптимизировано)
            frame = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                screenshot.height, screenshot.width, 4
            )
            
            # Оптимизированная конвертация в grayscale (RGB -> Y)
            gray = (0.299 * frame[:,:,2] + 0.587 * frame[:,:,1] + 0.114 * frame[:,:,0]).astype(np.uint8)
            
            return gray
            
        except Exception as e:
            return None
    
    def find_image(self, template, template_info):
        """Поиск изображения в определенной области"""
        if template is None:
            return None
        
        self.frame_count += 1
        
        # Быстрый скриншот
        screenshot = self.fast_screenshot()
        if screenshot is None:
            return None
        
        # Оптимизированный поиск с уменьшением разрешения для скорости
        h, w = template_info['h'], template_info['w']
        
        # Если шаблон большой, уменьшаем разрешение для поиска
        if w * h > 10000:  # если больше ~100x100 пикселей
            scale = 0.7
            small_screenshot = cv2.resize(screenshot, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            small_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            
            # Поиск
            result = cv2.matchTemplate(small_screenshot, small_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            # Масштабируем координаты обратно
            if max_val >= self.confidence:
                center_x = int((max_loc[0] + small_template.shape[1] // 2) / scale)
                center_y = int((max_loc[1] + small_template.shape[0] // 2) / scale)
            else:
                return None
        else:
            # Обычный поиск
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val < self.confidence:
                return None
                
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
        
        # Преобразуем в абсолютные координаты экрана
        abs_x = self.search_left + center_x
        abs_y = self.search_top + center_y
        
        # Добавляем в кэш для сглаживания
        self.pos_cache.append((abs_x, abs_y))
        if len(self.pos_cache) > self.cache_size:
            self.pos_cache.pop(0)
        
        # Фильтрация: медиана из кэша
        if len(self.pos_cache) >= 2:
            xs = [p[0] for p in self.pos_cache]
            ys = [p[1] for p in self.pos_cache]
            filtered_x = int(np.median(xs))
            filtered_y = int(np.median(ys))
        else:
            filtered_x, filtered_y = abs_x, abs_y
        
        return filtered_x, filtered_y, max_val
    
    def move_to_position(self, x, y):
        """Мгновенное перемещение курсора"""
        if self.last_position != (x, y):
            pyautogui.moveTo(x, y, duration=0, _pause=False)
            self.last_position = (x, y)
            return True
        return False
    
    def click_at_position(self, x, y):
        """Клик по указанным координатам"""
        pyautogui.click(x, y, _pause=False)
    
    def close(self):
        """Освобождение ресурсов"""
        self.sct.close()
    
    def get_stats(self):
        """Возвращает статистику для этого экземпляра"""
        return {
            'frame_count': self.frame_count
        }

class CatchPDAWorkerThread(QThread):
    """Поток для отслеживания accept.png"""
    log_message = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, confidence=0.7, click_cooldown=2.5):
        super().__init__()
        self.confidence = confidence
        self.click_cooldown = click_cooldown
        self.running = True
        
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
    
    def run(self):
        self.log_message.emit("Запуск потока отслеживания accept.png")
        self.status_updated.emit("Загрузка шаблона...")
        
        # Создаем поисковик
        finder = OptimizedImageFinder(confidence=self.confidence)
        
        try:
            # Загружаем шаблон с кэшированием
            template, template_info = OptimizedImageFinder.load_template_cached(accept_path)
            if template is None:
                self.log_message.emit(f"Ошибка: Не удалось загрузить изображение: {accept_path}")
                return
            
            self.log_message.emit(f"Шаблон: {template_info['w']}x{template_info['h']} пикселей (кэширован)")
            
            # Статистика
            start_time = time.time()
            detection_count = 0
            click_count = 0
            last_click_time = 0
            last_stats_time = start_time
            
            self.status_updated.emit("Поиск accept.png...")
            
            while self.running:
                # Поиск изображения
                result = finder.find_image(template, template_info)
                
                if result:
                    detection_count += 1
                    x, y, confidence_val = result
                    
                    current_time = time.time()
                    
                    if current_time - last_click_time >= self.click_cooldown:
                        click_count += 1
                        self.log_message.emit(f"Обнаружено! ({x}, {y}) Уверенность: {confidence_val:.2f}")
                        
                        finder.move_to_position(x, y)
                        finder.click_at_position(x, y)
                        self.log_message.emit("Клик выполнен!")
                        
                        last_click_time = current_time
                        self.status_updated.emit(f"Клик #{click_count} по ({x}, {y})")
                
                # Статистика раз в секунду
                current_time = time.time()
                if current_time - last_stats_time >= 1.0:
                    elapsed = current_time - start_time
                    fps = finder.frame_count / elapsed if elapsed > 0 else 0
                    
                    pos_str = f"({finder.last_position[0]}, {finder.last_position[1]})" if finder.last_position else "Поиск..."
                    detection_rate = (detection_count / finder.frame_count * 100) if finder.frame_count > 0 else 0
                    
                    status = f"FPS: {fps:.1f} | Обнаружение: {detection_rate:.1f}% | Клики: {click_count} | {pos_str}"
                    self.status_updated.emit(status)
                    last_stats_time = current_time
                
                # Минимальная пауза для снижения нагрузки
                self.msleep(5)
                
        except Exception as e:
            self.log_message.emit(f"ОШИБКА: {e}")
            self.status_updated.emit(f"Ошибка: {str(e)}")
        finally:
            finder.close()
            
            # Финальная статистика
            elapsed = time.time() - start_time
            self.log_message.emit(f"Всего кадров: {finder.frame_count}")
            self.log_message.emit(f"Средний FPS: {finder.frame_count/elapsed:.1f}")
            self.log_message.emit(f"Кликов: {click_count}")
            self.status_updated.emit("Отслеживание остановлено")
    
    def stop(self):
        self.running = False

class CatchPDAApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.confidence = 0.7
        self.click_cooldown = 2.5
        
        # Предварительная загрузка шаблона при старте приложения
        self.template_preloaded = False
        self.preload_template()
        
        self.initUI()
        
    def preload_template(self):
        """Предварительная загрузка шаблона при запуске"""
        try:
            if os.path.exists(accept_path):
                OptimizedImageFinder.load_template_cached(accept_path)
                self.template_preloaded = True
        except Exception as e:
            print(f"Не удалось предварительно загрузить шаблон: {e}")
    
    def initUI(self):
        self.setWindowTitle("Ловля КПК")
        self.setFixedSize(500, 200)  # Уменьшил высоту
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Заголовок
        title_label = QLabel("Ловля КПК")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Строка состояния
        self.status_label = QLabel("Состояние: не активно")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            background-color: {COLORS['bg_medium']};
            border-radius: 8px;
            min-height: 25px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Кнопка
        self.toggle_button = QPushButton("Запустить")
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_pressed']};
            }}
        """)
        self.toggle_button.clicked.connect(self.toggle_tracking)
        main_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
        self.check_accept_file()
    
    def check_accept_file(self):
        if not os.path.exists(accept_path):
            self.status_label.setText(f"ОШИБКА: accept.png не найден")
        else:
            self.status_label.setText("Состояние: готов к запуску")
    
    def toggle_tracking(self):
        if self.running:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking(self):
        if not os.path.exists(accept_path):
            self.status_label.setText(f"ОШИБКА: accept.png не найден")
            return
        
        self.running = True
        self.toggle_button.setText("Остановить")
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['danger_pressed']};
            }}
        """)
        
        self.worker_thread = CatchPDAWorkerThread(self.confidence, self.click_cooldown)
        self.worker_thread.log_message.connect(self.print_log)
        self.worker_thread.status_updated.connect(self.update_status_label)
        self.worker_thread.start()
    
    def stop_tracking(self):
        self.running = False
        self.toggle_button.setText("Запустить")
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_pressed']};
            }}
        """)
        
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
        
        self.status_label.setText("Состояние: не активно")
    
    def print_log(self, message):
        print(f"[LOG] {message}")
    
    def update_status_label(self, status_text):
        self.status_label.setText(f"Состояние: {status_text}")
    
    def closeEvent(self, event):
        if self.running:
            self.stop_tracking()
        event.accept()

def main():
    app = QApplication(sys.argv)
    catch_pda_app = CatchPDAApp()
    catch_pda_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()