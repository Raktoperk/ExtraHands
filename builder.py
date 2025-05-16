import os
import pyautogui
import time
import keyboard as key
import random
import cv2
import numpy as np
import tkinter as tk
from PIL import ImageGrab

class BuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Стройка")
        self.root.geometry("300x200")  # Увеличили высоту окна для нового поля
        self.root.resizable(False, False)
        
        self.running = False
        self.resolution_mode = "FullHD"  # По умолчанию FullHD
        self.delay_between_presses = 120  # Задержка по умолчанию в мс
        self.green_pixel_coords = {
            "FullHD": (765, 496),
            "QuadHD": (1084, 674)
        }

        # Стили для элементов
        button_style = {
            "font": ("Arial", 10),
            "bg": "#1E90FF",
            "fg": "white",
            "activebackground": "#4682B9",
            "activeforeground": "white",
            "bd": 0,
            "padx": 10,
            "pady": 5,
            "relief": "flat",
            "width": 10
        }

        label_style = {
            "font": ("Arial", 12),
            "fg": "black"
        }

        # Метка состояния
        self.status_label = tk.Label(root, text="Состояние: Не активно", **label_style)
        self.status_label.pack(pady=5)

        # Frame для поля ввода задержки
        delay_frame = tk.Frame(root)
        delay_frame.pack(pady=5)
        
        tk.Label(delay_frame, text="Задержка (мс):", **label_style).pack(side=tk.LEFT)
        
        self.delay_entry = tk.Entry(delay_frame, width=10)
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        self.delay_entry.insert(0, str(self.delay_between_presses))

        # Кнопка запуска/остановки (основная)
        self.toggle_button = tk.Button(
            root, 
            text="Запустить", 
            command=self.toggle_bot,
            **button_style
        )
        self.toggle_button.pack(pady=5)

        # Метка текущего разрешения
        self.resolution_label = tk.Label(root, text=f"Текущее разрешение: {self.resolution_mode}", **label_style)
        self.resolution_label.pack(pady=5)

        # Frame для кнопок смены разрешения
        resolution_frame = tk.Frame(root)
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

    def check_color(self, x, y, color):
        return pyautogui.pixelMatchesColor(x, y, color)

    def detect_image(self, screen, template_path):
        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                print(f"Ошибка: Не удалось загрузить изображение по пути {template_path}")
                return None

            w, h = template.shape[::-1]
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            threshold = 0.9
            if max_val >= threshold:
                return max_loc
            return None
        except Exception as e:
            print(f"Ошибка при обработке изображения: {e}")
            return None

    def checkImageKey(self, prop):
        image_path = f'keys/{prop}.png'
        if not os.path.exists(image_path):
            return

        screenshot = ImageGrab.grab()
        screen_np = np.array(screenshot)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        
        match_location = self.detect_image(screen_gray, image_path)

        if match_location is not None:
            time.sleep(random.uniform(0.1, 0.2))
            x, y = self.green_pixel_coords[self.resolution_mode]
            while self.running and self.check_color(x, y, (126, 211, 33)):
                key_code = self.get_key_code(prop)
                if key_code:
                    print(key_code)
                    # key.press(key_code)
                    # time.sleep(random.uniform(0.04, 0.06))  # Конвертируем мс в секунды
                    # key.release(key_code)
                time.sleep(random.uniform(self.delay_between_presses / 1000 + 0.005, self.delay_between_presses / 1000 + 0.025))

    def get_key_code(self, char):
        key_map = {
            'y': 'y',
            'f': 'f',
            'e': 'e',
        }
        return key_map.get(char.lower())

    def toggle_bot(self):
        if not self.running:
            try:
                # Получаем значение задержки из поля ввода
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
            self.checkImageKey('e')
            self.checkImageKey('f')
            self.checkImageKey('y')
            time.sleep(0.01)

if __name__ == "__main__":
    root = tk.Tk()
    app = BuilderApp(root)
    root.mainloop()