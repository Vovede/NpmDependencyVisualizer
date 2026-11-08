import requests
import json

from urllib.parse import quote
from pathlib import Path


class DependencyError(Exception):
    """Ошибка при получении зависимостей npm-пакета."""


def get_direct_dependencies(package_name, version, repository):
    """
    Получает прямые зависимости npm-пакета указанной версии.
    """

    # Формируем URL запроса
    package = quote(package_name, safe="@")
    package_version = quote(version, safe="")

    url = f"{repository.rstrip('/')}/{package}/{package_version}"

    try:
        response = requests.get(url, timeout=10)

        # Проверяем HTTP-статус ответа
        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        raise DependencyError(
            f"Не удалось получить информацию о пакете: {error}"
        ) from error

    try:
        package_data = response.json()
    except ValueError as error:
        raise DependencyError(
            "Сервер вернул некорректный JSON."
        ) from error

    # Извлекаем прямые зависимости
    dependencies = package_data.get("dependencies", {})

    if not isinstance(dependencies, dict):
        raise DependencyError(
            "Некорректный формат списка зависимостей."
        )

    return dependencies

def get_test_dependencies(package_name, version, repository):
    """
    Получает зависимости пакета из локального тестового репозитория.
    """

    repository_path = Path(repository)

    # Проверяем существование файла
    if not repository_path.is_file():
        raise DependencyError(
            f"Тестовый репозиторий не найден: {repository}"
        )

    try:
        with repository_path.open("r", encoding="utf-8") as file:
            repository_data = json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        raise DependencyError(
            f"Не удалось прочитать тестовый репозиторий: {error}"
        ) from error

    # Проверяем наличие пакета
    if package_name not in repository_data:
        raise DependencyError(
            f"Пакет {package_name} отсутствует в тестовом репозитории."
        )

    package_data = repository_data[package_name]

    if not isinstance(package_data, dict):
        raise DependencyError("Некорректное описание пакета.")

    # Проверяем версию
    if package_data.get("version") != version:
        raise DependencyError(
            f"Версия пакета {package_name} не найдена: {version}"
        )

    dependencies = package_data.get("dependencies", {})

    if not isinstance(dependencies, dict):
        raise DependencyError(
            "Некорректный формат списка зависимостей."
        )

    return dependencies

def get_dependencies(
    package_name,
    version,
    repository,
    test_mode=False
):
    """
    Выбирает источник получения зависимостей.
    """

    if test_mode:
        return get_test_dependencies(
            package_name,
            version,
            repository
        )

    return get_direct_dependencies(
        package_name,
        version,
        repository
    )