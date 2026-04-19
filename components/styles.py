"""
Единые стили для всех ботов
Минималистичная цветовая палитра
"""

# Основная цветовая палитра
COLORS = {
    # Основные цвета
    "primary": "#00adb5",        # Зеленый
    "primary_hover": "#0098a0",  # Зеленый (при наведении)
    "primary_pressed": "#01959c", # Зеленый (при нажатии)
    
    "secondary": "#acacac",      # Синий
    "secondary_hover": "#A5A5A5", # Синий (при наведении)
    "secondary_pressed": "#919191", # Синий (при нажатии)
    
    "accent": "#00c7d1",         # Фиолетовый
    "accent_hover": "#00b0b9",   # Фиолетовый (при наведении)
    "accent_pressed": "#00a0a8", # Фиолетовый (при нажатии)
    
    "danger": "#ca162e",         # Красный
    "danger_hover": "#be0f27",   # Красный (при наведении)
    "danger_pressed": "#b41227", # Красный (при нажатии)
    
    "warning": "#00c7d1",        # Оранжевый
    "warning_hover": "#00b0b9",  # Оранжевый (при наведении)
    
    "success": "#00c7d1",        # Светло-зеленый
    "success_hover": "#00b0b9",  # Светло-зеленый (при наведении)
    
    # Фоны
    "bg_dark": "#2b2b2b",        # Темный фон
    "bg_medium": "#3c3c3c",      # Средний фон
    "bg_light": "#1e1e1e",       # Светлый фон
    
    # Текст
    "text_primary": "#ffffff",   # Основной текст
    "text_secondary": "#cccccc", # Вторичный текст
    "text_muted": "#aaaaaa",     # Приглушенный текст
    "text_error": "#ff9999",     # Текст ошибки
    
    # Границы
    "border": "#555555",         # Стандартная граница
    "border_error": "#ff4444",   # Граница ошибки
    "border_accent": "#9C27B0",  # Акцентная граница
}

# Основные стили окон
WINDOW_STYLES = {
    "main_window": f"""
        background-color: {COLORS["bg_dark"]};
    """,
    
    "title": f"""
        color: {COLORS["text_primary"]};
        font-size: 16px;
        font-weight: bold;
    """,
    
    "status": f"""
        color: {COLORS["text_primary"]};
        font-size: 14px;
        font-weight: bold;
        padding: 5px;
    """,
}

# Стили кнопок
BUTTON_STYLES = {
    "primary": f"""
        QPushButton {{
            background-color: {COLORS["primary"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["primary_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["primary_pressed"]};
        }}
    """,
    
    "primary_small": f"""
        QPushButton {{
            background-color: {COLORS["primary"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: bold;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["primary_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["primary_pressed"]};
        }}
    """,
    
    "secondary": f"""
        QPushButton {{
            background-color: {COLORS["secondary"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["secondary_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["secondary_pressed"]};
        }}
    """,
    
    "secondary_small": f"""
        QPushButton {{
            background-color: {COLORS["secondary"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: bold;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["secondary_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["secondary_pressed"]};
        }}
    """,
    
    "accent": f"""
        QPushButton {{
            background-color: {COLORS["accent"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_pressed"]};
        }}
    """,
    
    "accent_small": f"""
        QPushButton {{
            background-color: {COLORS["accent"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: bold;
            min-width: 140px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_pressed"]};
        }}
    """,
    
    "danger": f"""
        QPushButton {{
            background-color: {COLORS["danger"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["danger_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["danger_pressed"]};
        }}
    """,
    
    "danger_small": f"""
        QPushButton {{
            background-color: {COLORS["danger"]};
            color: {COLORS["text_primary"]};
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: bold;
            min-width: 140px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["danger_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["danger_pressed"]};
        }}
    """,
    
    "warning": f"""
        QPushButton {{
            background-color: {COLORS["warning"]};
            color: black;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 11px;
            font-weight: bold;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["warning_hover"]};
        }}
    """,
    
    "success": f"""
        QPushButton {{
            background-color: {COLORS["success"]};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 11px;
            font-weight: bold;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["success_hover"]};
        }}
    """,
    
    "log_button": f"""
        QPushButton {{
            background-color: #607D8B;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: bold;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: #546E7A;
        }}
        QPushButton:pressed {{
            background-color: #455A64;
        }}
    """
}

# Стили фреймов и контейнеров
FRAME_STYLES = {
    "frame": f"""
        background-color: {COLORS["bg_medium"]};
        border-radius: 10px;
    """,
    
    "frame_light": f"""
        background-color: {COLORS["bg_light"]};
        border-radius: 8px;
    """,
    
    "frame_inner": f"""
        background-color: {COLORS["bg_light"]};
        border-radius: 8px;
    """,
}

# Стили полей ввода
INPUT_STYLES = {
    "line_edit": f"""
        QLineEdit {{
            background-color: {COLORS["bg_light"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 5px;
            padding: 5px;
            font-size: 13px;
            min-width: 70px;
        }}
        QLineEdit:focus {{
            border: 1px solid {COLORS["secondary"]};
        }}
    """,
    
    "line_edit_small": f"""
        QLineEdit {{
            background-color: {COLORS["bg_light"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 5px;
            padding: 4px;
            font-size: 13px;
            min-width: 40px;
        }}
        QLineEdit:focus {{
            border: 1px solid {COLORS["secondary"]};
        }}
    """,
    
    "spin_box": f"""
        QSpinBox {{
            background-color: {COLORS["bg_light"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 5px;
            padding: 4px;
            font-size: 13px;
            min-width: 70px;
        }}
        QSpinBox:focus {{
            border: 1px solid {COLORS["secondary"]};
        }}
    """,
    
    "text_edit": f"""
        QTextEdit {{
            background-color: {COLORS["bg_light"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 5px;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 11px;
            padding: 5px;
        }}
    """,
    
    "text_edit_error": f"""
        QTextEdit {{
            background-color: #2a1a1a;
            color: {COLORS["text_error"]};
            border: 1px solid {COLORS["border_error"]};
            border-radius: 5px;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 11px;
            padding: 5px;
        }}
    """,
}

# Стили меток
LABEL_STYLES = {
    "primary": f"""
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: 14px;
            font-weight: bold;
        }}
    """,
    
    "secondary": f"""
        QLabel {{
            color: {COLORS["text_secondary"]};
            font-size: 13px;
            font-weight: bold;
        }}
    """,
    
    "muted": f"""
        QLabel {{
            color: {COLORS["text_muted"]};
            font-size: 12px;
        }}
    """,
    
    "error": f"""
        QLabel {{
            color: {COLORS["text_error"]};
            font-size: 11px;
            font-weight: bold;
        }}
    """,
    
    "counter": f"""
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: 14px;
            font-weight: bold;
            min-width: 30px;
            text-align: left;
            margin-left: 0px;
            padding-left: 0px;
        }}
    """,
    
    "status": f"""
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: 11px;
            font-weight: bold;
            padding: 3px 8px;
            background-color: #333333;
            border-radius: 3px;
        }}
    """,
    
    "status_error": f"""
        QLabel {{
            color: {COLORS["text_error"]};
            font-size: 11px;
            font-weight: bold;
            padding: 3px 8px;
            background-color: #442222;
            border-radius: 3px;
        }}
    """,
}

# Стили чекбоксов
CHECKBOX_STYLES = {
    "standard": f"""
        QCheckBox {{
            color: {COLORS["text_primary"]};
            font-size: 13px;
            font-weight: bold;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
        }}
    """,
    
    "small": f"""
        QCheckBox {{
            color: {COLORS["text_primary"]};
            font-size: 12px;
            padding: 8px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
        }}
    """,
}

# Стили групповых панелей
GROUPBOX_STYLES = {
    "standard": f"""
        QGroupBox {{
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-weight: bold;
            border: 1px solid {COLORS["border"]};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
    """,
    
    "error": f"""
        QGroupBox {{
            color: {COLORS["text_error"]};
            font-size: 12px;
            font-weight: bold;
            border: 1px solid {COLORS["border_error"]};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
    """,
}

# Стили окна счетчика
COUNTER_WINDOW_STYLES = {
    "frame": f"""
        QFrame {{
            background-color: {COLORS["bg_medium"]};
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            padding-left: 4px;
        }}
    """,
    
    "text": f"""
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: 14px;
            font-weight: bold;
        }}
    """,
    
    "counter": f"""
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: 14px;
            font-weight: bold;
            min-width: 30px;
            text-align: left;
            margin-left: 0px;
            padding-left: 0px;
        }}
    """,
}