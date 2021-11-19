import boto3

class AwsS3:

    def __init__(self, access_key, secret_key, region, bucket_name):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.bucket_name = bucket_name
        self.session = boto3.Session(region_name=self.region,
                             aws_access_key_id=self.access_key,
                             aws_secret_access_key=self.secret_key)

    def list_files(self, submission_uuid):

        s3_resource = self.session.resource('s3')
        bucket = s3_resource.Bucket(self.bucket_name)

        fs = []
        for obj in bucket.objects.filter(Prefix=submission_uuid):
            # skip the top-level directory
            if obj.key == submission_uuid:
                continue
            fs.append(FileTransfer(path=os.getcwd(), key=obj.key, size=obj.size))



        self.user_profile = user_profile
        self.common_session = self.new_session()
        self.is_user = False # not admin
        self.bucket_name = None