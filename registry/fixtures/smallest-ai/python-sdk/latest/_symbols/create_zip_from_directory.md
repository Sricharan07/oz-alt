# create_zip_from_directory

**Kind:** function
**Signature:** `def create_zip_from_directory(directory: Path):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/cli/utils.py#create_zip_from_directory

## Example

```python
def create_zip_from_directory(directory: Path):
    """Create a zip file from a directory, excluding files based on .gitignore patterns."""

    excluded_patterns = {
        # Byte-compiled / optimized / DLL files
        "__pycache__",
        "*.py[codz]",
        "*$py.class",
        "*.so",
        # Distribution / packaging
        ".Python",
        "build",
        "develop-eggs",
        "dist",
        "downloads",
        "eggs",
        ".eggs",
        "lib",
        "lib64",
        "parts",
        "sdist",
        "var",
        "wheels",
        "share",
        "*.egg-info",
        ".installed.cfg",
        "*.egg",
        "MANIFEST",
        # PyInstaller
        "*.manifest",
        "*.spec",
        # Installer logs
        "pip-log.txt",
        "pip-delete-this-directory.txt",
        # Unit test / coverage reports
        "htmlcov",
        ".tox",
        ".nox",
        ".coverage",
        ".coverage.*",
        ".cache",
        "nosetests.xml",
        "coverage.xml",
        "*.cover",
        "*.py.cover",
        ".hypothesis",
        ".pytest_cache",
        "cover",
        # Translations
        "*.mo",
        "*.pot",
        # Django
        "*.log",
        "local_settings.py",
        "db.sqlite3",
        "db.sqlite3-journal",
        # Flask
        "instance",
        ".webassets-cache",
        # Scrapy
        ".scrapy",
        # Sphinx documentation
        "docs/_build",
        # PyBuilder
        ".pybuilder",
        "target",
        # Jupyter Notebook
        ".ipynb_checkpoints",
        # IPython
        "profile_default",
        "ipython_config.py",
        # pipenv, UV, poetry, pdm, pixi
        ".venv",
        "env",
        "venv",
        "ENV",
        "env.bak",
        "venv.bak",
        ".pdm-python",
        ".pdm-build",
        ".pixi",
        # PEP 582
        "__pypackages__",
        # Celery
        "celerybeat-schedule",
        "celerybeat.pid",
        # Redis
        "*.rdb",
        "*.aof",
        "*.pid",
        # RabbitMQ
        "mnesia",
        "rabbitmq",
        "rabbitmq-data",
        # ActiveMQ
        "activemq-data",
        # SageMath
        "*.sage.py",
        # Environments
        #
        # Disabling env for now until environment variable feature is not implemented on platform
        # ".env",
        ".envrc",
        # IDE settings
        ".spyderproject",
        ".spyproject",
        ".ropeproject",
        # mkdocs
        "site",
        # Type checkers
        ".mypy_cache",
        ".dmypy.json",
        "dmypy.json",
        ".pyre",
        ".pytype",
        # Cython
        "cython_debug",
        # Abstra
        ".abstra",
        # Ruff
```
