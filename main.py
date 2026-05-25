import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout,
                             QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

# Импортируем все модули
from builder import BuilderApp
from cooking import CookingBotApp
from gym import GymApp
from lucky_wheel import LuckyWheelApp
from mining import MiningBotApp
from port import PortApp
from antiafk import MainWindow as AntiAFKWindow
from turner import TurnerApp
from seamstress import SeamstressApp
from catch_pda import CatchPDAApp
from farm_cows import FarmCowsApp
from components.config_manager import config

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.open_windows = []  # Список открытых окон
        self.initUI()
        
    def initUI(self):
        # Настройки главного окна
        self.setWindowTitle("Extra Hands - Бесплатный бот для всех желающих")
        self.setGeometry(100, 100, 900, 500)
        self.setWindowIcon(QIcon('assets/icons/EHIcon.png'))
        
        # Стиль приложения
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton#donate_btn {
                background-color: #ff9800;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#donate_btn:hover {
                background-color: #f57c00;
            }
            QPushButton#donate_btn:pressed {
                background-color: #ef6c00;
            }
            QPushButton#reset_btn {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#reset_btn:hover {
                background-color: #7B1FA2;
            }
            QPushButton#reset_btn:pressed {
                background-color: #6A1B9A;
            }
            QLabel#author_label {
                color: #aaaaaa;
                font-size: 12px;
                text-decoration: none;
            }
            QLabel#author_label:hover {
                color: #00adb5;
                text-decoration: underline;
                cursor: pointer;
            }
        """)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # Заголовок приложения - минимальная высота
        header_frame = QFrame()
        header_frame.setMaximumHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)
        
        title_label = QLabel("Extra Hands")
        title_label.setFont(QFont("Arial", 30, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Бесплатный бот для всех желающих")
        subtitle_label.setFont(QFont("Arial", 13))
        subtitle_label.setStyleSheet("color: #aaaaaa;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        # Разделитель - тонкая линия
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #555555;")
        separator.setMaximumHeight(1)
        main_layout.addWidget(separator)
        
        # Сетка с карточками модулей 4x3
        self.create_modules_grid(main_layout)
        
        # Футер с кнопками - фиксированная высота
        footer_frame = QFrame()
        footer_frame.setMaximumHeight(50)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        
        # Ссылка на автора (левый нижний угол)
        self.author_label = QLabel("by: raktoperk")
        self.author_label.setObjectName("author_label")
        self.author_label.setCursor(Qt.PointingHandCursor)
        
        # Обработчик клика по тексту автора
        def open_author_link(event):
            webbrowser.open("https://www.blast.hk/members/572838/")
        
        self.author_label.mousePressEvent = open_author_link
        
        # Кнопка доната
        self.donate_btn = QPushButton("💰 Поддержать разработчика")
        self.donate_btn.setObjectName("donate_btn")
        self.donate_btn.setCursor(Qt.PointingHandCursor)
        self.donate_btn.clicked.connect(lambda: webbrowser.open("https://donate.stream/raktoperk"))
        
        # Кнопка сброса всех настроек
        self.reset_btn = QPushButton("⚙️ Сбросить все настройки")
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset_all_settings)
        
        # Кнопка закрытия всех окон
        self.close_all_btn = QPushButton("❌ Закрыть все окна")
        self.close_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #5d5d5d;
                color: #888888;
            }
        """)
        self.close_all_btn.clicked.connect(self.close_all_windows)
        self.close_all_btn.setEnabled(False)
        
        # Добавляем элементы в футер
        footer_layout.addWidget(self.author_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.donate_btn)
        footer_layout.addWidget(self.reset_btn)
        footer_layout.addWidget(self.close_all_btn)
        
        main_layout.addWidget(footer_frame)
        
        # Индикатор открытых окон
        self.windows_label = QLabel("Открытые окна: 0")
        self.windows_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
            }
        """)
        self.windows_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.windows_label)
    
    def reset_all_settings(self):
        """Сброс всех настроек к значениям по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Сброс настроек",
            "Вы уверены, что хотите сбросить ВСЕ настройки ботов к значениям по умолчанию?\n"
            "Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            config.reset_all()
            QMessageBox.information(
                self,
                "Сброс выполнен",
                "Все настройки сброшены до значений по умолчанию.\n"
                "При следующем запуске ботов настройки будут загружены заново."
            )
    
    def create_modules_grid(self, main_layout):
        """Создает сетку с карточками модулей 4x3"""
        modules_frame = QWidget()
        modules_frame.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        modules_layout = QGridLayout(modules_frame)
        modules_layout.setSpacing(12)
        modules_layout.setContentsMargins(0, 0, 0, 0)
        
        # Список модулей для сетки 4x3
        modules_info = [
            ("🎮", "AFK+", self.open_antiafk),
            ("🎡", "Колесо удачи", self.open_lucky_wheel),
            ("👨‍🍳", "Готовка", self.open_cooking),
            ("💪", "Тренажерный зал", self.open_gym),
            ("🏗️", "Стройка", self.open_builder),
            ("⚓", "Порт", self.open_port),
            ("⛏️", "Шахта", self.open_mining),
            ("🐄", "Коровник", self.open_farm_cows),
            ("🔧", "Токарь", self.open_turner),
            ("🧵", "Швея", self.open_seamstress),
        ]
        
        # Создаем сетку 4x3
        row, col = 0, 0
        total_rows = 3
        total_cols = 4
        
        for i in range(total_rows * total_cols):
            if i < len(modules_info):
                icon, title, callback = modules_info[i]
                module_card = self.create_module_card(icon, title, callback)
            else:
                # Создаем пустую карточку-заполнитель
                module_card = self.create_empty_card()
            
            modules_layout.addWidget(module_card, row, col)
            col += 1
            if col >= total_cols:
                col = 0
                row += 1
        
        # Растягиваем колонки равномерно
        for i in range(total_cols):
            modules_layout.setColumnStretch(i, 1)
        
        # Растягиваем строки равномерно
        for i in range(total_rows):
            modules_layout.setRowStretch(i, 1)
        
        # Добавляем модули в основной layout
        main_layout.addWidget(modules_frame, 1)
    
    def create_module_card(self, icon, title, callback):
        """Создает компактную карточку модуля без описания"""
        card = QPushButton()
        card.setMinimumSize(180, 100)
        card.setMaximumSize(220, 120)
        card.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                border: 2px solid #3c3c3c;
                border-radius: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #333333;
                border: 2px solid #00adb5;
            }
            QPushButton:pressed {
                background-color: #3c3c3c;
                border: 2px solid #00888f;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(4)
        
        # Иконка
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 22))
        icon_label.setStyleSheet("color: #ffffff;")
        icon_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_label)
        
        # Название
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        
        card.setToolTip(f"Нажмите, чтобы открыть {title}")
        card.clicked.connect(callback)
        
        return card
    
    def create_empty_card(self):
        """Создает пустую карточку-заполнитель"""
        card = QWidget()
        card.setMinimumSize(180, 100)
        card.setMaximumSize(220, 120)
        card.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        return card
    
    def open_farm_cows(self):
        window = FarmCowsApp()
        self.setup_window(window, "Коровник")

    def open_turner(self):
        window = TurnerApp()
        self.setup_window(window, "Токарь")
    
    def open_seamstress(self):
        window = SeamstressApp()
        self.setup_window(window, "Швея")
    
    def open_builder(self):
        window = BuilderApp()
        self.setup_window(window, "Стройка")
    
    def open_cooking(self):
        window = CookingBotApp()
        self.setup_window(window, "Готовка")
    
    def open_gym(self):
        window = GymApp()
        self.setup_window(window, "Тренажерный зал")
    
    def open_lucky_wheel(self):
        window = LuckyWheelApp()
        self.setup_window(window, "Колесо удачи")
    
    def open_mining(self):
        window = MiningBotApp()
        self.setup_window(window, "Шахта")
    
    def open_port(self):
        window = PortApp()
        self.setup_window(window, "Порт")
    
    def open_antiafk(self):
        window = AntiAFKWindow()
        self.setup_window(window, "Anti-AFK")
    
    def open_catch_pda(self):
        window = CatchPDAApp()
        self.setup_window(window, "Catch PDA")
    
    def setup_window(self, window, title):
        """Настраивает и показывает окно"""
        original_close = window.closeEvent
        
        def custom_close(event):
            if window in self.open_windows:
                self.open_windows.remove(window)
                self.update_windows_counter()
            if original_close:
                original_close(event)
        
        window.closeEvent = custom_close
        
        def on_destroyed():
            if window in self.open_windows:
                self.open_windows.remove(window)
                self.update_windows_counter()
        
        window.destroyed.connect(on_destroyed)
        
        self.open_windows.append(window)
        window.setWindowTitle(f"{title} - Extra Hands")
        window.show()
        self.update_windows_counter()
    
    def update_windows_counter(self):
        count = len(self.open_windows)
        self.windows_label.setText(f"Открытые окна: {count}")
        self.close_all_btn.setEnabled(count > 0)
    
    def close_all_windows(self):
        for window in self.open_windows[:]:
            if window and hasattr(window, 'close'):
                try:
                    window.close()
                except:
                    pass
        
        self.open_windows.clear()
        self.update_windows_counter()
    
    def closeEvent(self, event):
        self.close_all_windows()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Темная палитра
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2b2b2b;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
    """)
    
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()