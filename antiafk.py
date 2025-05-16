import time
import random
import keyboard as key
import tkinter as tk
from threading import Thread, Event
from queue import Queue

SCANCODES = {
    'w': 'w',    # Scancode для 'W'
    'a': 'a',    # Scancode для 'A'
    's': 's',    # Scancode для 'S'
    'd': 'd',    # Scancode для 'D'
}

class AntiafkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анти АФК")
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
        self.running = False
        self.bot_thread = None
        self.event = Event()
        self.message_queue = Queue()

        self.setup_ui()
        self.check_messages()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
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

        self.start_button = tk.Button(self.root, text="Запустить", 
                                    command=self.start_bot, **button_style)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Остановить", 
                                   command=self.stop_bot, **button_style)
        self.stop_button.pack(pady=10)

    def press_key(self, key_char):
        """Нажимает физическую клавишу по scancode (работает в любой раскладке)"""
        scancode = SCANCODES.get(key_char.lower())
        wait_time = random.uniform(1, 4)
        if scancode:
            key.press(scancode)
            time.sleep(wait_time)  # Короткая задержка для имитации нажатия
            key.release(scancode)
        else:
            key.send(key_char)  # Фолбэк на обычный метод, если scancode не найден

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
        time.sleep(5)  # Начальная задержка перед стартом
        
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
            
            # Используем event.wait вместо time.sleep для возможности прерывания
            self.event.wait(cycle_wait)
            self.event.clear()

    def check_messages(self):
        """Проверка сообщений в очереди для вывода в консоль"""
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

    def stop_bot(self):
        """Остановка бота"""
        if self.running:
            self.running = False
            self.event.set()  # Прерываем ожидание
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=1)
            self.message_queue.put("Бот остановлен")