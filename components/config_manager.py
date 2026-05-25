"""
Модуль для сохранения и загрузки настроек всех ботов
Поддерживает автосохранение параметров интерфейса
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Определяем базовую директорию приложения
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")
DEFAULT_CONFIG = {
    "version": "3.0",
    
    # Общие настройки для всех ботов
    "common": {
        "resolution_mode": "FullHD",
        "color_tolerance": 10
    },
    
    # AFK+ бот
    "antiafk": {
        "fast_mode": False
    },
    
    # Стройка
    "builder": {
        "delay_between_presses": 120,
        "resolution_mode": "FullHD",
        "color_tolerance": 10,
        "counter_visible": False
    },
    
    # Готовка
    "cooking": {
        "cycles": 1,
        "resolution_mode": "FullHD",
        "sequence": [],
        "counter_visible": False
    },
    
    # Качалка (тренажерный зал)
    "gym": {
        "cycles": 0,
        "key_with_food": "5",
        "miss_chance": 0,
        "espander": False,
        "bind_espander": "p",
        "min_time_between_sets": 35,
        "max_time_between_sets": 50,
        "counter_visible": False
    },
    
    # Колесо удачи
    "lucky_wheel": {
        "hours": 0,
        "minutes": 0,
        "resolution_mode": "FullHD"
    },
    
    # Шахта
    "mining": {
        "delay_between_presses": 120,
        "resolution_mode": "FullHD",
        "color_tolerance": 10,
        "counter_visible": False
    },
    
    # Порт
    "port": {
        "resolution_mode": "FullHD",
        "auto_run": False,
        "counter_visible": False
    },
    
    # Коровник
    "farm_cows": {
        "delay_between_presses": 180,
        "resolution_mode": "FullHD",
        "color_tolerance": 15,
        "counter_visible": False
    },
    
    # Швея
    "seamstress": {
        "total_time_sec": 35,
        "min_delay": 0.1,
        "max_delay": 0.3,
        "counter_visible": False
    },
    
    # Токарь
    "turner": {
        "vertical_offset": 50,
        "horizontal_offset": 5
    },
    
    # Ловля КПК
    "catch_pda": {
        "confidence": 0.7,
        "click_cooldown": 2.5
    }
}


class ConfigManager:
    """Управление конфигурацией ботов"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Синглтон для единого доступа к конфигурации"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Загружает конфигурацию из файла"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Объединяем с дефолтной конфигурацией
                    self._config = self._merge_config(DEFAULT_CONFIG.copy(), saved_config)
                print(f"Конфигурация загружена из: {CONFIG_FILE}")
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save_config()
    
    def _merge_config(self, default: Dict, saved: Dict) -> Dict:
        """Рекурсивное объединение конфигураций"""
        for key, value in saved.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    default[key] = self._merge_config(default[key], value)
                else:
                    default[key] = value
        return default
    
    def _save_config(self):
        """Сохраняет конфигурацию в файл"""
        try:
            # Создаем резервную копию перед сохранением
            if os.path.exists(CONFIG_FILE):
                backup_file = CONFIG_FILE + ".backup"
                try:
                    import shutil
                    shutil.copy2(CONFIG_FILE, backup_file)
                except:
                    pass
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            print(f"Конфигурация сохранена в: {CONFIG_FILE}")
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get(self, module: str, key: str = None, default: Any = None) -> Any:
        """
        Получить значение настройки
        
        Args:
            module: Имя модуля (common, builder, gym и т.д.)
            key: Имя ключа (если None, возвращает весь словарь модуля)
            default: Значение по умолчанию, если ключ не найден
        
        Returns:
            Значение настройки
        """
        if module not in self._config:
            return default
        
        if key is None:
            return self._config[module].copy()
        
        return self._config[module].get(key, default)
    
    def set(self, module: str, key: str, value: Any, auto_save: bool = True):
        """
        Установить значение настройки
        
        Args:
            module: Имя модуля
            key: Имя ключа
            value: Новое значение
            auto_save: Автоматически сохранить в файл
        """
        if module not in self._config:
            self._config[module] = {}
        
        self._config[module][key] = value
        
        if auto_save:
            self._save_config()
    
    def set_multiple(self, module: str, settings: Dict, auto_save: bool = True):
        """
        Установить несколько настроек для модуля
        
        Args:
            module: Имя модуля
            settings: Словарь с настройками {key: value}
            auto_save: Автоматически сохранить в файл
        """
        if module not in self._config:
            self._config[module] = {}
        
        self._config[module].update(settings)
        
        if auto_save:
            self._save_config()
    
    def save_sequence(self, module: str, sequence: list):
        """
        Сохранить последовательность действий для модуля
        
        Args:
            module: Имя модуля
            sequence: Список действий
        """
        self.set(module, "sequence", sequence, auto_save=True)
    
    def load_sequence(self, module: str) -> list:
        """Загрузить сохраненную последовательность"""
        return self.get(module, "sequence", [])
    
    def reset_module(self, module: str, auto_save: bool = True):
        """
        Сбросить настройки модуля до значений по умолчанию
        
        Args:
            module: Имя модуля
            auto_save: Автоматически сохранить
        """
        if module in DEFAULT_CONFIG:
            self._config[module] = DEFAULT_CONFIG[module].copy()
            if auto_save:
                self._save_config()
    
    def reset_all(self):
        """Сбросить все настройки до значений по умолчанию"""
        self._config = DEFAULT_CONFIG.copy()
        self._save_config()
    
    def export_config(self, filepath: str = None) -> str:
        """
        Экспортировать конфигурацию в файл
        
        Args:
            filepath: Путь для экспорта (если None, возвращает JSON строку)
        
        Returns:
            JSON строка с конфигурацией
        """
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        
        return json.dumps(self._config, ensure_ascii=False, indent=2)
    
    def import_config(self, filepath: str):
        """
        Импортировать конфигурацию из файла
        
        Args:
            filepath: Путь к файлу конфигурации
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            imported_config = json.load(f)
        
        self._config = self._merge_config(DEFAULT_CONFIG.copy(), imported_config)
        self._save_config()


# Создаем глобальный экземпляр для удобного импорта
config = ConfigManager()