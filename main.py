import tkinter as tk
import os
import webbrowser
from antiafk import AntiafkApp
from builder import BuilderApp
from cooking import CookingBotApp
from farmcows import FarmCowsApp
from luckywheel import LuckyWheelApp
from port import PortApp
from mining import MiningBotApp
from styles import button_style, exit_button_style, help_button_style, MAIN_BG

def run_app(app_class):
    root = tk.Tk()
    root.configure(bg=MAIN_BG)
    app = app_class(root)
    root.mainloop()

def exit_app():
    root.destroy()
    os._exit(0)

def open_link():
    webbrowser.open("https://www.donationalerts.com/r/raktoperk")

root = tk.Tk()
root.title("Extra Hands")
root.geometry("250x550")
root.configure(bg=MAIN_BG)

apps = [
    ("АнтиАФК", AntiafkApp),
    ("Колесо удачи", LuckyWheelApp),
    ("Кулинария", CookingBotApp),
    ("Стройка", BuilderApp),
    ("Порт", PortApp),
    ("Шахта", MiningBotApp),
    ("Ферма (коровы)", FarmCowsApp)
]

button_frame = tk.Frame(root, bg=MAIN_BG)
button_frame.pack(expand=True)

for app_name, app_class in apps:
    button = tk.Button(button_frame, text=app_name, 
                     command=lambda ac=app_class: run_app(ac), 
                     **button_style)
    button.pack(pady=5, anchor="center")

exit_button = tk.Button(button_frame, text="Выход", 
                      command=exit_app, 
                      **exit_button_style)
exit_button.pack(pady=5, anchor="center")

help_button = tk.Button(button_frame, text="Подкинуть монетку", 
                       command=open_link, 
                       **help_button_style)
help_button.pack(pady=5, anchor="center")

root.mainloop()