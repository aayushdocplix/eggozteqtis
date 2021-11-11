FROM python:3.6
RUN apt-get update
ENV PYTHONUNBUFFERED 1
RUN mkdir /Eggoz_Backend
WORKDIR /Eggoz_Backend
RUN apt-get update
RUN apt-get -y install curl gnupg
COPY requirements.txt /Eggoz_Backend/
RUN pip install -r requirements.txt
COPY . /Eggoz_Backend/
