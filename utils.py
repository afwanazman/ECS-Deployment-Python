import boto3
import os
import json
import logging
from config import aws_region, access, secret, vpc_id, project_name, log_group, ecs_cluster, container_name, task_family_name, repo_uri, image_tag, task_role_arn, execution_role_arn, subnets, security_groups, domain_name, cloudflare_api_token, cloudflare_zone_id, alb_dns_name

# Configure logging
logger = logging.getLogger(__name__)

session = boto3.Session(
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    region_name=aws_region
)
ecs_client = session.client('ecs')
elbv2_client = session.client('elbv2')
logs_client = session.client('logs')

def create_log_group(log_group):
    try:
        log_groups = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
        if not any(group['logGroupName'] == log_group for group in log_groups['logGroups']):
            logs_client.create_log_group(logGroupName=log_group)
            logger.info(f"Log group '{log_group}' created successfully.")
            logs_client.put_retention_policy(
                logGroupName=log_group,
                retentionInDays=7
            )
            logger.info(f"Retention policy set to 7 days for log group '{log_group}'.")
        else:
            logger.info(f"Log group '{log_group}' already exists.")
    except Exception as e:
        logger.error(f"Error checking/creating log group: {e}")

def create_target_group():
    try:
        response = elbv2_client.create_target_group(
            Name=project_name,
            Protocol='HTTPS',
            Port=443,
            VpcId=vpc_id,
            TargetType='ip',
            HealthCheckProtocol='HTTPS',
            HealthCheckPort='traffic-port',
            HealthCheckPath='/hc',
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=3,
            UnhealthyThresholdCount=3,
            Matcher={'HttpCode': '200-499'}
        )
        target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
        elbv2_client.modify_target_group_attributes(
            TargetGroupArn=target_group_arn,
            Attributes=[
                {'Key': 'stickiness.enabled', 'Value': 'true'},
                {'Key': 'stickiness.lb_cookie.duration_seconds', 'Value': '3600'}
            ]
        )
        logger.info(f"Target group '{project_name}' created successfully.")
        return target_group_arn
    except Exception as e:
        logger.error(f"Error creating target group: {e}")
        return None

def get_next_priority(listener_arn):
    try:
        response = elbv2_client.describe_rules(ListenerArn=listener_arn)
        priorities = [int(rule['Priority']) for rule in response['Rules'] if rule['Priority'].isdigit()]
        next_priority = max(priorities, default=99) + 1
        logger.info(f"Next priority determined: {next_priority}")
        return next_priority
    except Exception as e:
        logger.error(f"Error getting next priority: {e}")
        return 100

def create_rule(listener_arn, target_group_arn, domain_name, rules_list):
    try:
        priority = get_next_priority(listener_arn)
        response = elbv2_client.create_rule(
            ListenerArn=listener_arn,
            Conditions=[{'Field': 'host-header', 'HostHeaderConfig': {'Values': [domain_name]}}],
            Actions=[{'Type': 'forward', 'TargetGroupArn': target_group_arn}],
            Priority=priority
        )
        rule_arn = response['Rules'][0]['RuleArn']
        elbv2_client.add_tags(
            ResourceArns=[rule_arn],
            Tags=[{'Key': 'Name', 'Value': domain_name}]
        )
        logger.info(f"Rule created successfully with ARN: {rule_arn}")
        rules_list.append(rule_arn)
    except Exception as e:
        logger.error(f"Error creating rule: {e}")

def register_task_definition():
    try:
        response = ecs_client.register_task_definition(
            family=task_family_name,
            networkMode='awsvpc',
            containerDefinitions=[{
                'name': container_name,
                'image': f'{repo_uri}:{image_tag}',
                'cpu': 0,
                'portMappings': [{'containerPort': 443, 'hostPort': 443, 'protocol': 'tcp'}],
                'essential': True,
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': log_group,
                        'awslogs-region': aws_region,
                        'awslogs-stream-prefix': 'ecs'
                    }
                },
                'healthCheck': {
                    'command': ['CMD-SHELL', 'curl -fk https://localhost/ || exit 1'],
                    'interval': 30,
                    'timeout': 5,
                    'retries': 3,
                    'startPeriod': 60
                }
            }],
            enableExecuteCommand=true,
            taskRoleArn=task_role_arn,
            executionRoleArn=execution_role_arn,
            requiresCompatibilities=['FARGATE'],
            cpu='256',
            memory='2048',
            runtimePlatform={'cpuArchitecture': 'X86_64', 'operatingSystemFamily': 'LINUX'},
            tags=[
                {'key': 'Role', 'value': 'application'},
                {'key': 'Project', 'value': project_name},
                {'key': 'Environment', 'value': 'production'}
            ]
        )
        task_definition_arn = response['taskDefinition']['taskDefinitionArn']
        logger.info(f"Task definition registered successfully with ARN: {task_definition_arn}")
        return task_definition_arn
    except Exception as e:
        logger.error(f"Error registering task definition: {e}")
        return None

def create_ecs_service(task_definition_arn, target_group_arn):
    try:
        ecs_client.create_service(
            cluster=ecs_cluster,
            serviceName=project_name,
            taskDefinition=task_definition_arn,
            loadBalancers=[{'targetGroupArn': target_group_arn, 'containerName': container_name, 'containerPort': 443}],
            desiredCount=1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnets,
                    'securityGroups': security_groups,
                    'assignPublicIp': 'DISABLED'
                }
            }
        )
        logger.info(f"ECS service '{project_name}' created successfully.")
    except Exception as e:
        logger.error(f"Error creating ECS service: {e}")

def create_cname_record_cloudflare(api_token, zone_id, domain_name, target):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "CNAME",
        "name": domain_name,
        "content": target,
        "ttl": 300,
        "proxied": False
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"CNAME record created successfully for {domain_name} pointing to {target}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating CNAME record: {e}")
        
def save_deployment_info(task_definition_arn, target_group_arn, listener_arn, rules_list, timestamp):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        deployments_dir = os.path.join(script_dir, 'deployments')
        os.makedirs(deployments_dir, exist_ok=True)
        file_name = os.path.join(deployments_dir, f'deployment_info_{project_name}_{timestamp}.json')
        
        with open(file_name, 'w') as f:
            json.dump({
                'ecs_cluster': ecs_cluster,
                'service_name': project_name,
                'task_definition_arn': task_definition_arn,
                'target_group_arn': target_group_arn,
                'listener_arn': listener_arn,
                'rules': rules_list,
                'domain_name': domain_name,
                'cloudflare_api_token': cloudflare_api_token,
                'cloudflare_zone_id': cloudflare_zone_id,
                'alb_dns_name': alb_dns_name
            }, f)
        logger.info(f"Deployment information saved to {file_name}")
    except Exception as e:
        logger.error(f"Error saving deployment information: {e}")