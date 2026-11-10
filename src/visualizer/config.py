
import yaml
from pathlib import Path


class ConfigError(Exception):
    """Ошибка конфигурации приложения."""


def load_config(config_path):
    """
    Загружает конфигурацию из YAML-файла.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(
            f"Файл конфигурации не найден: {config_path}"
        )

    if not config_path.is_file():
        raise ConfigError(
            f"Указанный путь не является файлом: {config_path}"
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ConfigError(
            f"Ошибка чтения YAML: {error}"
        ) from error
    except OSError as error:
        raise ConfigError(
            f"Не удалось прочитать файл: {error}"
        ) from error

    if not isinstance(config, dict):
        raise ConfigError(
            "Конфигурация должна содержать YAML-словарь."
        )

    validate_config(config)
    return config


def validate_required_fields(config):
    required_fields = [
        "package_name",
        "repository",
        "test_mode",
        "version",
        "output_file",
        "max_depth",
        "filter_substring"
    ]

    for field in required_fields:
        if field not in config:
            raise ConfigError(
                f"Отсутствует обязательный параметр: {field}"
            )


def validate_nonempty_string(value, message):
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(message)


def validate_output_file(filename):
    validate_nonempty_string(
        filename,
        "Имя выходного файла должно быть непустой строкой."
    )

    output_path = Path(filename)

    if output_path.name != filename:
        raise ConfigError(
            "Имя выходного файла должно содержать "
            "только имя файла с расширением .png."
        )

    if output_path.suffix.lower() != ".png":
        raise ConfigError(
            "Имя выходного файла должно содержать "
            "только имя файла с расширением .png."
        )


def validate_max_depth(max_depth):
    if not isinstance(max_depth, int):
        raise ConfigError(
            "Максимальная глубина должна быть "
            "неотрицательным целым числом."
        )

    if isinstance(max_depth, bool):
        raise ConfigError(
            "Максимальная глубина должна быть "
            "неотрицательным целым числом."
        )

    if max_depth < 0:
        raise ConfigError(
            "Максимальная глубина должна быть "
            "неотрицательным целым числом."
        )


def validate_test_mode(test_mode):
    if not isinstance(test_mode, bool):
        raise ConfigError(
            "Параметр test_mode должен "
            "иметь значение true или false."
        )


def validate_filter_substring(substring):
    if not isinstance(substring, str):
        raise ConfigError(
            "Подстрока фильтрации должна быть строкой."
        )


def validate_config(config):
    """
    Проверяет корректность параметров конфигурации.
    """
    validate_required_fields(config)

    validate_nonempty_string(
        config["package_name"],
        "Имя пакета должно быть непустой строкой."
    )

    validate_nonempty_string(
        config["repository"],
        "Адрес репозитория должен быть непустой строкой."
    )

    validate_test_mode(config["test_mode"])

    validate_nonempty_string(
        config["version"],
        "Версия пакета должна быть непустой строкой."
    )

    validate_output_file(config["output_file"])
    validate_max_depth(config["max_depth"])
    validate_filter_substring(config["filter_substring"])
