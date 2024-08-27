import json
import boto3
import logging
import sys
import requests
from keys import access, secret

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = boto3.Session(
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    region_name='ap-southeast-5'
)

# Initialize boto3 clients
ecs_client = session.client('ecs')
elbv2_client = session.client('elbv2')

def load_deployment_info(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Deployment info file not found.")
        exit(1)
    except json.JSONDecodeError:
        logger.error("Deployment info file is not a valid JSON.")
        exit(1)

def delete_ecs_service(cluster, service):
    try:
        ecs_client.delete_service(cluster=cluster, service=service, force=True)
        logger.info(f"ECS service '{service}' deleted successfully.")
    except Exception as e:
        logger.error(f"Error during ECS service deletion: {e}")

def deregister_task_definition(task_definition_arn):
    try:
        ecs_client.deregister_task_definition(taskDefinition=task_definition_arn)
        logger.info(f"Task definition '{task_definition_arn}' deregistered successfully.")
    except Exception as e:
        logger.error(f"Error during task definition deregistration: {e}")

def delete_target_group(target_group_arn):
    try:
        elbv2_client.delete_target_group(TargetGroupArn=target_group_arn)
        logger.info(f"Target group '{target_group_arn}' deleted successfully.")
    except Exception as e:
        logger.error(f"Error during target group deletion: {e}")

def delete_alb_rules(rules_list):
    for rule_arn in rules_list:
        try:
            elbv2_client.delete_rule(RuleArn=rule_arn)
            logger.info(f"ALB rule '{rule_arn}' deleted successfully.")
        except elbv2_client.exceptions.ClientError as e:
            if 'OperationNotPermitted' in str(e):
                logger.warning(f"Default rule '{rule_arn}' cannot be deleted.")
            else:
                logger.error(f"Error during ALB rule deletion: {e}")

def delete_cname_record_cloudflare(api_token, zone_id, domain_name):
    try:
        # Get the DNS record ID
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=CNAME&name={domain_name}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        records = response.json().get('result', [])
        if not records:
            logger.warning(f"No CNAME record found for {domain_name}.")
            return

        record_id = records[0]['id']

        # Delete the DNS record
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        logger.info(f"CNAME record for {domain_name} deleted successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting CNAME record: {e}")

def main():
    if len(sys.argv) != 2:
        logger.error("Usage: python rollback.py <deployment_info_file>")
        exit(1)

    deployment_info_file = sys.argv[1]
    deployment_info = load_deployment_info(deployment_info_file)

    ecs_cluster = deployment_info.get('ecs_cluster')
    service_name = deployment_info.get('service_name')
    task_definition_arn = deployment_info.get('task_definition_arn')
    target_group_arn = deployment_info.get('target_group_arn')
    rules_list = deployment_info.get('rules', [])
    domain_name = deployment_info.get('domain_name')
    cloudflare_api_token = deployment_info.get('cloudflare_api_token')
    cloudflare_zone_id = deployment_info.get('cloudflare_zone_id')

    if not all([ecs_cluster, service_name, task_definition_arn, target_group_arn, rules_list is not None, domain_name, cloudflare_api_token, cloudflare_zone_id]):
        logger.error("Missing required deployment information.")
        exit(1)

    delete_ecs_service(ecs_cluster, service_name)
    deregister_task_definition(task_definition_arn)
    delete_alb_rules(rules_list)
    delete_target_group(target_group_arn)
    delete_cname_record_cloudflare(cloudflare_api_token, cloudflare_zone_id, domain_name)

    logger.info("Rollback completed.")

if __name__ == "__main__":
    main()