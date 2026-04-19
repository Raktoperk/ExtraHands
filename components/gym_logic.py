import cv2
import numpy as np
import time
import threading
import random
from .functions import press_key

# Пробуем использовать mss для быстрого скриншота
USE_MSS = False
mss = None

try:
    import mss
    import mss.tools
    USE_MSS = True
    print("MSS доступен для быстрого захвата экрана")
except ImportError:
    print("MSS не установлен, используем PIL.ImageGrab")

# Fallback на PIL
if not USE_MSS:
    try:
        from PIL import ImageGrab
        print("Используем PIL.ImageGrab для захвата экрана")
    except ImportError:
        print("PIL не установлен, захват экрана невозможен")
        exit(1)

# Область поиска [левый верхний угол: (735, 557) правый нижний угол: (1160, 960)]
SEARCH_AREA = (705, 527, 1190, 990)  # (left, top, right, bottom)

# Диапазоны цветов из 1.py
white_lower = np.array([250, 250, 250])
white_upper = np.array([255, 255, 255])

# Диапазоны цветов для зеленой окружности (из gym.py)
green_lower_hsv = np.array([35, 40, 40])
green_upper_hsv = np.array([85, 255, 220])

# Настройки
GREEN_RADIUS_OFFSET = 8  # Добавка к радиусу зеленой окружности (10-15px)
MISS_OFFSET = -10  # Отнимаемый радиус при промахе
DEFAULT_MISS_CHANCE = 0  # Шанс промаха по умолчанию (0%)

# Переменные для отслеживания состояния
green_radius = None
condition_triggered = False
miss_chance = DEFAULT_MISS_CHANCE  # Текущий шанс промаха

# Режим отладки (по умолчанию False для оптимизации)
DEBUG_MODE = True

# Кэширование для оптимизации
last_frame_time = 0
TARGET_FPS = 60
frame_time_target = 1.0 / TARGET_FPS
fps_counter = 0
fps_last_time = time.time()

# Для Windows DPI awareness (решение проблемы с двумя мониторами)
if hasattr(threading, 'local'):
    _thread_local = threading.local()
else:
    class SimpleLocal:
        def __init__(self):
            self._data = {}
        
        def __getattr__(self, name):
            if name in self._data:
                return self._data[name]
            raise AttributeError(f"'SimpleLocal' object has no attribute '{name}'")
        
        def __setattr__(self, name, value):
            if name == '_data':
                super().__setattr__(name, value)
            else:
                self._data[name] = value
    
    _thread_local = SimpleLocal()

def init_mss_for_thread():
    """Инициализировать MSS для текущего потока с обработкой ошибок"""
    global USE_MSS
    if not USE_MSS:
        return None
    
    try:
        # Создаем экземпляр MSS с явным указанием монитора
        mss_instance = mss.mss()
        
        # Получаем список мониторов
        monitors = mss_instance.monitors
        print(f"Доступно мониторов: {len(monitors)}")
        
        # Пробуем использовать монитор 1 (первый после основного)
        if len(monitors) > 1:
            # Пробуем определить, на каком мониторе находится область захвата
            # Для простоты используем монитор 1 (основной монитор обычно 1)
            monitor_idx = 1
            monitor = monitors[monitor_idx]
            
            # Проверяем, находится ли наша область на этом мониторе
            left, top, right, bottom = SEARCH_AREA
            width = right - left
            height = bottom - top
            
            # Сохраняем информацию о мониторе
            _thread_local.mss_monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            
            # Пробуем сделать тестовый захват
            test_screenshot = mss_instance.grab(_thread_local.mss_monitor)
            test_array = np.array(test_screenshot)
            
            if test_array.size > 0:
                print(f"Успешная инициализация MSS для монитора {monitor_idx}")
                _thread_local.mss_instance = mss_instance
                return mss_instance
            else:
                print("Тестовый захват вернул пустое изображение")
                mss_instance.close()
                return None
        else:
            print("Только один монитор доступен")
            mss_instance.close()
            return None
            
    except Exception as e:
        print(f"Ошибка инициализации MSS: {e}")
        return None

def get_mss_instance():
    """Получить или создать экземпляр MSS для текущего потока"""
    global USE_MSS
    if not USE_MSS:
        return None
    
    # Пытаемся получить существующий экземпляр
    if hasattr(_thread_local, 'mss_instance') and _thread_local.mss_instance is not None:
        try:
            # Проверяем, работает ли еще экземпляр
            # Простой тест - проверяем атрибут
            if hasattr(_thread_local.mss_instance, 'closed'):
                if _thread_local.mss_instance.closed:
                    # Пересоздаем
                    return init_mss_for_thread()
            return _thread_local.mss_instance
        except:
            # Если возникла ошибка, пересоздаем
            return init_mss_for_thread()
    else:
        # Создаем новый
        return init_mss_for_thread()

def fast_screenshot_mss():
    """Быстрый захват экрана с использованием MSS"""
    global USE_MSS
    if not USE_MSS:
        return None
    
    try:
        mss_instance = get_mss_instance()
        if mss_instance is None:
            return None
        
        # Используем сохраненную область монитора
        if hasattr(_thread_local, 'mss_monitor'):
            monitor = _thread_local.mss_monitor
        else:
            # Формируем область захвата
            left, top, right, bottom = SEARCH_AREA
            width = right - left
            height = bottom - top
            
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
        
        # Захватываем экран
        screenshot = mss_instance.grab(monitor)
        
        # Конвертируем в numpy array
        img = np.array(screenshot)
        
        # Конвертируем формат
        if img.shape[2] == 4:  # BGRA
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif img.shape[2] == 3:  # BGR (уже)
            pass
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
        return img
        
    except Exception as e:
        print(f"Ошибка MSS захвата: {e}")
        # При ошибке сбрасываем экземпляр MSS
        if hasattr(_thread_local, 'mss_instance'):
            _thread_local.mss_instance = None
        return None

def fast_screenshot_pil():
    """Захват экрана с использованием PIL (надежный метод)"""
    try:
        # Прямой захват области
        screenshot = ImageGrab.grab(bbox=SEARCH_AREA)
        
        # Конвертируем PIL Image в numpy array
        img = np.array(screenshot)
        
        # PIL возвращает RGB, конвертируем в BGR для OpenCV
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        print(f"Ошибка PIL захвата: {e}")
        return None

def fast_screenshot():
    """Умный захват экрана с приоритетом надежности"""
    global USE_MSS
    # Сначала пробуем MSS если доступен
    if USE_MSS:
        img = fast_screenshot_mss()
        if img is not None and img.size > 0:
            return img
    
    # Если MSS не сработал, используем PIL
    return fast_screenshot_pil()

def set_debug_mode(enabled):
    """Установить режим отладки"""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    return DEBUG_MODE

def set_miss_chance(percent):
    """Установить шанс промаха в процентах"""
    global miss_chance
    miss_chance = max(0, min(100, percent))  # Ограничиваем от 0 до 100
    print(f"Шанс промаха установлен: {miss_chance}%")
    return miss_chance

def should_miss():
    """Определить, должен ли произойти промах"""
    global miss_chance
    if miss_chance <= 0:
        return False
    roll = random.randint(1, 100)
    return roll <= miss_chance

def find_white_circle(image):
    """
    Обнаружение белой окружности (оптимизированная версия)
    """
    if image is None or image.size == 0:
        return None
    
    # Создаем маску для белого цвета
    white_mask = cv2.inRange(image, white_lower, white_upper)
    
    # Быстрая проверка: если белых пикселей слишком мало
    white_pixels = cv2.countNonZero(white_mask)
    if white_pixels < 30:
        return None
    
    # Быстрые морфологические операции
    white_mask = cv2.medianBlur(white_mask, 3)
    
    # Находим контуры
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Ищем самый большой контур
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    if area < 50:  # Минимальная площадь
        return None
    
    # Проверяем округлость
    perimeter = cv2.arcLength(largest_contour, True)
    if perimeter == 0:
        return None
    
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    if circularity < 0.5:
        return None
    
    # Получаем окружность
    (x, y), radius = cv2.minEnclosingCircle(largest_contour)
    return (int(x), int(y), int(radius))

def find_green_circle(image):
    """
    Обнаружение зеленой окружности (оптимизированная версия)
    """
    if image is None or image.size == 0:
        return None
    
    # Преобразуем в HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Маска для зеленого в HSV
    mask = cv2.inRange(hsv, green_lower_hsv, green_upper_hsv)
    
    # Быстрая проверка: если зеленых пикселей слишком мало
    green_pixels = cv2.countNonZero(mask)
    if green_pixels < 30:
        return None
    
    # Быстрые морфологические операции
    mask = cv2.medianBlur(mask, 3)
    
    # Находим контуры
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Ищем самый большой контур
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    if area < 50 or area > 50000:
        return None
    
    # Проверяем округлость
    perimeter = cv2.arcLength(largest_contour, True)
    if perimeter == 0:
        return None
    
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    if circularity < 0.4:
        return None
    
    # Получаем окружность
    (x, y), radius = cv2.minEnclosingCircle(largest_contour)
    return (int(x), int(y), int(radius))

def process_frame():
    """Обрабатывает один кадр"""
    global green_radius, condition_triggered, fps_counter, fps_last_time, last_frame_time, miss_chance
    
    current_time = time.time()
    
    # Контроль FPS
    if current_time - last_frame_time < frame_time_target:
        return None, False, False, False
    
    last_frame_time = current_time
    
    # Делаем скриншот
    img = fast_screenshot()
    if img is None or img.size == 0:
        return None, False, False, False
    
    # В режиме отладки создаем копию для отрисовки
    if DEBUG_MODE:
        original = img.copy()
        height, width = img.shape[:2]
        cv2.rectangle(original, (0, 0), (width-1, height-1), (255, 255, 0), 2)
    else:
        original = None
    
    # Находим окружности
    white_circle = find_white_circle(img)
    green_circle = find_green_circle(img)
    
    # Обновляем радиус зеленой окружности
    if green_circle is not None:
        _, _, new_green_radius = green_circle
        if green_radius != new_green_radius:
            green_radius = new_green_radius
    
    # Проверяем условие: радиус белой <= (радиусу зеленой + смещение)
    if white_circle is not None and green_radius is not None:
        _, _, white_radius = white_circle
        
        # Определяем, сработал ли промах
        missed = should_miss()
        
        if missed:
            # При промахе отнимаем 40px
            green_radius_with_offset = green_radius + MISS_OFFSET
            offset_text = f"ПРОМАХ: -40px"
        else:
            # Обычное смещение +15px
            green_radius_with_offset = green_radius + GREEN_RADIUS_OFFSET
            offset_text = f"+{GREEN_RADIUS_OFFSET}px"
        
        if white_radius <= green_radius_with_offset:
            if not condition_triggered:
                press_key('space')
                status = "ПРОМАХ!" if missed else "УСПЕХ!"
                print(f"⏰ {status} Радиус белой ({white_radius}) <= радиусу зеленой ({green_radius}) {offset_text} = {green_radius_with_offset}")
                condition_triggered = True
        else:
            # Сбрасываем флаг, если условие перестало выполняться
            condition_triggered = False
    
    # В режиме отладки добавляем отрисовку
    if DEBUG_MODE:
        show_circles = False
        
        # Подсчет FPS
        fps_counter += 1
        if current_time - fps_last_time >= 1.0:
            fps = fps_counter / (current_time - fps_last_time)
            fps_counter = 0
            fps_last_time = current_time
            
            # Отображаем FPS и шанс промаха
            cv2.putText(original, f'FPS: {fps:.1f}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(original, f'Промах: {miss_chance}%', (10, 55), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)
        
        # Рисуем окружности если найдены
        if white_circle:
            wx, wy, wr = white_circle
            cv2.circle(original, (wx, wy), wr, (0, 0, 255), 2)
            cv2.circle(original, (wx, wy), 2, (0, 0, 255), -1)
            show_circles = True
        
        if green_circle:
            gx, gy, gr = green_circle
            cv2.circle(original, (gx, gy), gr, (0, 255, 0), 2)
            cv2.circle(original, (gx, gy), 2, (0, 255, 0), -1)
            show_circles = True
        
        return original, white_circle is not None, green_circle is not None, show_circles
    
    return None, white_circle is not None, green_circle is not None, False

def run_detector(callback=None, miss_chance_percent=0):
    """Запуск детектора в фоновом режиме с настройкой шанса промаха"""
    global green_radius, condition_triggered, last_frame_time, USE_MSS, miss_chance
    
    # Инициализация
    green_radius = None
    condition_triggered = False
    last_frame_time = time.time()
    
    # Устанавливаем шанс промаха
    miss_chance = max(0, min(100, miss_chance_percent))
    
    print("Детектор окружностей запущен в фоновом режиме")
    print(f"Смещение: +{GREEN_RADIUS_OFFSET}px, Промах: -{abs(MISS_OFFSET)}px, Шанс промаха: {miss_chance}%, Целевой FPS: {TARGET_FPS}")
    
    # Инициализируем MSS для этого потока (если доступен)
    if USE_MSS:
        print("Попытка инициализации MSS...")
        mss_instance = init_mss_for_thread()
        if mss_instance is None:
            print("MSS не удалось инициализировать, использую PIL")
            USE_MSS = False
        else:
            print("MSS успешно инициализирован")
    
    frame_count = 0
    last_fps_time = time.time()
    last_debug_time = time.time()
    fps_samples = []
    
    while True:
        try:
            current_time = time.time()
            
            # Контроль FPS
            if current_time - last_frame_time < frame_time_target:
                time.sleep(0.001)  # Минимальная пауза
                continue
            
            last_frame_time = current_time
            
            # Делаем скриншот
            img = fast_screenshot()
            if img is None or img.size == 0:
                time.sleep(0.01)
                continue
            
            # Находим окружности
            white_circle = find_white_circle(img)
            green_circle = find_green_circle(img)
            
            # Обновляем радиус
            if green_circle is not None:
                _, _, new_green_radius = green_circle
                if green_radius != new_green_radius:
                    green_radius = new_green_radius
            
            # Проверяем условие
            if white_circle is not None and green_radius is not None:
                _, _, white_radius = white_circle
                
                # Определяем, сработал ли промах
                missed = should_miss()
                
                if missed:
                    # При промахе отнимаем 40px
                    green_radius_with_offset = green_radius + MISS_OFFSET
                    offset_info = f"ПРОМАХ: -{abs(MISS_OFFSET)}px"
                else:
                    # Обычное смещение +15px
                    green_radius_with_offset = green_radius + GREEN_RADIUS_OFFSET
                    offset_info = f"+{GREEN_RADIUS_OFFSET}px"
                
                if white_radius <= green_radius_with_offset:
                    if not condition_triggered:
                        press_key('space')
                        status = "ПРОМАХ!" if missed else "УСПЕХ!"
                        print(f"⏰ {status} Радиус белой ({white_radius}) <= радиусу зеленой ({green_radius}) {offset_info}")
                        condition_triggered = True
                        
                        if callback:
                            callback()
                else:
                    condition_triggered = False
            
            # Подсчет FPS для отладки
            frame_count += 1
            if current_time - last_fps_time >= 1.0:
                fps = frame_count / (current_time - last_fps_time)
                fps_samples.append(fps)
                
                # Держим только последние 10 значений
                if len(fps_samples) > 10:
                    fps_samples.pop(0)
                
                avg_fps = sum(fps_samples) / len(fps_samples)
                
                # Выводим статистику каждые 5 секунд
                if current_time - last_debug_time >= 5.0:
                    capture_method = "MSS" if USE_MSS else "PIL"
                    print(f"\r[Детектор] FPS: {avg_fps:.1f} | Метод: {capture_method} | Промах: {miss_chance}% | Белая: {'Да' if white_circle else 'Нет'} | Зеленая: {'Да' if green_circle else 'Нет'}", end="")
                    last_debug_time = current_time
                
                frame_count = 0
                last_fps_time = current_time
            
        except KeyboardInterrupt:
            print("\nДетектор остановлен")
            break
        except Exception as e:
            print(f"Ошибка детектора: {e}")
            time.sleep(0.1)

def main(debug=False, miss_chance_percent=0):
    """Основная функция с поддержкой режима отладки и шанса промаха"""
    global green_radius, condition_triggered, DEBUG_MODE, USE_MSS, miss_chance
    
    # Устанавливаем режим отладки
    DEBUG_MODE = debug
    
    # Устанавливаем шанс промаха
    miss_chance = miss_chance_percent
    
    if DEBUG_MODE:
        print("Детектор окружностей с ограниченной областью поиска (DEBUG MODE)")
        print(f"Целевой FPS: {TARGET_FPS}, Шанс промаха: {miss_chance}%")
        print(f"Смещение: +{GREEN_RADIUS_OFFSET}px, Промах: -{abs(MISS_OFFSET)}px")
        print("=" * 70)
    else:
        print("Детектор окружностей (оптимизированный режим)")
        print(f"Смещение: +{GREEN_RADIUS_OFFSET}px, Промах: -{abs(MISS_OFFSET)}px, Шанс промаха: {miss_chance}%")
        print("Нажмите Ctrl+C для выхода")
    
    # Инициализация
    green_radius = None
    condition_triggered = False
    
    while True:
        try:
            # Обрабатываем кадр
            result, white_found, green_found, circles_shown = process_frame()
            
            # В режиме отладки показываем результат
            if DEBUG_MODE and result is not None:
                # Показываем результат
                cv2.imshow('Radius Tracking Circle Detector', result)
                
                # Обработка клавиш
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('d'):
                    print("\nВыключение режима отладки...")
                    cv2.destroyAllWindows()
                    DEBUG_MODE = False
                    print("Режим отладки выключен")
                elif key == ord('+') or key == ord('='):
                    # Увеличиваем шанс промаха на 5%
                    new_chance = min(100, miss_chance + 5)
                    set_miss_chance(new_chance)
                elif key == ord('-'):
                    # Уменьшаем шанс промаха на 5%
                    new_chance = max(0, miss_chance - 5)
                    set_miss_chance(new_chance)
            
        except KeyboardInterrupt:
            print("\nПрерывание пользователем")
            break
        except Exception as e:
            print(f"\nОшибка: {e}")
            time.sleep(0.1)
    
    if DEBUG_MODE:
        cv2.destroyAllWindows()
    print("\nПрограмма завершена.")

if __name__ == "__main__":
    # Запуск с режимом отладки по умолчанию
    # Можно передать шанс промаха через аргументы командной строки
    import sys
    miss_chance_arg = 0
    if len(sys.argv) > 1:
        try:
            miss_chance_arg = int(sys.argv[1])
        except:
            pass
    main(debug=True, miss_chance_percent=miss_chance_arg)