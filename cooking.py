import sys
import random
import time
import logging
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit, QGridLayout,
                             QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor

from components.coordinates import cooking_coordinate

try:
    from components.styles import *
except ImportError:
    # Запасные значения если файл стилей не найден
    from components.styles import (
        COLORS, WINDOW_STYLES, BUTTON_STYLES, LABEL_STYLES, 
        CHECKBOX_STYLES, COUNTER_WINDOW_STYLES, FRAME_STYLES,
        INPUT_STYLES, GROUPBOX_STYLES
    )

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CounterWindow(QWidget):
    """Маленькое окно счетчика поверх всех окон"""
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.initUI()
        
    def initUI(self):
        # Окно поверх всех, без рамки
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        
        # Прозрачный фон
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основной фрейм с закругленными углами
        main_frame = QFrame(self)
        main_frame.setStyleSheet(COUNTER_WINDOW_STYLES["frame"])
        
        # Горизонтальный layout для текста и счетчика
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Текст
        text_label = QLabel("Приготовлено еды:")
        text_label.setStyleSheet(COUNTER_WINDOW_STYLES["text"])
        layout.addWidget(text_label)
        
        # Счетчик
        self.counter_label = QLabel("0")
        self.counter_label.setStyleSheet(COUNTER_WINDOW_STYLES["counter"])
        layout.addWidget(self.counter_label)
        
        # Добавляем растягивающий элемент
        layout.addStretch()
        
        # Устанавливаем layout для основного виджета
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # Устанавливаем фиксированный размер окна
        self.setFixedSize(250, 52)
        
        # Позиционируем в правом верхнем углу
        self.move_to_top_right()
        
    def paintEvent(self, event):
        """Переопределяем paintEvent для рисования закругленных углов"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(43, 43, 43)))
        painter.setPen(Qt.NoPen)
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 8, 8)
        
    def resizeEvent(self, event):
        """Обновляем при изменении размера"""
        super().resizeEvent(event)
        self.update()
        
    def move_to_top_right(self):
        """Помещает окно в правый верхний угол"""
        screen = QApplication.desktop().screenGeometry()
        x = screen.width() - self.width() - 20
        y = 10
        self.move(x, y)
        
    def increment_counter(self):
        """Увеличивает счетчик на 1"""
        self.counter += 1
        self.counter_label.setText(str(self.counter))
        
    def reset_counter(self):
        """Сбрасывает счетчик"""
        self.counter = 0
        self.counter_label.setText("0")
        
    def mousePressEvent(self, event):
        """Позволяет перемещать окно"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Перемещение окна"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

class CookingThread(QThread):
    """Поток для выполнения готовки"""
    status_updated = pyqtSignal(str)
    cycle_completed = pyqtSignal()
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, sequence, cycles, resolution_mode="FullHD"):
        super().__init__()
        self.sequence = sequence
        self.cycles = cycles
        self.resolution_mode = resolution_mode
        self.is_paused = False
        self.should_stop = False
        
        # Получаем координаты из общего модуля
        self.cells = cooking_coordinate.get(resolution_mode, cooking_coordinate["FullHD"])
        
    def run(self):
        try:
            self.status_updated.emit("Начинаем готовку...")
            time.sleep(2)  # Пауза перед стартом
            
            for cycle in range(self.cycles):
                if self.should_stop:
                    break
                    
                self.status_updated.emit(f"Цикл {cycle + 1}/{self.cycles}...")
                
                # Проверка паузы
                while self.is_paused and not self.should_stop:
                    time.sleep(0.5)
                    
                if self.should_stop:
                    break
                
                # Выполнение последовательности
                for action, coords in self.sequence:
                    if self.should_stop:
                        break
                        
                    # Проверка паузы
                    while self.is_paused and not self.should_stop:
                        time.sleep(0.5)
                    
                    if self.should_stop:
                        break
                    
                    # Выполняем клик
                    self.perform_click(coords)
                
                if self.should_stop:
                    break
                
                # Нажимаем кнопку готовки
                if "start_cooking" in self.cells:
                    self.perform_click(self.cells["start_cooking"], left_click=True)
                    time.sleep(1.0)
                
                # Сигнализируем о завершении цикла
                self.cycle_completed.emit()
                
                # Пауза между циклами
                if cycle < self.cycles - 1 and not self.should_stop:
                    sleep_time = random.uniform(6.0, 7.0)
                    time.sleep(sleep_time)
            
            if self.should_stop:
                self.status_updated.emit("Готовка остановлена")
            else:
                self.status_updated.emit(f"Готовка завершена! Циклов: {self.cycles}")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
    
    def perform_click(self, coords, left_click=False):
        """Выполняет клик с случайным смещением"""
        try:
            import pyautogui
            
            # Добавляем случайное смещение
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            x = coords[0] + offset_x
            y = coords[1] + offset_y
            
            # Перемещаем курсор
            pyautogui.moveTo(x, y, duration=random.uniform(0.2, 0.4))
            
            # Выполняем клик
            if left_click:
                pyautogui.click(button='left')
            else:
                pyautogui.click(button='right')
            
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            logging.error(f"Ошибка при клике: {e}")
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.should_stop = True

class CookingBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.cooking_thread = None
        self.sequence = []
        self.resolution_mode = "FullHD"
        
        # Создаем окно счетчика
        self.counter_window = CounterWindow()
        
        self.initUI()
        
    def initUI(self):
        # Настройка окна - увеличиваем высоту с 750 до 800
        self.setWindowTitle("Готовка")
        self.move(70, 40)
        self.setFixedSize(800, 800)  # Увеличили высоту окна
        self.setStyleSheet(WINDOW_STYLES["main_window"])
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Строка состояния
        self.status_label = QLabel("Состояние: Не активно")
        self.status_label.setStyleSheet(LABEL_STYLES["primary"])
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Фрейм для настроек
        settings_frame = QFrame()
        settings_frame.setStyleSheet(FRAME_STYLES["frame"])
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        settings_layout.setSpacing(10)
        
        # Поле для количество циклов
        cycles_layout = QHBoxLayout()
        cycles_label = QLabel("Количество циклов:")
        cycles_label.setStyleSheet(LABEL_STYLES["secondary"])
        cycles_layout.addWidget(cycles_label)
        
        self.cycles_entry = QLineEdit()
        self.cycles_entry.setText("1")
        self.cycles_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self.cycles_entry.setMaximumWidth(80)
        cycles_layout.addWidget(self.cycles_entry)
        cycles_layout.addStretch()
        
        settings_layout.addLayout(cycles_layout)
        
        # Фрейм для разрешения экрана
        resolution_frame = QFrame()
        resolution_frame.setStyleSheet(FRAME_STYLES["frame"])
        resolution_layout = QVBoxLayout(resolution_frame)
        resolution_layout.setContentsMargins(15, 10, 15, 10)
        resolution_layout.setSpacing(5)
        
        # Заголовок
        resolution_title = QLabel("Разрешение экрана:")
        resolution_title.setStyleSheet(LABEL_STYLES["secondary"])
        resolution_title.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(resolution_title)
        
        # Фрейм для кнопок разрешения
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet(FRAME_STYLES["frame_inner"])
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(10, 5, 10, 5)
        buttons_layout.setSpacing(15)  # Увеличиваем отступ между кнопками
        
        # Кнопка FullHD - уменьшаем минимальную ширину
        self.fullhd_button = QPushButton("FullHD")
        self.fullhd_button.setStyleSheet(BUTTON_STYLES["primary"])
        self.fullhd_button.clicked.connect(lambda: self.set_resolution("FullHD"))
        buttons_layout.addWidget(self.fullhd_button)
        
        # Кнопка QuadHD - уменьшаем минимальную ширину
        self.quadhd_button = QPushButton("QuadHD")
        self.quadhd_button.setStyleSheet(BUTTON_STYLES["secondary"])
        self.quadhd_button.clicked.connect(lambda: self.set_resolution("QuadHD"))
        buttons_layout.addWidget(self.quadhd_button)
        
        resolution_layout.addWidget(buttons_frame)
        
        # Метка текущего разрешения
        self.resolution_label = QLabel(f"Текущее: {self.resolution_mode}")
        self.resolution_label.setStyleSheet(LABEL_STYLES["muted"])
        self.resolution_label.setAlignment(Qt.AlignCenter)
        resolution_layout.addWidget(self.resolution_label)
        
        settings_layout.addWidget(resolution_frame)
        
        main_layout.addWidget(settings_frame)
        
        # Фрейм для инструментов и ячеек
        tools_frame = QFrame()
        tools_frame.setStyleSheet(FRAME_STYLES["frame"])
        tools_layout = QVBoxLayout(tools_frame)
        tools_layout.setContentsMargins(15, 10, 15, 10)
        
        # Инструменты
        tools_label = QLabel("Инструменты:")
        tools_label.setStyleSheet(LABEL_STYLES["secondary"])
        tools_layout.addWidget(tools_label)
        
        tools_buttons_layout = QHBoxLayout()
        tools = [("Нож", "knife"), ("Венчик", "whisk"), ("Огонь", "fire")]
        for text, action in tools:
            btn = QPushButton(text)
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, a=action: self.record_action(a))
            tools_buttons_layout.addWidget(btn)
        
        tools_layout.addLayout(tools_buttons_layout)
        
        # Ячейки
        cells_label = QLabel("Ячейки:")
        cells_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        tools_layout.addWidget(cells_label)
        
        # Создаем сетку для кнопок ячеек
        cells_grid = QGridLayout()
        cells_grid.setSpacing(5)
        
        # Первая строка: Вода и ячейки 1-2
        # Кнопка Вода в первой колонке
        water_btn = QPushButton("Вода")
        water_btn.setStyleSheet(BUTTON_STYLES["primary_small"])
        water_btn.clicked.connect(lambda: self.record_action("water"))
        cells_grid.addWidget(water_btn, 0, 0)
        
        # Ячейки 1-2 в колонках 1 и 2
        for i in range(1, 3):
            btn = QPushButton(f"Ячейка {i}")
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, c=f"cell_{i}": self.record_cell_action(c))
            cells_grid.addWidget(btn, 0, i)
        
        # Остальные ячейки (3-20) по 3 в строку (начиная со строки 1)
        for i in range(3, 21):
            row = ((i - 3) // 3) + 1
            col = (i - 3) % 3
            btn = QPushButton(f"Ячейка {i}")
            btn.setStyleSheet(BUTTON_STYLES["primary_small"])
            btn.clicked.connect(lambda checked, c=f"cell_{i}": self.record_cell_action(c))
            cells_grid.addWidget(btn, row, col)
        
        tools_layout.addLayout(cells_grid)
        main_layout.addWidget(tools_frame)
        
        # Фрейм для управления - ВЫСОТА ЭТОГО БЛОКА КОНТРОЛИРУЕТСЯ ЗДЕСЬ
        control_frame = QFrame()
        control_frame.setStyleSheet(FRAME_STYLES["frame"])
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        # Последовательность действий
        sequence_group = QGroupBox("Записанная последовательность:")
        sequence_group.setStyleSheet(GROUPBOX_STYLES["standard"])
        
        sequence_layout = QVBoxLayout()
        self.sequence_label = QLabel("Пусто")
        self.sequence_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                padding: 5px;
                background-color: #2b2b2b;
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        self.sequence_label.setWordWrap(True)
        sequence_layout.addWidget(self.sequence_label)
        sequence_group.setLayout(sequence_layout)
        
        control_layout.addWidget(sequence_group, 2)
        
        # Кнопки управления - УМЕНЬШАЕМ ОТСТУПЫ МЕЖДУ КНОПКАМИ
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)  # Уменьшено с 10 на 5 - это контролирует высоту между кнопками
        
        # Кнопки управления готовкой
        self.start_stop_btn = QPushButton("Запустить")
        self.start_stop_btn.setStyleSheet(BUTTON_STYLES["primary"])
        self.start_stop_btn.clicked.connect(self.toggle_cooking)
        buttons_layout.addWidget(self.start_stop_btn)
        
        # Кнопка управления окном счетчика (перемещена сюда)
        self.counter_btn = QPushButton("Показать счётчик")  # Текст изменен, так как счетчик скрыт
        self.counter_btn.setStyleSheet(BUTTON_STYLES["accent_small"])
        self.counter_btn.clicked.connect(self.toggle_counter_window)
        buttons_layout.addWidget(self.counter_btn)
        
        # Кнопки паузы
        pause_layout = QHBoxLayout()
        pause_layout.setSpacing(5)  # Уменьшаем отступ между кнопками паузы
        
        resume_btn = QPushButton("Продолжить (F7)")
        resume_btn.setStyleSheet(BUTTON_STYLES["success"])
        resume_btn.clicked.connect(self.resume_cooking)
        pause_layout.addWidget(resume_btn)
        
        pause_btn = QPushButton("Пауза (F8)")
        pause_btn.setStyleSheet(BUTTON_STYLES["success"])
        pause_btn.clicked.connect(self.pause_cooking)
        pause_layout.addWidget(pause_btn)
        
        buttons_layout.addLayout(pause_layout)
        
        control_layout.addLayout(buttons_layout, 1)
        main_layout.addWidget(control_frame)

        reset_btn = QPushButton("Сбросить последовательность")
        reset_btn.setStyleSheet(BUTTON_STYLES["danger_small"])
        reset_btn.clicked.connect(self.reset_sequence)
        buttons_layout.addWidget(reset_btn)
        
        # Убрал кнопку счетчика из main_layout, так как она теперь в блоке управления
        
        self.setLayout(main_layout)
        
        # Счетчик теперь изначально СКРЫТ - убрал строку показа счетчика
        # self.counter_window.show() - УДАЛЕНО
        
        # Устанавливаем горячие клавиши
        self.setup_hotkeys()
        
    def set_resolution(self, mode):
        """Устанавливает разрешение экрана"""
        self.resolution_mode = mode
        self.resolution_label.setText(f"Текущее: {self.resolution_mode}")
        
        # Обновляем стили кнопок
        if mode == "FullHD":
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["primary"])
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["secondary"])
        else:
            self.fullhd_button.setStyleSheet(BUTTON_STYLES["secondary"])
            self.quadhd_button.setStyleSheet(BUTTON_STYLES["primary"])
    
    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        # В PyQt5 горячие клавиши обрабатываются через keyPressEvent
        pass
    
    def keyPressEvent(self, event):
        """Обработка горячих клавиш"""
        if event.key() == Qt.Key_F7:
            self.resume_cooking()
        elif event.key() == Qt.Key_F8:
            self.pause_cooking()
        else:
            super().keyPressEvent(event)
    
    def record_action(self, action):
        """Запись действия инструмента"""
        try:
            cells = cooking_coordinate.get(self.resolution_mode, cooking_coordinate["FullHD"])
            if action in cells:
                coords = cells[action]
                self.sequence.append((action, coords))
                self.update_sequence_display()
            else:
                logging.error(f"Неизвестное действие: {action}")
        except Exception as e:
            logging.error(f"Ошибка записи действия: {e}")
    
    def record_cell_action(self, cell_key):
        """Запись ячейки"""
        try:
            cells = cooking_coordinate.get(self.resolution_mode, cooking_coordinate["FullHD"])
            if cell_key in cells:
                coords = cells[cell_key]
                self.sequence.append((cell_key, coords))
                self.update_sequence_display()
            else:
                logging.error(f"Неизвестная ячейка: {cell_key}")
        except Exception as e:
            logging.error(f"Ошибка записи ячейки: {e}")
    
    def update_sequence_display(self):
        """Обновление отображения последовательности"""
        sequence_text = ", ".join([f"{action}" for action, _ in self.sequence])
        self.sequence_label.setText(sequence_text if sequence_text else "Пусто")
    
    def reset_sequence(self):
        """Сброс последовательности"""
        self.sequence = []
        self.update_sequence_display()
        self.status_label.setText("Состояние: Последовательность сброшена")
    
    def pause_cooking(self):
        """Пауза готовки"""
        if self.cooking_thread and not self.cooking_thread.is_paused:
            self.cooking_thread.pause()
            self.status_label.setText("Состояние: На паузе (F7 - продолжить)")
    
    def resume_cooking(self):
        """Продолжение готовки"""
        if self.cooking_thread and self.cooking_thread.is_paused:
            self.cooking_thread.resume()
            self.status_label.setText("Состояние: Активно")
    
    def toggle_cooking(self):
        """Запуск/остановка готовки"""
        if self.running:
            self.stop_cooking()
        else:
            self.start_cooking()
    
    def start_cooking(self):
        """Запуск готовки"""
        if not self.sequence:
            QMessageBox.warning(self, "Ошибка", "Последовательность пуста!")
            return
        
        try:
            cycles = int(self.cycles_entry.text())
            if cycles <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректное число циклов")
            return
        
        # Сбрасываем счетчик перед началом готовки
        self.counter_window.reset_counter()
        
        self.running = True
        self.start_stop_btn.setText("Остановить")
        self.start_stop_btn.setStyleSheet(BUTTON_STYLES["danger"])
        
        # Создаем и запускаем поток готовки
        self.cooking_thread = CookingThread(self.sequence, cycles, self.resolution_mode)
        self.cooking_thread.status_updated.connect(self.update_status_label)
        self.cooking_thread.cycle_completed.connect(self.increment_counter)
        self.cooking_thread.finished.connect(self.on_cooking_finished)
        self.cooking_thread.error_occurred.connect(self.on_cooking_error)
        self.cooking_thread.start()
        
        self.status_label.setText("Состояние: Начинаем готовку...")
    
    def stop_cooking(self):
        """Остановка готовки"""
        if self.cooking_thread:
            self.cooking_thread.stop()
            self.cooking_thread.wait()
        
        self.running = False
        self.start_stop_btn.setText("Запустить")
        self.start_stop_btn.setStyleSheet(BUTTON_STYLES["primary"])
    
    def on_cooking_finished(self):
        """Обработка завершения готовки"""
        self.running = False
        self.start_stop_btn.setText("Запустить")
        self.start_stop_btn.setStyleSheet(BUTTON_STYLES["primary"])
    
    def on_cooking_error(self, error_msg):
        """Обработка ошибки готовки"""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при готовке: {error_msg}")
        self.stop_cooking()
    
    def increment_counter(self):
        """Увеличивает счетчик приготовленной еды"""
        self.counter_window.increment_counter()
    
    def toggle_counter_window(self):
        """Показать/скрыть окно счетчика"""
        if self.counter_window.isVisible():
            self.counter_window.hide()
            self.counter_btn.setText("Показать счётчик")
        else:
            self.counter_window.show()
            self.counter_window.move_to_top_right()
            self.counter_btn.setText("Скрыть счётчик")
    
    def update_status_label(self, status_text):
        """Обновляет метку статуса"""
        self.status_label.setText(f"Состояние: {status_text}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Останавливаем готовку
        if self.running:
            self.stop_cooking()
        
        # Закрываем окно счетчика
        self.counter_window.close()
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    cooking_app = CookingBotApp()
    cooking_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()