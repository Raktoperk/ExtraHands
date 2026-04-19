from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor

import sys
import os
import time
import cv2
import numpy as np
import pyautogui
from mss import mss

try:
    from components.styles import *
except ImportError:
    # Запасные значения если файл стилей не найден
    COLORS = {
        "primary": "#00adb5",
        "primary_hover": "#0098a0",
        "primary_pressed": "#01959c",
        "danger": "#ca162e",
        "danger_hover": "#be0f27",
        "danger_pressed": "#b41227",
        "bg_dark": "#2b2b2b",
        "bg_medium": "#3c3c3c",
        "bg_light": "#1e1e1e",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "border": "#555555",
    }

# Получаем абсолютный путь к папке со скриптом
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к изображению chisel.png
chisel_path = os.path.join(BASE_DIR, "assets", "turner", "chisel.png")

# ОПРЕДЕЛЕННАЯ ОБЛАСТЬ ПОИСКА
SEARCH_AREA = {
    'left': 635,
    'top': 655,
    'right': 1280,
    'bottom': 990
}

# Вычисляем ширину и высоту области
SEARCH_AREA['width'] = SEARCH_AREA['right'] - SEARCH_AREA['left']
SEARCH_AREA['height'] = SEARCH_AREA['bottom'] - SEARCH_AREA['top']

class TurnerWorkerThread(QThread):
    """Поток для отслеживания стамески"""
    log_message = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, vertical_offset=50, horizontal_offset=5):
        super().__init__()
        self.vertical_offset = vertical_offset
        self.horizontal_offset = horizontal_offset
        self.running = True
        
        # Настройки для максимальной скорости
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
        
    def run(self):
        self.log_message.emit("Запуск потока отслеживания стамески")
        self.status_updated.emit("Поиск стамески...")
        
        # Загружаем шаблон
        template = cv2.imread(chisel_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            error_msg = f"Ошибка: Не удалось загрузить изображение: {chisel_path}"
            self.log_message.emit(error_msg)
            self.status_updated.emit(error_msg)
            return
        
        h, w = template.shape
        
        self.log_message.emit(f"Шаблон: {w}x{h} пикселей")
        self.log_message.emit(f"Область поиска: {SEARCH_AREA['width']}x{SEARCH_AREA['height']}")
        self.log_message.emit(f"Смещение курсора: +{self.horizontal_offset} вправо, +{self.vertical_offset} вниз")
        
        # Инициализируем MSS для быстрого захвата
        mss_capture = None
        try:
            mss_capture = mss()
            self.log_message.emit("Использую MSS для быстрого захвата экрана")
        except Exception as e:
            self.log_message.emit(f"MSS не доступен, использую PyAutoGUI: {e}")
        
        # Предварительные вычисления для скорости
        half_w = w // 2
        half_h = h // 2
        
        # Кэш для плавности (3 последние позиции)
        pos_cache = []
        cache_size = 3
        
        # Статистика
        start_time = time.time()
        frame_count = 0
        detection_count = 0
        last_print_time = start_time
        last_position = None
        
        try:
            while self.running:
                frame_count += 1
                
                # ЗАХВАТ ОБЛАСТИ ЭКРАНА
                if mss_capture:
                    monitor = {
                        "left": SEARCH_AREA['left'],
                        "top": SEARCH_AREA['top'],
                        "width": SEARCH_AREA['width'],
                        "height": SEARCH_AREA['height']
                    }
                    screenshot = mss_capture.grab(monitor)
                    frame = np.array(screenshot)
                    # MSS возвращает BGRA, конвертируем в grayscale
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                else:
                    # PyAutoGUI как запасной вариант
                    screenshot = pyautogui.screenshot(
                        region=(
                            SEARCH_AREA['left'],
                            SEARCH_AREA['top'],
                            SEARCH_AREA['width'],
                            SEARCH_AREA['height']
                        )
                    )
                    frame = np.array(screenshot)
                    # PyAutoGUI возвращает RGB
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # ПОИСК ШАБЛОНА
                result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                # Если нашли с достаточной уверенностью
                if max_val > 0.8:
                    detection_count += 1
                    
                    # Локальные координаты в области -> глобальные координаты экрана
                    local_x = max_loc[0] + half_w
                    local_y = max_loc[1] + half_h
                    
                    global_x = SEARCH_AREA['left'] + local_x + self.horizontal_offset
                    global_y = SEARCH_AREA['top'] + local_y + self.vertical_offset
                    
                    # Добавляем в кэш для плавности
                    pos_cache.append((global_x, global_y))
                    if len(pos_cache) > cache_size:
                        pos_cache.pop(0)
                    
                    # Фильтрация: медиана из кэша
                    if len(pos_cache) >= 2:
                        xs = [p[0] for p in pos_cache]
                        ys = [p[1] for p in pos_cache]
                        filtered_x = int(np.median(xs))
                        filtered_y = int(np.median(ys))
                    else:
                        filtered_x, filtered_y = global_x, global_y
                    
                    # Перемещаем курсор только если позиция изменилась
                    if last_position != (filtered_x, filtered_y):
                        pyautogui.moveTo(filtered_x, filtered_y, _pause=False, duration=0)
                        last_position = (filtered_x, filtered_y)
                        self.status_updated.emit(f"Стамеска найдена: ({filtered_x}, {filtered_y})")
                
                # ВЫВОД СТАТИСТИКИ КАЖДУЮ СЕКУНДУ
                current_time = time.time()
                if current_time - last_print_time >= 1.0:
                    elapsed = current_time - start_time
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    detection_rate = (detection_count / frame_count * 100) if frame_count > 0 else 0
                    
                    # Компактный вывод в статус
                    if last_position:
                        pos_str = f"({last_position[0]}, {last_position[1]})"
                        status = f"FPS: {fps:.0f} | Обнаружение: {detection_rate:.1f}% | Позиция: {pos_str}"
                    else:
                        status = f"FPS: {fps:.0f} | Обнаружение: {detection_rate:.1f}% | Поиск..."
                    
                    self.status_updated.emit(status)
                    last_print_time = current_time
                
                # Небольшая пауза для снижения нагрузки на CPU
                self.msleep(10)
                
        except Exception as e:
            self.log_message.emit(f"ОШИБКА: {e}")
            self.status_updated.emit(f"Ошибка: {str(e)}")
        finally:
            if mss_capture:
                mss_capture.close()
            
            # ФИНАЛЬНАЯ СТАТИСТИКА
            total_time = time.time() - start_time
            self.log_message.emit(f"Общее время: {total_time:.2f} сек")
            self.log_message.emit(f"Всего кадров: {frame_count:,}")
            self.log_message.emit(f"Средний FPS: {frame_count/total_time:.1f}" if total_time > 0 else "N/A")
            self.log_message.emit(f"Обнаружений: {detection_count:,}")
            self.log_message.emit(f"Процент обнаружения: {detection_count/frame_count*100:.1f}%" if frame_count > 0 else "N/A")
            
            self.log_message.emit("Поток отслеживания остановлен")
            self.status_updated.emit("Отслеживание остановлено")
    
    def stop(self):
        self.running = False

class TurnerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.vertical_offset = 50  # Смещение вниз
        self.horizontal_offset = 5  # Смещение вправо
        
        self.initUI()
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle("Токарь")
        self.setFixedSize(500, 235)
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Заголовок
        title_label = QLabel("Токарь")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            /* Убрана голубая линия: border-bottom: 2px solid {COLORS['primary']}; */
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Фрейм для информации
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background-color: {COLORS['bg_medium']};
            border-radius: 10px;
            padding: 15px;
        """)
        info_layout = QVBoxLayout(info_frame)
        
        # Информация о области поиска
        area_info = QLabel(f"Область поиска: {SEARCH_AREA['width']}x{SEARCH_AREA['height']} пикселей")
        area_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        info_layout.addWidget(area_info)
        
        # Информация о смещении
        offset_info = QLabel(f"Смещение курсора: +{self.horizontal_offset}px вправо, +{self.vertical_offset}px вниз")
        offset_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        info_layout.addWidget(offset_info)
        
        # Путь к файлу
        file_info = QLabel(f"Файл шаблона: chisel.png")
        file_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        info_layout.addWidget(file_info)
        
        # main_layout.addWidget(info_frame)
        
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
        
        # Добавляем растягивающий элемент
        main_layout.addStretch(1)
        
        # Фрейм для кнопки управления
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            background-color: {COLORS['bg_medium']};
            border-radius: 10px;
            padding: 15px;
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка Запустить/Остановить
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
        control_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)
        
        self.setLayout(main_layout)
        
        # Проверяем наличие файла
        self.check_chisel_file()
        
    def check_chisel_file(self):
        """Проверяет наличие файла chisel.png"""
        if not os.path.exists(chisel_path):
            error_msg = f"ОШИБКА: Файл не найден: {chisel_path}"
            self.status_label.setText(error_msg)
            print(f"Убедитесь, что файл находится в папке assets/turner/")
        else:
            self.status_label.setText("Состояние: готов к запуску")
        
    def toggle_tracking(self):
        """Запускает или останавливает отслеживание"""
        if self.running:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking(self):
        """Запускает отслеживание стамески"""
        # Проверяем наличие файла перед запуском
        if not os.path.exists(chisel_path):
            error_msg = f"ОШИБКА: Файл не найден: {chisel_path}"
            self.status_label.setText(error_msg)
            print(f"Убедитесь, что файл находится в папке assets/turner/")
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
        self.status_label.setText("Состояние: запуск отслеживания...")
        
        # Создаем и запускаем рабочий поток
        self.worker_thread = TurnerWorkerThread(self.vertical_offset, self.horizontal_offset)
        self.worker_thread.log_message.connect(self.print_log)
        self.worker_thread.status_updated.connect(self.update_status_label)
        self.worker_thread.start()
        
        print("=" * 60)
        print("ЗАПУСК ОТСЛЕЖИВАНИЯ СТАМЕСКИ")
        print("=" * 60)
        print(f"Смещение курсора: +{self.horizontal_offset} вправо, +{self.vertical_offset} вниз")
        print("=" * 60)
        print("Нажмите Ctrl+C в консоли для остановки")
        print("=" * 60)
    
    def stop_tracking(self):
        """Останавливает отслеживание стамески"""
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
        self.status_label.setText("Состояние: остановка...")
        
        # Останавливаем рабочий поток
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
            
        self.status_label.setText("Состояние: не активно")
        print("\n" + "=" * 60)
        print("ОТСЛЕЖИВАНИЕ ОСТАНОВЛЕНО")
        print("=" * 60)
    
    def print_log(self, message):
        """Выводит сообщение в консоль (можно расширить для окна логов)"""
        print(f"[LOG] {message}")
    
    def update_status_label(self, status_text):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {status_text}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Гарантируем остановку потока при закрытии окна
        if self.running:
            self.stop_tracking()
        event.accept()

def main():
    app = QApplication(sys.argv)
    turner_app = TurnerApp()
    turner_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()