# Data files to EBI Archives

1. [Situation](#situation)
2. [Current data files archiving flow](#current-data-files-archiving-flow)
3. [Expected archiving flow](#expected-archiving-flow)


## Situation


We need to skip uploading data files to DSP and instead upload directly to ENA staging area in the SRA cluster. See dev ticket [1]. 


## Current data files archiving flow

- data files are currently uploaded to ENA via DSP.
- it is a manual process that is triggered by a wrangler or dev, and runs on the EBI cluster.
- there are a number of components/envs involved:
    - AWS S3 (where the data files live)
    - DSP (intermediary/broker - via tus-upload endpoint)
    - ENA Archive (where data needs to land, ultimately, in expected format)
    - EBI Cluster (the execution environment)
    - Archiver Service (builds the upload plan)
    - Ingest File Archiver (docker image of file archiving business)


### Upload via DSP
![Archiving Files to DSP](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ebi-ait/ingest-archiver/prabh-t-patch-1/doc/dsp_upload.diag)


### LSF job
The LSF job runs the Ingest file archiver (node app) image which does the following:

- downloads files from S3
- performs fastq2bam conversion (memory intensive)
- uploads to DSP via the tus-upload endpoint 
    - the data goes to the DSP staging area in the cluster
    - a process (script) in DSP then moves this data to ENA staging area

![Ingest file archiver](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ebi-ait/ingest-archiver/prabh-t-patch-1/doc/ingest_file_archiver.diag)


The file archiver can be run on a local machine and have been run on the Wrangler EC2 instance as well.


## Expected archiving flow

__Upload data files to ENA directly__

In doing so, we need to review our requirements.

_Not needed_

1. we do not need bam conversion anymore
    - ENA used to only accept 2 fastq per run (which is not compatible with some tech that HCA uses - 10x mainly)
    - now ENA accepts more files, perhaps not via the Webin-CLI submission route though (https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#prepare-the-files )


_Requirements to upload to ENA_

1. gzip compression - file needs to be gzip compressed
    - not all sequence files are submitted compressed.
2. md5 checksumming - we need to provide .md5 file
    - ENA requires md5 checksums (checksum_method='md5' in run/experiment XMLs). These are calculated for the user when submitting via the Web Uploader/Webin-CLI. Need to provide the *.md5 with the checksum string for each sequence file.
    - currently, in HCA file metadata, we do not store md5 (we store sha-256, sha-1, CRC-32C and S3 ETag of file) both in the file metadata doc (in mongo) and as S3 tags.
    - we need to calculate the md5, which will take a while for large files


### ENA Data files upload options
See [4]. There are basically 2 ways to upload files:
1. FTP/S 
2. Aspera 

Notes:
- The Webin-CLI uses either FTP/S or Aspera.
- The Webin-REST is not an option in our case.
- If files are already in the EBI network (cluster file system), they can be directly copied BUT unix permissions must be correct so that ena-admin group has read/write permissions to files and read/write/execute permissions to directories. The file/directory group MUST be ena-admin and that file/directory owner must belong to ena-admin group.

    If FTP/Aspera is used, then the upload service takes care of file/dir permissions.
- FTP is relatlvely easy to use e.g. a simple Python or Java client can be written to upload files/dirs recursively or use a command line as well, for e.g. lftp.

### Webin user 

Any submission made to ENA needs to come from a registered Webin user. For e.g. the registered DSP Webin user is Webin-46220. 

This Webin user is associated with a Webin upload area (ENA upload/staging area).

Webin user upload area
```
/fire/staging/era/upload/Webin-46220
```

Once we have the new email account, a Webin user account for HCA submissions to ENA will need to be created at https://www.ebi.ac.uk/ena/submit/webin/accountInfo.

Once we have the new Webin account, it has to be made a "broker" by filling in `broker_name` in ERAPRO submission_account table.




### Proposed Webin upload area directory structure

Currently sequence file references in the run/experiment XMLs use the base upload area location (see above).

To distinguish between submissions from the different environments, a directory structure following the format could be used:

```
<env>/<sub_uuid>
```

Run and experiment XMLs will have reference to files uploaded in the Webin upload area following this structure, for e.g. `/dev/d6a3bb80-493a-11ec-81d3-0242ac130003/file1.fastq.gz`.



## Covid19 Portal data submission to ENA

- data resided in S3
- needed to transfer to ENA, in the same way as we require for hca
- was one-off operation
- used an EBI VM, mounted S3 and the Webin user upload area, transferred data <- a better solution than getting files on an intermediate machine (unless processing required) then to ftp

- Webin upload area - mounted under /fire/staging/era/upload/Webin-XXXX on SRA cluster


## References
1. Upload data files to ENA directly - Product Dev ticket (https://app.zenhub.com/workspaces/dcp-ingest-product-development-5f71ca62a3cb47326bdc1b5c/issues/ebi-ait/dcp-ingest-central/521)
2. DSP Submission API https://submission.ebi.ac.uk/api (tus-upload)
3. Archiving SOP https://ebi-ait.github.io/hca-ebi-wrangler-central/SOPs/archiving_SOP.html (Step 2 of 3 - Archiving Files to DSP)
4. ENA doc - Uploading Files to ENA https://ena-docs.readthedocs.io/en/latest/submit/fileprep/upload.html
5. ftplib https://docs.python.org/3/library/ftplib.html
6. Mount S3 bucket https://github.com/s3fs-fuse/s3fs-fuse
7. s3-to-webin-utils https://github.com/ebi-ait/s3-to-webin-utils/tree/7330d34b1dd3f460067e7fd4207fcee53743aa36

