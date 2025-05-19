import random
import tkinter as tk
import pyautogui
import time
import keyboard
from styles import cooking_button_style, button_style, label_style, entry_style, MAIN_BG

class CookingBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Готовка")
        self.root.geometry("790x380")
        self.root.resizable(False, False)
        self.root.configure(bg=MAIN_BG)
        self.sequence = []
        self.cycle_count = tk.IntVar(value=1)
        self.is_paused = False
        self.should_stop = False

        # Основные элементы слева
        left_frame = tk.Frame(root, bg=MAIN_BG)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Поле ввода количества циклов
        tk.Label(left_frame, text="Введите количество циклов:", **label_style).grid(row=0, column=0, sticky="w")
        tk.Entry(left_frame, textvariable=self.cycle_count, **entry_style).grid(row=0, column=1, padx=5)

        # Кнопки инструментов
        tools_frame = tk.Frame(left_frame, bg=MAIN_BG)
        tools_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        tools = [("Нож", "knife"), ("Венчик", "whisk"), ("Огонь", "fire")]
        for i, (text, action) in enumerate(tools):
            tk.Button(tools_frame, text=text, command=lambda a=action: self.record_action(a), 
                     **button_style).grid(row=0, column=i, padx=5)

        # Последовательность действий
        tk.Label(left_frame, text="Записанные ячейки:", **label_style).grid(row=2, column=0, columnspan=2, sticky="w")
        self.sequence_label = tk.Label(left_frame, text="", wraplength=300, **label_style)
        self.sequence_label.grid(row=3, column=0, columnspan=2, sticky="w")

        # Горизонтальный блок кнопок управления (Запуск/Стоп и Сброс)
        control_frame = tk.Frame(left_frame, bg=MAIN_BG)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(10, 5))
        
        # Кнопка Запустить/Стоп (слева)
        self.start_stop_btn = tk.Button(
            control_frame, 
            text="Запустить", 
            command=self.toggle_cooking, 
            **button_style
        )
        self.start_stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопка Сброс (справа)
        tk.Button(
            control_frame, 
            text="Сброс", 
            command=self.reset_sequence, 
            **button_style
        ).pack(side=tk.LEFT)

        # Информация о паузе
        pause_frame = tk.Frame(left_frame, bg=MAIN_BG)
        pause_frame.grid(row=5, column=0, columnspan=2, pady=(5, 0))
        
        tk.Label(pause_frame, text="Управление паузой:", **label_style).grid(row=0, column=0, sticky="w")
        tk.Label(pause_frame, text="F7 - продолжить", **label_style).grid(row=1, column=0, sticky="w")
        tk.Label(pause_frame, text="F8 - пауза", **label_style).grid(row=2, column=0, sticky="w")
        
        self.pause_status = tk.Label(pause_frame, text="Статус: не активно", **label_style)
        self.pause_status.grid(row=3, column=0, sticky="w")

        # Строка отчета
        self.report_label = tk.Label(left_frame, text="", **label_style)
        self.report_label.grid(row=6, column=0, columnspan=2, pady=(5, 10))

        # Вертикальная сетка ячеек справа
        cell_frame = tk.Frame(root, bg=MAIN_BG)
        cell_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.special_cells = {
            "knife": (686, 572),
            "whisk": (809, 572),
            "fire": (928, 572),
            "water": (1078, 284),
        }

        self.cells = {
            "cell_1": (1160, 284), "cell_2": (1248, 284),
            "cell_3": (1078, 375), "cell_4": (1160, 375), "cell_5": (1248, 375),
            "cell_6": (1078, 458), "cell_7": (1160, 458), "cell_8": (1248, 458),
            "cell_9": (1078, 542), "cell_10": (1160, 542), "cell_11": (1248, 542),
            "cell_12": (1078, 626), "cell_13": (1160, 626), "cell_14": (1248, 626),
            "cell_15": (1078, 712), "cell_16": (1160, 712), "cell_17": (1248, 712),
            "cell_18": (1078, 792), "cell_19": (1160, 792), "cell_20": (1248, 792)
        }

        # Создаем первую строку с кнопкой "Вода" и двумя первыми ячейками
        first_row = tk.Frame(cell_frame, bg=MAIN_BG)
        first_row.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        # Кнопка "Вода"
        tk.Button(
            first_row, 
            text="Вода", 
            command=lambda: self.record_action("water"), 
            **cooking_button_style
        ).grid(row=0, column=0, padx=5, pady=2)
        
        # Ячейки 1 и 2
        for i in range(1, 3):
            cell_key = f"cell_{i}"
            tk.Button(
                first_row, 
                text=f"({i})", 
                command=lambda k=cell_key: self.record_cell_action(k), 
                **cooking_button_style
            ).grid(row=0, column=i, padx=5, pady=2)

        # Остальные ячейки
        for row in range(1, 7):
            for col in range(3):
                cell_number = (row-1) * 3 + col + 3
                if cell_number > 20:
                    continue
                cell_key = f"cell_{cell_number}"
                btn = tk.Button(
                    cell_frame, 
                    text=f"({cell_number})", 
                    command=lambda k=cell_key: self.record_cell_action(k), 
                    **cooking_button_style
                )
                btn.grid(row=row, column=col, pady=2, padx=2)

        # Настройка веса строк и столбцов
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        # Регистрируем горячие клавиши
        keyboard.add_hotkey('F8', self.pause_cooking)
        keyboard.add_hotkey('F7', self.resume_cooking)

    def get_random_offset(self, max_offset=25):
        return random.randint(-max_offset, max_offset)

    def record_action(self, action):
        base_x, base_y = self.special_cells[action]
        coords = (base_x + self.get_random_offset(), base_y + self.get_random_offset())
        self.sequence.append((action, coords))
        self.update_sequence_display()

    def record_cell_action(self, cell_key):
        base_x, base_y = self.cells[cell_key]
        coords = (base_x + self.get_random_offset(), base_y + self.get_random_offset())
        self.sequence.append((cell_key, coords))
        self.update_sequence_display()

    def update_sequence_display(self):
        sequence_text = ", ".join([f"{action}" for action, _ in self.sequence])
        self.sequence_label.config(text=sequence_text)

    def reset_sequence(self):
        self.sequence = []
        self.update_sequence_display()
        self.report_label.config(text="Последовательность сброшена")

    def pause_cooking(self):
        if not self.is_paused and hasattr(self, 'cooking_in_progress') and self.cooking_in_progress:
            self.is_paused = True
            self.pause_status.config(text="Статус: на паузе")
            self.report_label.config(text="Готовка приостановлена (F7 - продолжить)")

    def resume_cooking(self):
        if self.is_paused and hasattr(self, 'cooking_in_progress') and self.cooking_in_progress:
            self.is_paused = False
            self.pause_status.config(text="Статус: активно")
            self.report_label.config(text="Готовка продолжена")

    def toggle_cooking(self):
        if hasattr(self, 'cooking_in_progress') and self.cooking_in_progress:
            self.stop_cooking()
        else:
            self.start_cooking()

    def stop_cooking(self):
        self.should_stop = True
        self.cooking_in_progress = False
        self.start_stop_btn.config(text="Запустить")
        self.report_label.config(text="Готовка остановлена пользователем")

    def start_cooking(self):
        if not self.sequence:
            self.report_label.config(text="Ошибка: последовательность пуста")
            return
            
        self.is_paused = False
        self.should_stop = False
        self.cooking_in_progress = True
        self.start_stop_btn.config(text="Остановить")
        self.pause_status.config(text="Статус: активно")
        self.report_label.config(text="Выполняется готовка...")
        self.root.update()
        time.sleep(5)
        
        cycles = self.cycle_count.get()
        for cycle in range(cycles):
            if self.should_stop:
                self.report_label.config(text=f"Готовка прервана на цикле {cycle+1} из {cycles}")
                break
                
            while self.is_paused:
                time.sleep(0.1)
                if self.should_stop:
                    self.report_label.config(text=f"Готовка прервана на цикле {cycle+1} из {cycles}")
                    return
                    
            self.report_label.config(text=f"Цикл {cycle+1} из {cycles}...")
            self.root.update()
            
            for action, coords in self.sequence:
                if self.should_stop:
                    break
                    
                while self.is_paused:
                    time.sleep(0.1)
                    if self.should_stop:
                        self.report_label.config(text=f"Готовка прервана на цикле {cycle+1} из {cycles}")
                        return
                
                duration1 = random.uniform(0.3, 0.5)
                duration2 = random.uniform(0.3, 0.5)
                duration3 = random.uniform(0.3, 0.5)
                
                if action in self.special_cells:
                    pyautogui.moveTo(coords[0], coords[1], duration=duration1)
                    pyautogui.click(button='right')
                elif action.startswith("cell"):
                    x, y = coords
                    pyautogui.moveTo(x, y, duration=duration2)
                    pyautogui.click(button='right')
                
                time.sleep(random.uniform(0.03, 0.1))
            
            if self.should_stop:
                break
                
            # Нажатие кнопки готовки
            start_x, start_y = 803, 673
            pyautogui.moveTo(start_x + self.get_random_offset(), start_y + self.get_random_offset(), duration=duration3)
            pyautogui.click(button='left')
            
            # Увеличенное время ожидания между циклами
            if cycle < cycles - 1:
                time.sleep(random.uniform(5.5, 6.0))
    
        self.cooking_in_progress = False
        self.start_stop_btn.config(text="Запустить")
        if not self.should_stop:
            self.report_label.config(text=f"Готовка завершена! Выполнено {cycles} циклов.")
        self.pause_status.config(text="Статус: не активно")

if __name__ == "__main__":
    root = tk.Tk()
    app = CookingBotApp(root)
    root.mainloop()