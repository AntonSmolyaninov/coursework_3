"""
Модуль конфигурации приложения.

Содержит настройки подключения к БД и список компаний для парсинга.
"""

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


@dataclass
class Config:
    """
    Класс конфигурации приложения.

    Attributes:
        host: Хост PostgreSQL
        port: Порт PostgreSQL
        user: Имя пользователя
        password: Пароль
        database: Название базы данных
    """

    host: str = os.getenv("PG_HOST", "localhost")
    port: str = os.getenv("PG_PORT", "5432")
    user: str = os.getenv("PG_USER", "postgres")
    password: str = os.getenv("PG_PASSWORD", "")
    database: str = os.getenv("PG_DATABASE", "hh_vacancies")

    def get_db_params(self) -> dict:
        """
        Получить параметры подключения к БД.

        Returns:
            Словарь с параметрами подключения
        """
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.database,
        }

    def get_base_params(self) -> dict:
        """
        Получить базовые параметры (без имени БД).

        Returns:
            Словарь с параметрами для создания БД
        """
        return {"host": self.host, "port": self.port, "user": self.user, "password": self.password}


# Список ID компаний для парсинга (10 интересных IT-компаний)
EMPLOYER_IDS: List[str] = [
    "4029257",  # РУСАЛ
    "1122462",  # Skyeng
    "3529",  # Сбербанк
    "78638",  # Тинькофф
    "15478",  # VK
    "2180",  # Ozon
    "84585",  # Авито
    "97839",  # Полюс
    "174",  # Полиметалл
    "3388",  # Газпромбанк
]


def format_salary(salary_from: int | None, salary_to: int | None) -> str:
    """
    Форматировать зарплату для отображения.

    Args:
        salary_from: Минимальная зарплата
        salary_to: Максимальная зарплата

    Returns:
        Отформатированная строка с зарплатой
    """
    if salary_from and salary_to:
        return f"{salary_from:,} - {salary_to:,} руб.".replace(",", " ")
    elif salary_from:
        return f"от {salary_from:,} руб.".replace(",", " ")
    elif salary_to:
        return f"до {salary_to:,} руб.".replace(",", " ")
    return "не указана"
