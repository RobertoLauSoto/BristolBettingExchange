import boto3

sqs = boto3.resource('sqs')

# Create the work queue. This returns an SQS.Queue instance
bbeQueue = sqs.create_queue(QueueName='bbeQueue')

