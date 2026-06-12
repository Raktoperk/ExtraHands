"""
Бот для автоматизации Колеса удачи
"""

import sys
import time
from typing import Optional

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt

from components.base_bot import BaseBotApp, BaseWorker
from components.coordinates import lucky_wheel_coordinate
from components.functions import click_coordinates, press_key
from components.config_manager import config
from components.styles import FRAME_STYLES, BUTTON_STYLES, LABEL_STYLES, INPUT_STYLES


class LuckyWheelWorker(BaseWorker):
    """Рабочий поток для колеса удачи"""
    
    # Константа: 4 часа 10 минут в секундах
    CYCLE_WAIT_SECONDS = 15000  # 4 часа 10 минут
    
    def __init__(self, resolution_mode: str, initial_delay_minutes: float = 0):
        super().__init__()
        self._resolution_mode = resolution_mode
        self._initial_delay_seconds = initial_delay_minutes * 60 + 10  # +1 минута
        self._cycle_count = 0
    
    def run(self) -> None:
        """Основной метод потока"""
        
        self.log_message.emit(f"Настройки: начальная задержка={self._initial_delay_seconds} сек, цикл={self.CYCLE_WAIT_SECONDS} сек")
        
        # ========== НАЧАЛЬНАЯ ЗАДЕРЖКА (только перед первым циклом) ==========
        if self._initial_delay_seconds > 0:
            self.log_message.emit(f"⏰ Начальная задержка перед ПЕРВЫМ запуском: {self._initial_delay_seconds / 60:.1f} минут")
            self.status_updated.emit(f"Ожидание {self._initial_delay_seconds / 60:.1f} мин перед запуском...")
            
            if not self._safe_sleep_interruptible(self._initial_delay_seconds):
                self.log_message.emit("Начальная задержка прервана пользователем")
                return
            
            self.log_message.emit("✅ Начальная задержка завершена, приступаю к работе")
        
        if not self.is_running:
            return
        
        coords = lucky_wheel_coordinate.get(self._resolution_mode)
        if not coords:
            self.log_message.emit(f"ОШИБКА: Нет координат для разрешения {self._resolution_mode}")
            return
        
        # ========== ОСНОВНОЙ ЦИКЛ ==========
        while self.is_running:
            self._cycle_count += 1
            self.log_message.emit(f"🔄 Запуск цикла #{self._cycle_count}")
            
            # Нажатие F10 для открытия меню
            self.log_message.emit("Нажимаю F10")
            press_key('f10')
            
            if not self._safe_sleep_interruptible(2):
                break
            if not self.is_running:
                break
            
            # Клик по магазину
            click_coordinates(coords["shop"])
            if not self._safe_sleep_interruptible(2):
                break
            if not self.is_running:
                break
            
            # Клик по колесу удачи
            click_coordinates(coords["luckywheel"])
            if not self._safe_sleep_interruptible(2):
                break
            if not self.is_running:
                break
            
            # Клик по Spin
            click_coordinates(coords["spin"])
            if not self._safe_sleep_interruptible(15):
                break
            if not self.is_running:
                break
            
            # Двойное нажатие ESC для закрытия
            press_key('esc')
            if not self._safe_sleep_interruptible(2):
                break
            
            press_key('esc')
            
            if not self.is_running:
                break
            
            self.log_message.emit(f"✅ Цикл #{self._cycle_count} завершен")
            
            # ========== ОЖИДАНИЕ МЕЖДУ ЦИКЛАМИ ==========
            # Всегда 15000 секунд между циклами
            self.log_message.emit(f"⏰ Ожидание {self.CYCLE_WAIT_SECONDS / 60:.1f} мин (4ч 10м) до следующего цикла...")
            self.status_updated.emit(f"Ожидание {self.CYCLE_WAIT_SECONDS / 60:.1f} мин до след. цикла...")
            
            if not self._safe_sleep_interruptible(self.CYCLE_WAIT_SECONDS):
                self.log_message.emit("Ожидание между циклами прервано пользователем")
                break
        
        self.log_message.emit(f"Поток колеса удачи остановлен. Выполнено циклов: {self._cycle_count}")
        self.status_updated.emit("Остановлен")
    
    def _safe_sleep_interruptible(self, seconds: float, check_interval: float = 0.5) -> bool:
        """
        Прерываемый сон с частой проверкой флага остановки.
        
        Args:
            seconds: Время сна в секундах
            check_interval: Интервал проверки флага остановки (секунды)
        
        Returns:
            True если сон завершился нормально, False если была остановка
        """
        elapsed = 0.0
        while elapsed < seconds and self.is_running:
            sleep_time = min(check_interval, seconds - elapsed)
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))
            elapsed += check_interval
        return self.is_running


class LuckyWheelApp(BaseBotApp):
    """Приложение для автоматизации колеса удачи"""
    
    def __init__(self):
        super().__init__(
            title="Колесо удачи",
            window_width=550,
            window_height=420,
            has_resolution=True,
            has_delay=False,
            has_log=True,
            has_counter=False
        )
        self._hours_entry: Optional[QLineEdit] = None
        self._minutes_entry: Optional[QLineEdit] = None
    
    def _add_custom_settings(self, parent_layout: QVBoxLayout) -> None:
        """Добавляет поля для ввода времени ожидания"""
        # Часы
        hours_frame = QFrame()
        hours_frame.setStyleSheet(FRAME_STYLES["frame"])
        hours_layout = QHBoxLayout(hours_frame)
        hours_layout.setContentsMargins(20, 10, 20, 10)
        
        hours_label = QLabel("Часы (0-4):")
        hours_label.setStyleSheet(LABEL_STYLES["secondary"])
        hours_layout.addWidget(hours_label)
        
        self._hours_entry = QLineEdit("0")
        self._hours_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self._hours_entry.setMaximumWidth(80)
        hours_layout.addWidget(self._hours_entry)
        hours_layout.addStretch()
        parent_layout.addWidget(hours_frame)
        
        # Минуты
        minutes_frame = QFrame()
        minutes_frame.setStyleSheet(FRAME_STYLES["frame"])
        minutes_layout = QHBoxLayout(minutes_frame)
        minutes_layout.setContentsMargins(20, 10, 20, 10)
        
        minutes_label = QLabel("Минуты (0-59):")
        minutes_label.setStyleSheet(LABEL_STYLES["secondary"])
        minutes_layout.addWidget(minutes_label)
        
        self._minutes_entry = QLineEdit("0")
        self._minutes_entry.setStyleSheet(INPUT_STYLES["line_edit"])
        self._minutes_entry.setMaximumWidth(80)
        minutes_layout.addWidget(self._minutes_entry)
        minutes_layout.addStretch()
        parent_layout.addWidget(minutes_frame)
    
    def _get_delay_minutes(self) -> float:
        """Получает задержку в минутах из полей ввода"""
        try:
            hours = int(self._hours_entry.text()) if self._hours_entry else 0
            minutes = float(self._minutes_entry.text()) if self._minutes_entry else 0
            
            if hours < 0 or hours > 4:
                return 0
            if minutes < 0 or minutes > 59:
                return 0
            
            return hours * 60 + minutes
        except ValueError:
            return 0
    
    def _create_worker(self) -> Optional[BaseWorker]:
        delay_minutes = self._get_delay_minutes()
        return LuckyWheelWorker(self._resolution_mode, delay_minutes)
    
    def _start_bot(self) -> None:
        """Запускает бота"""
        delay_minutes = self._get_delay_minutes()
        
        self._worker = self._create_worker()
        if not self._worker:
            return
        
        super()._start_bot()
        
        self._worker.log_message.connect(self._add_log)
        self._worker.status_updated.connect(self._update_status)
        self._worker.start()
        
        hours = int(self._hours_entry.text()) if self._hours_entry else 0
        minutes = float(self._minutes_entry.text()) if self._minutes_entry else 0
        
        self._add_log("=" * 50)
        self._add_log(f"🚀 БОТ ЗАПУЩЕН")
        self._add_log(f"Разрешение: {self._resolution_mode}")
        if hours > 0 or minutes > 0:
            self._add_log(f"⏰ Начальная задержка: {hours}ч {minutes}мин + 1 минута = {delay_minutes * 60 + 60:.0f} сек")
        else:
            self._add_log(f"⏰ Начальная задержка: 0 (запуск немедленно)")
        self._add_log(f"🔄 Между циклами: 4 часа 10 минут ({LuckyWheelWorker.CYCLE_WAIT_SECONDS} сек)")
        self._add_log("=" * 50)
    
    def _stop_bot(self) -> None:
        """Останавливает бота"""
        self._running = False
        if self._toggle_button:
            self._toggle_button.setText("Запустить")
            self._toggle_button.setStyleSheet(BUTTON_STYLES["primary"])
        
        if self._worker:
            self._worker.stop()
            self._worker.wait(5000)
            if self._worker.isRunning():
                self._add_log("ВНИМАНИЕ: Поток не остановился принудительно")
            self._worker = None
    
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки"""
        self._resolution_mode = config.get("lucky_wheel", "resolution_mode", "FullHD")
        hours = config.get("lucky_wheel", "hours", 0)
        minutes = config.get("lucky_wheel", "minutes", 0)
        
        if self._hours_entry:
            self._hours_entry.setText(str(hours))
        if self._minutes_entry:
            self._minutes_entry.setText(str(minutes))
        
        self._set_resolution(self._resolution_mode)
    
    def _save_settings(self) -> None:
        """Сохраняет текущие настройки"""
        hours = int(self._hours_entry.text()) if self._hours_entry else 0
        minutes = float(self._minutes_entry.text()) if self._minutes_entry else 0
        
        config.set_multiple("lucky_wheel", {
            "resolution_mode": self._resolution_mode,
            "hours": hours,
            "minutes": minutes
        })
    
    def closeEvent(self, event) -> None:
        """Обработчик закрытия окна"""
        self._save_settings()
        if self._running:
            self._stop_bot()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = LuckyWheelApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()