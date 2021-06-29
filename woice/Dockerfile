FROM python:3.9-slim-buster

LABEL maintainer "Immanuel Kolapo <immanuelcaspian@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential git gcc python3-dev \
    && python -m pip install --upgrade pip

RUN mkdir /woice
WORKDIR /woice
COPY . /woice

RUN pip install -r ./requirements.txt

RUN chmod +x ./entrypoint.sh
