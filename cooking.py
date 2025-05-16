import random
import tkinter as tk
import pyautogui
import time

class CookingBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Готовка")
        self.sequence = []  # Записанная последовательность ячеек
        self.cycle_count = tk.IntVar(value=1)  # Количество циклов, начальное значение = 1

        # Стили для кнопок, полей ввода и меток
        self.button_style = {
            "font": ("Arial", 10),
            "bg": "#1E90FF",  # цвет фона
            "fg": "white",    # цвет текста
            "activebackground": "#4682B9",  # Цвет фона при нажатии
            "activeforeground": "white",     # Цвет текста при нажатии
            "bd": 0,          # Без рамки
            "padx": 5,        # Отступ по горизонтали
            "pady": 5,        # Отступ по вертикали
            "relief": "flat",  # Плоский стиль
            "width": 8        # Ширина кнопки
        }

        self.entry_style = {
            "font": ("Arial", 10),
            "relief": "solid",
            "bd": 1,
            "width": 10,
        }

        self.label_style = {
            "font": ("Arial", 10),
            "fg": "black"
        }

        # Поле ввода количества повторений цикла
        tk.Label(root, text="Введите количество циклов:", **self.label_style).grid(row=0, column=0, sticky="w", padx=10)
        tk.Entry(root, textvariable=self.cycle_count, **self.entry_style).grid(row=0, column=1, padx=10)

        # Фрейм для кнопок нож, венчик, огонь
        action_frame = tk.Frame(root)
        action_frame.grid(row=1, column=0, columnspan=2, pady=10)

        tk.Button(action_frame, text="Нож", command=lambda: self.record_action("knife"), **self.button_style).grid(row=0, column=0, padx=5)
        tk.Button(action_frame, text="Венчик", command=lambda: self.record_action("whisk"), **self.button_style).grid(row=0, column=1, padx=5)
        tk.Button(action_frame, text="Огонь", command=lambda: self.record_action("fire"), **self.button_style).grid(row=0, column=2, padx=5)

        # Строка для отображения последовательности действий
        tk.Label(root, text="Записанные ячейки:", **self.label_style).grid(row=2, column=0, columnspan=2, sticky="w", padx=10)
        self.sequence_label = tk.Label(root, text="", wraplength=500, **self.label_style)
        self.sequence_label.grid(row=3, column=0, columnspan=2, padx=10)

        # Фрейм для кнопок "запустить" и "сбросить"
        button_frame = tk.Frame(root)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Запустить", command=self.start_cooking, **self.button_style).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Сброс", command=self.reset_sequence, **self.button_style).grid(row=0, column=1, padx=5)

        # Фрейм для кнопки "вода" и ячеек
        grid_frame = tk.Frame(root)
        grid_frame.grid(row=0, column=2, rowspan=5, padx=10, pady=10)

        # Кнопка "вода" в первой строке
        tk.Button(grid_frame, text="Вода", command=lambda: self.record_action("water"), **self.button_style).grid(row=0, column=0, pady=5)

        self.special_cells = {
            "knife": (686, 572),
            "whisk": (809, 572),
            "fire": (928, 572),
            "water": (1078, 284),
        }

        # Кнопки для ячеек с фиксированными координатами
        self.cells = {
            "cell_0_0": (1160, 284), "cell_0_1": (1248, 284), 
            "cell_0_2": (1078, 375), "cell_0_3": (1160, 375), "cell_0_4": (1248, 375),
            "cell_0_5": (1078, 458), "cell_0_6": (1160, 458), "cell_1_0": (1248, 458),
            "cell_1_1": (1078, 542), "cell_1_2": (1160, 542), "cell_1_3": (1248, 542),
            "cell_1_4": (1078, 626), "cell_1_5": (1160, 626), "cell_1_6": (1248, 626),
            "cell_2_0": (1078, 712), "cell_2_1": (1160, 712), "cell_2_2": (1248, 712),
            "cell_2_3": (1078, 792), "cell_2_4": (1160, 792), "cell_2_5": (1248, 792)
        }

        # Нумерация ячеек для интерфейса
        cell_number = 1
        for i in range(3):
            for j in range(7):
                # Пропускаем ячейку с индексом 21 (cell_2_1)
                if i == 2 and j == 6:
                    continue
                cell_key = f"cell_{i}_{j}"
                cell_button_text = f"({cell_number})"
                btn = tk.Button(grid_frame, text=cell_button_text, command=lambda key=cell_key: self.record_cell_action(key), **self.button_style)
                btn.grid(row=i + 1, column=j, pady=2, padx=2)
                cell_number += 1

    def get_random_offset(self, max_offset=25):
        """Получаем случайное смещение для имитации случайных кликов в пределах ячейки"""
        return random.randint(-max_offset, max_offset)

    def record_action(self, action):
        """Запись действия в последовательность"""
        base_x, base_y = self.special_cells[action]
        coords = (base_x + self.get_random_offset(), base_y + self.get_random_offset())
        self.sequence.append((action, coords))
        self.update_sequence_display()

    def record_cell_action(self, cell_key):
        """Запись действия для ячейки с координатами x и y"""
        base_x, base_y = self.cells[cell_key]
        coords = (base_x + self.get_random_offset(), base_y + self.get_random_offset())
        self.sequence.append((cell_key, coords))
        self.update_sequence_display()

    def update_sequence_display(self):
        """Обновление строки с последовательностью действий"""
        sequence_text = ", ".join([f"{action}" for action, _ in self.sequence])
        self.sequence_label.config(text=sequence_text)

    def reset_sequence(self):
        """Сброс последовательности действий"""
        self.sequence = []
        self.update_sequence_display()
        print("Последовательность сброшена")

    def start_cooking(self):
        time.sleep(5)
        """Запуск цикла готовки на основе записанной последовательности"""
        cycles = self.cycle_count.get()
        for _ in range(cycles):
            for action, coords in self.sequence:
                duration1 = random.uniform(0.3, 0.5)
                duration2 = random.uniform(0.3, 0.5)
                duration3 = random.uniform(0.3, 0.5)
                if action in self.special_cells:
                    print(f"Наводим курсор на {action} с координатами {coords}")
                    pyautogui.moveTo(coords[0], coords[1], duration=duration1)
                    pyautogui.click(button='right')
                elif action.startswith("cell"):
                    x, y = coords
                    print(f"Наводим курсор на координаты ячейки ({x}, {y})")
                    pyautogui.moveTo(x, y, duration=duration2)
                    pyautogui.click(button='right')
                sleeptime = random.uniform(0.03, 0.1)
                time.sleep(sleeptime)  # Случайная задержка между действиями
            # Автоматический запуск готовки в конце каждого цикла
            start_x, start_y = 803, 673
            pyautogui.moveTo(start_x + self.get_random_offset(), start_y + self.get_random_offset(), duration=duration3)
            pyautogui.click(button='left')
            print("Запущена готовка")
            waittime = random.uniform(4.7, 5)
            time.sleep(waittime)

