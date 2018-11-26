[![Ingest Archiver Build Status](https://travis-ci.org/HumanCellAtlas/ingest-archiver.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/ingest-archiver)
[![Maintainability](https://api.codeclimate.com/v1/badges/8ce423001595db4e6de7/maintainability)](https://codeclimate.com/github/HumanCellAtlas/ingest-archiver/maintainability)
[![codecov](https://codecov.io/gh/HumanCellAtlas/ingest-archiver/branch/master/graph/badge.svg)](https://codecov.io/gh/HumanCellAtlas/ingest-archiver)

# Ingest Archiver
The archiver service is an ingest component that:
- submits metadata to the appropriate external accessioning authorities. These are currently only EBI authorities (e.g. Biosamples).
- converts metadata into the format accepted by each external authority

In the future it will:
- update HCA metadata with accessions provided by external authorities

The archiver uses the [USI Submissions API](https://submission-dev.ebi.ac.uk/api/docs/how_to_submit_data_programatically.html#_overview) to communicate with EBI external authorities.

This component is currently invoked manually after an HCA submission.

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
