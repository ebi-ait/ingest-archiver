# How to test/trigger the direct archiver

There is a script to trigger the direct archiver under the repository's root folder: `submit_to_archives.py`.
It needs the `submission_UUID` as the input parameter.

There is 1 mandatory configuration parameter, too.
You need to setup an environment variable for `ARCHIVER_API_KEY`. You can get this value from AWS Secret Manager.
It is under the `ingest/archiver/wrangler/secrets` secret storage.

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
