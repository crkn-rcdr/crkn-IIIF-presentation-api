FROM python:3.12

RUN pip install --no-cache-dir poetry

RUN apt-get update && apt-get install -y netcat-openbsd

WORKDIR /presentation-api

COPY pyproject.toml poetry.lock* /presentation-api/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev 

COPY . /presentation-api/


