# This script retrieves and prints a list of all EC2 instances and SSM managed instances. 
# It then prints a list of EC2 instances that are not managed by SSM.
import boto3
from botocore.exceptions import NoCredentialsError, BotoCoreError

def get_ec2_instances():
    try:
        return [i['InstanceId'] for r in boto3.client('ec2').describe_instances()['Reservations'] for i in r['Instances']]
    except (NoCredentialsError, BotoCoreError) as e:
        print(f"Failed to get EC2 instances: {e}")
        return []

def get_ssm_instances():
    try:
        return [i['InstanceId'] for i in boto3.client('ssm').describe_instance_information()['InstanceInformationList']]
    except (NoCredentialsError, BotoCoreError) as e:
        print(f"Failed to get SSM instances: {e}")
        return []

ec2_instances = get_ec2_instances()
ssm_instances = get_ssm_instances()

print('EC2 instances:')
print(ec2_instances)

print('SSM managed instances:')
print(ssm_instances)

print('Unmanaged EC2 instances:')
print(set(ec2_instances) - set(ssm_instances))