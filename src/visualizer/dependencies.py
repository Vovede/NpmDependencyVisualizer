import requests
import json

from urllib.parse import quote
from pathlib import Path
from semantic_version import Version, NpmSpec


class DependencyError(Exception):
    """Ошибка при получении зависимостей npm-пакета."""


def get_direct_dependencies(package_name, version, repository):
    """
    Получает прямые зависимости npm-пакета.
    Поддерживает точные версии и диапазоны версий.
    """

    package = quote(package_name, safe="@")

    # Проверяем, является ли версия точной
    try:
        exact_version = Version(version)
    except ValueError:
        exact_version = None

    # Если версия точная, запрашиваем конкретную запись
    if exact_version is not None:
        url = (
            f"{repository.rstrip('/')}/"
            f"{package}/{quote(version, safe='')}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            package_data = response.json()

        except requests.exceptions.RequestException as error:
            raise DependencyError(
                f"Не удалось получить информацию о пакете: {error}"
            ) from error

        except ValueError as error:
            raise DependencyError(
                "Сервер вернул некорректный JSON."
            ) from error

    else:
        # Для диапазона получаем метаданные всех версий пакета
        url = f"{repository.rstrip('/')}/{package}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            package_data = response.json()

        except requests.exceptions.RequestException as error:
            raise DependencyError(
                f"Не удалось получить информацию о пакете: {error}"
            ) from error

        except ValueError as error:
            raise DependencyError(
                "Сервер вернул некорректный JSON."
            ) from error

        # Проверяем диапазон версий
        try:
            version_spec = NpmSpec(version)
        except ValueError as error:
            raise DependencyError(
                f"Некорректный диапазон версий: {version}"
            ) from error

        versions = package_data.get("versions", {})

        if not isinstance(versions, dict):
            raise DependencyError(
                "Некорректный формат списка версий пакета."
            )

        # Находим версии, удовлетворяющие диапазону
        matching_versions = []

        for version_string in versions:
            try:
                candidate = Version(version_string)

                if version_spec.match(candidate):
                    matching_versions.append(candidate)

            except ValueError:
                continue

        if not matching_versions:
            raise DependencyError(
                f"Не найдена версия пакета {package_name}, "
                f"удовлетворяющая диапазону {version}."
            )

        # Выбираем наиболее новую подходящую версию
        selected_version = str(max(matching_versions))

        package_data = versions[selected_version]

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