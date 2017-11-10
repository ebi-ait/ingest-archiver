FROM jfloff/alpine-python:3.4-slim
MAINTAINER Alegria Aclan "aaclan@ebi.ac.uk"

RUN mkdir /app
COPY archiver /app/archiver
COPY tests /app/tests
COPY config.py listener.py requirements.txt /app/
WORKDIR /app

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["python"]
CMD ["listener.py"]
