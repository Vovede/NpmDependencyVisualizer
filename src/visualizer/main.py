import argparse
import subprocess

from visualizer.config import load_config, ConfigError
from visualizer.dependencies import get_dependencies, DependencyError
from visualizer.graph import build_dependency_graph, get_loading_order, export_to_d2
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="NPM Dependency Visualizer"
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Путь к YAML-файлу конфигурации"
    )

    parser.add_argument(
        "--loading-order",
        action="store_true",
        help="Вывести порядок загрузки зависимостей"
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)

        loading_order_mode = args.loading_order

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

        # Создаём папку для результатов, если её нет
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Экспортируем граф в формат D2
        d2_file = output_dir / f"{Path(config['output_file']).stem}.d2"
        export_to_d2(graph, d2_file)

        print(f"D2-файл успешно создан: {d2_file}")

        # Создаём PNG-изображение с помощью D2
        png_file = output_dir / config["output_file"]

        subprocess.run(
            [
                r"C:\Program Files\D2\d2.exe",
                str(d2_file),
                str(png_file)
            ],
            check=True
        )

        print(f"PNG-диаграмма успешно создана: {png_file}")

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

        # Выводим порядок загрузки зависимостей
        if loading_order_mode:
            print("\nПорядок загрузки зависимостей:")
            print("-" * 40)

            loading_order, loading_cycles = get_loading_order(graph)

            if loading_cycles:
                print("Обнаружены циклические зависимости:")
                for cycle in loading_cycles:
                    print(" -> ".join(cycle))

                print(
                    "\nНевозможно гарантировать корректный полный "
                    "порядок загрузки из-за циклических зависимостей."
                )

                print("Порядок обхода графа (не является полным порядком загрузки):")
            else:
                print("Зависимости расположены раньше зависимых пакетов:")

            for index, package in enumerate(loading_order, start=1):
                print(f"{index}. {package}")

            print("-" * 40)

    except (ConfigError, DependencyError) as error:
        print(f"Ошибка: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()