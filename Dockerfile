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
COPY config.py archiver_app.py requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python", "archiver_app.py"]

