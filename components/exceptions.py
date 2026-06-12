"""
Специфичные исключения для ботов
"""

class BotError(Exception):
    """Базовое исключение для всех ботов"""
    pass

class ImageNotFoundError(BotError):
    """Изображение не найдено на экране"""
    pass

class ColorNotDetectedError(BotError):
    """Ожидаемый цвет не обнаружен"""
    pass

class ConfigurationError(BotError):
    """Ошибка конфигурации или настроек"""
    pass

class ResolutionNotSupportedError(BotError):
    """Разрешение экрана не поддерживается"""
    pass

class WorkerStopError(BotError):
    """Ошибка при остановке рабочего потока"""
    pass