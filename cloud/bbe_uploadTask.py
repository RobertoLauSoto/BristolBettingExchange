import boto3
import uuid

s3_resource = boto3.resource('s3')

def create_bucket_name(bucket_prefix):
    return ''.join([bucket_prefix, str(uuid.uuid4())])

def create_bucket(bucket_prefix, s3_connection):
    bucket_name = create_bucket_name(bucket_prefix)
    bucket_response = s3_connection.create_bucket(
        Bucket=bucket_name)
    print(bucket_name)
    return bucket_name, bucket_response

bucket_name, response = create_bucket(
    bucket_prefix='bbe-task', s3_connection=s3_resource.meta.client)

s3_resource.meta.client.upload_file(
    Filename='bbe_doTask.py', Bucket=bucket_name,
    Key='bbe_doTask.py'
)