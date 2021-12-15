FROM quay.io/ebi-ait/ingest-base-images:python_3.7-slim

RUN apt-get update && \
    apt-get install -y git

RUN mkdir /app
WORKDIR /app

COPY api ./api
COPY archiver ./archiver
COPY converter ./converter
COPY hca ./hca
COPY submitter ./submitter
COPY utils ./utils
COPY tests ./tests
COPY config.py archiver_app.py requirements.txt requirements-dev.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements-dev.txt

ENTRYPOINT ["python", "-m", "unittest"]
