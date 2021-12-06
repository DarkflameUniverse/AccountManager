# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY wsgi.py wsgi.py
COPY ./app /app

EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", ":8000", "-w", "4", "wsgi:app"]