# Resolves 'A' record of a domain using dns.resolver, formats the IP to CIDR notation.
# Utilizes boto3 for potential AWS EC2 interactions and logging for event tracking.
# Current date is fetched in 'dd.mm.yyyy' format and a list 'NewEntries' is created but not used in this excerpt.

import logging
from http import client
from urllib import response
import boto3
import dns.resolver
from datetime import datetime

logger = logging.getlogger()

client = boto3.client('ec2')
todays_date = datetime.today().strftime('%d.%m.%Y')
answers = dns.resolver.resolve('collectors.eu.sumologic.com', 'A')
NewEntries = []
for rdata in answers:
    cidr_address = rdata.address +'/32'
    NewEntries.append({'Cidr': cidr_address, 'Description': 'Sumologic '+ todays_date})
print(NewEntries)

# Get the details of the prefix list
response = client.describe_managed_prefix_lists(
    PrefixListIds=['<your-prefix-list-id>']
)

# Extract the current version
current_version = response['PrefixLists'][0]['Version']

# Now use current_version in your modify_managed_prefix_list call
response = client.modify_managed_prefix_list(
    PrefixListId='<your-prefix-list-id>',
    CurrentVersion=current_version,
    PrefixListName='sumologic_ip_range',
    AddEntries=NewEntries,
    MaxEntries=15
)