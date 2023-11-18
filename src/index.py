import boto3
import json
import os


def lambda_handler(event, context):
    # Step 1: Fetch SSM parameter named IP_BLOCK_LIST of type StringList
    ssm_param_name = os.environ.get("IP_BLOCK_LIST_SSM_NAME", "IP_BLOCK_LIST")
    ssm_client = boto3.client("ssm")

    try:
        response = ssm_client.get_parameter(Name=ssm_param_name, WithDecryption=False)
        ip_block_list = json.loads(response["Parameter"]["Value"])
    except Exception as e:
        print(f"Error fetching SSM parameter: {e}")
        return {"statusCode": 500, "body": json.dumps("Error fetching SSM parameter")}

    # Step 2: Fetch all VPCs in the current region
    ec2_client = boto3.client("ec2")

    try:
        response = ec2_client.describe_vpcs()
        vpcs = response["Vpcs"]
    except Exception as e:
        print(f"Error fetching VPCs: {e}")
        return {"statusCode": 500, "body": json.dumps("Error fetching VPCs")}

    # Step 3: Fetch all NACL IDs associated with VPCs
    nacl_ids = []
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        try:
            response = ec2_client.describe_network_acls(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
            )
            nacls = response["NetworkAcls"]
            nacl_ids.extend([nacl["NetworkAclId"] for nacl in nacls])
        except Exception as e:
            print(f"Error fetching NACLs for VPC {vpc_id}: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error fetching NACLs for VPC {vpc_id}"),
            }

    # Step 4: Update each NACL with a deny rule for IP_BLOCK_LIST
    for nacl_id in nacl_ids:
        try:
            response = ec2_client.describe_network_acls(NetworkAclIds=[nacl_id])
            nacl = response["NetworkAcls"][0]
            rule_number = (
                max([entry["RuleNumber"] for entry in nacl["Entries"]], default=0) + 1
            )

            # Check if a rule with the same source IP and deny rule already exists
            existing_rules = [
                entry
                for entry in nacl["Entries"]
                if entry.get("CidrBlock") in ip_block_list
                and entry.get("RuleAction") == "deny"
            ]
            if not existing_rules:
                # Add a deny rule for each IP in the block list
                for ip in ip_block_list:
                    nacl["Entries"].append(
                        {
                            "CidrBlock": ip,
                            "RuleNumber": rule_number,
                            "Protocol": "-1",
                            "RuleAction": "deny",
                        }
                    )
                    rule_number += 1

                # Update the NACL with the modified entries
                ec2_client.replace_network_acl_entries(
                    NetworkAclId=nacl_id, Entries=nacl["Entries"]
                )
        except Exception as e:
            print(f"Error updating NACL {nacl_id}: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error updating NACL {nacl_id}"),
            }

    return {"statusCode": 200, "body": json.dumps("NACLs updated successfully")}
