import ctypes
import time
import random
from .key_codes import LAYOUT_MAP
import keyboard as Key
import pyautogui
import numpy as np
import cv2

# Конвертация в миллисекунды

def toMS(num = 1):
    return num / 1000 # Просто делит введённое число на 1000 (1с = 0.001мс)



# Нажатие физической клавиши с определённой задержкой

def get_keyboard_layout():
    """Определяет текущую раскладку клавиатуры"""
    try:
        # Получаем дескриптор активного окна
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        # Получаем ID потока окна
        thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, 0)
        
        # Получаем раскладку клавиатуры для потока
        layout_id = ctypes.windll.user32.GetKeyboardLayout(thread_id)
        
        # Младшее слово содержит код языка (0x409 - английский, 0x419 - русский)
        lang_id = layout_id & 0xFFFF
        
        if lang_id == 0x419:  # Русский
            return 'ru'
        elif lang_id == 0x409:  # Английский (США)
            return 'en'
        else:
            # По умолчанию считаем английской
            return 'en'
    except:
        # В случае ошибки считаем английской раскладкой
        return 'en'


def convert_key_for_layout(key, target_layout='en'):
    """
    Преобразует клавишу для нужной раскладки
    target_layout: 'en' - для нажатия, 'ru' - для отображения
    """
    if not isinstance(key, str) or len(key) != 1:
        return key
    
    # Если целевая раскладка английская, конвертируем русские символы в английские
    if target_layout == 'en':
        # Проверяем, является ли символ русским
        if key in LAYOUT_MAP:
            return LAYOUT_MAP[key]
    
    # Если целевая раскладка русская или символ не найден, возвращаем как есть
    return key



def press_key(key, boundary=(toMS(60), toMS(140)), use_ctypes=False):
    """Нажатие клавиши с учётом текущей раскладки"""
    
    # Определяем текущую раскладку
    current_layout = get_keyboard_layout()
    
    # Преобразуем клавишу, если нужно
    if current_layout == 'ru':
        # Если раскладка русская, преобразуем русские символы в английские
        # для правильного нажатия физических клавиш
        key_to_press = convert_key_for_layout(key, target_layout='en')
    else:
        # Для английской раскладки оставляем как есть
        key_to_press = key
    
    # Если key_to_press - строка из нескольких символов (комбинация),
    # обрабатываем каждый символ отдельно
    if isinstance(key_to_press, str) and '+' in key_to_press:
        parts = key_to_press.split('+')
        for part in parts:
            # Преобразуем каждую часть, если это одиночный символ
            if len(part) == 1:
                part = convert_key_for_layout(part, target_layout='en')
            Key.press(part)
            time.sleep(random.uniform(*boundary) / len(parts))  # Распределяем задержку
        for part in reversed(parts):
            if len(part) == 1:
                part = convert_key_for_layout(part, target_layout='en')
            Key.release(part)
    else:
        # Одиночная клавиша
        Key.press(key_to_press)
        time.sleep(random.uniform(*boundary))
        Key.release(key_to_press)


# Дополнительная функция для печати текста с учётом раскладки
def type_text(text, delay_between_keys=(toMS(60), toMS(140))):
    """Печатает текст с учётом текущей раскладки клавиатуры"""
    current_layout = get_keyboard_layout()
    
    for char in text:
        if current_layout == 'ru':
            # Преобразуем каждый символ для английской раскладки
            key_to_press = convert_key_for_layout(char, target_layout='en')
        else:
            key_to_press = char
        
        press_key(key_to_press, boundary=delay_between_keys)


# Клик ЛКМ в заданных координатах

def click_coordinates(coordinates):
    pyautogui.click(coordinates[0], coordinates[1])


# Проверка заданного цвета в заданных координатах

def check_color(coordinates=(0, 0), color=(0, 0, 0), tolerance=0):
    """
    Проверяет соответствие цвета пикселя в заданных координатах.
    
    Args:
        coordinates (tuple): Координаты (x, y) для проверки
        color (tuple): Ожидаемый цвет (r, g, b)
        tolerance (int): Допустимая погрешность для каждого канала цвета (0-255)
    
    Returns:
        bool: True если цвет соответствует с учётом погрешности, иначе False
    """
    try:
        # Получаем текущий цвет пикселя
        current_color = pyautogui.pixel(*coordinates)
        
        # Если погрешность равна 0, используем точное сравнение
        if tolerance == 0:
            return pyautogui.pixelMatchesColor(*coordinates, color)
        
        # Сравниваем цвета с учётом погрешности
        for current_channel, expected_channel in zip(current_color, color):
            if abs(current_channel - expected_channel) > tolerance:
                return False
        return True
        
    except Exception as e:
        print(f"Ошибка при проверке цвета: {e}")
        return False

# Поиск заданного изображения на экране и определение координат его центра

def detect_image(template_path, threshold=0.8): # (Задаваемое изображение, точность соответствия)
        # Загрузка изображения
        template = cv2.imread(template_path, 0)

        # Проверка наличия изображения        
        # if template is None:
        #     print(f"Ошибка: Не удалось загрузить изображение по пути {template_path}")
        #     return None
        
        # Обработка изображения
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        w, h = template.shape[:2] # Опредение разрешения исходного изображения

        center = (max_loc[0] + w // 2, max_loc[1] + h // 2) # Подсчёт центральных координат

        if max_val >= threshold: # Если соответствует, то выведет координаты центра, иначе "None"
            return center 
        else:
            return None
