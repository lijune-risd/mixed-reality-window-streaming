
FROM python:3.9.7-slim-buster

RUN pip install --upgrade pip
COPY ./requirements-headless.txt /
RUN pip install -r requirements-headless.txt

COPY . /usr/src/app/
WORKDIR /usr/src/app
ENTRYPOINT ["./gunicorn_init.sh"]

