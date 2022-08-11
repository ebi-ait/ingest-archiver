# How to test/trigger the direct archiver

## Prerequisites

1. The submission had to go through metadata/data and graph validation.
2. After the validation steps it had to be submitted to the EBI archives.
That should change the status of the submission to `Archiving`. 

   This is the flow of this status change: `Submitted` -> `Processing` -> `Archiving`  
   Please wait while the status become `Archiving`.


## Data files archive
Before proceeding to the metadata archiving, the sequence files first need to be archived.
This can be triggered by sending a HTTP POST request to the `/archiveSubmissions/data` endpoint of the ingest archiver.

Follow the steps:
1. Select the correct Archiver endpoint (`ingest_archiver_url`) depending on the environment
    - dev - https://archiver.ingest.dev.archive.data.humancellatlas.org
    - staging - https://archiver.ingest.staging.archive.data.humancellatlas.org
    - prod - https://archiver.ingest.archive.data.humancellatlas.org

2. Set an environment variable for the URL of ingest archiver: `export INGEST_ARCHIVER_URL=<select one from the above list>`
3. Set an environment variable for the used deployment environment: `export ENVIRONMENT='<env>'`
Replace `<env>` with `dev`, `staging` or `prod` in the command above.

4. Get the Archiver API key (`ARCHIVER_API_KEY`).
```
export ARCHIVER_API_KEY=`aws --region us-east-1 secretsmanager get-secret-value --secret-id ingest/archiver/wrangler/secrets --query SecretString --output text | jq -jr .$(echo $ENVIRONMENT)_archiver_api_key`
```
5. Set an environment variable for the UUID of the submission for which sequence data files are to be archived: `export SUBMISSION_UUID=<replace this with the submission UUID>`

6. Trigger the data archive request
```
curl -X POST $INGEST_ARCHIVER_URL/archiveSubmissions/data -H 'Content-Type: application/json' -H "Api-Key:$ARCHIVER_API_KEY" -d "{\"sub_uuid\": \"$SUBMISSION_UUID\"}"
```

7. Check the data archive result. You might have to wait 1-2 minutes to get a proper result.

```
curl -X GET $INGEST_ARCHIVER_URL/archiveSubmissions/data/$SUBMISSION_UUID -H "Api-Key:$ARCHIVER_API_KEY" | jq
```

A data file archived successfully if its `fileArchiveResult` key in the response is not `null`.
This may take a while for large submission so please be patient and check regularly (repeat the `GET` request) until all files are archived.
You have to check all the `fileArchiveResult` keys in the response of the above curl request.
If that does not help, then please go back to step 3
and trigger the data file archiving again.

Only proceed to metadata archive if all data files are successfully archived.

## Metadata archive


1. Clone this repository to your computer and cd to the repository's root folder.
2. Create and active virtual environment in the repository's root folder.

   ```bash
   python -mvenv .venv
   source .venv/bin/activate
   ```

3. Install all the requirements for the repository.

   ```
   pip install -r requirements.txt
   ```

4. There is a script to trigger the direct archiver under the repository's root folder: `submit_to_archives.py`. 
It needs the `submission_UUID` as the input parameter.

   There is a mandatory configuration parameter, too.
You need to setup an environment variable for `ARCHIVER_API_KEY`. You can get this value from AWS Secret Manager.
It is under the `ingest/archiver/wrangler/secrets` secret storage.
You can get the above value from AWS Secret Manager with this command line action for dev environment.

   **Note**: You probably have done this step already when you archived the data files.
In that case you don't have to repeat it, as you already have that value. 

   ```
   aws --region us-east-1 secretsmanager get-secret-value --secret-id ingest/archiver/wrangler/secrets --query SecretString --output text | jq -jr .$ENVIRONMENT_archiver_api_key_archiver_api_key; echo -e
   ```
   
   There is one optional configuration parameter.
   - ENVIRONMENT, possible values: `dev`, `staging`, `prod`, the default value is `dev`.
   We already defined this environment variable earlier.
   
   Here is an example how to execute the script from the command line:

   ```
   export ENVIRONMENT='dev'; export ARCHIVER_API_KEY='<VALUE FROM AWS SECRET MANAGER>'; python submit_to_archives.py <submission_uuid>
   ```

   Possible successful output:

   ```commandline
   2022-05-11 11:33:21,777 - __main__ - INFO - Archiving has started in dev environment for submission: 83484149-f413-46ac-a530-e5e231c8a780. This could take some time. Please, be patience.
   2022-05-11 11:33:22,770 - __main__ - INFO - {
       "archiveJob": {
           "_links": {
               "archiveJob": {
                   "href": "https://api.ingest.dev.archive.data.humancellatlas.org/archiveJobs/627b90f20916177e0ea32ed2"
               },
               "self": {
                   "href": "https://api.ingest.dev.archive.data.humancellatlas.org/archiveJobs/627b90f20916177e0ea32ed2"
               }
           },
           "createdDate": "2022-05-11T10:33:22.076749Z",
           "overallStatus": "Pending",
           "submissionUuid": "83484149-f413-46ac-a530-e5e231c8a780"
       },
       "message": "Direct archiving successfully triggered!"
   }
   ```

5. You have to click on the URL of the created archive job resource to get its status and result.
You might have to refresh it a couple of times while its status (in the `overallStatus` field) is still `Pending` or `Running`.

6. When the created archive job resource status is `Completed` then you can check all the archive results under the `resultsFromArchives` key in the resulted JSON response.

   Here is an example of a successful response:

   ```commandline
   {
     "submissionUuid": "12345678-abcd-46ac-a530-e5e231c8a780",
     "createdDate": "2022-05-11T10:33:22.076Z",
     "responseDate": "2022-05-11T10:34:34.908Z",
     "overallStatus": "Completed",
     "resultsFromArchives": {
       "samples": {
         "info": "Biosamples from HCA biomaterials",
         "entities": [
           {
             "entity_type": "biomaterials",
             "is_update": false,
             "biosamples_accession": "SAMEA15001419",
             "uuid": "f029e6be-04dc-473a-8337-1440438fcc04"
           },
           {
             "entity_type": "biomaterials",
             "is_update": false,
             "biosamples_accession": "SAMEA15001420",
             "uuid": "bc5d2991-19de-4e85-8c03-5c8684cc250f"
           },
           {
             "entity_type": "biomaterials",
             "is_update": false,
             "biosamples_accession": "SAMEA15001421",
             "uuid": "f5c2b6db-3243-4a60-be23-a0a6178c15df"
           }
         ]
       },
       "project": {
         "entity_type": "projects",
         "uuid": "fa0df9c6-ff77-41f5-bc25-e04df2b88571",
         "biostudies_accession": "S-BSST900",
         "is_update": false,
         "info": "BioStudies from HCA projects",
         "ena_project_accession": "ERP137281"
       },
       "hca_assays": {
         "info": "ENA experiments and runs from HCA assays",
         "experiments": [
           {
             "process_uuid": "0433ba12-3156-4fe1-abda-90725ef19a60",
             "ena_experiment_accession": "ERX9193747",
             "ena_experiment_is_update": false,
             "ena_run_accession": "ERR9640925",
             "ena_run_is_update": false,
             "files": [
               "84f36c8b-355a-44d3-bd1b-4aed06550425",
               "537baf03-82bd-4d37-a92a-f2e27c44f400"
             ]
           },
           {
             "process_uuid": "2b2f86bb-ae2e-40a9-8751-3baa47c25d3b",
             "ena_experiment_accession": "ERX9193748",
             "ena_experiment_is_update": false,
             "ena_run_accession": "ERR9640926",
             "ena_run_is_update": false,
             "files": [
               "417db418-9ca3-4c65-bff2-d72fe3d1627e",
               "3d96ebf6-ce1d-490a-bab5-36cca417ce41"
             ]
           },
           {
             "process_uuid": "560865be-84ea-44c3-9bc0-96810598bbb9",
             "ena_experiment_accession": "ERX9193749",
             "ena_experiment_is_update": false,
             "ena_run_accession": "ERR9640927",
             "ena_run_is_update": false,
             "files": [
               "a2dbdad0-a07a-4e1b-a015-1a7c35c9e7d6",
               "ed0c9df3-8c49-4c68-a21d-53e2dc9bb256"
             ]
           }
         ]
       }
     },
     "_links": {
       "self": {
         "href": "https://api.ingest.dev.archive.data.humancellatlas.org/archiveJobs/627b90f20916177e0ea32ed2"
       },
       "archiveJob": {
         "href": "https://api.ingest.dev.archive.data.humancellatlas.org/archiveJobs/627b90f20916177e0ea32ed2"
       }
     }
   }
   ```
7. The archiving process also updated all the relevant ingest resources (biomaterials, project, processes)
with all the accessions came from the various archives. You can check it in the Ingest-UI application.
8. If the archiving process went well the submission status has been updated to `Archived`.

## Troubleshooting

1. If you are using our `dev` or `staging` environment the metadata archiving
(executing the `submit_to_archives.py` script) should be on the same day as the data files archiving.
The reason: ENA recreating their test database every day from production data.
If you submitted some files in the previous days those files has been deleted at the end of the day
and that is going to create a problem if the metadata archiving happens on a later day.
The referenced files in the metadata are going to be missing.
