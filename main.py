import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout,
                             QMessageBox, QDialog, QScrollArea, QCheckBox)
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


class SettingsDialog(QDialog):
    """Диалоговое окно настроек видимости модулей"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        self.load_settings()
    
    def initUI(self):
        self.setWindowTitle("Настройка ботов")
        self.setFixedSize(400, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 8px;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #00adb5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #0098a0;
            }
            QPushButton#close_btn {
                background-color: #555555;
            }
            QPushButton#close_btn:hover {
                background-color: #666666;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("Выберите отображаемые боты")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Область прокрутки для чекбоксов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #00adb5;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Контейнер для чекбоксов
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(5, 5, 5, 5)
        checkbox_layout.setSpacing(6)
        
        # Список модулей с их идентификаторами и отображаемыми названиями
        self.modules = [
            ("afk", "🎮 AFK+"),
            ("lucky_wheel", "🎡 Колесо удачи"),
            ("cooking", "👨‍🍳 Готовка"),
            ("gym", "💪 Тренажерный зал"),
            ("builder", "🏗️ Стройка"),
            ("port", "⚓ Порт"),
            ("mining", "⛏️ Шахта"),
            ("farm_cows", "🐄 Коровник"),
            ("turner", "🔧 Токарь"),
            # ("seamstress", "🧵 Швея"),
        ]
        
        self.checkboxes = {}
        
        for module_id, display_name in self.modules:
            checkbox = QCheckBox(display_name)
            checkbox.setProperty("module_id", module_id)
            checkbox_layout.addWidget(checkbox)
            self.checkboxes[module_id] = checkbox
        
        checkbox_layout.addStretch()
        scroll_area.setWidget(checkbox_container)
        layout.addWidget(scroll_area)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self.select_all)
        buttons_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Снять все")
        deselect_all_btn.clicked.connect(self.deselect_all)
        buttons_layout.addWidget(deselect_all_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_settings(self):
        """Загружает настройки видимости модулей"""
        for module_id, checkbox in self.checkboxes.items():
            visible = config.get("main_window", f"show_{module_id}", True)
            checkbox.setChecked(visible)
    
    def save_settings(self):
        """Сохраняет настройки видимости модулей"""
        for module_id, checkbox in self.checkboxes.items():
            config.set("main_window", f"show_{module_id}", checkbox.isChecked())
        
        # Обновляем главное окно
        if self.parent:
            self.parent.rebuild_modules_grid()
        
        self.close()
    
    def select_all(self):
        """Выбирает все чекбоксы"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        """Снимает все чекбоксы"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.open_windows = []  # Список открытых окон
        self.modules_frame = None  # Фрейм с модулями
        self.modules_layout = None  # Layout модулей
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
            QPushButton#settings_btn {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 14px;
            }
            QPushButton#settings_btn:hover {
                background-color: #3c3c3c;
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
        
        # Сетка с карточками модулей
        self.modules_frame = QWidget()
        self.modules_frame.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        self.modules_layout = QGridLayout(self.modules_frame)
        self.modules_layout.setSpacing(12)
        self.modules_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заполняем сетку модулями
        self.rebuild_modules_grid()
        
        main_layout.addWidget(self.modules_frame, 1)
        
        # Футер с кнопками - фиксированная высота
        footer_frame = QFrame()
        footer_frame.setMaximumHeight(50)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        
        # Левая часть футера (автор и настройки)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        
        # Ссылка на автора
        self.author_label = QLabel("by: raktoperk")
        self.author_label.setObjectName("author_label")
        self.author_label.setCursor(Qt.PointingHandCursor)
        
        # Обработчик клика по тексту автора
        def open_author_link(event):
            webbrowser.open("https://www.blast.hk/members/572838/")
        
        self.author_label.mousePressEvent = open_author_link
        left_layout.addWidget(self.author_label)
        
        # Кнопка настроек отображения ботов (под автором)
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("settings_btn")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedWidth(30)
        self.settings_btn.setFixedHeight(30)
        self.settings_btn.setFont(QFont("Arial", 25))
        self.settings_btn.setToolTip("Настройка отображаемых ботов")
        self.settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(self.settings_btn)
        
        footer_layout.addWidget(left_container)
        footer_layout.addStretch()
        
        # Кнопка доната
        self.donate_btn = QPushButton("💰 Поддержать разработчика")
        self.donate_btn.setObjectName("donate_btn")
        self.donate_btn.setCursor(Qt.PointingHandCursor)
        self.donate_btn.clicked.connect(lambda: webbrowser.open("https://donate.stream/raktoperk"))
        footer_layout.addWidget(self.donate_btn)
        
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
    
    def open_settings(self):
        """Открывает окно настроек отображения ботов"""
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def rebuild_modules_grid(self):
        """Перестраивает сетку модулей на основе сохранённых настроек"""
        # Очищаем текущие модули
        if self.modules_layout:
            while self.modules_layout.count():
                item = self.modules_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Список модулей для сетки
        all_modules = [
            ("afk", "AFK+", self.open_antiafk, "🎮"),
            ("lucky_wheel", "Колесо удачи", self.open_lucky_wheel, "🎡"),
            ("cooking", "Готовка", self.open_cooking, "👨‍🍳"),
            ("gym", "Тренажерный зал", self.open_gym, "💪"),
            ("builder", "Стройка", self.open_builder, "🏗️"),
            ("port", "Порт", self.open_port, "⚓"),
            ("mining", "Шахта", self.open_mining, "⛏️"),
            ("farm_cows", "Коровник", self.open_farm_cows, "🐄"),
            ("turner", "Токарь", self.open_turner, "🔧"),
            # ("seamstress", "Швея", self.open_seamstress, "🧵"),
        ]
        
        # Фильтруем модули по настройкам видимости
        visible_modules = []
        for module_id, title, callback, icon in all_modules:
            if config.get("main_window", f"show_{module_id}", True):
                visible_modules.append((module_id, title, callback, icon))
        
        # Создаем сетку
        row, col = 0, 0
        total_cols = 4
        
        for i, (module_id, title, callback, icon) in enumerate(visible_modules):
            module_card = self.create_module_card(icon, title, callback, module_id)
            self.modules_layout.addWidget(module_card, row, col)
            
            col += 1
            if col >= total_cols:
                col = 0
                row += 1
        
        # Если нет видимых модулей, показываем сообщение
        if not visible_modules:
            empty_label = QLabel("Нет активных ботов.\nНажмите ⚙️ Настройка ботов чтобы включить отображение.")
            empty_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 14px;
                    text-align: center;
                    padding: 40px;
                }
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.modules_layout.addWidget(empty_label, 0, 0, 1, total_cols)
        else:
            # Растягиваем колонки равномерно
            for i in range(total_cols):
                self.modules_layout.setColumnStretch(i, 1)
            
            # Растягиваем строки равномерно
            for i in range(row + 1):
                self.modules_layout.setRowStretch(i, 1)
    
    def create_module_card(self, icon, title, callback, module_id):
        """Создает компактную карточку модуля"""
        card = QPushButton()
        card.setProperty("module_id", module_id)
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
    
    # def open_seamstress(self):
    #     window = SeamstressApp()
    #     self.setup_window(window, "Швея")
    
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