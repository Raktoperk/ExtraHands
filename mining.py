import os
import pyautogui
import time
import random
import tkinter as tk
import ctypes
from styles import button_style, label_style, entry_style, MAIN_BG

class MiningBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Шахта")
        self.root.geometry("500x250")
        self.root.resizable(False, False)
        self.root.configure(bg=MAIN_BG)
        
        self.running = False
        self.resolution_mode = "FullHD"
        self.delay_between_presses = 120
        self.target_color = (126, 211, 33)
        self.target_coords = {
            "FullHD": (960, 495),
            "QuadHD": (0, 0)  # Заполните нужные координаты для QuadHD
        }

        # Метка состояния
        self.status_label = tk.Label(
            root, 
            text="Состояние: Не активно", 
            **label_style
        )
        self.status_label.pack(pady=5)

        # Frame для поля ввода задержки
        delay_frame = tk.Frame(root, bg=MAIN_BG)
        delay_frame.pack(pady=5)
        
        tk.Label(
            delay_frame, 
            text="Задержка (мс):", 
            **label_style
        ).pack(side=tk.LEFT)
        
        self.delay_entry = tk.Entry(
            delay_frame, 
            **entry_style,
            width=7
        )
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        self.delay_entry.insert(0, str(self.delay_between_presses))

        # Кнопка запуска/остановки
        self.toggle_button = tk.Button(
            root, 
            text="Запустить", 
            command=self.toggle_bot,
            **button_style
        )
        self.toggle_button.pack(pady=5)

        # Метка текущего разрешения
        self.resolution_label = tk.Label(
            root, 
            text=f"Текущее разрешение: {self.resolution_mode}", 
            **label_style
        )
        self.resolution_label.pack(pady=5)

        # Frame для кнопок смены разрешения
        resolution_frame = tk.Frame(root, bg=MAIN_BG)
        resolution_frame.pack(pady=5)

        # Кнопка FullHD
        self.fullhd_button = tk.Button(
            resolution_frame, 
            text="FullHD", 
            command=lambda: self.set_resolution("FullHD"),
            **button_style
        )
        self.fullhd_button.pack(side=tk.LEFT, padx=5)

        # Кнопка QuadHD
        self.quadhd_button = tk.Button(
            resolution_frame, 
            text="QuadHD", 
            command=lambda: self.set_resolution("QuadHD"),
            **button_style
        )
        self.quadhd_button.pack(side=tk.LEFT, padx=5)

    def set_resolution(self, mode):
        self.resolution_mode = mode
        self.resolution_label.config(text=f"Текущее разрешение: {self.resolution_mode}")

    def check_color(self):
        x, y = self.target_coords[self.resolution_mode]
        return pyautogui.pixelMatchesColor(x, y, self.target_color)

    def press_key_e(self):
        while self.running and self.check_color():
            ctypes.windll.user32.keybd_event(0x45, 0, 0, 0)  # Нажатие E
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x45, 0, 2, 0)  # Отпускание E
            
            # Задержка с небольшим случайным отклонением
            delay_seconds = self.delay_between_presses / 1000
            time.sleep(random.uniform(delay_seconds + 0.005, delay_seconds + 0.015))

    def toggle_bot(self):
        if not self.running:
            try:
                self.delay_between_presses = int(self.delay_entry.get())
                if self.delay_between_presses < 0:
                    raise ValueError("Задержка не может быть отрицательной")
            except ValueError as e:
                self.status_label.config(text=f"Ошибка: {str(e)}")
                return
                
            self.running = True
            self.status_label.config(text="Состояние: Активно")
            self.toggle_button.config(text="Остановить")
            import threading
            bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            bot_thread.start()
        else:
            self.running = False
            self.status_label.config(text="Состояние: Не активно")
            self.toggle_button.config(text="Запустить")

    def run_bot(self):
        while self.running:
            if self.check_color():
                self.press_key_e()
            time.sleep(0.01)

if __name__ == "__main__":
    root = tk.Tk()
    app = MiningBotApp(root)
    root.mainloop()