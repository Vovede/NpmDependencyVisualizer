import yaml
from pathlib import Path


class ConfigError(Exception):
    """Ошибка конфигурации приложения."""


def load_config(config_path):
    """
    Загружает конфигурацию из YAML-файла.
    """

    config_path = Path(config_path)

    # Проверяем существование файла
    if not config_path.exists():
        raise ConfigError(f"Файл конфигурации не найден: {config_path}")

    # Проверяем, что это файл
    if not config_path.is_file():
        raise ConfigError(f"Указанный путь не является файлом: {config_path}")

    # Читаем YAML
    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ConfigError(f"Ошибка чтения YAML: {error}") from error
    except OSError as error:
        raise ConfigError(f"Не удалось прочитать файл: {error}") from error

    # Проверяем структуру конфигурации
    if not isinstance(config, dict):
        raise ConfigError("Конфигурация должна содержать YAML-словарь.")

    validate_config(config)

    return config


def validate_config(config):
    """
    Проверяет корректность параметров конфигурации.
    """

    required_fields = [
        "package_name",
        "repository",
        "test_mode",
        "version",
        "output_file",
        "max_depth",
        "filter_substring"
    ]

    # Проверяем наличие всех параметров
    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Отсутствует обязательный параметр: {field}")

    # Проверяем типы данных
    if not isinstance(config["package_name"], str) or not config["package_name"].strip():
        raise ConfigError("Имя пакета должно быть непустой строкой.")

    if not isinstance(config["repository"], str) or not config["repository"].strip():
        raise ConfigError("Адрес репозитория должен быть непустой строкой.")

    if not isinstance(config["test_mode"], bool):
        raise ConfigError("Параметр test_mode должен иметь значение true или false.")

    if not isinstance(config["version"], str) or not config["version"].strip():
        raise ConfigError("Версия пакета должна быть непустой строкой.")

    if not isinstance(config["output_file"], str) or not config["output_file"].strip():
        raise ConfigError("Имя выходного файла должно быть непустой строкой.")

    output_path = Path(config["output_file"])
    if output_path.name != config["output_file"] or output_path.suffix.lower() != ".png":
        raise ConfigError("Имя выходного файла должно содержать только имя файла с расширением .png.")

    if (
        not isinstance(config["max_depth"], int)
        or isinstance(config["max_depth"], bool)
        or config["max_depth"] < 0
    ):
        raise ConfigError("Максимальная глубина должна быть неотрицательным целым числом.")

    if not isinstance(config["filter_substring"], str):
        raise ConfigError("Подстрока фильтрации должна быть строкой.")
