import tkinter as tk
import pyautogui
import threading
import time
import random
import ctypes
from styles import button_style, exit_button_style, MAIN_BG, label_style, entry_style

class FarmCowsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ферма (коровник)")
        self.root.geometry("500x250")
        self.root.configure(bg=MAIN_BG)
        
        self.running = False
        self.force_pause = False
        self.resolution = "FullHD"
        self.base_delay = 180
        
        # Координаты для FullHD
        self.fullhd_coords = {
            "color_a": (910, 875),
            "color_d": (1060, 875),
            "danger_color": (1220, 840)
        }
        
        # Настройки цветового детектирования
        self.danger_color = (255, 105, 86)  # Базовый цвет для сравнения
        self.color_tolerance = 15  # Допустимое отклонение по каждому каналу RGB
        
        self.create_widgets()
    
    def create_widgets(self):
        # Поле ввода задержки
        delay_frame = tk.Frame(self.root, bg=MAIN_BG)
        delay_frame.pack(pady=5)
        
        tk.Label(delay_frame, text="Задержка (мс):", **label_style).pack(side=tk.LEFT)
        
        self.delay_entry = tk.Entry(delay_frame, **entry_style, width=7)
        self.delay_entry.insert(0, str(self.base_delay))
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        
        # Метка статуса
        self.status_label = tk.Label(self.root, text="Состояние: не активно", **label_style)
        self.status_label.pack(pady=10)

        # Кнопка старт/стоп
        self.start_button = tk.Button(self.root, text="Старт", command=self.toggle_bot, **button_style)
        self.start_button.pack(pady=10)
        
        # Раздел смены разрешения
        resolution_frame = tk.Frame(self.root, bg=MAIN_BG)
        resolution_frame.pack(pady=10, side=tk.BOTTOM)
        
        # Метка текущего разрешения
        self.resolution_label = tk.Label(
            resolution_frame, 
            text=f"Текущее разрешение: {self.resolution}", 
            **label_style
        )
        self.resolution_label.pack()
        
        # Фрейм для кнопок разрешения
        resolution_buttons_frame = tk.Frame(resolution_frame, bg=MAIN_BG)
        resolution_buttons_frame.pack(pady=5)
        
        self.fullhd_btn = tk.Button(
            resolution_buttons_frame, 
            text="FullHD", 
            command=lambda: self.set_resolution("FullHD"),
            **button_style
        )
        self.fullhd_btn.pack(side=tk.LEFT, padx=5)
        
        self.quadhd_btn = tk.Button(
            resolution_buttons_frame, 
            text="QuadHD", 
            command=lambda: self.set_resolution("QuadHD"),
            **button_style
        )
        self.quadhd_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_resolution_buttons()
    
    def set_resolution(self, resolution):
        self.resolution = resolution
        self.resolution_label.config(text=f"Текущее разрешение: {self.resolution}")
        self.update_resolution_buttons()
    
    def update_resolution_buttons(self):
        if self.resolution == "FullHD":
            self.fullhd_btn.config(bg="#ff8a00")
            self.quadhd_btn.config(bg="#ff8a00")
        else:
            self.fullhd_btn.config(bg="#ff8a00")
            self.quadhd_btn.config(bg="#ff8a00")
    
    def get_current_coords(self):
        return self.fullhd_coords if self.resolution == "FullHD" else self.quadhd_coords
    
    def colors_are_similar(self, color1, color2, tolerance):
        """Проверяет, похожи ли цвета с учетом допуска"""
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))
    
    def safe_key_press(self, key):
        """Безопасное нажатие клавиши через виртуальные коды"""
        try:
            key_map = {'A': 0x41, 'D': 0x44, 'a': 0x41, 'd': 0x44}
            if key in key_map:
                ctypes.windll.user32.keybd_event(key_map[key], 0, 0, 0)
                time.sleep(0.05)
                ctypes.windll.user32.keybd_event(key_map[key], 0, 2, 0)
        except:
            pass
    
    def check_danger_color(self):
        """Проверяет опасный цвет и похожие оттенки"""
        coords = self.get_current_coords()
        try:
            current_color = pyautogui.pixel(*coords["danger_color"])
            return self.colors_are_similar(current_color, self.danger_color, self.color_tolerance)
        except:
            return False
    
    def handle_danger_color(self):
        """Обрабатывает ситуацию с опасным цветом"""
        if self.check_danger_color():
            if not self.force_pause:
                self.force_pause = True
                self.status_label.config(text="Состояние: ПАУЗА (опасный цвет)")
                self.root.update()
            
            # Случайная пауза от 5 до 8 секунд
            pause_time = random.uniform(0.005, 0.015)
            time.sleep(pause_time)
            return True
        
        if self.force_pause:
            self.force_pause = False
            self.status_label.config(text="Состояние: активно")
            self.root.update()
            time.sleep(0.5)  # Дополнительная пауза после восстановления
        
        return False
    
    def check_white_color(self, coord):
        """Проверяет белый цвет в указанных координатах"""
        try:
            return pyautogui.pixel(*coord) == (255, 255, 255)
        except:
            return False
    
    def run_bot_cycle(self):
        """Один полный цикл работы бота"""
        coords = self.get_current_coords()
        
        # 1. Приоритетная проверка опасного цвета
        if self.handle_danger_color():
            return  # Пропускаем цикл при обнаружении опасного цвета
        
        # 2. Проверка белых цветов для клавиш
        if self.check_white_color(coords["color_a"]):
            self.safe_key_press('A')
            time.sleep((self.base_delay / 1000) + random.uniform(0.005, 0.025))
        elif self.check_white_color(coords["color_d"]):
            self.safe_key_press('D')
            time.sleep((self.base_delay / 1000) + random.uniform(0.005, 0.025))
        else:
            time.sleep(0.05)  # Короткая пауза при отсутствии действий
    
    def run_bot(self):
        """Основной цикл работы бота"""
        while self.running:
            self.run_bot_cycle()
    
    def toggle_bot(self):
        if self.running:
            self.running = False
            self.status_label.config(text="Состояние: не активно")
            self.start_button.config(text="Старт")
        else:
            try:
                self.base_delay = int(self.delay_entry.get())
                if self.base_delay < 0:
                    raise ValueError
            except ValueError:
                self.status_label.config(text="Ошибка: неверная задержка")
                return
                
            self.running = True
            self.force_pause = False
            self.status_label.config(text="Состояние: активно")
            self.start_button.config(text="Стоп")
            threading.Thread(target=self.run_bot, daemon=True).start()

def run_color_bot():
    root = tk.Tk()
    app = FarmCowsApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_color_bot()