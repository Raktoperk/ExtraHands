"""
Оптимизированный модуль для поиска изображений на экране
Использует MSS для быстрого захвата и OpenCV для поиска
"""

import os
import sys
from typing import Optional, Tuple, Dict, Any
from functools import lru_cache

import cv2
import numpy as np
import pyautogui

from mss import mss


class OptimizedImageFinder:
    """
    Оптимизированный поиск изображений с кэшированием шаблонов
    Поддерживает ограниченную область поиска и сглаживание координат
    """
    
    # Кэш шаблонов на уровне класса
    _template_cache: Dict[str, np.ndarray] = {}
    _template_info_cache: Dict[str, Dict[str, int]] = {}
    
    def __init__(self, 
                 confidence: float = 0.8,
                 search_area: Optional[Tuple[int, int, int, int]] = None,
                 use_cache: bool = True,
                 smoothing: bool = True,
                 smoothing_size: int = 3):
        """
        Args:
            confidence: Порог уверенности (0-1)
            search_area: Область поиска (left, top, right, bottom) или None для всего экрана
            use_cache: Использовать кэш шаблонов
            smoothing: Использовать сглаживание координат
            smoothing_size: Размер буфера сглаживания
        """
        self._confidence = confidence
        self._search_area = search_area
        self._use_cache = use_cache
        self._smoothing = smoothing
        self._smoothing_size = smoothing_size
        
        self._sct = mss()
        self._last_position: Optional[Tuple[int, int]] = None
        self._position_buffer: list = []
        self._frame_count = 0
        
        # Предварительные вычисления для области поиска
        if search_area:
            self._search_left, self._search_top, self._search_right, self._search_bottom = search_area
            self._search_width = self._search_right - self._search_left
            self._search_height = self._search_bottom - self._search_top
        else:
            self._search_left = self._search_top = 0
            self._search_width = self._search_height = None
        
        # Настройка pyautogui для максимальной скорости
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
    
    @classmethod
    def load_template(cls, template_path: str, use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Загружает шаблон изображения с кэшированием
        
        Args:
            template_path: Путь к файлу шаблона
            use_cache: Использовать кэш
            
        Returns:
            Шаблон в градациях серого или None при ошибке
        """
        if use_cache and template_path in cls._template_cache:
            return cls._template_cache[template_path]
        
        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            
            if use_cache:
                cls._template_cache[template_path] = template
                cls._template_info_cache[template_path] = {
                    'h': template.shape[0],
                    'w': template.shape[1]
                }
            
            return template
        except Exception:
            return None
    
    @classmethod
    def get_template_info(cls, template_path: str) -> Dict[str, int]:
        """Возвращает информацию о шаблоне (ширина, высота)"""
        return cls._template_info_cache.get(template_path, {})
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Быстрый захват экрана или области
        
        Returns:
            Изображение в градациях серого или None при ошибке
        """
        try:
            if self._search_width is not None:
                # Захват только области поиска
                monitor = {
                    'left': self._search_left,
                    'top': self._search_top,
                    'width': self._search_width,
                    'height': self._search_height
                }
                screenshot = self._sct.grab(monitor)
                
                # Конвертация в numpy array
                frame = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                    screenshot.height, screenshot.width, 4
                )
                # Конвертация в grayscale (оптимизированная формула)
                gray = (0.299 * frame[:,:,2] + 0.587 * frame[:,:,1] + 0.114 * frame[:,:,0]).astype(np.uint8)
                return gray
            else:
                # Захват всего экрана
                screenshot = self._sct.grab(self._sct.monitors[1])
                frame = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                    screenshot.height, screenshot.width, 4
                )
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        except Exception:
            return None
    
    def find_image(self, template_path: str) -> Optional[Tuple[int, int, float]]:
        """
        Поиск изображения на экране
        
        Args:
            template_path: Путь к шаблону
            
        Returns:
            Кортеж (x, y, confidence) или None если не найдено
        """
        template = self.load_template(template_path, self._use_cache)
        if template is None:
            return None
        
        self._frame_count += 1
        
        # Захват экрана
        screenshot = self.capture_screen()
        if screenshot is None:
            return None
        
        h, w = template.shape
        
        # Оптимизация: уменьшаем разрешение для больших шаблонов
        if w * h > 10000:
            scale = 0.7
            small_screenshot = cv2.resize(screenshot, None, fx=scale, fy=scale, 
                                         interpolation=cv2.INTER_NEAREST)
            small_template = cv2.resize(template, None, fx=scale, fy=scale,
                                       interpolation=cv2.INTER_NEAREST)
            
            result = cv2.matchTemplate(small_screenshot, small_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self._confidence:
                center_x = int((max_loc[0] + small_template.shape[1] // 2) / scale)
                center_y = int((max_loc[1] + small_template.shape[0] // 2) / scale)
            else:
                return None
        else:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val < self._confidence:
                return None
            
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
        
        # Преобразование в абсолютные координаты
        if self._search_width is not None:
            abs_x = self._search_left + center_x
            abs_y = self._search_top + center_y
        else:
            abs_x, abs_y = center_x, center_y
        
        # Сглаживание координат
        if self._smoothing:
            self._position_buffer.append((abs_x, abs_y))
            if len(self._position_buffer) > self._smoothing_size:
                self._position_buffer.pop(0)
            
            if len(self._position_buffer) >= 2:
                xs = [p[0] for p in self._position_buffer]
                ys = [p[1] for p in self._position_buffer]
                abs_x = int(np.median(xs))
                abs_y = int(np.median(ys))
        
        return abs_x, abs_y, max_val
    
    def move_to(self, x: int, y: int) -> bool:
        """
        Мгновенное перемещение курсора (только если позиция изменилась)
        
        Returns:
            True если позиция изменилась, иначе False
        """
        if self._last_position != (x, y):
            pyautogui.moveTo(x, y, duration=0, _pause=False)
            self._last_position = (x, y)
            return True
        return False
    
    def click_at(self, x: int, y: int, button: str = 'left') -> None:
        """Клик по указанным координатам"""
        pyautogui.click(x, y, button=button, _pause=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику"""
        return {
            'frame_count': self._frame_count,
            'last_position': self._last_position
        }
    
    def find_image_coords(self, template_path: str) -> Optional[Tuple[int, int]]:
        """Поиск изображения и возврат только координат (без уверенности)"""
        result = self.find_image(template_path)
        if result:
            return (result[0], result[1])
        return None

    def close(self) -> None:
        """Освобождение ресурсов"""
        if self._sct:
            self._sct.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


def quick_find_image(template_path: str, 
                     confidence: float = 0.8,
                     search_area: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
    """
    Быстрый поиск изображения (один раз)
    
    Args:
        template_path: Путь к шаблону
        confidence: Порог уверенности
        search_area: Область поиска (left, top, right, bottom)
        
    Returns:
        Координаты центра или None
    """
    finder = OptimizedImageFinder(confidence=confidence, search_area=search_area, smoothing=False)
    try:
        result = finder.find_image(template_path)
        return (result[0], result[1]) if result else None
    finally:
        finder.close()