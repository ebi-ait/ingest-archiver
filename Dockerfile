FROM python:3.6-slim

RUN mkdir /app
WORKDIR /app

COPY archiver ./archiver
COPY tests ./tests
COPY config.py listener.py cli.py requirements.txt ./

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "cli.py"]

