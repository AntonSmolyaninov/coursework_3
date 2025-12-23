"""
Модуль пользовательского интерфейса.

Содержит функции для взаимодействия с пользователем через консоль.
"""

from src.config import format_salary
from src.db_manager import DBManager


def print_separator(char: str = "─", length: int = 60) -> None:
    """Вывести разделитель."""
    print(char * length)


def print_header(title: str) -> None:
    """
    Вывести заголовок раздела.

    Args:
        title: Текст заголовка
    """
    print()
    print_separator("═")
    print(f"  {title}")
    print_separator("═")


def show_menu() -> str:
    """
    Показать главное меню и получить выбор пользователя.

    Returns:
        Выбор пользователя (строка)
    """
    print()
    print_separator()
    print("ГЛАВНОЕ МЕНЮ")
    print_separator()
    print("  1. Список компаний и количество вакансий")
    print("  2. Все вакансии")
    print("  3. Средняя зарплата")
    print("  4. Вакансии с зарплатой выше средней")
    print("  5. Поиск вакансий по ключевому слову")
    print("  6. Статистика базы данных")
    print("  7. Перезагрузить данные с hh.ru")
    print("  0. Выход")
    print_separator()

    return input("Выберите пункт меню: ").strip()


def show_companies_and_vacancies(manager: DBManager) -> None:
    """
    Показать список компаний и количество вакансий.

    Args:
        manager: Экземпляр DBManager
    """
    print_header("КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ")

    data = manager.get_companies_and_vacancies_count()

    if not data:
        print("Данные не найдены.")
        return

    print(f"{'№':<4} {'Компания':<40} {'Вакансий':>10}")
    print_separator()

    total_vacancies = 0
    for i, (company, count) in enumerate(data, 1):
        print(f"{i:<4} {company:<40} {count:>10}")
        total_vacancies += count

    print_separator()
    print(f"Всего компаний: {len(data)}")
    print(f"Всего вакансий: {total_vacancies}")


def show_all_vacancies(manager: DBManager, limit: int = 20) -> None:
    """
    Показать все вакансии.

    Args:
        manager: Экземпляр DBManager
        limit: Максимальное количество для отображения
    """
    print_header("ВСЕ ВАКАНСИИ")

    data = manager.get_all_vacancies()

    if not data:
        print("Вакансии не найдены.")
        return

    print(f"  Найдено вакансий: {len(data)}\n")

    for i, (company, vacancy, sal_from, sal_to, url) in enumerate(data[:limit], 1):
        salary = format_salary(sal_from, sal_to)
        print(f"{i}. {vacancy}")
        print(f"{company}")
        print(f"{salary}")
        print(f"{url}")
        print()

    if len(data) > limit:
        print(f"  ... и ещё {len(data) - limit} вакансий")


def show_avg_salary(manager: DBManager) -> None:
    """
    Показать среднюю зарплату.

    Args:
        manager: Экземпляр DBManager
    """
    print_header("СРЕДНЯЯ ЗАРПЛАТА")

    avg = manager.get_avg_salary()

    if avg:
        formatted = f"{float(avg):,.0f}".replace(",", " ")
        print(f"Средняя зарплата по всем вакансиям: {formatted} руб.")
    else:
        print("Не удалось рассчитать среднюю зарплату.")
        print("Возможно, нет вакансий с указанной зарплатой.")


def show_vacancies_higher_salary(manager: DBManager, limit: int = 15) -> None:
    """
    Показать вакансии с зарплатой выше средней.

    Args:
        manager: Экземпляр DBManager
        limit: Максимальное количество для отображения
    """
    print_header("ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ")

    avg = manager.get_avg_salary()
    if avg:
        formatted = f"{float(avg):,.0f}".replace(",", " ")
        print(f"  (Средняя зарплата: {formatted} руб.)\n")

    data = manager.get_vacancies_with_higher_salary()

    if not data:
        print("  Вакансии не найдены.")
        return

    print(f"  Найдено вакансий: {len(data)}\n")

    for i, (company, vacancy, sal_from, sal_to, url) in enumerate(data[:limit], 1):
        salary = format_salary(sal_from, sal_to)
        print(f"  {i}. {vacancy}")
        print(f"{company}")
        print(f"{salary}")
        print()

    if len(data) > limit:
        print(f"  ... и ещё {len(data) - limit} вакансий")


def search_vacancies(manager: DBManager, limit: int = 15) -> None:
    """
    Поиск вакансий по ключевому слову.

    Args:
        manager: Экземпляр DBManager
        limit: Максимальное количество для отображения
    """
    print_header("ПОИСК ВАКАНСИЙ")

    keyword = input("Введите ключевое слово (например, Python): ").strip()

    if not keyword:
        print("Ключевое слово не введено.")
        return

    data = manager.get_vacancies_with_keyword(keyword)

    if not data:
        print(f"Вакансии со словом '{keyword}' не найдены.")
        return

    print(f"\n  Найдено вакансий: {len(data)}\n")

    for i, (company, vacancy, sal_from, sal_to, url) in enumerate(data[:limit], 1):
        salary = format_salary(sal_from, sal_to)
        print(f"  {i}. {vacancy}")
        print(f"{company}")
        print(f"{salary}")
        print(f"{url}")
        print()

    if len(data) > limit:
        print(f"  ... и ещё {len(data) - limit} вакансий")


def show_statistics(manager: DBManager) -> None:
    """
    Показать статистику базы данных.

    Args:
        manager: Экземпляр DBManager
    """
    print_header("СТАТИСТИКА БАЗЫ ДАННЫХ")

    employers = manager.get_total_employers_count()
    vacancies = manager.get_total_vacancies_count()
    avg_salary = manager.get_avg_salary()

    print(f" Всего компаний в БД:  {employers}")
    print(f" Всего вакансий в БД:  {vacancies}")

    if avg_salary:
        formatted = f"{float(avg_salary):,.0f}".replace(",", " ")
        print(f" Средняя зарплата:     {formatted} руб.")

    if employers > 0:
        avg_per_company = vacancies / employers
        print(f" Вакансий на компанию: {avg_per_company:.1f}")
