import boto3
import json
import os
import traceback


def get_ssm_parameter(ssm_client, parameter_name):
    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=False)
        return response["Parameter"]["Value"].split(",")
    except Exception as e:
        traceback.print_exc()
        print(f"Error fetching SSM parameter {parameter_name}: {e}")
        raise


def get_vpc_ids(ec2_client):
    try:
        response = ec2_client.describe_vpcs()
        return [vpc["VpcId"] for vpc in response["Vpcs"]]
    except Exception as e:
        print(f"Error fetching VPCs: {e}")
        raise


def get_nacl_ids(ec2_client, vpc_id):
    try:
        response = ec2_client.describe_network_acls(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        return [nacl["NetworkAclId"] for nacl in response["NetworkAcls"]]
    except Exception as e:
        print(f"Error fetching NACLs for VPC {vpc_id}: {e}")
        raise


def find_available_rule_number(existing_rule_numbers, rule_number=100):
    while rule_number in existing_rule_numbers and rule_number <= 32766:
        rule_number += 1

    if rule_number > 32766:
        print("No available slot for rule_number")
        return None

    return rule_number


def transform_to_cidr(ip_list):
    return [ip if "/" in ip else f"{ip}/32" for ip in ip_list]

def update_nacls(ec2_client, nacl_ids, ip_block_list):
    for nacl_id in nacl_ids:
        try:
            response = ec2_client.describe_network_acls(NetworkAclIds=[nacl_id])
            nacl = response["NetworkAcls"][0]

            existing_rule_numbers = {
                entry["RuleNumber"]
                for entry in nacl["Entries"]
                if entry["Egress"] is False
            }

            # Find the first available rule_number
            rule_number = find_available_rule_number(
                existing_rule_numbers=existing_rule_numbers
            )
            if rule_number is None:
                continue

            existing_rules = [
                entry
                for entry in nacl["Entries"]
                if entry.get("CidrBlock") in ip_block_list
                and entry.get("RuleAction") == "deny"
                and not entry["Egress"]
            ]

            for existing_rule in existing_rules:
                # If a rule for the same IP already exists, skip deletion and recreation
                ip = existing_rule.get("CidrBlock")
                if ip in ip_block_list:
                    ip_block_list.remove(ip)


            for ip in ip_block_list:
                ec2_client.create_network_acl_entry(
                    NetworkAclId=nacl_id,
                    RuleNumber=rule_number,
                    Protocol="-1",
                    RuleAction="deny",
                    Egress=False,
                    CidrBlock=ip,
                )
                rule_number = find_available_rule_number(
                    rule_number=rule_number + 1,
                    existing_rule_numbers=existing_rule_numbers,
                )
                if rule_number is None:
                    break  # Exit the loop if there are no available slots
        except Exception as e:
            print(f"Error updating NACL {nacl_id}: {e}")
            raise

def lambda_handler(event, context):
    ssm_param_name = os.environ.get("IP_BLOCK_LIST", "IP_BLOCK_LIST")
    ssm_client = boto3.client("ssm")
    ec2_client = boto3.client("ec2")

    try:
        ip_block_list = get_ssm_parameter(ssm_client, ssm_param_name)
        vpc_ids = get_vpc_ids(ec2_client)

        for vpc_id in vpc_ids:
            nacl_ids = get_nacl_ids(ec2_client, vpc_id)
            transformed_ip_block_list = transform_to_cidr(ip_block_list)
            update_nacls(ec2_client, nacl_ids, transformed_ip_block_list)

        return {"statusCode": 200, "body": json.dumps("NACLs updated successfully")}
    except Exception as e:
        print(f"Lambda execution failed: {e}")
        return {"statusCode": 500, "body": json.dumps("Internal Server Error")}


# Example usage
lambda_handler({}, {})
