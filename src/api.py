"""
Модуль для работы с публичным API hh.ru.

Предоставляет класс HHApi для получения информации о работодателях и вакансиях.
"""

from time import sleep
from typing import Dict, List, Optional

import requests


class HHApi:
    """
    Класс для взаимодействия с API hh.ru.

    Позволяет получать информацию о работодателях и их вакансиях
    через публичный API HeadHunter.

    Attributes:
        BASE_URL: Базовый URL API hh.ru
        session: Сессия для HTTP-запросов
    """

    BASE_URL: str = "https://api.hh.ru"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            }
        )

    def _make_request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """
        Выполнить GET-запрос к API.

        Args:
            endpoint: Конечная точка API
            params: Параметры запроса

        Returns:
            JSON-ответ или None при ошибке
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP ошибка: {e}")
            return None
        except requests.exceptions.ConnectionError:
            print("Ошибка соединения с сервером")
            return None
        except requests.exceptions.Timeout:
            print("Превышено время ожидания ответа")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None

    def get_employer(self, employer_id: str) -> Optional[Dict]:
        """
        Получить информацию о работодателе по ID.

        Args:
            employer_id: ID работодателя на hh.ru

        Returns:
            Словарь с данными о работодателе или None
        """
        return self._make_request(f"employers/{employer_id}")

    def get_employers(self, employer_ids: List[str]) -> List[Dict]:
        """
        Получить информацию о нескольких работодателях.

        Args:
            employer_ids: Список ID работодателей

        Returns:
            Список словарей с данными о работодателях
        """
        employers = []

        for employer_id in employer_ids:
            print(f"Загрузка компании ID={employer_id}...", end=" ")
            employer = self.get_employer(employer_id)

            if employer:
                employers.append(employer)
                print(f"✓ {employer.get('name', 'Unknown')}")
            else:
                print("✗ Не найдена")

            sleep(0.25)  # Пауза для избежания блокировки

        return employers

    def get_vacancies_by_employer(self, employer_id: str, per_page: int = 100) -> List[Dict]:
        """
        Получить вакансии работодателя.

        Args:
            employer_id: ID работодателя
            per_page: Количество вакансий на странице (макс. 100)

        Returns:
            Список словарей с данными о вакансиях
        """
        all_vacancies = []
        page = 0

        while True:
            params = {"employer_id": employer_id, "per_page": per_page, "page": page, "only_with_salary": False}

            data = self._make_request("vacancies", params)

            if not data:
                break

            vacancies = data.get("items", [])
            if not vacancies:
                break

            all_vacancies.extend(vacancies)

            # Проверяем, есть ли ещё страницы
            pages = data.get("pages", 1)
            if page >= pages - 1:
                break

            page += 1
            sleep(0.25)

        return all_vacancies

    def get_all_vacancies(self, employer_ids: List[str]) -> Dict[str, List[Dict]]:
        """
        Получить все вакансии для списка работодателей.

        Args:
            employer_ids: Список ID работодателей

        Returns:
            Словарь {employer_id: [список вакансий]}
        """
        all_vacancies = {}

        for employer_id in employer_ids:
            print(f"Вакансии компании ID={employer_id}...", end=" ")
            vacancies = self.get_vacancies_by_employer(employer_id)
            all_vacancies[employer_id] = vacancies
            print(f"✓ Загружено: {len(vacancies)}")

        return all_vacancies
