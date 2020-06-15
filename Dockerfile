FROM python:3.7-slim

RUN apt-get update && \
    apt-get install -y git

RUN mkdir /app
WORKDIR /app

COPY archiver ./archiver
COPY conversion ./conversion
COPY api ./api
COPY utils ./utils
COPY config.py cli.py requirements.txt ./

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "cli.py"]

