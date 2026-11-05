import argparse

from visualizer.config import load_config, ConfigError
from visualizer.dependencies import get_direct_dependencies, DependencyError


def main():
    parser = argparse.ArgumentParser(
        description="NPM Dependency Visualizer"
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Путь к YAML-файлу конфигурации"
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)

        print("\nПараметры конфигурации:")
        print("-" * 40)

        for key, value in config.items():
            print(f"{key}: {value}")

        print("-" * 40)
        print("Конфигурация успешно загружена.")

        # Получаем прямые зависимости пакета
        print("\nПолучение прямых зависимостей...")

        dependencies = get_direct_dependencies(
            config["package_name"],
            config["version"],
            config["repository"]
        )

        print("\nПрямые зависимости:")
        print("-" * 40)

        if dependencies:
            for name, version in dependencies.items():
                print(f"{name}: {version}")
        else:
            print("У пакета нет прямых зависимостей.")

        print("-" * 40)

    except (ConfigError, DependencyError) as error:
        print(f"Ошибка: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()