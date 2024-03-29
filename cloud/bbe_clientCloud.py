import boto3
import uuid

def create_bucket_name(bucket_prefix):
    return ''.join([bucket_prefix, str(uuid.uuid4())])

def create_bucket(bucket_prefix, s3_connection):
    session = boto3.session.Session()
    current_region = session.region_name
    bucket_name = create_bucket_name(bucket_prefix)
    bucket_response = s3_connection.create_bucket(
        Bucket=bucket_name)
        # CreateBucketConfiguration={
        #     'LocationConstraint': 'us-east-1'})
    print(bucket_name)
    return bucket_name

if __name__ == "__main__":
    sqs = boto3.resource('sqs')
    s3_resource = boto3.resource('s3')

    queue = sqs.get_queue_by_name(QueueName='bbeQueue')

    print("______       ______       ______\n"+
           "| ___ \      | ___ \      |  ___|\n"+
           "| |_/ /      | |_/ /      | |__\n"+
           "| ___ \      | ___ \      |  __|\n"+
           "| |_/ /      | |_/ /      | |___\n"+
           "\____/ristol \____/etting \____/xchange\n")

    BBE_name   = input('Enter a name for the BBE instance:')
    Race_name  = input('Enter a name for the race:')
    while True:
        DistanceString   = input('Enter a distance in metres:')
        try:
            Distance = float(DistanceString)
            break
        except ValueError:
            print("Please enter a valid distance:")
    while True:
        NumHorsesString  = input('Enter a number of horses:') 
        try:
            NumHorses = int(NumHorsesString)
            break
        except ValueError:
            print("Please enter a valid number:")
    while True:
        NumBettorsString = input('Enter a number of bettors:')
        try:
            NumBettors = int(NumBettorsString)
            break
        except ValueError:
            print("Please enter a valid number:")
    while True:
        bbeSimsString = input('Enter the amount of BBE simulations you would like to run:')
        try:
            bbeSims = int(bbeSimsString)
            break
        except ValueError:
            print("Please enter a valid number:")

    bbeBucketName = create_bucket(bucket_prefix='bbe-bucket', s3_connection=s3_resource.meta.client)

    for i in range(bbeSims):
        queue.send_message(
            MessageAttributes={
                'BbeName': {
                    'DataType': 'String',
                    'StringValue': '{0}_{1}'.format(BBE_name, i+1)
                },
                'RaceName': {
                    'DataType': 'String',
                    'StringValue': '{0}'.format(Race_name)
                },
                'RaceDistance': {
                    'DataType': 'Number',
                    'StringValue': '%d'% Distance
                },
                'NumHorses': {
                    'DataType': 'Number',
                    'StringValue': '%d'% NumHorses
                },
                'NumBettors': {
                    'DataType': 'Number',
                    'StringValue': '%d'% NumBettors
                },
                'BbeBucket': {
                    'DataType': 'String',
                    'StringValue': '{0}'.format(bbeBucketName)
                },
                'TotalSims': {
                    'DataType': 'Number',
                    'StringValue': '%d'% bbeSims
                }
            },
            MessageBody=(
                'BBE instance {0} to be completed. Upload to bucket {1}'.format(i+1, bbeBucketName)
            )
        )
    print("Upload of BBE Simulation to AWS complete. Please download the graphs from the S3 bucket generated for results!")