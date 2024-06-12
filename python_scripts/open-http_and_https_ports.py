#Script to find all open ports to the world in all regions in AWS
import boto3
import pandas as pd
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
def check_ingress_connections(security_group, results):
    region = security_group.meta.client.meta.region_name
    for rule in security_group.ip_permissions:
        for ip_range in rule['IpRanges']:
            if ip_range['CidrIp'] == '0.0.0.0/0':
                result = {
                    'Security Group': security_group.group_name,
                    #'Description': description,
                    'Region': region,
                    'Protocol': rule['IpProtocol'],
                    'Port Range': f"{rule['FromPort']}-{rule['ToPort']}"
                }
                results.append(result)
def export_to_excel(results):
    df = pd.DataFrame(results)
    writer = pd.ExcelWriter('security_group_ingress_connections.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Ingress Connections', index=False)
    writer.close()
def main():
    security_groups = get_all_security_groups()
    results = []
    for sg in security_groups:
        check_ingress_connections(sg, results)
    export_to_excel(results)
if __name__ == '__main__':
    main()
