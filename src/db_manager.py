"""
Модуль с классом DBManager для работы с данными в PostgreSQL.

Предоставляет методы для анализа данных о компаниях и вакансиях.
"""

from typing import Any, List, Optional, Tuple

import psycopg2
from psycopg2.extensions import connection


class DBManager:
    """
    Класс для управления данными в базе PostgreSQL.

    Предоставляет методы для получения статистики и поиска
    информации о компаниях и вакансиях.

    Attributes:
        conn_params: Параметры подключения к БД
    """

    def __init__(self, host: str, port: str, database: str, user: str, password: str) -> None:
        """
        Инициализация DBManager.

        Args:
            host: Хост базы данных
            port: Порт базы данных
            database: Название базы данных
            user: Имя пользователя
            password: Пароль
        """
        self._conn_params = {"host": host, "port": port, "dbname": database, "user": user, "password": password}

    def _get_connection(self) -> connection:
        """
        Создать соединение с базой данных.

        Returns:
            Объект соединения psycopg2
        """
        return psycopg2.connect(**self._conn_params)

    def execute_query(self, query: str, params: tuple[Any, ...] | None = None):
        """
        Выполнить SQL-запрос и вернуть результат.

        Args:
            query: SQL-запрос
            params: Параметры запроса

        Returns:
            Список кортежей с результатами
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def _execute_scalar(self, query: str, params: tuple = None) -> Any:
        """ Выполнить запрос и вернуть одно значение. """
        result = self._execute_query(query, params)
        return result[0][0] if result else None

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получить список всех компаний и количество вакансий у каждой.

        Использует LEFT JOIN для включения компаний без вакансий.

        Returns:
            Список кортежей (название_компании, количество_вакансий)
        """
        query = """
            SELECT
                e.name AS company_name,
                COUNT(v.vacancy_id) AS vacancies_count
            FROM employer e
            LEFT JOIN vacancy v ON e.employer_id = v.employer_id
            GROUP BY e.employer_id, e.name
            ORDER BY vacancies_count DESC, e.name
        """
        return self._execute_query(query)

    def get_all_vacancies(self) -> List[Tuple[str, str, Optional[int], Optional[int], str]]:
        """
        Получить список всех вакансий с информацией о компании.

        Returns:
            Список кортежей (компания, вакансия, зарплата_от, зарплата_до, url)
        """
        query = """
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.url
            FROM vacancy v
            JOIN employer e ON v.employer_id = e.employer_id
            ORDER BY
                COALESCE(v.salary_from, v.salary_to, 0) DESC,
                e.name,
                v.name
        """
        return self._execute_query(query)

    def get_avg_salary(self) -> Optional[float]:
        """
        Получить среднюю зарплату по всем вакансиям.

        Учитывает salary_from и salary_to, вычисляя среднее значение.

        Returns:
            Средняя зарплата или None, если данных нет
        """
        query = """
            SELECT AVG(
                CASE
                    WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
                        THEN (salary_from + salary_to) / 2.0
                    WHEN salary_from IS NOT NULL
                        THEN salary_from
                    WHEN salary_to IS NOT NULL
                        THEN salary_to
                END
            )::NUMERIC(12, 2) AS avg_salary
            FROM vacancy
            WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
        """
        return self._execute_scalar(query)

    def get_vacancies_with_higher_salary(self) -> List[Tuple[str, str, int, int, str]]:
        """
        Получить вакансии с зарплатой выше средней.

        Использует подзапрос с CTE для расчёта средней зарплаты
        и фильтрует вакансии через WHERE.

        Returns:
            Список вакансий с зарплатой выше средней
        """
        query = """
            WITH avg_salary AS (
                SELECT AVG(
                    CASE
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
                            THEN (salary_from + salary_to) / 2.0
                        WHEN salary_from IS NOT NULL
                            THEN salary_from
                        WHEN salary_to IS NOT NULL
                            THEN salary_to
                    END
                ) AS avg_sal
                FROM vacancy
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            )
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.url
            FROM vacancy v
            JOIN employer e ON v.employer_id = e.employer_id
            CROSS JOIN avg_salary
            WHERE (
                CASE
                    WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL
                        THEN (v.salary_from + v.salary_to) / 2.0
                    WHEN v.salary_from IS NOT NULL
                        THEN v.salary_from
                    WHEN v.salary_to IS NOT NULL
                        THEN v.salary_to
                END
            ) > avg_salary.avg_sal
            ORDER BY
                COALESCE(v.salary_from, v.salary_to, 0) DESC
        """
        return self._execute_query(query)

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, int, int, str]]:
        """
        Получить вакансии, содержащие ключевое слово в названии.

        Использует оператор ILIKE для регистронезависимого поиска.

        Args:
            keyword: Ключевое слово для поиска

        Returns:
            Список вакансий, содержащих ключевое слово
        """
        query = """
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.url
            FROM vacancy v
            JOIN employer e ON v.employer_id = e.employer_id
            WHERE v.name ILIKE %s
            ORDER BY
                COALESCE(v.salary_from, v.salary_to, 0) DESC,
                e.name
        """
        return self._execute_query(query, (f"%{keyword}%",))

    def get_total_vacancies_count(self) -> int:
        """
        Получить общее количество вакансий в БД.

        Returns:
            Количество вакансий
        """
        query = "SELECT COUNT(*) FROM vacancy"
        return self._execute_scalar(query) or 0

    def get_total_employers_count(self) -> int:
        """
        Получить общее количество компаний в БД.

        Returns:
            Количество компаний
        """
        query = "SELECT COUNT(*) FROM employer"
        return self._execute_scalar(query) or 0
