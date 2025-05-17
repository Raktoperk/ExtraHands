import tkinter as tk
import pyautogui
import keyboard as key
from threading import Thread
from styles import button_style, label_style, MAIN_BG

SCANCODES = {
    'e': 'e'
}

class PortApp:
    def __init__(self, root):
        # Координаты для поиска зелёного цвета в зависимости от разрешения
        self.resolution_green_coordinates = {
            "FullHD": (965, 501),  # Координаты для FullHD
            "QuadHD": (1288, 670)  # Координаты для QuadHD
        }

        self.root = root
        self.root.title("Порт")
        self.root.geometry("550x220")
        self.root.configure(bg=MAIN_BG)
        self.root.resizable(False, False)
        # self.root.iconbitmap("icon.ico")

        self.running = False
        self.active_resolution = "FullHD"  # По умолчанию активное разрешение
        self.green_color = (126, 211, 33)  # Зелёный цвет для поиска

        # Строка состояния
        self.status_label = tk.Label(root, text="Состояние: не активно", **label_style)
        self.status_label.pack(pady=5)

        # Создание фрейма для кнопок управления
        control_frame = tk.Frame(root, bg=MAIN_BG)
        control_frame.pack(pady=10)

        # Кнопка Запустить/Остановить
        self.toggle_button = tk.Button(control_frame, text="Запустить", command=self.toggle_task, **button_style)
        self.toggle_button.pack(side="left", padx=5)

        # Метка активного разрешения
        self.resolution_label = tk.Label(root, text=f"Активное разрешение: {self.active_resolution}", **label_style)
        self.resolution_label.pack(pady=5)

        # Создание фрейма для кнопок разрешения
        resolution_frame = tk.Frame(root, bg=MAIN_BG)
        resolution_frame.pack(pady=5)

        # Кнопка FullHD
        self.fullhd_button = tk.Button(resolution_frame, text="FullHD", command=lambda: self.set_resolution("FullHD"), **button_style)
        self.fullhd_button.pack(side="left", padx=5)

        # Кнопка QuadHD
        self.quadhd_button = tk.Button(resolution_frame, text="QuadHD", command=lambda: self.set_resolution("QuadHD"), **button_style)
        self.quadhd_button.pack(side="left", padx=5)

    def check_color(self, x, y, color):
        return pyautogui.pixelMatchesColor(x, y, color)

    def press_key(self, key_char):
        """Нажимает физическую клавишу по scancode (работает в любой раскладке)"""
        scancode = SCANCODES.get(key_char.lower())
        if scancode:
            key.send(scancode)
        else:
            pyautogui.press(key_char)  # Фолбэк на обычный метод, если scancode не найден

    def task(self):
        while self.running:
            # Получаем текущие координаты для активного разрешения
            x, y = self.resolution_green_coordinates[self.active_resolution]
            if self.check_color(x, y, self.green_color):
                # Отправляем скан-код клавиши E (не зависит от раскладки)
                self.press_key('e')

    def toggle_task(self):
        if self.running:
            self.running = False
            self.toggle_button.config(text="Запустить")
            self.status_label.config(text="Состояние: Не активно")
        else:
            self.running = True
            self.toggle_button.config(text="Остановить")
            self.status_label.config(text="Состояние: Активно")
            thread = Thread(target=self.task)
            thread.start()

    def set_resolution(self, resolution):
        self.active_resolution = resolution
        self.resolution_label.config(text=f"Активное разрешение: {resolution}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PortApp(root)
    root.mainloop()