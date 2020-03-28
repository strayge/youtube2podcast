FROM python:3.7-slim

ENV PYTHONUNBUFFERED 1

RUN mkdir /src
WORKDIR /src

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
