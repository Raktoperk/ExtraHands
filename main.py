import tkinter as tk
import os
import webbrowser  # Импортируем модуль для работы с браузером
from antiafk import AntiafkApp
from builder import BuilderApp
from cooking import CookingBotApp
from luckywheel import LuckyWheelApp
from port import PortApp

def run_app(app_class):
    root = tk.Tk()
    app = app_class(root)
    root.mainloop()

def exit_app():
    root.destroy()  # Закрываем главное окно
    os._exit(0)  # Завершаем процесс

def open_link():
    webbrowser.open("https://www.donationalerts.com/r/raktoperk")  # Замените на нужную вам ссылку

# Создание главного окна
root = tk.Tk()
root.title("Extra Hands")
root.geometry("250x550")  # Увеличили высоту окна для новой кнопки

# Стиль для кнопок
button_style = {
    "font": ("Arial", 12),
    "bg": "#1E90FF",
    "fg": "white",
    "activebackground": "#4682B9",
    "activeforeground": "white",
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 15
}

exit_button_style = {
    "font": ("Arial", 12),
    "bg": "#b00f17",
    "fg": "white",
    "activebackground": "#850a10",
    "activeforeground": "white",
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 15,
}

help_button_style = {
    "font": ("Arial", 12),
    "bg": "#302e2e",
    "fg": "white",
    "activebackground": "#262525",
    "activeforeground": "white",
    "bd": 0,
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "width": 15,
}

# Список приложений
apps = [
    ("АнтиАФК", AntiafkApp),
    ("Колесо удачи", LuckyWheelApp),
    ("Кулинария", CookingBotApp),
    ("Стройка", BuilderApp),
    ("Порт", PortApp)
]

# Фрейм для центрирования кнопок
button_frame = tk.Frame(root)
button_frame.pack(expand=True)

# Создание кнопок для каждого приложения
for app_name, app_class in apps:
    button = tk.Button(button_frame, text=app_name, command=lambda ac=app_class: run_app(ac), **button_style)
    button.pack(pady=5, anchor="center")

# Кнопка выхода
exit_button = tk.Button(button_frame, text="Выход", command=exit_app, **exit_button_style)
exit_button.pack(pady=5, anchor="center")

# Кнопка помощи (открывает ссылку)
help_button = tk.Button(button_frame, text="Подкинуть монетку", command=open_link, **help_button_style)
help_button.pack(pady=5, anchor="center")

# Запуск главного цикла
root.mainloop()