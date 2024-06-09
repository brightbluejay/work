# This file is a script that retrieves a list of all Lambda functions 
# in the eu-west-1 region that are using the Node.js 16.x runtime.
import boto3
import csv
import os


def get_account_alias(session):
    iam_client = session.client("iam")
    aliases = iam_client.list_account_aliases()["AccountAliases"]
    return aliases[0] if aliases else "No alias found"


def list_nodejs16_lambdas(session):
    lambda_client = session.client("lambda", region_name="eu-west-1")
    paginator = lambda_client.get_paginator("list_functions")
    nodejs16_lambdas = []
    for page in paginator.paginate():
        for function in page["Functions"]:
            if function.get("Runtime") == "nodejs16.x":
                nodejs16_lambdas.append(function["FunctionArn"])
    return nodejs16_lambdas


def append_to_csv(account_id, account_alias, nodejs16_lambdas):
    # Check if file exists to write headers only once
    file_exists = os.path.isfile("lambda_list.csv")
    with open("lambda_list.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(
                ["AWS ACCOUNT", "ACCOUNT ALIAS", "List of Nodejs16.x Lambdas"]
            )
        for lambda_arn in nodejs16_lambdas:
            writer.writerow([account_id, account_alias, lambda_arn])


def main():
    session = boto3.Session()
    account_id = session.client("sts").get_caller_identity().get("Account")
    account_alias = get_account_alias(session)
    nodejs16_lambdas = list_nodejs16_lambdas(session)
    append_to_csv(account_id, account_alias, nodejs16_lambdas)


if __name__ == "__main__":
    main()
