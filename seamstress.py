from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import time
import random
import os
from datetime import datetime

try:
    from components.styles import *
except ImportError:
    COLORS = {
        "primary": "#00adb5",
        "primary_hover": "#0098a0",
        "primary_pressed": "#01959c",
        "accent": "#ff9800",
        "accent_hover": "#f57c00",
        "accent_pressed": "#ef6c00",
        "danger": "#ca162e",
        "danger_hover": "#be0f27",
        "danger_pressed": "#b41227",
        "bg_dark": "#2b2b2b",
        "bg_medium": "#3c3c3c",
        "bg_light": "#1e1e1e",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_muted": "#aaaaaa",
        "text_error": "#ff9999",
        "border": "#555555",
    }

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.log_count = 0
        self.error_count = 0
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        self.setWindowTitle("Логи швеи")
        self.setFixedSize(700, 400)
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Верхняя панель
        top_panel = QHBoxLayout()
        
        clear_all_btn = QPushButton("Очистить всё")
        clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["accent"]};
                color: {COLORS["text_primary"]};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS["accent_hover"]}; }}
            QPushButton:pressed {{ background-color: {COLORS["accent_pressed"]}; }}
        """)
        clear_all_btn.clicked.connect(self.clear_all_logs)
        top_panel.addWidget(clear_all_btn)
        
        clear_errors_btn = QPushButton("Очистить ошибки")
        clear_errors_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["danger"]};
                color: {COLORS["text_primary"]};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS["danger_hover"]}; }}
            QPushButton:pressed {{ background-color: {COLORS["danger_pressed"]}; }}
        """)
        clear_errors_btn.clicked.connect(self.clear_errors)
        top_panel.addWidget(clear_errors_btn)
        
        top_panel.addStretch()
        main_layout.addLayout(top_panel)
        
        # Основное содержимое
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Логи
        log_group = QGroupBox("Логи")
        log_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS["text_primary"]};
                font-size: 12px;
                font-weight: bold;
                border: 1px solid {COLORS["border"]};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
        """)
        
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS["bg_light"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 5px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 5px;
            }}
        """)
        log_layout.addWidget(self.log_text)
        
        # Ошибки
        error_group = QGroupBox("Ошибки")
        error_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS["text_error"]};
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #ff4444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
        """)
        
        error_layout = QVBoxLayout(error_group)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #2a1a1a;
                color: {COLORS["text_error"]};
                border: 1px solid #ff4444;
                border-radius: 5px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 5px;
            }}
        """)
        error_layout.addWidget(self.error_text)
        
        content_layout.addWidget(log_group, 1)
        content_layout.addWidget(error_group, 1)
        main_layout.addLayout(content_layout)
        
        # Статистика
        stats_layout = QHBoxLayout()
        
        self.log_count_label = QLabel("Логов: 0")
        self.log_count_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS["text_primary"]};
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                background-color: #333333;
                border-radius: 3px;
            }}
        """)
        stats_layout.addWidget(self.log_count_label)
        
        self.error_count_label = QLabel("Ошибок: 0")
        self.error_count_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS["text_error"]};
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                background-color: #442222;
                border-radius: 3px;
            }}
        """)
        stats_layout.addWidget(self.error_count_label)
        
        stats_layout.addStretch()
        
        copy_errors_btn = QPushButton("Копировать ошибки")
        copy_errors_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["primary"]};
                color: {COLORS["text_primary"]};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS["primary_hover"]}; }}
            QPushButton:pressed {{ background-color: {COLORS["primary_pressed"]}; }}
        """)
        copy_errors_btn.clicked.connect(self.copy_errors_to_clipboard)
        stats_layout.addWidget(copy_errors_btn)
        
        main_layout.addLayout(stats_layout)
        self.setLayout(main_layout)
    
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
        self.log_count += 1
        self.log_count_label.setText(f"Логов: {self.log_count}")
        
        # Проверка на ошибку
        error_keywords = ['ОШИБКА', 'ERROR', 'EXCEPTION', 'FAIL', 'FAILED', 'КРИТИЧЕСКАЯ', 'WARNING', 'ВНИМАНИЕ']
        if any(keyword in message.upper() for keyword in error_keywords):
            self.add_error(message)
    
    def add_error(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.error_text.append(f"[{timestamp}] {message}")
        self.error_text.verticalScrollBar().setValue(self.error_text.verticalScrollBar().maximum())
        
        self.error_count += 1
        self.error_count_label.setText(f"Ошибок: {self.error_count}")
    
    def clear_all_logs(self):
        self.log_text.clear()
        self.error_text.clear()
        self.log_count = 0
        self.error_count = 0
        self.log_count_label.setText("Логов: 0")
        self.error_count_label.setText("Ошибок: 0")
    
    def clear_errors(self):
        self.error_text.clear()
        self.error_count = 0
        self.error_count_label.setText("Ошибок: 0")
    
    def copy_errors_to_clipboard(self):
        errors = self.error_text.toPlainText()
        if errors:
            clipboard = QApplication.clipboard()
            clipboard.setText(errors)
            
            btn = self.sender()
            if btn:
                original_text = btn.text()
                btn.setText("Скопировано!")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1500, lambda: btn.setText(original_text))

class SeamstressWorker(QThread):
    log_message = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    action_updated = pyqtSignal(str)
    
    def __init__(self, total_time_sec, images_folder, min_delay=0.1, max_delay=0.3):
        super().__init__()
        self.running = True
        self.total_time_sec = total_time_sec
        self.images_folder = images_folder
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.pyautogui = None
        self.coordinates = {}
        
    def init_pyautogui(self):
        """Ленивая инициализация pyautogui"""
        if self.pyautogui is None:
            import pyautogui
            self.pyautogui = pyautogui
            self.pyautogui.PAUSE = 0.1
            self.pyautogui.FAILSAFE = False
    
    def find_image(self, image_name):
        """Ищет изображение на экране с разными уровнями уверенности"""
        try:
            filepath = os.path.join(self.images_folder, image_name)
            for confidence in [0.9, 0.85, 0.8, 0.75]:
                try:
                    location = self.pyautogui.locateOnScreen(filepath, confidence=confidence)
                    if location:
                        x = location.left + location.width // 2
                        y = location.top + location.height // 2
                        return (x, y, confidence)
                except self.pyautogui.ImageNotFoundException:
                    continue
        except Exception as e:
            self.log_message.emit(f"Ошибка при поиске {image_name}: {e}")
        return None
    
    def click_at_position(self, x, y, click_type="left", delay=0.1):
        """Выполняет клик по указанным координатам"""
        try:
            move_duration = random.uniform(0.15, 0.3)
            self.pyautogui.moveTo(x, y, duration=move_duration)
            time.sleep(0.1)
            
            if click_type == "left":
                self.pyautogui.click(button='left')
            elif click_type == "double":
                self.pyautogui.click()
                time.sleep(random.uniform(0.3, 0.8))
                self.pyautogui.click()
            
            time.sleep(delay)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка при клике: {e}")
            return False
    
    def execute_click_sequence(self):
        """Выполняет последовательность кликов"""
        self.log_message.emit("Начинаю последовательность кликов...")
        
        # Клик по 1.png
        if "1.png" in self.coordinates:
            x, y = self.coordinates["1.png"]
            self.action_updated.emit(f"Клик по 1.png")
            self.click_at_position(x, y, "left", 0.3)
        
        # Двойные клики по 2-19.png
        for i in range(2, 20):
            if not self.running:
                break
                
            filename = f"{i}.png"
            if filename in self.coordinates:
                self.action_updated.emit(f"Двойной клик по {filename}")
                x, y = self.coordinates[filename]
                self.click_at_position(x, y, "double", 0.2)
                
                if i < 19:
                    time.sleep(random.uniform(self.min_delay, self.max_delay))
        
        # Клик по 20.png
        if "20.png" in self.coordinates:
            x, y = self.coordinates["20.png"]
            self.action_updated.emit("Клик по 20.png")
            self.click_at_position(x, y, "left", 0.2)
        
        self.log_message.emit("Последовательность завершена!")
    
    def run(self):
        self.init_pyautogui()
        self.log_message.emit("Запуск потока швеи")
        self.status_updated.emit("Ожидание 1.png...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                self.log_message.emit(f"Цикл #{cycle_count}")
                
                # Ожидание 1.png
                found_1 = False
                while self.running and not found_1:
                    self.action_updated.emit("Поиск 1.png...")
                    result = self.find_image("1.png")
                    
                    if result:
                        x, y, confidence = result
                        self.log_message.emit(f"✓ Найдено: 1.png ({confidence:.2f})")
                        found_1 = True
                        self.coordinates = {"1.png": (x, y)}
                        break
                    
                    time.sleep(0.3)
                
                if not self.running:
                    break
                
                # Поиск остальных изображений
                found_count = 1
                for i in range(2, 21):
                    if not self.running:
                        break
                        
                    filename = f"{i}.png"
                    self.action_updated.emit(f"Поиск {filename}...")
                    
                    result = self.find_image(filename)
                    if result:
                        x, y, confidence = result
                        self.log_message.emit(f"✓ Найдено: {filename} ({confidence:.2f})")
                        self.coordinates[filename] = (x, y)
                        found_count += 1
                        time.sleep(random.uniform(0.05, 0.15))
                
                self.log_message.emit(f"Найдено: {found_count}/20")
                
                if found_count >= 2:
                    self.execute_click_sequence()
                    self.status_updated.emit(f"Цикл #{cycle_count} завершен")
                    
                    # Ожидание перед следующим циклом
                    if self.total_time_sec > 0:
                        remaining = self.total_time_sec
                        while self.running and remaining > 0:
                            self.status_updated.emit(f"Ожидание: {remaining} сек")
                            time.sleep(1)
                            remaining -= 1
                else:
                    self.log_message.emit("Недостаточно изображений. Пропускаю цикл.")
                    time.sleep(2)
                    
            except Exception as e:
                self.log_message.emit(f"Ошибка в цикле: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
        
        self.log_message.emit("Поток швеи остановлен")
    
    def stop(self):
        self.running = False

class SeamstressApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.worker_thread = None
        self.total_time_sec = 35
        self.min_delay = 0.1
        self.max_delay = 0.3
        self.images_folder = os.path.join(BASE_DIR, "assets", "seamstress")
        
        self.log_window = LogWindow()
        
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Швея - Последовательный кликер")
        self.setFixedSize(550, 400)
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Статус
        self.status_label = QLabel("Состояние: не активно")
        self.status_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Действие
        self.action_label = QLabel("Текущее действие: ожидание")
        self.action_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding: 8px;
            background-color: {COLORS['bg_medium']};
            border-radius: 8px;
        """)
        self.action_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.action_label)
        
        # Настройки
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"background-color: {COLORS['bg_medium']}; border-radius: 10px;")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        settings_layout.setSpacing(10)
        
        settings_title = QLabel("Настройки:")
        settings_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: bold;")
        settings_title.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(settings_title)
        
        # Время выполнения
        time_layout = QHBoxLayout()
        time_label = QLabel("Время выполнения (сек):")
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        time_layout.addWidget(time_label)
        
        self.time_entry = QLineEdit(str(self.total_time_sec))
        self.time_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
                min-width: 70px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}
        """)
        self.time_entry.setMaximumWidth(100)
        time_layout.addWidget(self.time_entry)
        time_layout.addStretch()
        settings_layout.addLayout(time_layout)
        
        # Задержки
        delays_layout = QVBoxLayout()
        
        min_layout = QHBoxLayout()
        min_label = QLabel("Мин. задержка (сек):")
        min_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        min_layout.addWidget(min_label)
        
        self.min_delay_entry = QLineEdit(str(self.min_delay))
        self.min_delay_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
                min-width: 70px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}
        """)
        self.min_delay_entry.setMaximumWidth(100)
        min_layout.addWidget(self.min_delay_entry)
        min_layout.addStretch()
        delays_layout.addLayout(min_layout)
        
        max_layout = QHBoxLayout()
        max_label = QLabel("Макс. задержка (сек):")
        max_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        max_layout.addWidget(max_label)
        
        self.max_delay_entry = QLineEdit(str(self.max_delay))
        self.max_delay_entry.setStyleSheet(self.min_delay_entry.styleSheet())
        self.max_delay_entry.setMaximumWidth(100)
        max_layout.addWidget(self.max_delay_entry)
        max_layout.addStretch()
        delays_layout.addLayout(max_layout)
        
        settings_layout.addLayout(delays_layout)
        
        # Информация о папке
        images_info = QLabel(f"Папка: {self.images_folder}")
        images_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        images_info.setWordWrap(True)
        settings_layout.addWidget(images_info)
        
        main_layout.addWidget(settings_frame)
        main_layout.addStretch(1)
        
        # Управление
        control_frame = QFrame()
        control_frame.setStyleSheet(f"background-color: {COLORS['bg_medium']}; border-radius: 10px;")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 10, 20, 10)
        
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
            QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}
            QPushButton:pressed {{ background-color: {COLORS['primary_pressed']}; }}
        """)
        self.toggle_button.clicked.connect(self.toggle_bot)
        control_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(control_frame)
        
        # Кнопка логов
        log_layout = QHBoxLayout()
        log_layout.addStretch()
        
        self.log_btn = QPushButton("Показать логи")
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #546E7A; }
            QPushButton:pressed { background-color: #455A64; }
        """)
        self.log_btn.clicked.connect(self.toggle_log_window)
        log_layout.addWidget(self.log_btn)
        
        main_layout.addLayout(log_layout)
        self.setLayout(main_layout)
        
        self.check_images_folder()
    
    def check_images_folder(self):
        """Проверяет наличие изображений"""
        if not os.path.exists(self.images_folder):
            error_msg = "Папка с изображениями не найдена!"
            self.status_label.setText(error_msg)
            self.add_log(f"ВНИМАНИЕ: {error_msg}")
            return False
        
        missing_files = [f"{i}.png" for i in range(1, 21) 
                        if not os.path.exists(os.path.join(self.images_folder, f"{i}.png"))]
        
        if missing_files:
            error_msg = f"Отсутствуют файлы: {', '.join(missing_files[:3])}{'...' if len(missing_files) > 3 else ''}"
            self.status_label.setText(error_msg)
            self.add_log(f"ВНИМАНИЕ: {error_msg}")
            return False
        
        self.add_log(f"Все 20 файлов найдены в папке: {self.images_folder}")
        return True
    
    def toggle_log_window(self):
        if self.log_window.isVisible():
            self.log_window.hide()
            self.log_btn.setText("Показать логи")
        else:
            self.log_window.show()
            screen_geometry = QApplication.desktop().availableGeometry()
            x = screen_geometry.width() - self.log_window.width() - 20
            y = screen_geometry.height() - self.log_window.height() - 20
            self.log_window.move(x, y)
            self.log_btn.setText("Скрыть логи")
    
    def toggle_bot(self):
        if self.running:
            self.stop_bot()
        else:
            self.start_bot()
    
    def start_bot(self):
        if not self.check_images_folder():
            return
        
        try:
            self.total_time_sec = int(self.time_entry.text())
            self.min_delay = float(self.min_delay_entry.text())
            self.max_delay = float(self.max_delay_entry.text())
            
            if self.total_time_sec < 0:
                raise ValueError("Время не может быть отрицательным")
            if self.min_delay < 0 or self.max_delay < 0:
                raise ValueError("Задержки не могут быть отрицательными")
            if self.min_delay > self.max_delay:
                raise ValueError("Мин. задержка должна быть меньше макс.")
                
        except ValueError as e:
            error_msg = f"Ошибка: {str(e)}"
            self.status_label.setText(error_msg)
            self.add_log(f"ОШИБКА: {error_msg}")
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
            QPushButton:hover {{ background-color: {COLORS['danger_hover']}; }}
            QPushButton:pressed {{ background-color: {COLORS['danger_pressed']}; }}
        """)
        self.status_label.setText("Запуск...")
        self.action_label.setText("Инициализация")
        
        self.worker_thread = SeamstressWorker(self.total_time_sec, self.images_folder, self.min_delay, self.max_delay)
        self.worker_thread.log_message.connect(self.add_log)
        self.worker_thread.status_updated.connect(self.update_status_label)
        self.worker_thread.action_updated.connect(self.update_action_label)
        self.worker_thread.start()
        
        self.add_log(f"Бот запущен. Время выполнения: {self.total_time_sec} сек")
        self.add_log(f"Задержки: {self.min_delay:.2f} - {self.max_delay:.2f} сек")
    
    def stop_bot(self):
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
            QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}
            QPushButton:pressed {{ background-color: {COLORS['primary_pressed']}; }}
        """)
        self.status_label.setText("Не активно")
        self.action_label.setText("Ожидание")
        
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.worker_thread = None
        
        self.add_log("Бот остановлен")
    
    def add_log(self, message):
        self.log_window.add_log(message)
    
    def update_status_label(self, status_text):
        self.status_label.setText(f"Состояние: {status_text}")
    
    def update_action_label(self, action_text):
        self.action_label.setText(f"Текущее действие: {action_text}")
    
    def closeEvent(self, event):
        if self.running:
            self.stop_bot()
        self.log_window.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    seamstress_app = SeamstressApp()
    seamstress_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()