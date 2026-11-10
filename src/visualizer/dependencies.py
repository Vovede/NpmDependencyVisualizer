import requests
import json

from urllib.parse import quote
from pathlib import Path
from semantic_version import Version, NpmSpec


class DependencyError(Exception):
    """Ошибка при получении зависимостей npm-пакета."""


def fetch_package_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as error:
        raise DependencyError(
            f"Не удалось получить информацию о пакете: {error}"
        ) from error

    except ValueError as error:
        raise DependencyError(
            "Сервер вернул некорректный JSON."
        ) from error


def select_version(package_data, package_name, version):
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

    selected_version = str(max(matching_versions))
    return versions[selected_version]


def validate_dependencies(package_data):
    dependencies = package_data.get("dependencies", {})

    if not isinstance(dependencies, dict):
        raise DependencyError(
            "Некорректный формат списка зависимостей."
        )

    return dependencies


def get_direct_dependencies(package_name, version, repository):
    """
    Получает прямые зависимости npm-пакета.
    Поддерживает точные версии и диапазоны версий.
    """
    package = quote(package_name, safe="@")

    try:
        Version(version)
        exact_version = True
    except ValueError:
        exact_version = False

    if exact_version:
        url = (
            f"{repository.rstrip('/')}/"
            f"{package}/{quote(version, safe='')}"
        )
        package_data = fetch_package_data(url)

    else:
        url = f"{repository.rstrip('/')}/{package}"
        package_data = fetch_package_data(url)
        package_data = select_version(
            package_data, package_name, version
        )

    return validate_dependencies(package_data)


def load_test_repository(repository):
    repository_path = Path(repository)

    if not repository_path.is_file():
        raise DependencyError(
            f"Тестовый репозиторий не найден: {repository}"
        )

    try:
        with repository_path.open(
            "r", encoding="utf-8"
        ) as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        raise DependencyError(
            f"Не удалось прочитать тестовый репозиторий: {error}"
        ) from error


def get_test_dependencies(package_name, version, repository):
    """
    Получает зависимости пакета из локального тестового репозитория.
    """
    repository_data = load_test_repository(repository)

    if package_name not in repository_data:
        raise DependencyError(
            f"Пакет {package_name} отсутствует "
            "в тестовом репозитории."
        )

    package_data = repository_data[package_name]

    if not isinstance(package_data, dict):
        raise DependencyError("Некорректное описание пакета.")

    if package_data.get("version") != version:
        raise DependencyError(
            f"Версия пакета {package_name} не найдена: {version}"
        )

    return validate_dependencies(package_data)


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
            package_name, version, repository
        )

    return get_direct_dependencies(
        package_name, version, repository
    )
