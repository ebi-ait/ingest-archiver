#!/usr/bin/env bash

BASE_DIR=$(dirname "$0")

DEFAULT_DIR=output
DEFAULT_INGEST_URL=http://api.ingest.humancellatlas.org

output_dir=$DEFAULT_DIR
ingest_url=$DEFAULT_INGEST_URL

for arg in "$@"
do
case $arg in
     -o=*|--output=*)
     output_dir=${arg#*=}
     shift
     ;;
     -u=*|--url=*)
     ingest_url=${arg#*=}
     shift
     ;;
     *)
     if [ -z $input_file ]; then
         input_file=$arg
     else
         echo "Unknown argument [$arg]."
         exit 1
     fi
     ;;
esac
done

if [ -z $input_file ]; then
    echo "No id list file provided."
    exit 1
fi

if [ ! -d $output_dir ]; then
    mkdir -p $output_dir
fi

if [ ! -f $input_file ]; then
    echo "Input file does not exist."
    exit 1
fi

for uuid in $(cat $input_file)
do
    output_file=$output_dir/archive_$uuid.yaml
    cat $BASE_DIR/job-template.yaml | sed "s/\${BUNDLE_UUID}/$uuid/" |\
        sed "s~\${INGEST_URL}~$ingest_url~g" > $output_file
done