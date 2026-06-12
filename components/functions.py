"""
Общие утилитарные функции для ботов
Оптимизированные версии с типизацией
"""

import ctypes
import time
import random
from typing import Tuple, Optional, Union, List

import pyautogui
import cv2
import numpy as np
import keyboard  # ← импорт на уровне модуля (оптимизация)

from components.key_codes import LAYOUT_MAP
from components.constants import PRESS_KEY_DURATION, COLOR_TOLERANCE_NORMAL


def to_ms(seconds: float) -> float:
    """Конвертирует секунды в миллисекунды (фактически просто возвращает значение)"""
    return seconds


def get_keyboard_layout() -> str:
    """
    Определяет текущую раскладку клавиатуры
    
    Returns:
        'ru' для русской, 'en' для английской
    """
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, 0)
        layout_id = ctypes.windll.user32.GetKeyboardLayout(thread_id)
        lang_id = layout_id & 0xFFFF
        
        if lang_id == 0x419:  # Русский
            return 'ru'
        else:
            return 'en'
    except Exception:
        return 'en'


def convert_key_for_layout(key: str, target_layout: str = 'en') -> str:
    """
    Преобразует клавишу для нужной раскладки
    
    Args:
        key: Клавиша для преобразования
        target_layout: Целевая раскладка ('en' или 'ru')
    
    Returns:
        Преобразованная клавиша
    """
    if not isinstance(key, str) or len(key) != 1:
        return key
    
    if target_layout == 'en':
        return LAYOUT_MAP.get(key, key)
    
    return key


def press_key(key: str, boundary: Tuple[float, float] = PRESS_KEY_DURATION) -> None:
    """
    Нажатие клавиши с учётом текущей раскладки
    
    Args:
        key: Клавиша для нажатия
        boundary: Диапазон времени удержания (мин, макс) в секундах
    """
    current_layout = get_keyboard_layout()
    
    # Преобразование для русской раскладки
    if current_layout == 'ru':
        key_to_press = convert_key_for_layout(key, target_layout='en')
    else:
        key_to_press = key
    
    # Обработка комбинаций клавиш
    if isinstance(key_to_press, str) and '+' in key_to_press:
        parts = key_to_press.split('+')
        for part in parts:
            if len(part) == 1:
                part = convert_key_for_layout(part, target_layout='en')
            keyboard.press(part)
            time.sleep(random.uniform(*boundary) / len(parts))
        for part in reversed(parts):
            if len(part) == 1:
                part = convert_key_for_layout(part, target_layout='en')
            keyboard.release(part)
    else:
        keyboard.press(key_to_press)
        time.sleep(random.uniform(*boundary))
        keyboard.release(key_to_press)


def click_coordinates(coordinates: Tuple[int, int], 
                      button: str = 'left', 
                      duration: float = 0.1) -> None:
    """
    Клик в заданных координатах
    
    Args:
        coordinates: Координаты (x, y)
        button: Кнопка мыши ('left', 'right', 'middle')
        duration: Длительность перемещения
    """
    pyautogui.moveTo(coordinates[0], coordinates[1], duration=duration)
    pyautogui.click(button=button)


def check_color(coordinates: Tuple[int, int], 
                color: Tuple[int, int, int], 
                tolerance: int = COLOR_TOLERANCE_NORMAL) -> bool:
    """
    Проверяет цвет пикселя в заданных координатах
    
    Args:
        coordinates: Координаты (x, y)
        color: Ожидаемый цвет (r, g, b)
        tolerance: Допустимая погрешность для каждого канала
    
    Returns:
        True если цвет соответствует с учётом погрешности
    """
    try:
        if tolerance == 0:
            return pyautogui.pixelMatchesColor(coordinates[0], coordinates[1], color)
        
        current_color = pyautogui.pixel(coordinates[0], coordinates[1])
        for cur, exp in zip(current_color, color):
            if abs(cur - exp) > tolerance:
                return False
        return True
    except Exception:
        return False


def detect_image(template_path: str, 
                 threshold: float = 0.8,
                 region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
    """
    Поиск изображения на экране
    
    Args:
        template_path: Путь к шаблону
        threshold: Порог уверенности (0-1)
        region: Область поиска (left, top, width, height)
    
    Returns:
        Координаты центра изображения или None
    """
    try:
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return None
        
        # Захват экрана
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        
        # Поиск
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h, w = template.shape
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        
        return None
    except Exception:
        return None


def wait_for_color(coordinates: Tuple[int, int],
                   color: Tuple[int, int, int],
                   timeout: float = 30.0,
                   check_interval: float = 0.1,
                   tolerance: int = COLOR_TOLERANCE_NORMAL) -> bool:
    """
    Ожидает появления заданного цвета
    
    Args:
        coordinates: Координаты для проверки
        color: Ожидаемый цвет
        timeout: Таймаут в секундах
        check_interval: Интервал проверки
        tolerance: Допуск цвета
    
    Returns:
        True если цвет появился в течение таймаута
    """
    elapsed = 0.0
    while elapsed < timeout:
        if check_color(coordinates, color, tolerance):
            return True
        time.sleep(check_interval)
        elapsed += check_interval
    return False


def wait_for_color_disappear(coordinates: Tuple[int, int],
                              color: Tuple[int, int, int],
                              timeout: float = 30.0,
                              check_interval: float = 0.1,
                              tolerance: int = COLOR_TOLERANCE_NORMAL) -> bool:
    """
    Ожидает исчезновения заданного цвета
    
    Args:
        coordinates: Координаты для проверки
        color: Проверяемый цвет
        timeout: Таймаут в секундах
        check_interval: Интервал проверки
        tolerance: Допуск цвета
    
    Returns:
        True если цвет исчез в течение таймаута
    """
    elapsed = 0.0
    while elapsed < timeout:
        if not check_color(coordinates, color, tolerance):
            return True
        time.sleep(check_interval)
        elapsed += check_interval
    return False


def get_screen_resolution() -> Tuple[int, int]:
    """
    Возвращает текущее разрешение экрана
    
    Returns:
        Кортеж (width, height)
    """
    screen = pyautogui.size()
    return screen.width, screen.height


def detect_resolution_mode() -> str:
    """
    Определяет режим разрешения экрана
    
    Returns:
        'FullHD' для 1920x1080, 'QuadHD' для 2560x1440, иначе 'FullHD'
    """
    width, height = get_screen_resolution()
    if width == 1920 and height == 1080:
        return "FullHD"
    elif width == 2560 and height == 1440:
        return "QuadHD"
    else:
        return "FullHD"