import time
import random
import keyboard as key
import tkinter as tk
from threading import Thread, Event
from queue import Queue
from styles import button_style, label_style, MAIN_BG

class AntiafkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анти АФК")
        self.root.geometry("500x150")  # Уменьшили ширину, так как кнопок стало меньше
        self.root.resizable(False, False)
        self.root.configure(bg=MAIN_BG)
        
        self.running = False
        self.bot_thread = None
        self.event = Event()
        self.message_queue = Queue()

        self.setup_ui()
        self.check_messages()

    def setup_ui(self):
        """Настройка центрированного интерфейса без кнопок клавиш"""
        # Главный контейнер для центрирования
        main_container = tk.Frame(self.root, bg=MAIN_BG)
        main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Центральный фрейм с содержимым
        center_frame = tk.Frame(main_container, bg=MAIN_BG)
        center_frame.pack(expand=True)

        # Строка состояния (сверху)
        self.status_label = tk.Label(
            center_frame,
            text="Состояние: Не активно",
            **label_style
        )
        self.status_label.pack(pady=(0, 15))

        # Фрейм для кнопок управления (по центру)
        button_frame = tk.Frame(center_frame, bg=MAIN_BG)
        button_frame.pack()

        # Кнопки управления
        self.start_button = tk.Button(
            button_frame,
            text="Запустить",
            command=self.start_bot,
            **button_style
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(
            button_frame,
            text="Остановить",
            command=self.stop_bot,
            **button_style
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

    def press_key(self, key_char):
        """Нажимает физическую клавишу"""
        wait_time = random.uniform(1, 4)
        key.press(key_char)
        time.sleep(wait_time)
        key.release(key_char)

    def open_phone(self):
        """Имитация открытия телефона"""
        if not self.running:
            return
            
        wait_time = random.uniform(1, 90)
        self.message_queue.put(f'Телефон будет открыт {wait_time:.2f} секунд')
        
        key.send('up')
        time.sleep(wait_time)
        key.send('backspace')

    def bot_logic(self):
        """Основная логика работы бота"""
        time.sleep(5)
        
        while self.running:
            cycles = random.randint(1, 8)
            self.message_queue.put(f'Будет {cycles} циклов')
            
            for _ in range(cycles):
                if not self.running:
                    return
                    
                key_to_press = random.choice(['w', 'a', 's', 'd'])
                if key_to_press == 'up':
                    self.open_phone()
                else:
                    self.press_key(key_to_press)
                    
                if not self.running:
                    return
            
            cycle_wait = random.uniform(60, 120)
            self.message_queue.put(f'Следующий цикл через {cycle_wait:.2f} секунд')
            
            self.event.wait(cycle_wait)
            self.event.clear()

    def check_messages(self):
        """Проверка сообщений в очереди"""
        while not self.message_queue.empty():
            print(self.message_queue.get())
        self.root.after(100, self.check_messages)

    def start_bot(self):
        """Запуск бота"""
        if not self.running:
            self.running = True
            self.event = Event()
            self.bot_thread = Thread(target=self.bot_logic)
            self.bot_thread.start()
            self.message_queue.put("Бот запущен")
            self.status_label.config(text="Состояние: Активно")

    def stop_bot(self):
        """Остановка бота"""
        if self.running:
            self.running = False
            self.event.set()
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=1)
            self.message_queue.put("Бот остановлен")
            self.status_label.config(text="Состояние: Не активно")