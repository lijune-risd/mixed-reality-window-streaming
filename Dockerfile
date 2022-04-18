
FROM python:3.9.7-slim-buster


ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y
RUN apt install libgl1-mesa-glx -y
RUN apt-get install 'ffmpeg'\
    'libsm6'\
    'libxext6'  -y

RUN pip install --upgrade pip
COPY ./requirements-headless.txt /
RUN pip install -r requirements-headless.txt

COPY . /usr/src/app/
WORKDIR /usr/src/app
ENTRYPOINT ["./gunicorn_init.sh"]

