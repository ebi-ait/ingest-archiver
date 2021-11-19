import os
from ftplib import FTP, FTP_TLS


class FtpUploader:
    def __init__(self, host, user, pwd, secure=False):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.secure = secure
        if secure:
            self.ftp = FTP_TLS(host, user, pwd)
            self.ftp.prot_p()
        else:
            self.ftp = FTP(host, user, pwd)

def ftp_stor(self, file):
    file = open(file, "rb")
    self.ftp.storbinary("STOR " + os.path.basename(file), file)
    file.close()


def upload(self):
    # step 1 get a list of files to be uploaded
    # step 2 compress files using gz
    # step 3 calculate checksums of compressed files (and create .md5 files)
    fs = []
    for f in fs:
        self.ftp_stor(f)


def close_conn(self):
    self.ftp.close()

def test(self):
    file1="/mnt/d/tmp/org-hca-data-archive-upload-dev/59c26104-86a6-4fd3-8a94-90df84be1101/SRR3562314_1.fastq.gz"
    file2="/mnt/d/tmp/org-hca-data-archive-upload-dev/59c26104-86a6-4fd3-8a94-90df84be1101/SRR3562314_2.fastq.gz"
    #print(md5(file1))
    #print(md5(file2))
    self.ftp_stor(file1)
    self.ftp_stor(file2)
