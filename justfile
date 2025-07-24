lint:
    ruff check
    ruff format --check
    toml-sort --check pyproject.toml

pretty:
    ruff check --fix
    ruff format
    toml-sort pyproject.toml

typecheck:
    mypy --show-traceback .


