FROM python:3.8

RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

ENV PYTHONUNBUFFERED 1

RUN mkdir /src
WORKDIR /src

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
