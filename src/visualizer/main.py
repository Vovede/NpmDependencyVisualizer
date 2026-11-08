import argparse

from visualizer.config import load_config, ConfigError
from visualizer.dependencies import get_dependencies, DependencyError
from visualizer.graph import build_dependency_graph


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


        # Кэшируем уже полученные зависимости
        dependency_cache = {}

        def dependency_loader(name, version):
            key = (name, version)

            if key not in dependency_cache:
                dependency_cache[key] = get_dependencies(
                    name,
                    version,
                    config["repository"],
                    config["test_mode"]
                )

            return dependency_cache[key]

        # Получаем прямые зависимости корневого пакета
        dependencies = dependency_loader(
            config["package_name"],
            config["version"]
        )

        print("\nПрямые зависимости:")
        print("-" * 40)

        if dependencies:
            for name, version in dependencies.items():
                print(f"{name}: {version}")
        else:
            print("У пакета нет прямых зависимостей.")

        print("-" * 40)

        # Строим граф транзитивных зависимостей
        print("\nПостроение графа зависимостей...")

        graph = build_dependency_graph(
            config["package_name"],
            config["version"],
            dependency_loader,
            max_depth=config["max_depth"],
            filter_substring=config["filter_substring"]
        )

        print("\nГраф зависимостей:")
        print("-" * 40)

        for package, dependencies in graph.graph.items():
            print(f"{package} -> {', '.join(dependencies) if dependencies else 'нет зависимостей'}")

        print("-" * 40)

        # Выводим обнаруженные циклы
        print("\nОбнаруженные циклы:")

        if graph.cycles:
            for cycle in graph.cycles:
                print(" -> ".join(cycle))
        else:
            print("Циклические зависимости не обнаружены.")

        print("-" * 40)

    except (ConfigError, DependencyError) as error:
        print(f"Ошибка: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()