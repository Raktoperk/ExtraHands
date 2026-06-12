#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Автоматическая сборка Extra Hands через PyInstaller
Сборка в папку Extra_Hands (не dist)
"""

import os
import sys
import shutil
import subprocess
import importlib
from pathlib import Path

# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}\n")

def print_step(text):
    print(f"{Colors.BLUE}▶ {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}! {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

# Константы
OUTPUT_DIR = "Extra_Hands"  # Папка для сборки


def check_dependencies():
    """Проверяет установленные зависимости"""
    print_step("Проверка зависимостей...")
    
    packages = {
        'pyinstaller': 'PyInstaller',
        'PyQt5': 'PyQt5',
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'pyautogui': 'pyautogui',
        'keyboard': 'keyboard',
        'pynput': 'pynput',
        'mss': 'mss',
        'pillow': 'PIL',
    }
    
    missing = []
    
    for pip_name, import_name in packages.items():
        try:
            importlib.import_module(import_name)
            print_success(f"{pip_name} ✓")
        except ImportError:
            missing.append(pip_name)
            print_error(f"{pip_name} ✗ (не установлен)")
    
    if missing:
        print_warning(f"\nУстановите недостающие пакеты:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True


def clean_build():
    """Очищает старые сборки"""
    print_step("Очистка старых сборок...")
    
    dirs_to_remove = ['build', 'dist', OUTPUT_DIR, '__pycache__']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_success(f"Удалена папка: {dir_name}")
    
    # Удаляем все .spec файлы кроме нашего
    for f in Path('.').glob('*.spec'):
        if f.name != 'ExtraHands.spec':
            f.unlink()
            print_success(f"Удален файл: {f}")
    
    # Очищаем __pycache__ во всех папках
    for pycache in Path('.').rglob('__pycache__'):
        if pycache.is_dir():
            shutil.rmtree(pycache)
            print_success(f"Удален: {pycache}")


def check_files():
    """Проверяет наличие необходимых файлов"""
    print_step("Проверка файлов проекта...")
    
    required_files = [
        'main.py',
        'components/__init__.py',
        'components/base_bot.py',
        'components/config_manager.py',
        'assets/icons/EHIcon.ico',
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Найден: {file}")
        else:
            missing.append(file)
            print_error(f"Отсутствует: {file}")
    
    if missing:
        print_error(f"\nОтсутствуют {len(missing)} файлов!")
        return False
    
    # Проверяем наличие всех ботов (опционально)
    bots = ['antiafk.py', 'builder.py', 'cooking.py', 'farm_cows.py', 
            'gym.py', 'lucky_wheel.py', 'mining.py', 'port.py', 
            'seamstress.py', 'turner.py', 'catch_pda.py']
    
    for bot in bots:
        if os.path.exists(bot):
            print_success(f"Найден: {bot}")
        else:
            print_warning(f"Не найден: {bot} (опционально)")
    
    return True


def build_exe():
    """Сборка exe файла напрямую в папку Extra_Hands"""
    print_step("Сборка исполняемого файла...")
    
    # Создаём папку для сборки если её нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Формируем команду PyInstaller
    # --distpath указывает корневую папку для сборки
    # Но PyInstaller всё равно создаёт подпапку с именем программы
    # Поэтому после сборки переместим файл
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--icon=assets/icons/EHIcon.ico',
        f'--distpath={OUTPUT_DIR}',
        '--workpath=build',
        '--specpath=.',
        '--add-data=assets;assets',
        '--add-data=components;components',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=components.functions',
        '--hidden-import=components.gym_logic',
        '--hidden-import=components.image_processor',
        '--hidden-import=components.base_bot',
        '--hidden-import=components.config_manager',
        '--hidden-import=components.ui_components',
        '--hidden-import=components.styles',
        '--hidden-import=components.colors',
        '--hidden-import=components.coordinates',
        '--hidden-import=components.constants',
        '--hidden-import=components.key_codes',
        '--clean',
        '--noconfirm',
        '--name=Extra Hands',
        'main.py'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print_success("Сборка завершена успешно!")
            
            # PyInstaller создал папку с именем программы внутри OUTPUT_DIR
            # Перемещаем exe наверх
            exe_subfolder = os.path.join(OUTPUT_DIR, 'Extra Hands')
            exe_file = os.path.join(exe_subfolder, 'Extra Hands.exe')
            target_exe = os.path.join(OUTPUT_DIR, 'Extra Hands.exe')
            
            if os.path.exists(exe_file):
                shutil.move(exe_file, target_exe)
                # Удаляем пустую подпапку
                try:
                    os.rmdir(exe_subfolder)
                except OSError:
                    pass  # Папка могла быть не пустой
                print_success(f"Файл перемещён в: {target_exe}")
            
            return True
        else:
            print_error(f"Ошибка сборки! Код: {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Ошибка при выполнении PyInstaller: {e}")
        return False


def copy_assets():
    """Копирует папку assets в директорию сборки"""
    print_step("Копирование папки assets...")
    
    assets_src = Path("assets")
    assets_dst = Path(OUTPUT_DIR) / "assets"
    
    if not assets_src.exists():
        print_error(f"Папка assets не найдена: {assets_src}")
        return False
    
    # Удаляем старую папку assets, если есть
    if assets_dst.exists():
        shutil.rmtree(assets_dst)
        print_success(f"Удалена старая папка: {assets_dst}")
    
    try:
        shutil.copytree(assets_src, assets_dst)
        print_success(f"Скопирована папка: {assets_src} -> {assets_dst}")
        return True
    except Exception as e:
        print_error(f"Ошибка копирования assets: {e}")
        return False

def create_readme():
    """Создаёт README файл в папке сборки"""
    print_step("Создание README.txt...")
    
    readme_content = """========================================
                Extra Hands
========================================

✨ БОТ ГОТОВ К РАБОТЕ! ✨

Для запуска:
1. Запустите "Extra Hands.exe"
2. При первом запуске может потребоваться разрешение антивируса

⚠️ ВАЖНО:
- Для работы F7/F8 вне окна программы запустите от имени администратора
- Если не работают боты с изображениями - проверьте папку assets

📁 Структура:
- Extra Hands.exe - основной файл программы
- assets/ - папка с изображениями для ботов (НЕ УДАЛЯТЬ!)
- settings.json - файл настроек

💡 Поддерживаемые разрешения:
- FullHD (1920x1080)
- QuadHD (2560x1440)

https://www.blast.hk/members/572838/
"""
    
    readme_path = Path(OUTPUT_DIR) / "README.txt"
    
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print_success(f"Создан: {readme_path}")
    except Exception as e:
        print_warning(f"Не удалось создать README: {e}")


def create_portable_archive():
    """Создаёт ZIP архив для распространения"""
    print_step("Создание ZIP архива...")
    
    import zipfile
    
    if not os.path.exists(OUTPUT_DIR):
        print_error(f"Папка {OUTPUT_DIR} не найдена!")
        return False
    
    zip_name = f'{OUTPUT_DIR}_Portable.zip'
    
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(OUTPUT_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(OUTPUT_DIR))
                    zipf.write(file_path, arcname)
                    print(f"  Добавлен: {arcname}")
        
        print_success(f"Создан архив: {zip_name}")
        return True
    except Exception as e:
        print_error(f"Ошибка создания архива: {e}")
        return False


def main():
    """Основная функция сборки"""
    print_header("EXTRA HANDS - СБОРКА ПРОЕКТА")
    print(f"Целевая папка: {OUTPUT_DIR}")
    
    # 1. Проверка зависимостей
    if not check_dependencies():
        print_error("Установите недостающие зависимости и повторите попытку")
        sys.exit(1)
    
    # 2. Очистка
    response = input(f"\n{Colors.YELLOW}Очистить старые сборки? (y/N): {Colors.END}")
    if response.lower() == 'y':
        clean_build()
    
    # 3. Проверка файлов
    if not check_files():
        response = input(f"\n{Colors.YELLOW}Продолжить сборку? (y/N): {Colors.END}")
        if response.lower() != 'y':
            sys.exit(1)
    
    # 4. Сборка exe
    print()
    if not build_exe():
        sys.exit(1)
    
    # 5. Копирование assets
    copy_assets()
    
    # 6. Создание README
    create_readme()
    
    # 7. Создание архива (опционально)
    print()
    response = input(f"{Colors.YELLOW}Создать ZIP архив для распространения? (y/N): {Colors.END}")
    if response.lower() == 'y':
        create_portable_archive()
    
    # Финальный вывод
    print_header("СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
    
    # Поиск готового файла
    exe_path = os.path.join(OUTPUT_DIR, 'Extra Hands.exe')
    
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n{Colors.GREEN}Готовый файл: {exe_path}{Colors.END}")
        print(f"{Colors.GREEN}Размер: {size_mb:.1f} MB{Colors.END}")
    else:
        # Альтернативный поиск
        alt_path = os.path.join(OUTPUT_DIR, 'Extra Hands', 'Extra Hands.exe')
        if os.path.exists(alt_path):
            size_mb = os.path.getsize(alt_path) / 1024 / 1024
            print(f"\n{Colors.GREEN}Готовый файл: {alt_path}{Colors.END}")
            print(f"{Colors.GREEN}Размер: {size_mb:.1f} MB{Colors.END}")
    
    print(f"\n{Colors.BOLD}Структура папки {OUTPUT_DIR}:{Colors.END}")
    print(f"  📁 {OUTPUT_DIR}/")
    print(f"    📄 Extra Hands.exe")
    print(f"    📁 assets/")
    # print(f"    📄 settings.json (если был)")
    print(f"    📄 README.txt")


if __name__ == '__main__':
    main()