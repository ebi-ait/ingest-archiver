# How to test/trigger the direct archiver

## Data files archive
Before proceeding to the metadata archiving, the sequence files first need to be archived.
This can be triggered by sending a HTTP POST request to the `/archiveSubmissions/data` endpoint of the ingest archiver.

Follow the steps:
1. Select the correct Archiver endpoint (`ingest_archiver_url`) depending on the environment
    - dev - https://archiver.ingest.dev.archive.data.humancellatlas.org
    - staging - https://archiver.ingest.staging.archive.data.humancellatlas.org
    - prod - https://archiver.ingest.archive.data.humancellatlas.org
    
2. Get the Archiver API key (`archiver_api_key`).
```
aws --region us-east-1 secretsmanager get-secret-value --secret-id ingest/archiver/wrangler/secrets --query SecretString --output text | jq -jr .{env}_archiver_api_key
```
Replace `{env}` with `dev`, `staging` or `prod` in the command above.

3. Trigger the data archive request
```
curl -X POST {ingest_archiver_url}/archiveSubmissions/data -H 'Content-Type: application/json' -H "Api-Key:{archiver_api_key}" -d '{"sub_uuid": "{sub_uuid}"}'
```

Where `sub_uuid` refers to the submission UUID for which sequence data files are to be archived.

4. Check the data archive result.

```
curl -X GET {ingest_archiver_url}/archiveSubmissions/data/<sub_uuid>' -H "Api-Key:{archiver_api_key}" 
```
Only proceed to metadata archive if all data files are successful archived. This may take a while for large submission so please be patient and check regularly until all files are archived.

## Metadata archive


There is a script to trigger the direct archiver under the repository's root folder: `submit_to_archives.py`.
It needs the `submission_UUID` as the input parameter.

There is a mandatory configuration parameter, too.
You need to setup an environment variable for `ARCHIVER_API_KEY`. You can get this value from AWS Secret Manager.
It is under the `ingest/archiver/wrangler/secrets` secret storage.
You can get the above value from AWS Secret Manager with this command line action for dev environment.

`aws --region us-east-1 secretsmanager get-secret-value --secret-id ingest/archiver/wrangler/secrets --query SecretString --output text | jq -jr .dev_archiver_api_key; echo -e`

You can use the above command for staging and production with the replacement of `.dev_archiver_api_key` in the command.

- For staging: `staging_archiver_api_key`
- For production: `prod_archiver_api_key`

There is one optional configuration parameter.
- ENVIRONMENT, possible values: `dev`, `staging`, `prod`, the default value is `dev`.

Here is an example how to execute the script from the command line:

`export ENVIRONMENT='dev'; export ARCHIVER_API_KEY='<VALUE FROM AWS SECRET MANAGER>'; python submit_to_archives.py 88888888-4444-4444-4444-121212121212`

Possible successful output:

```commandline
2022-01-10 11:10:21,210 - __main__ - INFO - Archiving has started in dev environment for submission: 88888888-4444-4444-4444-121212121212. This could take some time. Please, be patience.
2022-01-10 11:10:39,883 - __main__ - INFO - Response: {'biosamples_accessions': ['SAMEA8566024', 'SAMEA8566026', 'SAMEA8566028'], 'biostudies_accession': 'S-BSST175', 'ena_accessions': ['ERP134513']}
2022-01-10 11:10:39,883 - __main__ - INFO - You can check the result of archiving in the following webpages:
2022-01-10 11:10:39,884 - __main__ - INFO - {
    "Submitted samples in BioSamples": [
        "https://wwwdev.ebi.ac.uk/biosamples/SAMEA8566024",
        "https://wwwdev.ebi.ac.uk/biosamples/SAMEA8566026",
        "https://wwwdev.ebi.ac.uk/biosamples/SAMEA8566028"
    ],
    "Submitted studies in BioStudies": [
        "https://wwwdev.ebi.ac.uk/biostudies/studies/S-BSST175"
    ],
    "Submitted entities in ENA": [
        "https://wwwdev.ebi.ac.uk/ena/submit/webin/report/studies/ERP134513"
    ]
}
```