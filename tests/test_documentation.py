import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE_PATH = os.path.join(ROOT, "examples", "context_manager_usage.py")


def test_readme_md_shows_context_manager_as_primary_example():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        content = f.read()
    basics_start = content.index("The Basics")
    first_code_block_start = content.index("``` python", basics_start)
    first_code_block_end = content.index("```", first_code_block_start + len("``` python"))
    first_code_block = content[first_code_block_start:first_code_block_end]
    assert "with records.Database(" in first_code_block


def test_readme_rst_shows_context_manager_as_primary_example():
    with open(os.path.join(ROOT, "README.rst"), encoding="utf-8") as f:
        content = f.read()
    basics_start = content.index("The Basics")
    first_code_block_start = content.index(".. code:: python", basics_start)
    second_code_block_start = content.index(
        ".. code:: python", first_code_block_start + len(".. code:: python")
    )
    first_code_block = content[first_code_block_start:second_code_block_start]
    assert "with records.Database(" in first_code_block


def test_readme_md_mentions_py_typed():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        content = f.read()
    assert "py.typed" in content


def test_readme_rst_mentions_py_typed():
    with open(os.path.join(ROOT, "README.rst"), encoding="utf-8") as f:
        content = f.read()
    assert "py.typed" in content


def test_context_manager_example_exists():
    assert os.path.isfile(EXAMPLE_PATH)


def test_context_manager_example_runs_successfully():
    result = subprocess.run(
        [sys.executable, EXAMPLE_PATH],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "db.open after the with block: False" in result.stdout
    assert "db.open after the exception: False" in result.stdout
