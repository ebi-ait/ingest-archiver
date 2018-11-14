import json
import logging
import sys

from optparse import OptionParser

from archiver.archiver import IngestArchiver

if __name__ == '__main__':
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()
    parser.add_option("-b", "--bundle_uuid", help="Bundle UUID")
    parser.add_option("-i", "--ingest_url", help="Ingest API url")
    parser.add_option("-e", "--exclude_types", help="e.g. \"project,study,sample,sequencingExperiment,sequencingRun\"")

    (options, args) = parser.parse_args()

    if not options.bundle_uuid:
        logging.error("You must supply a Bundle UUID")
        exit(2)

    if not options.ingest_url:
        logging.error("You must supply the Ingest API url.")
        exit(2)

    exclude_types = []
    if options.exclude_types:
        exclude_types = [x.strip() for x in options.exclude_types.split(',')]
        logging.warning(f"Excluding {', '.join(exclude_types)}")

    archiver = IngestArchiver(ingest_url=options.ingest_url, exclude_types=exclude_types)
    assay_bundle = archiver.get_assay_bundle(options.bundle_uuid)
    entities_dict = archiver.get_archivable_entities(assay_bundle)
    archive_submission = archiver.archive(entities_dict)
    print('##################### SUMMARY')
    archive_submission.generate_report()


