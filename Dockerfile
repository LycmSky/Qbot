FROM python:3.9.12-slim-bullseye
WORKDIR /app
COPY . /app
RUN apt-get update -y && apt-get install curl -y && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    $HOME/.local/bin/poetry config virtualenvs.create false && \
    $HOME/.local/bin/poetry install --no-interaction --no-ansi
CMD $HOME/.local/bin/poetry run python main.py
