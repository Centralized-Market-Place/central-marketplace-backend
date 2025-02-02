FROM python:3.13 AS requirements-stage

WORKDIR /tmp

RUN pip install poetry==1.8.5

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.13

WORKDIR /code
EXPOSE 8443

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      postgresql-client

RUN pip install --no-cache-dir --default-timeout=600 --upgrade -r /code/requirements.txt

COPY ./src /code
COPY ./.env /code

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8443"]
