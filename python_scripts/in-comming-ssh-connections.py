# This script checks all AWS security groups for incoming SSH connections and exports the results to an Excel file.
import boto3
import pandas as pd # `pip install pandas` if not installed

def get_all_security_groups():
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_regions()
    all_security_groups = []
    for region in response['Regions']:
        region_name = region['RegionName']
        ec2 = boto3.resource('ec2', region_name=region_name)
        security_groups = list(ec2.security_groups.all())
        all_security_groups.extend(security_groups)
    return all_security_groups
def check_ssh_connections(security_group, results):
    region = security_group.meta.client.meta.region_name
    for rule in security_group.ip_permissions:
        if rule['IpProtocol'] == 'tcp' and rule['FromPort'] <= 22 <= rule['ToPort']:
            for ip_range in rule['IpRanges']:
                result = {
                    'Security Group ID': security_group.group_id,
                    'Security Group Name': security_group.group_name,
                    'Region': region,
                    'Protocol': rule['IpProtocol'],
                    'Port Range': f"{rule['FromPort']}-{rule['ToPort']}",
                    'CIDR IP Range': ip_range['CidrIp']
                }
                results.append(result)
def export_to_excel(results):
    df = pd.DataFrame(results)
    writer = pd.ExcelWriter('ssh_ingress_connections.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='SSH Ingress Connections', index=False)
    writer.save()
def main():
    all_security_groups = get_all_security_groups()
    results = []
    for security_group in all_security_groups:
        check_ssh_connections(security_group, results)
    export_to_excel(results)

if __name__ == '__main__':
    main()














