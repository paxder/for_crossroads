import boto3
from botocore.exceptions import ClientError
import time
from api.api import DynamoApi
import random
import string
from hashlib import md5
import io

class Storage:
    def __init__(self, user_id):
        """ Init """
        self.user_id = user_id
        self.s3 = boto3.client('s3')
        self.bucket = 'alex-7861d52aeeb72fd3413538272abe840e972b51f9'
        self.object_key = 'audio-uploads/'

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        return ''.join(random.choice(chars) for _ in range(size))

    def add(self, body, extension) -> str:
        """ 
        Add audio file/ Upload a file to an S3 bucket

        :param body: File contents to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :param extension : file extension
        :return: String if file was uploaded, else False
        """ 
        ts = str(int(time.time()))
        file_uid = self.user_id + '_' + ts + '_' + self.id_generator() + '.' + extension
        object_name = self.object_key + file_uid 

        try:
            response = self.s3.put_object(
                Body=body,
                Bucket=self.bucket,
                Key=object_name,
            )
        except ClientError as e:
            #return {'e': str(e)}
            return False

        return file_uid

    def delete(self, filename : str) -> bool:
        """
        Delete a file from S3

        :param filename string
        :return bool
        """
        s3 = boto3.resource('s3')
        s3.Object(self.bucket, 'audio-uploads/' + filename).delete()
        return
        
    def getAudio(self):
        """
        Download an audio file, will read contents into memory rather 
        than from disk.

        :deprecated, using cloudfront for downloads
        :return bin object
        """
        return
        """
        try:
            # read file to memory
            outfile = io.BytesIO()
            self.s3.download_fileobj(self.bucket, self.object_key + '8000000000_OMTWMK_1624906066', outfile)
            outfile.seek(0)    
        except ClientError as e:
            return {'e': str(e)}
        return outfile
        """
"""
from google.cloud import storage

def upload_blob(source_file_name, destination_blob_name):
    Uploads a file to the bucket.
    # The path to your file to upload
    # source_file_name = "local/path/to/file"

    bucket_name = 'testing9d9dv9df9'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob('/audio/' + source_file_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )
"""
