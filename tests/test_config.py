import pytest
import yaml

from visualizer.config import load_config, ConfigError


@pytest.fixture
def valid_config():
    return {
        "package_name": "lodash",
        "repository": "https://registry.npmjs.org",
        "test_mode": False,
        "version": "4.17.21",
        "output_file": "dependency_graph.png",
        "max_depth": 3,
        "filter_substring": ""
    }


def create_config_file(tmp_path, config):
    config_path = tmp_path / "config.yaml"

    with config_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(config, file)

    return config_path


def test_load_valid_config(tmp_path, valid_config):
    config_path = create_config_file(tmp_path, valid_config)

    result = load_config(config_path)

    assert result == valid_config


def test_missing_config_file(tmp_path):
    config_path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError, match="не найден"):
        load_config(config_path)


@pytest.mark.parametrize(
    "field",
    [
        "package_name",
        "repository",
        "test_mode",
        "version",
        "output_file",
        "max_depth",
        "filter_substring"
    ]
)
def test_missing_required_field(tmp_path, valid_config, field):
    config = valid_config.copy()
    del config[field]

    config_path = create_config_file(tmp_path, config)

    with pytest.raises(ConfigError, match="Отсутствует обязательный параметр"):
        load_config(config_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("package_name", ""),
        ("package_name", 123),
        ("repository", ""),
        ("repository", 123),
        ("test_mode", "false"),
        ("version", ""),
        ("version", 123),
        ("output_file", ""),
        ("output_file", "graph.jpg"),
        ("output_file", "../graph.png"),
        ("max_depth", -1),
        ("max_depth", 3.5),
        ("max_depth", True),
        ("filter_substring", 123)
    ]
)
def test_invalid_parameter(tmp_path, valid_config, field, value):
    config = valid_config.copy()
    config[field] = value

    config_path = create_config_file(tmp_path, config)

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_empty_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("", encoding="utf-8")

    with pytest.raises(ConfigError, match="YAML-словарь"):
        load_config(config_path)


def test_invalid_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("package_name: [lodash", encoding="utf-8")

    with pytest.raises(ConfigError, match="Ошибка чтения YAML"):
        load_config(config_path)
