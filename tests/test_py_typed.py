import configparser
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_py_typed_marker_file_exists_and_is_empty():
    py_typed_path = os.path.join(ROOT, "py.typed")
    assert os.path.isfile(py_typed_path)
    with open(py_typed_path) as f:
        assert f.read() == ""


def test_py_typed_is_registered_in_manifest_in():
    with open(os.path.join(ROOT, "MANIFEST.in")) as f:
        assert "py.typed" in f.read()


def test_py_typed_is_registered_in_setup_py_package_data():
    with open(os.path.join(ROOT, "setup.py")) as f:
        assert "py.typed" in f.read()


def test_mypy_ini_declares_mypy_section():
    config = configparser.ConfigParser()
    config.read(os.path.join(ROOT, "mypy.ini"))
    assert "mypy" in config


def test_mypy_records_py_is_clean():
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--config-file", "mypy.ini", "records.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
