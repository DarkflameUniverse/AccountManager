# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY wsgi.py wsgi.py
COPY entrypoint.sh entrypoint.sh
COPY ./app /app
COPY ./migrations /migrations

EXPOSE 8000
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
