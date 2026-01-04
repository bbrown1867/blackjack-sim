coverage:
    uv run coverage run .venv/bin/pytest tests
    uv run coverage html
    uv run coverage report

format:
    uv run ruff format

lint:
    uv run ruff format --check
    uv run ruff check
    uv run ty check

play:
    uv run blackjack play

simulate:
    uv run blackjack simulate

test:
    uv run pytest tests
