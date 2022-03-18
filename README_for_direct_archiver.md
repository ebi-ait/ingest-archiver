# How to test/trigger the direct archiver

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
...
2022-01-10 11:10:39,883 - __main__ - INFO - You can check the result of archiving in the following webpages:
2022-01-10 11:10:39,884 - __main__ - INFO - {
    biosamples archive": {
        "biomaterials": [
            {
                "uuid": "2bdbf12f-dcef-4455-a544-5484395134ef",
                "accession": "SAMEA9168567",
                "updated": false,
                "url": "https://wwwdev.ebi.ac.uk/biosamples/samples/SAMEA9168567"
            },
            {
                "uuid": "14fc15fd-ab72-429c-a3e2-62e1b6884c61",
                "accession": "SAMEA9168568",
                "updated": false,
                "url": "https://wwwdev.ebi.ac.uk/biosamples/samples/SAMEA9168568"
            },
            {
                "uuid": "e65fe906-9e31-4c40-accc-d9d62006e6e3",
                "accession": "SAMEA9168569",
                "updated": false,
                "url": "https://wwwdev.ebi.ac.uk/biosamples/samples/SAMEA9168569"
            }
        ]
    ],
    "bioStudies archives": {
        "projects" : [
            {
                "uuid": "83743747-da4e-47ce-afa4-5020c99342f9",
                "accession": "S-BSST175",
                "updated": false,
                "url": "https://wwwdev.ebi.ac.uk/biostudies/studies/S-BSST175"
            }
        ]
    },
    "ena archives": {
        "projects": [
            {
                "uuid": "e236309a-8488-4a0c-bc2a-40c8288acbdb",
                "accession": "ERP136384",
                "updated": false,
                "url": "https://wwwdev.ebi.ac.uk/ena/submit/webin/report/studies/ERP136384"
            }
        ]
    }
}
```
