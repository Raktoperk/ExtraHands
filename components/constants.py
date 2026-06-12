"""
Константы для всех ботов
Централизованное хранение магических чисел
"""

from typing import Tuple

# ============ Времена нажатий (секунды) ============
PRESS_KEY_DURATION: Tuple[float, float] = (0.04, 0.12)      # Стандартное время нажатия
PRESS_KEY_FAST: Tuple[float, float] = (0.03, 0.06)          # Быстрое нажатие
PRESS_KEY_SLOW: Tuple[float, float] = (0.9, 1.0)            # Долгое нажатие
PRESS_KEY_E: Tuple[float, float] = (0.04, 0.12)             # Для клавиши E
PRESS_KEY_A_D: Tuple[float, float] = (0.04, 0.12)           # Для клавиш A/D

# ============ Таймауты (секунды) ============
ACTION_TIMEOUT: int = 15                     # Таймаут действия
CLICK_COOLDOWN: float = 2.5                  # Задержка между кликами
LUCKY_WHEEL_CYCLE_TIME: int = 15000          # 4 часа 10 минут
GYM_MARKER_TIMEOUT: int = 10                 # Таймаут маркера тренажерного зала
HUNGRY_CHECK_DELAY: Tuple[float, float] = (5, 8)  # Задержка при голоде

# ============ Задержки по умолчанию (миллисекунды) ============
DEFAULT_DELAY_BUILDER: int = 120
DEFAULT_DELAY_MINING: int = 120
DEFAULT_DELAY_FARM_COWS: int = 180
DEFAULT_DELAY_ANTIAFK_FAST: Tuple[float, float] = (0.03, 0.06)
DEFAULT_DELAY_ANTIAFK_STANDARD: Tuple[float, float] = (0.9, 1.0)

# ============ Допуски цвета ============
COLOR_TOLERANCE_NORMAL: int = 10
COLOR_TOLERANCE_HIGH: int = 15
COLOR_TOLERANCE_ZERO: int = 0

# ============ Размеры и смещения ============
GREEN_RADIUS_OFFSET: int = 8                 # Смещение радиуса зеленой окружности
MISS_OFFSET: int = -10                       # Отнимаемый радиус при промахе
SMOOTHING_SIZE: int = 3                     # Размер буфера сглаживания
CLICK_OFFSET_RANGE: int = 15                 # Диапазон случайного смещения клика
MOVEMENT_DURATION: Tuple[float, float] = (0.15, 0.3)  # Длительность движения мыши

# ============ Поиск изображений ============
IMAGE_CONFIDENCE_NORMAL: float = 0.8
IMAGE_CONFIDENCE_STRICT: float = 0.9
IMAGE_CONFIDENCE_LAX: float = 0.7
IMAGE_SCALE_THRESHOLD: int = 10000           # Порог для уменьшения изображения

# ============ FPS ограничения ============
TARGET_FPS: int = 60
MIN_FRAME_TIME: float = 1.0 / TARGET_FPS

# ============ Цвета RGB ============
COLOR_LIGHT_GREEN: Tuple[int, int, int] = (126, 211, 33)
COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
COLOR_WHITE_MARKER: Tuple[int, int, int] = (253, 253, 253)
COLOR_DANGER: Tuple[int, int, int] = (255, 105, 86)

# ============ Проверка голода ============
HUNGER_CHECK_MIN: int = 5      # Минимальное количество подходов между проверками голода
HUNGER_CHECK_MAX: int = 10     # Максимальное количество подходов между проверками голода
HUNGER_COLOR_COORDS: Tuple[int, int] = (910, 240)  # Координаты проверки голода (из test.py)
HUNGER_COLOR_TARGET: Tuple[int, int, int] = (194, 90, 18)  # Цвет голода RGB(194, 90, 18)
HUNGER_COLOR_TOLERANCE: int = 15  # Допуск для цвета голода

# ============ Логирование ============
ERROR_KEYWORDS: Tuple[str, ...] = (
    'ОШИБКА', 'ERROR', 'EXCEPTION', 'FAIL', 
    'FAILED', 'КРИТИЧЕСКАЯ', 'WARNING', 'ВНИМАНИЕ'
)