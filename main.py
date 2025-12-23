"""
Главный модуль проекта - точка входа.

Проект для получения данных о компаниях и вакансиях с hh.ru
и сохранения их в базу данных PostgreSQL.

Запуск:
    poetry run python main.py
"""

import psycopg2
from psycopg2 import OperationalError

from src.api import HHApi
from src.config import EMPLOYER_IDS, Config
from src.db_manager import DBManager
from src.db_setup import create_database, create_tables, drop_tables, insert_employers, insert_vacancies
from src.utils import (print_header, print_separator, search_vacancies, show_all_vacancies, show_avg_salary,
                       show_companies_and_vacancies, show_menu, show_statistics, show_vacancies_higher_salary)


def load_data_from_hh(config: Config) -> None:
    """
    Загрузить данные с hh.ru в базу данных.

    Args:
        config: Объект конфигурации
    """
    print_header("ЗАГРУЗКА ДАННЫХ С HH.RU")

    # Создаём базу данных
    print("\n Создание базы данных...")
    create_database(config.database, config.get_base_params())

    # Подключаемся к созданной БД
    conn = psycopg2.connect(**config.get_db_params())

    try:
        # Пересоздаём таблицы
        print("\n Создание таблиц...")
        drop_tables(conn)
        create_tables(conn)

        # Инициализируем API
        api = HHApi()

        # Получаем данные о компаниях
        print("\n Загрузка информации о компаниях...")
        employers = api.get_employers(EMPLOYER_IDS)

        if not employers:
            print("Не удалось загрузить данные о компаниях")
            return

        # Получаем вакансии
        print("\n Загрузка вакансий...")
        vacancies = api.get_all_vacancies(EMPLOYER_IDS)

        # Сохраняем в БД
        print("\n Сохранение данных в БД...")
        insert_employers(conn, employers)
        insert_vacancies(conn, vacancies)

        print("\n" + "═" * 60)
        print(" ДАННЫЕ УСПЕШНО ЗАГРУЖЕНЫ!")
        print("═" * 60)

    except Exception as e:
        print(f"\n Ошибка при загрузке данных: {e}")
        raise
    finally:
        conn.close()


def create_db_manager(config: Config) -> DBManager:
    """
    Создать экземпляр DBManager.

    Args:
        config: Объект конфигурации

    Returns:
        Экземпляр DBManager
    """
    return DBManager(
        host=config.host, port=config.port, database=config.database, user=config.user, password=config.password
    )


def check_database_exists(config: Config) -> bool:
    """
    Проверить, существует ли база данных и содержит ли она данные.

    Args:
        config: Объект конфигурации

    Returns:
        True если БД существует и содержит данные
    """
    try:
        manager = create_db_manager(config)
        count = manager.get_total_employers_count()
        return count > 0
    except OperationalError:
        return False
    except Exception:
        return False


def main() -> None:
    """Главная функция программы."""
    print()
    print("═" * 60)
    print("       Курсовой проект по работе с БД")
    print("═" * 60)

    # Загружаем конфигурацию
    config = Config()

    # Проверяем наличие данных в БД
    if not check_database_exists(config):
        print("\n База данных пуста или не существует.")
        print(" Начинаем загрузку данных с hh.ru...")
        load_data_from_hh(config)
    else:
        print("\n Подключение к базе данных установлено")

    # Создаём менеджер БД
    manager = create_db_manager(config)

    # Главный цикл программы
    while True:
        choice = show_menu()

        if choice == "1":
            show_companies_and_vacancies(manager)

        elif choice == "2":
            show_all_vacancies(manager)

        elif choice == "3":
            show_avg_salary(manager)

        elif choice == "4":
            show_vacancies_higher_salary(manager)

        elif choice == "5":
            search_vacancies(manager)

        elif choice == "6":
            show_statistics(manager)

        elif choice == "7":
            confirm = input("\n  Перезагрузить все данные? (да/нет): ").strip().lower()
            if confirm in ("да", "yes", "y", "д"):
                load_data_from_hh(config)
                manager = create_db_manager(config)

        elif choice == "0":
            print()
            print_separator("═")
            print(" Спасибо за использование! До свидания!")
            print_separator("═")
            print()
            break

        else:
            print("\n Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
