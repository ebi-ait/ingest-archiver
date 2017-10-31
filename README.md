# Ingest Archiver
Take a valid HCA metadata and submits to archives returning accession id.

## Components
- Converter: Take valid HCA JSON and return valid USI JSON

## TODO:
- Update README.md
- Provide import instructions for Intellij
- Provide requirements.txt (or similar) for dependencies
- Move tests and test data into a suitable location to any Python standards
- Add travis build and test execution
- Provide a serverless framework configuration to deploy converter as Lambda that  accepts HCA JSON via HTTP POST and return USI JSON
- Deploy to AWS

## HCA to USI attribute mapping
- content.id->title
- uuid.uuid->alias (temporary)
- content.species.ontology->taxonId
- content.species.text->taxon
- submissionDate->attributes[<index>].name["release"]
- content.*.key->attributes[<index>].name[key]
- content.*.value->attributes[<index>].name[value]