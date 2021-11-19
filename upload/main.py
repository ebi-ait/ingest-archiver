import argparse
import re
from upload.aws_s3_client import AwsS3
import upload.ftp_uploader
from upload.utils import is_valid_uuid


ENVS = ['dev', 'staging', 'prod']
BUCKET_NAME_PREFIX = 'org-hca-data-archive-upload-'

DEFAULT_ENV = 'dev'

HOST = 'webin.ebi.ac.uk'
DEFAULT_WEBIN_USER = 'Webin-46220' # DSP Webin user


class Src:
    def __init__(self, bucket, submission_uuid, files=[]):
        self.bucket = bucket
        self.submission_uuid = submission_uuid
        self.files = files


class Dest:
    def __init__(self, host, user, pwd, path):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.path = path


def valid_uuid(uuid):
    if not is_valid_uuid(uuid):
        msg = "invalid submission uuid"
        raise argparse.ArgumentTypeError(msg)
    return uuid

def valid_webin_user(user):
    if not re.match(r"Webin-[0-9]+", user):
        msg = "invalid Webin user - needs to be in the format 'Webin-XXXXX'"
        raise argparse.ArgumentTypeError(msg)
    return user

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HCA-ENA FTP file uploader")
    parser.add_argument('-uuid', type=valid_uuid, help='Submission uuid')
    parser.add_argument('-e', choices=ENVS, default=DEFAULT_ENV, help=f'Environment. Default {DEFAULT_ENV}')


    parser.add_argument('-u', help=f'Webin user. Default {DEFAULT_WEBIN_USER}', default=DEFAULT_WEBIN_USER, type=valid_webin_user, nargs='?')
    parser.add_argument('-p', help='Webin user password', nargs='?', required=True)

    args = parser.parse_args()
    src = Src(BUCKET_NAME_PREFIX+args.e, args.uuid)
    dest = Dest(HOST, args.u, args.p, f'{args.e}/{args.uuid}')
    # step 1 get a list of files to be uploaded
    AwsS3().get_files(args.uuid)
    # step 2 compress files using gz
    # step 3 calculate checksums of compressed files (and create .md5 files)

    #ftp(src, dest)

