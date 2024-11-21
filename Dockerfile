FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

EXPOSE 8000

CMD ["python", "main.py"]
