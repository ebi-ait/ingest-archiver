# Job Generation

`generate_jobs.sh` is a tool whose purpose is to generate a bunch of Kubernetes
 Job manifests, one for each provided bundle UUID in a plain list file.
 
## Usage
 
 To generate a batch of bundles for archiving, a list of bundle UUIDs 
 each separated by a new line must first be prepared in a file. For example,
 
 ```
 e6103f1b-0f0d-4ef0-b7d5-0642d7fc0ef4
 fbae60c0-30b9-4174-9488-c824b0c96e56
 f80b0b08-eb61-4ac5-954e-d1bf9f004410
 ```
 
 can be placed in a file called `batch_01.lst`. As the script generates one 
 manifest per bundle UUID, this list is expected to create 3. Feed this list
 to the tool:
 
     generate_jobs.sh -o=batch_01 batch_01.lst
     
and it should create the manifests into `$PWD/batch_01` directory. The newly 
created batch of jobs can be run as any Kubernetes resource:

    kubectl create -f batch_01
    
 For more information about how to use the script, the `-h` or `--help` can 
 be used:
 
     generate_jobs.sh -h
