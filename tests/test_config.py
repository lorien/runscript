import logging

from runscript.cli import (
    DEFAULT_LOGGING_LEVEL,
    read_runscript_config,
    resolve_logging_level,
    setup_logging,
)


def test_read_runscript_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.runscript]\nlogging_level = "INFO"\n'
    )
    assert read_runscript_config() == {"logging_level": "INFO"}


def test_read_runscript_config_no_section(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[tool.isort]\nprofile = "black"\n')
    assert read_runscript_config() == {}


def test_read_runscript_config_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert read_runscript_config() == {}


def test_read_runscript_config_invalid_toml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("this is not = = toml")
    assert read_runscript_config() == {}


def test_resolve_logging_level_string():
    assert resolve_logging_level({"logging_level": "INFO"}) == logging.INFO


def test_resolve_logging_level_string_lowercase():
    assert resolve_logging_level({"logging_level": "debug"}) == logging.DEBUG


def test_resolve_logging_level_missing():
    assert resolve_logging_level({}) == DEFAULT_LOGGING_LEVEL


def test_resolve_logging_level_unknown():
    assert resolve_logging_level({"logging_level": "BOGUS"}) == DEFAULT_LOGGING_LEVEL


def test_resolve_logging_level_not_a_string():
    assert resolve_logging_level({"logging_level": 20}) == DEFAULT_LOGGING_LEVEL


def test_setup_logging_from_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.runscript]\nlogging_level = "WARNING"\n'
    )
    setup_logging(clear_handlers=True)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING
    assert root_logger.handlers[-1].level == logging.WARNING
    assert not logging.getLogger("runscript").isEnabledFor(logging.INFO)
    # Restore a sane state for other tests.
    setup_logging(clear_handlers=True, level=DEFAULT_LOGGING_LEVEL)
