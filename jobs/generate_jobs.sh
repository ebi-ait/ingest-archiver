#!/usr/bin/env bash

DEFAULT_DIR=output

output_dir=$DEFAULT_DIR

for arg in "$@"
do
case $arg in
     -o=*|--output=*)
     output_dir=${1#*=}
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
    cat job-template.yaml | sed "s/\${BUNDLE_UUID}/$uuid/" > $output_dir/archive_$uuid.yaml
done