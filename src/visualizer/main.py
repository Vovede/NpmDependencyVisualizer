
import argparse
from pathlib import Path

from visualizer.config import load_config, ConfigError


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

    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
