# Цветовая палитра
ORANGE_PRIMARY = "#ff8a00"
ORANGE_SECONDARY = "#FFA500"
ORANGE_DARK = "#da7804"
DARK_GRAY = "#1a1918"
LIGHT_GRAY = "#1a1c20"
WHITE = "#efede4"
BLACK = "#000000"

# Основные стили
MAIN_BG = DARK_GRAY
BUTTON_BG = ORANGE_PRIMARY
BUTTON_ACTIVE_BG = ORANGE_DARK
BUTTON_FG = WHITE
BUTTON_ACTIVE_FG = WHITE
LABEL_FG = WHITE
ENTRY_BG = WHITE
ENTRY_FG = BLACK

FONT_FAMILY = "Arial"
FONT_SIZE = 12
FONT_WEIGHT = "bold"

# Стиль кнопок
button_style = {
    "font": (FONT_FAMILY, FONT_SIZE, FONT_WEIGHT),
    "bg": BUTTON_BG,
    "fg": BUTTON_FG,
    "activebackground": BUTTON_ACTIVE_BG,
    "activeforeground": BUTTON_ACTIVE_FG,
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 12
}
cooking_button_style = {
    "font": (FONT_FAMILY, FONT_SIZE, FONT_WEIGHT),
    "bg": BUTTON_BG,
    "fg": BUTTON_FG,
    "activebackground": BUTTON_ACTIVE_BG,
    "activeforeground": BUTTON_ACTIVE_FG,
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 2
}

# Стиль кнопки выхода
exit_button_style = {
    "font": (FONT_FAMILY, FONT_SIZE, FONT_WEIGHT),
    "bg": MAIN_BG,
    "fg": ORANGE_PRIMARY,
    "activebackground": MAIN_BG,
    "activeforeground": ORANGE_SECONDARY,
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 15
}

# Стиль кнопки помощи
help_button_style = {
    "font": (FONT_FAMILY, FONT_SIZE, FONT_WEIGHT),
    "bg": LIGHT_GRAY,
    "fg": WHITE,
    "activebackground": "#5D5D5D",
    "activeforeground": ORANGE_PRIMARY,
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 15
}

# Стиль меток
label_style = {
    "font": (FONT_FAMILY, FONT_SIZE, FONT_WEIGHT),
    "fg": LABEL_FG,
    "bg": MAIN_BG
}

# Стиль полей ввода
entry_style = {
    "font": ("Arial", 12, FONT_WEIGHT),
    "bg": ENTRY_BG,
    "fg": ENTRY_FG,
    "relief": "solid",
    "bd": 0
}