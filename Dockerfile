FROM python:3.12

RUN pip install --no-cache-dir poetry

WORKDIR /presentation-api

COPY pyproject.toml poetry.lock* /presentation-api/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev 

COPY . /presentation-api/

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
