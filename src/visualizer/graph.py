class DependencyGraph:
    """Граф зависимостей npm-пакетов."""

    def __init__(self):
        # Список смежности: пакет -> его зависимости
        self.graph = {}

        # Обнаруженные циклы
        self.cycles = []


def build_dependency_graph(
    package_name,
    version,
    dependency_loader,
    max_depth=3,
    filter_substring=""
):
    """
    Строит граф транзитивных зависимостей
    с помощью рекурсивного обхода DFS.
    """

    result = DependencyGraph()

    # Посещённые вершины
    visited = set()

    # Вершины, находящиеся в текущем пути обхода
    recursion_stack = []

    def dfs(current_package, current_version, depth):
        # Не обходим уже посещённые пакеты повторно
        if current_package in visited:
            return

        visited.add(current_package)
        recursion_stack.append(current_package)

        # Добавляем вершину в граф
        result.graph.setdefault(current_package, [])

        # Если достигнута максимальная глубина,
        # не загружаем зависимости этого пакета
        if depth < max_depth:
            # Получаем прямые зависимости текущего пакета
            dependencies = dependency_loader(current_package, current_version)

            for dependency, dependency_version in dependencies.items():

                # Добавляем ребро графа
                result.graph[current_package].append(dependency)

                # Проверяем циклическую зависимость
                if dependency in recursion_stack:
                    cycle = recursion_stack[
                                recursion_stack.index(dependency):
                            ] + [dependency]

                    if cycle not in result.cycles:
                        result.cycles.append(cycle)

                    continue

                # Если пакет ещё не посещался, запускаем DFS
                if dependency not in visited:
                    dfs(
                        dependency,
                        dependency_version,
                        depth + 1
                    )

                else:
                    result.graph.setdefault(dependency, [])

        recursion_stack.pop()

    dfs(package_name, version, 0)

    # Фильтрация вершин по подстроке
    if filter_substring:
        filtered_graph = {}

        for package, dependencies in result.graph.items():

            # Корневой пакет всегда сохраняется,
            # но его зависимости фильтруются
            if package == package_name:
                filtered_graph[package] = [
                    dependency
                    for dependency in dependencies
                    if filter_substring.lower() in dependency.lower()
                ]

            # Остальные пакеты сохраняются,
            # если содержат искомую подстроку
            elif filter_substring.lower() in package.lower():
                filtered_graph[package] = dependencies.copy()

        result.graph = filtered_graph

        # Пересчитываем циклы для отфильтрованного графа
        result.cycles = []

        visited = set()
        recursion_stack = []

        def find_cycles(current_package):
            if current_package not in result.graph:
                return

            visited.add(current_package)
            recursion_stack.append(current_package)

            for dependency in result.graph[current_package]:
                if dependency in recursion_stack:
                    cycle = recursion_stack[
                                recursion_stack.index(dependency):
                            ] + [dependency]

                    if cycle not in result.cycles:
                        result.cycles.append(cycle)

                elif (
                        dependency in result.graph
                        and dependency not in visited
                ):
                    find_cycles(dependency)

            recursion_stack.pop()

        find_cycles(package_name)

    return result

def get_loading_order(graph):
    """
    Определяет порядок загрузки пакетов.
    Зависимости располагаются раньше пакетов,
    которые от них зависят.
    """

    loading_order = []
    visited = set()
    recursion_stack = []
    cycles = []

    def dfs(package):
        if package in recursion_stack:
            cycle = recursion_stack[recursion_stack.index(package):] + [package]

            if cycle not in cycles:
                cycles.append(cycle)

            return

        if package in visited:
            return

        visited.add(package)
        recursion_stack.append(package)

        for dependency in graph.graph.get(package, []):
            if dependency in graph.graph:
                dfs(dependency)

        recursion_stack.pop()
        loading_order.append(package)

    for package in graph.graph:
        dfs(package)

    return loading_order, cycles


def export_to_d2(graph, output_file):
    """
    Экспортирует граф зависимостей в формат D2.
    """
    with open(output_file, "w", encoding="utf-8") as file:
        for package, dependencies in graph.graph.items():
            for dependency in dependencies:
                file.write(f'"{package}" -> "{dependency}"\n')

            # Изолированные вершины тоже должны отображаться
            if not dependencies:
                file.write(f'"{package}"\n')
