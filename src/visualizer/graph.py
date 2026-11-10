class DependencyGraph:
    """Граф зависимостей npm-пакетов."""

    def __init__(self):
        self.graph = {}
        self.cycles = []


def find_cycle(package, stack):
    if package not in stack:
        return None

    start = stack.index(package)
    return stack[start:] + [package]


def record_cycle(cycles, cycle):
    if cycle and cycle not in cycles:
        cycles.append(cycle)


def filter_graph(graph, root, substring):
    filtered = {}

    for package, dependencies in graph.items():
        if package == root:
            filtered[package] = [
                dep for dep in dependencies
                if substring.lower() in dep.lower()
            ]
        elif substring.lower() in package.lower():
            filtered[package] = dependencies.copy()

    return filtered


def find_graph_cycles(graph, root):
    cycles = []
    visited = set()
    stack = []

    def dfs(package):
        visited.add(package)
        stack.append(package)

        for dependency in graph.get(package, []):
            cycle = find_cycle(dependency, stack)
            if cycle:
                record_cycle(cycles, cycle)
            elif dependency in graph and dependency not in visited:
                dfs(dependency)

        stack.pop()

    dfs(root)
    return cycles


def _build_graph(package_name, version, dependency_loader, max_depth):
    result = DependencyGraph()
    visited = set()
    recursion_stack = []

    def dfs(current_package, current_version, depth):
        if current_package in visited:
            return

        visited.add(current_package)
        recursion_stack.append(current_package)
        result.graph.setdefault(current_package, [])

        if depth < max_depth:
            dependencies = dependency_loader(
                current_package, current_version
            )

            for dependency, dep_version in dependencies.items():
                result.graph[current_package].append(dependency)

                cycle = find_cycle(dependency, recursion_stack)
                if cycle:
                    record_cycle(result.cycles, cycle)
                    continue

                if dependency not in visited:
                    dfs(dependency, dep_version, depth + 1)
                else:
                    result.graph.setdefault(dependency, [])

        recursion_stack.pop()

    dfs(package_name, version, 0)
    return result



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
    result = _build_graph(
        package_name, version, dependency_loader, max_depth
    )

    if filter_substring:
        result.graph = filter_graph(
            result.graph, package_name, filter_substring
        )
        result.cycles = find_graph_cycles(
            result.graph, package_name
        )

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
        cycle = find_cycle(package, recursion_stack)
        if cycle:
            record_cycle(cycles, cycle)
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
            if dependencies:
                for dependency in dependencies:
                    file.write(
                        f'"{package}" -> "{dependency}"\n'
                    )
            else:
                file.write(f'"{package}"\n')
