import pytest
import requests
from unittest.mock import Mock

from visualizer.dependencies import (
    get_direct_dependencies,
    DependencyError
)


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