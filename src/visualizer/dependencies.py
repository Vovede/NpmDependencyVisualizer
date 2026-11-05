import requests
from urllib.parse import quote


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