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

4. Check the data archive result. You might have to wait 1-2 minutes to get a proper result.

   ```
   curl -X GET {ingest_archiver_url}/archiveSubmissions/data/<sub_uuid> -H "Api-Key:{archiver_api_key}" 
   ```
   If the `fileArchiveResult` key is `null` in any of the `files` in the response, then probably you have to wait a bit more
and repeat the `GET` request. If that does not help, then please go back to step 3
and trigger the data file archiving again.

Only proceed to metadata archive if all data files are successful archived. This may take a while for large submission so please be patient and check regularly until all files are archived.

## Metadata archive


1. Clone this repository to your computer and cd to the repository's root folder.
2. Create and active virtual environment in the repository's root folder.

   ```
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
   aws --region us-east-1 secretsmanager get-secret-value --secret-id ingest/archiver/wrangler/secrets --query SecretString --output text | jq -jr .dev_archiver_api_key; echo -e
   ```
   
   You can use the above command for staging and production with the replacement of `.dev_archiver_api_key` in the command.

   - For staging: `staging_archiver_api_key`
   - For production: `prod_archiver_api_key`

   There is one optional configuration parameter.
   - ENVIRONMENT, possible values: `dev`, `staging`, `prod`, the default value is `dev`.
   
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

6. You have to click on the URL of the created archive job resource to get its status and result.
You might have to refresh it a couple of times while its status is still `Pending` or `Running`.

7. When the created archive job resource status is `Completed` then you can check all the archive results under the `resultsFromArchives` key in the resulted JSON response.

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
8. The archiving process also updated all the relevant ingest resources (biomaterials, project, processes)
with all the accessions came from the various archives. You can check it in the Ingest-UI application. 