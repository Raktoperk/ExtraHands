import tkinter as tk
import pyautogui
import time
import keyboard as key
from threading import Thread
from styles import button_style, label_style, entry_style, MAIN_BG

class LuckyWheelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Колесо удачи")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        self.root.configure(bg=MAIN_BG)

        self.running = False

        # Поля для ввода часов и минут
        tk.Label(root, text="Введите количество часов (от 0 до 4):", **label_style).pack()
        self.hours_entry = tk.Entry(root, **entry_style, width=20)
        self.hours_entry.pack()

        tk.Label(root, text="Введите количество минут (от 0 до 59):", **label_style).pack()
        self.minutes_entry = tk.Entry(root, **entry_style, width=20)
        self.minutes_entry.pack()

        # Кнопка запуска/остановки
        self.toggle_button = tk.Button(root, text="Запустить", command=self.start_bot, **button_style)
        self.toggle_button.pack(pady=10)

        # Строка состояния
        self.status_label = tk.Label(root, text="Состояние: не активно", **label_style)
        self.status_label.pack()

        # Текст с активным разрешением
        self.resolution_var = tk.StringVar(value="FullHD")
        self.resolution_label = tk.Label(root, text=f"Активное разрешение: {self.resolution_var.get()}", **label_style)
        self.resolution_label.pack()

        # Контейнер для кнопок разрешения
        resolution_frame = tk.Frame(root, bg=MAIN_BG)
        resolution_frame.pack(pady=5)

        # Кнопки для выбора разрешения
        fullhd_button = tk.Button(resolution_frame, text="FullHD", command=lambda: self.set_resolution("FullHD"), **button_style)
        fullhd_button.pack(side="left", padx=5)

        quadhd_button = tk.Button(resolution_frame, text="QuadHD", command=lambda: self.set_resolution("QuadHD"), **button_style)
        quadhd_button.pack(side="left", padx=5)

        # Метка для отображения результата
        self.result_label = tk.Label(root, text="", **label_style)
        self.result_label.pack()

    def set_resolution(self, res):
        """Установка разрешения"""
        self.resolution_var.set(res)
        self.resolution_label.config(text=f"Активное разрешение: {res}")

    def click_coordinates(self, coordinates):
        pyautogui.click(coordinates[0], coordinates[1])

    def action(self, resolution):
        coordinates = {
            "FullHD": {"shop": (1286, 275), "roulette": (577, 335), "luckywheel": (685, 642), "spin": (972, 896)},
            "QuadHD": {"shop": (1600, 455), "roulette": (900, 515), "luckywheel": (1080, 825), "spin": (1275, 1065)}
        }

        while self.running:
            key.press('f10')
            time.sleep(1)
            key.release('f10')
            time.sleep(2)

            self.click_coordinates(coordinates[resolution]["shop"])
            time.sleep(2)
            self.click_coordinates(coordinates[resolution]["roulette"])
            time.sleep(2)
            self.click_coordinates(coordinates[resolution]["luckywheel"])
            time.sleep(2)
            self.click_coordinates(coordinates[resolution]["spin"])
            time.sleep(40)

            key.press('esc')
            time.sleep(1)
            key.release('esc')
            time.sleep(2)
            key.press('esc')
            time.sleep(1)
            key.release('esc')

            time.sleep(15000)

    def start_bot(self):
        try:
            hours = int(self.hours_entry.get() or 0)
            minutes = float(self.minutes_entry.get() or 0)
            resolution = self.resolution_var.get()

            if hours < 0 or hours > 4 or minutes < 0 or minutes > 59:
                self.result_label.config(text="Пожалуйста, введите корректное значение.")
                return

            if not self.running:
                self.running = True
                self.status_label.config(text="Состояние: активно")
                self.toggle_button.config(text="Остановить")
                self.result_label.config(text="Можно открыть игру...")

                total_seconds = hours * 3600 + minutes * 60 + 60

                # Запуск действия в отдельном потоке
                Thread(target=self.run_bot, args=(total_seconds, resolution)).start()
            else:
                self.running = False
                self.status_label.config(text="Состояние: не активно")
                self.toggle_button.config(text="Запустить")
                self.result_label.config(text="Процесс остановлен.")
        except ValueError:
            self.result_label.config(text="Пожалуйста, введите корректные числа.")

    def run_bot(self, total_seconds, resolution):
        time.sleep(total_seconds)
        self.action(resolution)