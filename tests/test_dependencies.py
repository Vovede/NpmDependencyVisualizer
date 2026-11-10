import pytest
import requests
from unittest.mock import Mock

from visualizer.dependencies import (get_test_dependencies,
                                     get_direct_dependencies,
                                     DependencyError)


def test_get_direct_dependencies_success(monkeypatch):
    """Проверка успешного получения зависимостей."""

    response = Mock()
    response.json.return_value = {
        "dependencies": {
            "accepts": "~1.3.8",
            "body-parser": "1.20.3"
        }
    }

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: response
    )

    result = get_direct_dependencies(
        "express",
        "4.21.2",
        "https://registry.npmjs.org"
    )

    assert result == {
        "accepts": "~1.3.8",
        "body-parser": "1.20.3"
    }


def test_package_without_dependencies(monkeypatch):
    """Проверка пакета без прямых зависимостей."""

    response = Mock()
    response.json.return_value = {}

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: response
    )

    result = get_direct_dependencies(
        "lodash",
        "4.17.21",
        "https://registry.npmjs.org"
    )

    assert result == {}


def test_http_request_error(monkeypatch):
    """Проверка обработки ошибки HTTP-запроса."""

    def raise_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection failed")

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        raise_error
    )

    with pytest.raises(DependencyError, match="Не удалось получить"):
        get_direct_dependencies(
            "express",
            "4.21.2",
            "https://registry.npmjs.org"
        )


def test_invalid_json(monkeypatch):
    """Проверка обработки некорректного JSON."""

    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: response
    )

    with pytest.raises(DependencyError, match="некорректный JSON"):
        get_direct_dependencies(
            "express",
            "4.21.2",
            "https://registry.npmjs.org"
        )


def test_invalid_dependencies_format(monkeypatch):
    """Проверка некорректного формата списка зависимостей."""

    response = Mock()
    response.json.return_value = {
        "dependencies": ["accepts", "body-parser"]
    }

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: response
    )

    with pytest.raises(DependencyError, match="Некорректный формат"):
        get_direct_dependencies(
            "express",
            "4.21.2",
            "https://registry.npmjs.org"
        )


def test_get_test_dependencies_success(tmp_path):
    repository = tmp_path / "repository.json"

    repository.write_text(
        """
        {
            "A": {
                "version": "1.0",
                "dependencies": {
                    "B": "1.0",
                    "C": "1.0"
                }
            }
        }
        """,
        encoding="utf-8"
    )

    result = get_test_dependencies("A", "1.0", str(repository))

    assert result == {
        "B": "1.0",
        "C": "1.0"
    }


def test_test_repository_package_not_found(tmp_path):
    repository = tmp_path / "repository.json"
    repository.write_text("{}", encoding="utf-8")

    with pytest.raises(DependencyError, match="отсутствует"):
        get_test_dependencies("A", "1.0", str(repository))


def test_test_repository_version_not_found(tmp_path):
    repository = tmp_path / "repository.json"

    repository.write_text(
        """
        {
            "A": {
                "version": "2.0",
                "dependencies": {}
            }
        }
        """,
        encoding="utf-8"
    )

    with pytest.raises(DependencyError, match="Версия пакета"):
        get_test_dependencies("A", "1.0", str(repository))


def test_test_repository_file_not_found(tmp_path):
    repository = tmp_path / "missing.json"

    with pytest.raises(DependencyError, match="не найден"):
        get_test_dependencies("A", "1.0", str(repository))


def test_test_repository_invalid_json(tmp_path):
    repository = tmp_path / "repository.json"
    repository.write_text("{invalid json}", encoding="utf-8")

    with pytest.raises(DependencyError, match="Не удалось прочитать"):
        get_test_dependencies("A", "1.0", str(repository))

from unittest.mock import Mock


def test_get_direct_dependencies_version_range(monkeypatch):
    mock_response = Mock()
    mock_response.json.return_value = {
        "versions": {
            "1.0.0": {"dependencies": {"package-a": "^1.0.0"}},
            "1.5.0": {"dependencies": {"package-b": "^2.0.0"}},
            "2.0.0": {"dependencies": {"package-c": "^3.0.0"}}
        }
    }

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: mock_response
    )

    result = get_direct_dependencies(
        "test-package",
        "^1.0.0",
        "https://registry.npmjs.org"
    )

    assert result == {"package-b": "^2.0.0"}


def test_get_direct_dependencies_no_matching_version(monkeypatch):
    mock_response = Mock()
    mock_response.json.return_value = {
        "versions": {
            "1.0.0": {"dependencies": {}}
        }
    }

    monkeypatch.setattr(
        "visualizer.dependencies.requests.get",
        lambda *args, **kwargs: mock_response
    )

    with pytest.raises(DependencyError):
        get_direct_dependencies(
            "test-package",
            "^2.0.0",
            "https://registry.npmjs.org"
        )