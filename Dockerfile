FROM quay.io/ebi-ait/ingest-base-images:python_3.7-slim

RUN apt-get update && \
    apt-get install -y git

RUN mkdir /app
WORKDIR /app

COPY archiver ./archiver
COPY conversion ./conversion
COPY api ./api
COPY utils ./utils
COPY config.py app.py requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python", "app.py"]

