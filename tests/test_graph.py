import pytest

from visualizer.graph import build_dependency_graph


@pytest.fixture
def test_dependencies():
    """Искусственный граф зависимостей для тестирования."""

    return {
        "A": {"B": "1.0", "C": "1.0"},
        "B": {"D": "1.0"},
        "C": {"E": "1.0"},
        "D": {},
        "E": {"F": "1.0"},
        "F": {}
    }


def create_loader(dependencies):
    """Создаёт функцию загрузки зависимостей из тестового словаря."""

    def loader(package_name, version):
        return dependencies.get(package_name, {})

    return loader


def test_build_dependency_graph(test_dependencies):
    """Проверка построения полного графа."""

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(test_dependencies),
        max_depth=3
    )

    assert graph.graph == {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["E"],
        "D": [],
        "E": ["F"],
        "F": []
    }


def test_max_depth(test_dependencies):
    """Проверка ограничения глубины обхода."""

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(test_dependencies),
        max_depth=1
    )

    assert graph.graph == {
        "A": ["B", "C"],
        "B": [],
        "C": []
    }


def test_cycle_detection():
    """Проверка обнаружения циклических зависимостей."""

    dependencies = {
        "A": {"B": "1.0"},
        "B": {"C": "1.0"},
        "C": {"A": "1.0"}
    }

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(dependencies),
        max_depth=5
    )

    assert graph.cycles == [
        ["A", "B", "C", "A"]
    ]


def test_repeated_dependency():
    """Проверка повторяющейся зависимости."""

    dependencies = {
        "A": {"B": "1.0", "C": "1.0"},
        "B": {"D": "1.0"},
        "C": {"D": "1.0"},
        "D": {}
    }

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(dependencies),
        max_depth=3
    )

    assert graph.graph == {
        "A": ["B", "C"],
        "B": ["D"],
        "D": [],
        "C": ["D"]
    }


def test_filter_substring(test_dependencies):
    """Проверка фильтрации пакетов по подстроке."""

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(test_dependencies),
        max_depth=3,
        filter_substring="B"
    )

    assert graph.graph == {
        "A": ["B"],
        "B": ["D"]
    }

def test_filter_substring_e(test_dependencies):
    """Проверка фильтрации пакетов по подстроке E."""

    graph = build_dependency_graph(
        "A",
        "1.0",
        create_loader(test_dependencies),
        max_depth=3,
        filter_substring="E"
    )

    assert graph.graph == {
        "A": [],
        "E": ["F"]
    }

    assert graph.cycles == []