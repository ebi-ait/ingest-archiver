[![Ingest Archiver Build Status](https://travis-ci.org/HumanCellAtlas/ingest-archiver.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/ingest-archiver)
[![Maintainability](https://api.codeclimate.com/v1/badges/8ce423001595db4e6de7/maintainability)](https://codeclimate.com/github/HumanCellAtlas/ingest-archiver/maintainability)
[![codecov](https://codecov.io/gh/HumanCellAtlas/ingest-archiver/branch/master/graph/badge.svg)](https://codecov.io/gh/HumanCellAtlas/ingest-archiver)

# Ingest Archiver
The archiver service is one of the ingest components which is responsible for the following:
- submitting metadata submitted to ingest database to appropriate external accessioning authorities (i.e. EBI archives - BioSamples etc.)
- converting the metadata from ingest into a structure or format that each external accessioning authorities accepts
- informing the accessioning service of the accessions acquired from submitting the ingest metadata / updating the metadata (Currently, the archiver updates the metadata directly in ingest core. Ideally, only the accessioning service should how the accessions will be updated. This should be implemented in the future.)
- updating the archive should the data in ingest has been updated

Currently, the archiver uses the [USI Submissions API](https://submission-dev.ebi.ac.uk/api/docs/ref_overview.html) to communicate with EBI archives. This service is designed to be used as the interface to EBI archive submissions where the accessions will be obtained.

This component listens for submissions on the ingest messaging queue. When a submission is completed in ingest the archiver will receive a message containing the submission uuid and trigger the archiving process.

Only the samples are the metadata being archived in BioSamples (thru USI) at the moment.

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

#### Python 3

- Install [Python OSX Install](http://docs.python-guide.org/en/latest/starting/install3/osx/#install3-osx)
- Install [Pipenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenvironments-ref)

```
# Add path for pipenv:

sudo vi /etc/paths.d/python3
/Users/<user>/Library/Python/3.6/bin
```

#### Installing python modules
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
### How to run

```
python listener.py

```

### How to run the tests

```
python -m unittest discover -s tests -t tests

```

## Deployment
See https://github.com/HumanCellAtlas/ingest-kube-deployment.

An AAP username and password is also needed to use the USI API and must be set in the config.py or as environment variable.

## Versioning

For the versions available, see the [tags on this repository](https://github.com/HumanCellAtlas/ingest-archiver/tags).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details