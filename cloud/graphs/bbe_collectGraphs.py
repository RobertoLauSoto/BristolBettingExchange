import boto3

s3=boto3.client('s3')
list=s3.list_objects(Bucket='bbe-bucketd20de7f7-3472-41e3-b732-9c0804b60766')['Contents']
for key in list:
    s3.download_file('bbe-bucketd20de7f7-3472-41e3-b732-9c0804b60766', key['Key'], key['Key'])