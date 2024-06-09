import urllib.request, urllib.parse, urllib.error
import boto3
import ast
import json
import logging
print('Loading function')

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    s3 = boto3.client('s3')
    sns_message = ast.literal_eval(event['Records'][0]['Sns']['Message'])
    # print(sns_message) #- uncomment to debug
    target_bucket = context.function_name
    target_key = 'example.com/dataSources/fastlyjson/'
    source_bucket = str(sns_message['Records'][0]['s3']['bucket']['name'])
    key = str(urllib.parse.unquote_plus(sns_message['Records'][0]['s3']['object']['key']))
    # print(key) #-uncomment to debug
    copy_source = {'Bucket':source_bucket, 'Key':key}
    destinaion =  {'Bucket':target_bucket, 'Key': target_key}
    #print(copy_source) #-uncomment to debug
    print("Copying %s from bucket %s to bucket %s ..." % (key, source_bucket, target_bucket))
    #s3.copy_object(Bucket=target_bucket+'/'+target_key, Key=key, CopySource=copy_source)
    s3.copy_object(Bucket=target_bucket, Key=target_key + key, CopySource=copy_source)
    
    return {
        'statusCode': 200,
        'body': json.dumps('File has been Successfully Copied')
    }