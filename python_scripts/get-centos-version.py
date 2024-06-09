# Get's the list of all EC2 instances in the AWS account and retrieves the CentOS version of each instance using the AWS Systems Manager (SSM) service.

import time
import boto3
import xlsxwriter
from botocore.exceptions import ClientError

# Create an EC2 client
ec2_client = boto3.client("ec2", region_name="us-east-1")
ssm_client = boto3.client("ssm", region_name="us-east-1")
# Get a list of instance IDs in your AWS account
response = ec2_client.describe_instances()
instances = response["Reservations"]
# Create a new Excel workbook and add a worksheet
workbook = xlsxwriter.Workbook("centos_versions.xlsx")
worksheet = workbook.add_worksheet()
# Write headers to the worksheet
worksheet.write("A1", "Instance ID")
worksheet.write("B1", "CentOS Version")


# Retry decorator for handling InvocationDoesNotExist error
def retry_on_invocation_does_not_exist(max_retries=3, delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if e.response["Error"]["Code"] == "InvocationDoesNotExist":
                        if i == max_retries - 1:
                            raise
                        else:
                            time.sleep(delay)
                    else:
                        raise

        return wrapper

    return decorator


# Function to retrieve CentOS version using SSM command
@retry_on_invocation_does_not_exist()
def get_centos_version(instance_id):
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["cat /etc/centos-release"]},
        )
        return response["Command"]["CommandId"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceId":
            return "Instance not available"
        else:
            raise


# Iterate over each instance
row = 2
for reservation in instances:
    for instance in reservation["Instances"]:
        instance_id = instance["InstanceId"]
        command_id = get_centos_version(instance_id)
        # Get command output if instance is available
        if command_id != "Instance not available":
            output = ""
            while True:
                time.sleep(2)
                response = ssm_client.get_command_invocation(
                    CommandId=command_id, InstanceId=instance_id
                )
                if response["Status"] in ["InProgress", "Delayed"]:
                    time.sleep(2)
                elif response["Status"] == "Success":
                    output += response["StandardOutputContent"]
                    if "NextToken" not in response:
                        break
                else:
                    output = response["StandardErrorContent"]
                    break
            centos_version = output.strip().split("\n")[0] if output else "N/A"
        else:
            centos_version = command_id
        # Write the instance ID and CentOS version to the worksheet
        worksheet.write(f"A{row}", instance_id)
        worksheet.write(f"B{row}", centos_version)
        row += 1
# Close the workbook
workbook.close()
print("CentOS versions exported to centos_versions.xlsx")
