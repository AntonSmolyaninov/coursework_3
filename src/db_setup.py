"""
Модуль для работы с базой данных PostgreSQL.

Содержит функции для создания БД, таблиц и вставки данных.
"""

from typing import Dict, List

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, connection


def create_database(db_name: str, params: Dict[str, str]) -> None:
    """
    Создать базу данных, если она не существует.

    Args:
        db_name: Название базы данных
        params: Параметры подключения (host, port, user, password)
    """
    conn = psycopg2.connect(
        host=params["host"], port=params["port"], user=params["user"], password=params["password"], dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            # Проверяем существование БД
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))

            if not cur.fetchone():
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"  ✓ База данных '{db_name}' создана")
            else:
                print(f"  ✓ База данных '{db_name}' уже существует")
    finally:
        conn.close()


def drop_tables(conn: connection) -> None:
    """
    Удалить существующие таблицы.

    Args:
        conn: Соединение с базой данных
    """
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS vacancy CASCADE")
        cur.execute("DROP TABLE IF EXISTS employer CASCADE")
    conn.commit()
    print("  ✓ Старые таблицы удалены")


def create_tables(conn: connection) -> None:
    """
    Создать таблицы employer и vacancy.

    Args:
        conn: Соединение с базой данных
    """
    with conn.cursor() as cur:
        # Таблица работодателей
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employer (
                employer_id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url VARCHAR(255),
                alternate_url VARCHAR(255),
                vacancies_url VARCHAR(255),
                open_vacancies INTEGER DEFAULT 0,
                description TEXT,
                area VARCHAR(100)
            )
        """
        )

        # Таблица вакансий с внешним ключом на employer
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vacancy (
                vacancy_id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                employer_id INTEGER NOT NULL REFERENCES employer(employer_id) ON DELETE CASCADE,
                salary_from INTEGER,
                salary_to INTEGER,
                salary_currency VARCHAR(10),
                url VARCHAR(255),
                requirement TEXT,
                responsibility TEXT,
                experience VARCHAR(100),
                employment VARCHAR(100),
                schedule VARCHAR(100),
                area VARCHAR(100),
                published_at TIMESTAMP
            )
        """
        )

        # Индексы для ускорения поиска
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_vacancy_employer
            ON vacancy(employer_id)
        """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_vacancy_salary
            ON vacancy(salary_from, salary_to)
        """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_vacancy_name
            ON vacancy(name)
        """
        )

    conn.commit()
    print("  ✓ Таблицы созданы")


def insert_employer(conn: connection, employer: Dict) -> None:
    """
    Вставить данные о работодателе.

    Args:
        conn: Соединение с базой данных
        employer: Словарь с данными о работодателе
    """
    area = employer.get("area", {})
    area_name = area.get("name") if area else None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO employer (
                employer_id, name, url, alternate_url,
                vacancies_url, open_vacancies, description, area
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (employer_id) DO UPDATE SET
                name = EXCLUDED.name,
                open_vacancies = EXCLUDED.open_vacancies,
                description = EXCLUDED.description
        """,
            (
                employer.get("id"),
                employer.get("name"),
                employer.get("url"),
                employer.get("alternate_url"),
                employer.get("vacancies_url"),
                employer.get("open_vacancies", 0),
                employer.get("description"),
                area_name,
            ),
        )
    conn.commit()


def insert_vacancy(conn: connection, vacancy: Dict, employer_id: int) -> None:
    """
    Вставить данные о вакансии.

    Args:
        conn: Соединение с базой данных
        vacancy: Словарь с данными о вакансии
        employer_id: ID работодателя
    """
    salary = vacancy.get("salary") or {}
    snippet = vacancy.get("snippet") or {}
    experience = vacancy.get("experience") or {}
    employment = vacancy.get("employment") or {}
    schedule = vacancy.get("schedule") or {}
    area = vacancy.get("area") or {}

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vacancy (
                vacancy_id, name, employer_id, salary_from, salary_to,
                salary_currency, url, requirement, responsibility,
                experience, employment, schedule, area, published_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vacancy_id) DO UPDATE SET
                name = EXCLUDED.name,
                salary_from = EXCLUDED.salary_from,
                salary_to = EXCLUDED.salary_to
        """,
            (
                vacancy.get("id"),
                vacancy.get("name"),
                employer_id,
                salary.get("from"),
                salary.get("to"),
                salary.get("currency"),
                vacancy.get("alternate_url"),
                snippet.get("requirement"),
                snippet.get("responsibility"),
                experience.get("name"),
                employment.get("name"),
                schedule.get("name"),
                area.get("name"),
                vacancy.get("published_at"),
            ),
        )
    conn.commit()


def insert_employers(conn: connection, employers: List[Dict]) -> int:
    """
    Вставить список работодателей в БД.

    Args:
        conn: Соединение с базой данных
        employers: Список словарей с данными

    Returns:
        Количество добавленных записей
    """
    for employer in employers:
        insert_employer(conn, employer)

    print(f"  ✓ Добавлено компаний: {len(employers)}")
    return len(employers)


def insert_vacancies(conn: connection, vacancies_dict: Dict[int, List[Dict]]) -> int:
    """
    Вставить вакансии всех работодателей.

    Args:
        conn: Соединение с базой данных
        vacancies_dict: Словарь {employer_id: [вакансии]}

    Returns:
        Общее количество добавленных вакансий
    """
    total = 0

    for employer_id, vacancies in vacancies_dict.items():
        for vacancy in vacancies:
            insert_vacancy(conn, vacancy, employer_id)
        total += len(vacancies)

    print(f"  ✓ Добавлено вакансий: {total}")
    return total
