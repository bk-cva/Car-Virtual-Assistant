FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app
RUN pip install --no-cache -r requirements.txt

COPY scripts /app/scripts
COPY src /app/src

EXPOSE 5000
